"""
ASTRA Bot
==========
The ongoing Discord bot for the ASTRA server. Run this continuously.

Features:
  - /task commands  — GitHub Projects sprint board
  - /sprint commands — sprint management
  - /incident command — structured incident reporting
  - Auto-thread creation in #active-incidents
  - Daily digest at 9AM CDT in #daily-status-updates
  - GitHub PR polling every 5 minutes → #pull-request-reviews

Usage:
    pip install -r requirements.txt
    export DISCORD_BOT_TOKEN=your_discord_token
    export GITHUB_TOKEN=your_github_classic_token
    python astra_bot.py
"""

import discord
from discord import app_commands
from discord.ext import tasks
import os
import json
import re
import datetime
import pytz
import httpx
import asyncio
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN  = os.environ.get("DISCORD_BOT_TOKEN", "")
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO    = "aaryan778/ASTRA"
GITHUB_OWNER   = "aaryan778"
CDT            = pytz.timezone("America/Chicago")

# Persistent state file (stores incident counter, last seen PR, project ID)
STATE_FILE = Path(__file__).parent / "astra_state.json"


# ─── STATE MANAGEMENT ─────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "incident_counter": 0,
        "last_pr_id": 0,
        "github_project_id": None,
        "github_project_number": None,
        "sprint_name": None,
        "sprint_fields": {},   # field_id -> {name, options: {name: option_id}}
    }


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def next_incident_id(state: dict) -> str:
    state["incident_counter"] += 1
    save_state(state)
    return f"INC-{state['incident_counter']:03d}"


# ─── GITHUB API ───────────────────────────────────────────────────────────────
GH_REST    = "https://api.github.com"
GH_GRAPHQL = "https://api.github.com/graphql"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def gh_rest(method: str, path: str, **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method, f"{GH_REST}{path}",
            headers=GH_HEADERS, timeout=30, **kwargs
        )
        return resp.json()


async def gh_graphql(query: str, variables: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GH_GRAPHQL,
            headers={**GH_HEADERS, "Accept": "application/json"},
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        return resp.json()


# ── GitHub Projects v2 helpers ─────────────────────────────────────────────

async def get_owner_node_id() -> str:
    data = await gh_graphql('{ user(login: "%s") { id } }' % GITHUB_OWNER)
    return data["data"]["user"]["id"]


async def create_github_project(title: str) -> dict:
    owner_id = await get_owner_node_id()
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 { id number url }
      }
    }
    """
    data = await gh_graphql(mutation, {"ownerId": owner_id, "title": title})
    return data["data"]["createProjectV2"]["projectV2"]


async def get_project_fields(project_id: str) -> dict:
    """Returns {field_name: {id, options: {option_name: option_id}}}"""
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field { id name }
              ... on ProjectV2SingleSelectField {
                id name
                options { id name }
              }
            }
          }
        }
      }
    }
    """
    data = await gh_graphql(query, {"projectId": project_id})
    fields = {}
    for node in data["data"]["node"]["fields"]["nodes"]:
        if not node:
            continue
        name = node.get("name", "")
        entry = {"id": node["id"]}
        if "options" in node:
            entry["options"] = {opt["name"]: opt["id"] for opt in node["options"]}
        fields[name] = entry
    return fields


async def add_issue_to_project(project_id: str, issue_node_id: str) -> str:
    """Returns the project item ID."""
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    data = await gh_graphql(mutation, {
        "projectId": project_id,
        "contentId": issue_node_id,
    })
    return data["data"]["addProjectV2ItemById"]["item"]["id"]


async def update_project_item_status(
    project_id: str, item_id: str, field_id: str, option_id: str
):
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId
        itemId: $itemId
        fieldId: $fieldId
        value: { singleSelectOptionId: $optionId }
      }) { projectV2Item { id } }
    }
    """
    await gh_graphql(mutation, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": field_id,
        "optionId": option_id,
    })


async def create_github_issue(
    title: str,
    body: str,
    assignees: list[str] = None,
    labels: list[str] = None,
) -> dict:
    payload = {"title": title, "body": body}
    if assignees:
        payload["assignees"] = assignees
    if labels:
        payload["labels"] = labels
    return await gh_rest("POST", f"/repos/{GITHUB_REPO}/issues", json=payload)


async def close_github_issue(issue_number: int):
    await gh_rest(
        "PATCH", f"/repos/{GITHUB_REPO}/issues/{issue_number}",
        json={"state": "closed"}
    )


async def get_open_issues() -> list:
    return await gh_rest("GET", f"/repos/{GITHUB_REPO}/issues?state=open&per_page=50")


async def get_open_prs() -> list:
    return await gh_rest("GET", f"/repos/{GITHUB_REPO}/pulls?state=open&per_page=20")


async def ensure_label_exists(label: str):
    """Create label if it doesn't exist yet."""
    label_colors = {
        "ai-engine": "9b59b6",  "observability": "e67e22",
        "backend":   "3498db",  "frontend":      "2ecc71",
        "devops":    "e74c3c",  "simulation":    "f39c12",
        "incident":  "e74c3c",  "research":      "1abc9c",
        "bug":       "d73a4a",  "urgent":        "e74c3c",
        "blocked":   "cccccc",
    }
    color = label_colors.get(label, "ededed")
    existing = await gh_rest("GET", f"/repos/{GITHUB_REPO}/labels")
    names = [l["name"] for l in existing] if isinstance(existing, list) else []
    if label not in names:
        await gh_rest(
            "POST", f"/repos/{GITHUB_REPO}/labels",
            json={"name": label, "color": color}
        )


# ─── SEVERITY DETECTION ───────────────────────────────────────────────────────
SEVERITY_KEYWORDS = {
    "CRITICAL": ["down", "outage", "crash", "crashed", "unresponsive", "failed",
                 "unreachable", "critical", "offline", "killed", "oom"],
    "WARNING":  ["slow", "degraded", "latency", "warning", "high memory",
                 "high cpu", "unstable", "intermittent", "timeout"],
    "INFO":     ["notice", "monitoring", "watching", "investigating", "update",
                 "info", "fyi", "heads up"],
}
SEVERITY_EMOJI = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}


def detect_severity(text: str) -> str:
    text_lower = text.lower()
    for sev, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return sev
    return "WARNING"


def incident_thread_name(inc_id: str, severity: str, title: str) -> str:
    emoji = SEVERITY_EMOJI[severity]
    now   = datetime.datetime.now(pytz.utc)
    ts    = now.strftime("%b %-d %H:%M UTC")
    short = title[:50] + ("..." if len(title) > 50 else "")
    return f"{inc_id} {emoji} {severity} | {short} — {ts}"


# ─── BOT SETUP ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot   = discord.Client(intents=intents)
tree  = app_commands.CommandTree(bot)
state = load_state()


def get_channel(guild: discord.Guild, name: str) -> discord.TextChannel | None:
    return discord.utils.get(guild.text_channels, name=name)


async def ensure_project(guild: discord.Guild):
    """Create the GitHub Project board if it doesn't exist yet."""
    if state.get("github_project_id"):
        return
    ch = get_channel(guild, "sprint-board")
    project = await create_github_project("ASTRA Sprint Board")
    state["github_project_id"]     = project["id"]
    state["github_project_number"] = project["number"]
    fields = await get_project_fields(project["id"])
    state["sprint_fields"] = {k: v for k, v in fields.items()}
    save_state(state)
    if ch:
        await ch.send(
            f"✅ **ASTRA Sprint Board created on GitHub Projects**\n"
            f"Board: {project['url']}\n"
            f"All `/task` commands will sync to this board automatically."
        )


# ─── DAILY DIGEST ─────────────────────────────────────────────────────────────
@tasks.loop(time=datetime.time(hour=9, minute=0,
                               tzinfo=pytz.timezone("America/Chicago")))
async def daily_digest():
    for guild in bot.guilds:
        ch = get_channel(guild, "daily-status-updates")
        if not ch:
            continue

        issues = await get_open_issues()
        prs    = await get_open_prs()

        # Count by status label
        in_progress = [i for i in issues if any(
            l["name"] == "in-progress" for l in i.get("labels", []))]
        backlog     = [i for i in issues if not any(
            l["name"] in ("in-progress", "in-review", "done")
            for l in i.get("labels", []))]
        in_review   = [i for i in issues if any(
            l["name"] == "in-review" for l in i.get("labels", []))]

        now  = datetime.datetime.now(CDT)
        date = now.strftime("%A, %B %-d")

        lines = [f"📋 **ASTRA Daily Digest — {date}**\n"]

        lines.append("**OPEN TASKS**")
        if in_progress:
            lines.append(f"  In Progress → {len(in_progress)} tasks")
            for i in in_progress[:5]:
                assignees = ", ".join(
                    a["login"] for a in i.get("assignees", [])
                ) or "unassigned"
                lines.append(f"    · {i['title'][:55]}  ({assignees})")
        lines.append(f"  Backlog   → {len(backlog)} tasks")
        lines.append(f"  In Review → {len(in_review)} tasks")

        lines.append("\n**PULL REQUESTS AWAITING REVIEW**")
        if prs:
            for pr in prs[:5]:
                lines.append(f"  · PR #{pr['number']}: {pr['title'][:55]}")
        else:
            lines.append("  None open right now.")

        lines.append("\n───────────────────────────────")
        lines.append("Have a good one. — ASTRA Bot")

        await ch.send("\n".join(lines))


# ─── AUTO-THREAD FOR #active-incidents ────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.guild:
        return
    if message.channel.name != "active-incidents":
        return
    # Only create threads for plain messages (not system messages)
    if message.type != discord.MessageType.default:
        return

    severity  = detect_severity(message.content)
    inc_id    = next_incident_id(state)
    thread_name = incident_thread_name(inc_id, severity, message.content[:80])

    thread = await message.create_thread(
        name=thread_name,
        auto_archive_duration=10080,  # 7 days
    )
    emoji = SEVERITY_EMOJI[severity]
    await thread.send(
        f"{emoji} **{inc_id} — {severity}**\n\n"
        f"Incident opened by {message.author.mention}\n"
        f"Use this thread for all updates and investigation.\n\n"
        f"**Commands:**\n"
        f"`/incident update {inc_id} \"status message\"`\n"
        f"`/incident resolve {inc_id} \"resolution summary\"`\n"
        f"`/incident close {inc_id}`\n\n"
        f"Post updates chronologically as you investigate.\n"
        f"Tag Aaryan for approval before any infrastructure changes."
    )


# ─── /incident SLASH COMMAND ──────────────────────────────────────────────────
class IncidentModal(discord.ui.Modal, title="Open a New Incident"):
    inc_title   = discord.ui.TextInput(label="Title", max_length=100,
                    placeholder="e.g. EC2 instance i-0abc unresponsive")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph,
                    placeholder="What are you seeing? What already tried?")
    service     = discord.ui.TextInput(label="Service / Component", max_length=60,
                    placeholder="e.g. EC2, Ollama Server, RCA Engine, API")
    severity    = discord.ui.TextInput(label="Severity (CRITICAL / WARNING / INFO)",
                    max_length=10, default="CRITICAL")
    assigned_to = discord.ui.TextInput(label="Assign to (GitHub username, optional)",
                    required=False, placeholder="e.g. Bhargav")

    async def on_submit(self, interaction: discord.Interaction):
        sev     = self.severity.value.upper()
        if sev not in SEVERITY_EMOJI:
            sev = "CRITICAL"
        inc_id  = next_incident_id(state)
        emoji   = SEVERITY_EMOJI[sev]
        now     = datetime.datetime.now(pytz.utc)
        ts      = now.strftime("%b %-d %H:%M UTC")
        name    = f"{inc_id} {emoji} {sev} | {self.inc_title.value[:50]} — {ts}"

        ch = get_channel(interaction.guild, "active-incidents")
        if not ch:
            await interaction.response.send_message(
                "Could not find #active-incidents channel.", ephemeral=True)
            return

        msg = await ch.send(
            f"{emoji} **{inc_id} — {sev}**\n"
            f"**Service:** {self.service.value}\n"
            f"**Reported by:** {interaction.user.mention}\n"
            f"**Description:** {self.description.value}"
        )
        thread = await msg.create_thread(name=name, auto_archive_duration=10080)

        assignees = []
        if self.assigned_to.value.strip():
            assignees = [a.strip() for a in self.assigned_to.value.split(",")]

        # Create GitHub issue for the incident
        issue = await create_github_issue(
            title=f"[{inc_id}] {self.inc_title.value}",
            body=(
                f"**Severity:** {sev}\n"
                f"**Service:** {self.service.value}\n"
                f"**Reported by:** {interaction.user.display_name}\n\n"
                f"**Description:**\n{self.description.value}\n\n"
                f"**Discord Thread:** (link manually after creation)\n"
            ),
            assignees=assignees,
            labels=["incident"],
        )

        issue_url = issue.get("html_url", "")
        await thread.send(
            f"{emoji} **{inc_id} — {sev} | {self.inc_title.value}**\n\n"
            f"**Service:** {self.service.value}\n"
            f"**Assigned to:** {self.assigned_to.value or 'unassigned'}\n"
            f"**GitHub Issue:** {issue_url}\n\n"
            f"Post all updates here chronologically.\n"
            f"Aaryan must approve any infrastructure changes."
        )

        await interaction.response.send_message(
            f"✅ {inc_id} opened. Thread created in #active-incidents.\n{issue_url}",
            ephemeral=True
        )


@tree.command(name="incident", description="Open a new incident")
async def incident_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(IncidentModal())


# ─── /task COMMANDS ───────────────────────────────────────────────────────────
task_group = app_commands.Group(name="task", description="Sprint board task management")


@task_group.command(name="create", description="Create a new task on the sprint board")
@app_commands.describe(
    title="Task title",
    assign="GitHub username(s) comma-separated — e.g. Bhargav or Bhargav,Asif",
    priority="Priority: critical / high / medium / low",
    label="Label: ai-engine / backend / frontend / observability / devops / bug / urgent"
)
async def task_create(
    interaction: discord.Interaction,
    title: str,
    assign: str = "",
    priority: str = "medium",
    label: str = "",
):
    await interaction.response.defer()
    await ensure_project(interaction.guild)

    assignees = [a.strip() for a in assign.split(",") if a.strip()]
    labels    = [label.strip()] if label.strip() else []
    labels.append(priority.lower() if priority else "medium")

    # Ensure labels exist on GitHub
    for lbl in labels:
        await ensure_label_exists(lbl)

    body = (
        f"**Priority:** {priority}\n"
        f"**Assigned to:** {assign or 'unassigned'}\n"
        f"**Created via:** Discord #sprint-board\n"
        f"**Sprint:** {state.get('sprint_name', 'Backlog')}"
    )
    issue = await create_github_issue(title, body, assignees, labels)

    issue_num  = issue.get("number")
    issue_url  = issue.get("html_url", "")
    issue_node = issue.get("node_id", "")

    # Add to GitHub Project
    if state.get("github_project_id") and issue_node:
        await add_issue_to_project(state["github_project_id"], issue_node)

    await interaction.followup.send(
        f"✅ **Task #{issue_num} created**\n"
        f"**Title:** {title}\n"
        f"**Assigned:** {assign or 'unassigned'}\n"
        f"**Priority:** {priority}\n"
        f"**Label:** {label or '—'}\n"
        f"**Status:** Backlog\n"
        f"→ {issue_url}"
    )


@task_group.command(name="list", description="List open tasks")
@app_commands.describe(
    assign="Filter by GitHub username",
    label="Filter by label",
    status_filter="Filter by status label: in-progress / in-review / done"
)
async def task_list(
    interaction: discord.Interaction,
    assign: str = "",
    label: str = "",
    status_filter: str = "",
):
    await interaction.response.defer()
    issues = await get_open_issues()

    if assign:
        issues = [i for i in issues if any(
            a["login"].lower() == assign.lower()
            for a in i.get("assignees", []))]
    if label:
        issues = [i for i in issues if any(
            l["name"].lower() == label.lower()
            for l in i.get("labels", []))]
    if status_filter:
        issues = [i for i in issues if any(
            l["name"].lower() == status_filter.lower()
            for l in i.get("labels", []))]

    if not issues:
        await interaction.followup.send("No tasks found matching those filters.")
        return

    lines = [f"**Open Tasks** ({len(issues)} found)\n"]
    for i in issues[:20]:
        assignees = ", ".join(a["login"] for a in i.get("assignees", [])) or "—"
        labels    = " ".join(f"`{l['name']}`" for l in i.get("labels", []))
        lines.append(f"**#{i['number']}** {i['title'][:60]}")
        lines.append(f"  Assigned: {assignees}  {labels}")
    if len(issues) > 20:
        lines.append(f"\n...and {len(issues) - 20} more. See GitHub Projects board.")

    await interaction.followup.send("\n".join(lines))


@task_group.command(name="status", description="Update task status")
@app_commands.describe(
    issue_number="Task number (e.g. 14)",
    new_status="New status: in-progress / in-review / done / backlog"
)
async def task_status(
    interaction: discord.Interaction,
    issue_number: int,
    new_status: str,
):
    await interaction.response.defer()
    STATUS_LABELS = ["backlog", "in-progress", "in-review", "done"]

    # Remove old status labels, add new one
    issue = await gh_rest("GET", f"/repos/{GITHUB_REPO}/issues/{issue_number}")
    current_labels = [l["name"] for l in issue.get("labels", [])
                      if l["name"] not in STATUS_LABELS]
    current_labels.append(new_status.lower())

    await ensure_label_exists(new_status.lower())
    await gh_rest(
        "PATCH", f"/repos/{GITHUB_REPO}/issues/{issue_number}",
        json={"labels": current_labels}
    )

    status_emoji = {"in-progress": "🔄", "in-review": "👀",
                    "done": "✅", "backlog": "📋"}.get(new_status.lower(), "📋")
    await interaction.followup.send(
        f"{status_emoji} **Task #{issue_number}** moved to **{new_status}**\n"
        f"→ github.com/{GITHUB_REPO}/issues/{issue_number}"
    )


@task_group.command(name="close", description="Close a task")
@app_commands.describe(issue_number="Task number to close")
async def task_close(interaction: discord.Interaction, issue_number: int):
    await interaction.response.defer()
    await close_github_issue(issue_number)
    await interaction.followup.send(
        f"✅ Task #{issue_number} closed.\n"
        f"→ github.com/{GITHUB_REPO}/issues/{issue_number}"
    )


@task_group.command(name="assign", description="Assign or reassign a task")
@app_commands.describe(
    issue_number="Task number",
    assign="GitHub username(s) comma-separated"
)
async def task_assign(
    interaction: discord.Interaction,
    issue_number: int,
    assign: str,
):
    await interaction.response.defer()
    assignees = [a.strip() for a in assign.split(",") if a.strip()]
    await gh_rest(
        "PATCH", f"/repos/{GITHUB_REPO}/issues/{issue_number}",
        json={"assignees": assignees}
    )
    await interaction.followup.send(
        f"👤 Task #{issue_number} assigned to **{assign}**\n"
        f"→ github.com/{GITHUB_REPO}/issues/{issue_number}"
    )


@task_group.command(name="priority", description="Change task priority")
@app_commands.describe(
    issue_number="Task number",
    priority="Priority: critical / high / medium / low"
)
async def task_priority(
    interaction: discord.Interaction,
    issue_number: int,
    priority: str,
):
    await interaction.response.defer()
    issue = await gh_rest("GET", f"/repos/{GITHUB_REPO}/issues/{issue_number}")
    PRIORITY_LABELS = ["critical", "high", "medium", "low"]
    current = [l["name"] for l in issue.get("labels", [])
               if l["name"] not in PRIORITY_LABELS]
    current.append(priority.lower())
    await ensure_label_exists(priority.lower())
    await gh_rest(
        "PATCH", f"/repos/{GITHUB_REPO}/issues/{issue_number}",
        json={"labels": current}
    )
    await interaction.followup.send(
        f"🎯 Task #{issue_number} priority set to **{priority}**"
    )


@task_group.command(name="label", description="Add a label to a task")
@app_commands.describe(issue_number="Task number", label="Label to add")
async def task_label(
    interaction: discord.Interaction,
    issue_number: int,
    label: str,
):
    await interaction.response.defer()
    issue = await gh_rest("GET", f"/repos/{GITHUB_REPO}/issues/{issue_number}")
    current = [l["name"] for l in issue.get("labels", [])]
    if label not in current:
        current.append(label)
    await ensure_label_exists(label)
    await gh_rest(
        "PATCH", f"/repos/{GITHUB_REPO}/issues/{issue_number}",
        json={"labels": current}
    )
    await interaction.followup.send(f"🏷️ Label `{label}` added to Task #{issue_number}")


@task_group.command(name="search", description="Search tasks by keyword")
@app_commands.describe(keyword="Keyword to search for in task titles")
async def task_search(interaction: discord.Interaction, keyword: str):
    await interaction.response.defer()
    issues = await get_open_issues()
    results = [i for i in issues if keyword.lower() in i["title"].lower()]
    if not results:
        await interaction.followup.send(f"No tasks found matching `{keyword}`.")
        return
    lines = [f"**Search: \"{keyword}\"** — {len(results)} result(s)\n"]
    for i in results[:15]:
        assignees = ", ".join(a["login"] for a in i.get("assignees", [])) or "—"
        lines.append(f"**#{i['number']}** {i['title'][:70]}  (assigned: {assignees})")
    await interaction.followup.send("\n".join(lines))


@task_group.command(name="report", description="Full team progress summary")
async def task_report(interaction: discord.Interaction):
    await interaction.response.defer()
    issues = await get_open_issues()

    def has_label(issue, name):
        return any(l["name"] == name for l in issue.get("labels", []))

    in_progress = [i for i in issues if has_label(i, "in-progress")]
    in_review   = [i for i in issues if has_label(i, "in-review")]
    backlog     = [i for i in issues if not any(
        has_label(i, s) for s in ("in-progress", "in-review"))]

    prs = await get_open_prs()

    lines = [
        f"**📊 ASTRA Team Report — {datetime.datetime.now(CDT).strftime('%B %-d, %Y')}**",
        f"Sprint: **{state.get('sprint_name', 'No active sprint')}**\n",
        f"**In Progress ({len(in_progress)}):**",
    ]
    for i in in_progress:
        assignees = ", ".join(a["login"] for a in i.get("assignees", [])) or "—"
        lines.append(f"  · #{i['number']} {i['title'][:55]}  → {assignees}")

    lines.append(f"\n**In Review ({len(in_review)}):**")
    for i in in_review:
        lines.append(f"  · #{i['number']} {i['title'][:55]}")

    lines.append(f"\n**Backlog ({len(backlog)}):**")
    for i in backlog[:5]:
        lines.append(f"  · #{i['number']} {i['title'][:55]}")
    if len(backlog) > 5:
        lines.append(f"  ...and {len(backlog) - 5} more")

    lines.append(f"\n**PRs Open:** {len(prs)}")

    await interaction.followup.send("\n".join(lines))


@task_group.command(name="overdue", description="Show tasks that are overdue")
async def task_overdue(interaction: discord.Interaction):
    await interaction.response.defer()
    issues = await get_open_issues()
    now = datetime.datetime.now(pytz.utc)
    overdue = []
    for i in issues:
        created = datetime.datetime.fromisoformat(
            i["created_at"].replace("Z", "+00:00"))
        age_days = (now - created).days
        if age_days > 14:
            overdue.append((age_days, i))

    if not overdue:
        await interaction.followup.send("✅ No overdue tasks found.")
        return

    overdue.sort(reverse=True)
    lines = [f"**⏰ Overdue Tasks ({len(overdue)})**\n"]
    for age, i in overdue[:15]:
        assignees = ", ".join(a["login"] for a in i.get("assignees", [])) or "—"
        lines.append(f"**#{i['number']}** _{age} days old_ — {i['title'][:55]}")
        lines.append(f"  Assigned: {assignees}")
    await interaction.followup.send("\n".join(lines))


tree.add_command(task_group)


# ─── /sprint COMMANDS ─────────────────────────────────────────────────────────
sprint_group = app_commands.Group(name="sprint", description="Sprint management")


@sprint_group.command(name="start", description="Start a new sprint")
@app_commands.describe(name="Sprint name, e.g. Sprint 1")
async def sprint_start(interaction: discord.Interaction, name: str):
    state["sprint_name"] = name
    save_state(state)
    await interaction.response.send_message(
        f"🚀 **{name} started!**\n"
        f"Use `/task create` to add tasks.\n"
        f"Use `/sprint summary` to see progress.\n"
        f"Use `/sprint end` when the sprint is complete."
    )


@sprint_group.command(name="end", description="End the current sprint")
async def sprint_end(interaction: discord.Interaction):
    await interaction.response.defer()
    issues = await get_open_issues()
    sprint = state.get("sprint_name", "Current Sprint")

    def has_label(issue, name):
        return any(l["name"] == name for l in issue.get("labels", []))

    in_progress = [i for i in issues if has_label(i, "in-progress")]
    in_review   = [i for i in issues if has_label(i, "in-review")]
    backlog     = [i for i in issues if not any(
        has_label(i, s) for s in ("in-progress", "in-review"))]

    state["sprint_name"] = None
    save_state(state)

    lines = [
        f"**🏁 {sprint} — Ended**\n",
        f"**In Progress at close ({len(in_progress)}) — carry forward:**",
    ]
    for i in in_progress:
        lines.append(f"  · #{i['number']} {i['title'][:60]}")
    lines.append(f"\n**In Review ({len(in_review)}) — carry forward:**")
    for i in in_review:
        lines.append(f"  · #{i['number']} {i['title'][:60]}")
    lines.append(f"\n**Backlog remaining:** {len(backlog)} tasks")
    lines.append(
        f"\nRun `/sprint start \"Sprint X\"` to begin the next sprint.\n"
        f"Post a post-mortem in #post-incident-reviews for this sprint."
    )
    await interaction.followup.send("\n".join(lines))


@sprint_group.command(name="summary", description="Show current sprint progress")
async def sprint_summary(interaction: discord.Interaction):
    await interaction.response.defer()
    issues = await get_open_issues()
    sprint = state.get("sprint_name", "No active sprint")

    def has_label(issue, name):
        return any(l["name"] == name for l in issue.get("labels", []))

    in_progress = [i for i in issues if has_label(i, "in-progress")]
    in_review   = [i for i in issues if has_label(i, "in-review")]
    backlog     = [i for i in issues if not any(
        has_label(i, s) for s in ("in-progress", "in-review"))]

    lines = [
        f"**📊 {sprint} — Summary**\n",
        f"**In Progress ({len(in_progress)}):**",
    ]
    for i in in_progress:
        assignees = ", ".join(a["login"] for a in i.get("assignees", [])) or "—"
        lines.append(f"  🔄 #{i['number']} {i['title'][:55]}  ({assignees})")
    lines.append(f"\n**In Review ({len(in_review)}):**")
    for i in in_review:
        lines.append(f"  👀 #{i['number']} {i['title'][:55]}")
    lines.append(f"\n**Backlog:** {len(backlog)} tasks remaining")

    await interaction.followup.send("\n".join(lines))


@sprint_group.command(name="carry", description="Carry unfinished tasks to next sprint")
@app_commands.describe(next_sprint="Name of the next sprint")
async def sprint_carry(interaction: discord.Interaction, next_sprint: str):
    old_sprint = state.get("sprint_name", "Previous Sprint")
    state["sprint_name"] = next_sprint
    save_state(state)
    await interaction.response.send_message(
        f"↩️ Unfinished tasks carried from **{old_sprint}** to **{next_sprint}**.\n"
        f"Sprint **{next_sprint}** is now active."
    )


tree.add_command(sprint_group)


# ─── GITHUB PR POLLING ────────────────────────────────────────────────────────
@tasks.loop(minutes=5)
async def poll_github_prs():
    """Check for new PRs and post them to #pull-request-reviews."""
    for guild in bot.guilds:
        ch = get_channel(guild, "pull-request-reviews")
        if not ch:
            continue

        prs = await get_open_prs()
        if not isinstance(prs, list):
            continue

        for pr in prs:
            pr_id = pr.get("number", 0)
            if pr_id <= state.get("last_pr_id", 0):
                continue

            # New PR found
            state["last_pr_id"] = max(state.get("last_pr_id", 0), pr_id)
            save_state(state)

            user      = pr.get("user", {}).get("login", "unknown")
            title     = pr.get("title", "No title")
            url       = pr.get("html_url", "")
            base      = pr.get("base", {}).get("ref", "main")
            head      = pr.get("head", {}).get("ref", "feature")
            body      = (pr.get("body") or "")[:200]
            reviewers = [r["login"] for r in pr.get("requested_reviewers", [])]

            lines = [
                f"📬 **PULL REQUEST OPENED — #{pr_id}**\n",
                f"**Title:** {title}",
                f"**Author:** {user}",
                f"**Branch:** `{head}` → `{base}`",
            ]
            if reviewers:
                lines.append(f"**Review requested from:** {', '.join(reviewers)}")
            if body:
                lines.append(f"**Description:** {body}")
            lines.append(f"\n→ {url}")

            await ch.send("\n".join(lines))
            await asyncio.sleep(1)


# ─── BOT EVENTS ───────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    global state
    state = load_state()
    print(f"[ASTRA Bot] Logged in as {bot.user}")

    # Sync slash commands
    for guild in bot.guilds:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print(f"[ASTRA Bot] Slash commands synced to: {guild.name}")
        await ensure_project(guild)

    # Start background tasks
    if not daily_digest.is_running():
        daily_digest.start()
    if not poll_github_prs.is_running():
        poll_github_prs.start()

    print("[ASTRA Bot] ✅ All systems running.")
    print(f"  → Daily digest: 9AM CDT")
    print(f"  → PR polling: every 5 minutes")
    print(f"  → Incident auto-thread: active")
    print(f"  → Sprint board: /task and /sprint commands ready")


# ─── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    missing = []
    if not DISCORD_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        print("Set them with:")
        for m in missing:
            print(f"  export {m}=your_value_here")
    else:
        bot.run(DISCORD_TOKEN)
