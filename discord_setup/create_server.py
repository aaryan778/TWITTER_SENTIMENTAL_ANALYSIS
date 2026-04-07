"""
ASTRA Discord Server Creation Script
=====================================
Run this ONCE after:
  1. Creating the server manually on Discord
  2. Inviting the bot to the server
  3. Copying the Server ID (right-click server → Copy Server ID)

Usage:
    pip install -r requirements.txt
    export DISCORD_BOT_TOKEN=your_token_here
    export DISCORD_GUILD_ID=your_server_id_here
    python create_server.py
"""

import discord
import asyncio
import os

BOT_TOKEN  = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID   = int(os.environ.get("DISCORD_GUILD_ID", "0"))
SERVER_NAME = "ASTRA | AI-SRE Platform"

# ─── CHANNEL STRUCTURE ────────────────────────────────────────────────────────
# (channel-name, type, topic)
SERVER_STRUCTURE = {
    "WELCOME & COMMUNICATIONS": [
        ("announcements",          "text",  "Official project updates, releases, and milestones — Admin only"),
        ("general-discussion",     "text",  "Open team discussion — anything loosely related to the project"),
        ("team-introductions",     "text",  "Introduce yourself once — name, role, background"),
        ("resources-and-references","text", "Shared bookmarks — papers, diagrams, docs, useful links"),
        ("daily-status-updates",   "text",  "9AM CDT automated digest + personal daily updates"),
    ],
    "STRATEGY & PLANNING": [
        ("project-requirements",   "text",  "Functional and non-functional requirements — the ground truth"),
        ("problem-statements",     "text",  "Structured problem definitions — why we are building what we are building"),
        ("system-architecture",    "text",  "Architecture diagrams, ADRs, component designs (eraser.io)"),
        ("objectives-and-milestones","text","OKRs, sprint milestones, roadmap"),
        ("research-and-development","text", "Research notes, experiment results, proposals"),
    ],
    "AI ENGINE — CORE": [
        ("llm-development",        "text",  "Ollama LLM — model selection, fine-tuning, server config"),
        ("rca-engine-development", "text",  "RCA pipeline, prompt engineering, output format"),
        ("agent-framework",        "text",  "Agent architecture, tool use, decision logic"),
        ("model-evaluation-and-benchmarks","text","Benchmark results, accuracy metrics, eval runs"),
        ("memory-context-design",  "text",  "Agent memory architecture, RAG design, context management"),
    ],
    "OBSERVABILITY & INFRASTRUCTURE": [
        ("cloudwatch-monitoring",  "text",  "AWS CloudWatch alarms, log groups, Insights queries"),
        ("datadog-and-newrelic",   "text",  "Datadog / New Relic setup, dashboards, alerting"),
        ("grafana-and-prometheus", "text",  "Grafana dashboards, Prometheus metrics, PromQL"),
        ("splunk-log-analysis",    "text",  "Splunk data inputs, SPL queries, saved searches"),
        ("infrastructure-general", "text",  "AWS account, IAM, VPC, EC2, cost management"),
    ],
    "SIMULATION & QUALITY ASSURANCE": [
        ("ec2-failure-simulation", "text",  "Failure scenario designs, simulation runs, results"),
        ("log-ingestion-pipeline", "text",  "Log fetcher, Drain3 parser, normalization pipeline"),
        ("rca-output-reports",     "text",  "AI-generated RCA reports — auto-posted by ASTRA bot"),
        ("test-scenarios-and-cases","text", "Test case library, regression tests, QA coverage"),
    ],
    "INCIDENT MANAGEMENT & AUDIT": [
        ("active-incidents",       "text",  "Post here to open an incident — bot auto-creates thread"),
        ("post-incident-reviews",  "text",  "Post-mortems within 48h of resolution — blameless"),
        ("access-violation-alerts","text",  "Unauthorized access alerts and security anomalies"),
        ("audit-and-compliance",   "text",  "Audit trail — infrastructure changes, agent actions, costs"),
        ("cost-anomaly-alerts",    "text",  "AWS cost anomalies, budget alerts, monthly summaries"),
    ],
    "BACKEND ENGINEERING": [
        ("api-development",        "text",  "API endpoint design, versioning, integration docs"),
        ("database-and-schema",    "text",  "Schema design, migrations, query optimization"),
        ("ollama-server-configuration","text","Ollama setup, model inventory, inference config"),
        ("authentication-and-security","text","Auth design, secrets management, security reviews"),
        ("devops-and-ci-cd",       "text",  "CI/CD pipelines, Docker, deployment runbooks"),
    ],
    "FRONTEND ENGINEERING": [
        ("ui-development",         "text",  "React/Next.js components, pages, state management"),
        ("deployment-pipeline",    "text",  "Vercel production, preview deployments, Streamlit demos"),
        ("ux-and-design-feedback", "text",  "Wireframes, design reviews, usability feedback"),
        ("staging-and-production", "text",  "Environment status board, smoke tests, rollback decisions"),
    ],
    "PROJECT OPERATIONS": [
        ("task-assignments",       "text",  "Responsibility matrix — who owns what area of the project"),
        ("sprint-board",           "text",  "Sprint tasks — /task and /sprint commands live here"),
        ("pull-request-reviews",   "text",  "PR notifications auto-posted here — review requests"),
        ("release-notes",          "text",  "Changelogs for every version release"),
    ],
    "VOICE ROOMS": [
        ("War Room",               "voice", "Incident response"),
        ("Team Standup",           "voice", "Daily standup"),
        ("R&D Brainstorm",         "voice", "Research and design discussion"),
        ("General Collaboration",  "voice", "Open team voice"),
    ],
}

# ─── PINNED MESSAGES PER CHANNEL ──────────────────────────────────────────────
CHANNEL_PINS = {
    "announcements": """**#announcements — Channel Guide**

This is the front page of the server. Only Aaryan posts here.
If it's in announcements, it matters and affects the whole team.

**What goes here:**
→ Sprint starts and ends
→ Major milestones reached
→ New team members joining
→ Architectural decisions that affect everyone
→ Outages or production-level issues

**What does NOT go here:**
→ Day-to-day updates (use #daily-status-updates)
→ Questions (use #general-discussion)

**Post format:**
```
📌 [TYPE] — Short Title
What happened / what's changing:
What you need to do (if anything):
— Aaryan
```""",

    "general-discussion": """**#general-discussion — Channel Guide**

Main room. Low structure. Keep it project-related.

**What goes here:**
→ Quick questions that don't fit anywhere else
→ Interesting reads relevant to what we're building
→ Asking for a second opinion on something
→ "Has anyone dealt with X before?" conversations

**Tips:**
→ If your message starts a real conversation, use threads
→ If sharing a link, add one line explaining why it's relevant
→ If it belongs in a specific channel, use that channel""",

    "team-introductions": """**#team-introductions — Channel Guide**

Every person who joins posts here once.

**Template:**
```
Name:
Role on ASTRA:
Background / what I work with:
What I'm focused on right now:
One thing I want to get out of this project:
```

**Rules:**
→ One post per person — edit it if you want to update
→ No replies here — say hi in #general-discussion instead""",

    "resources-and-references": """**#resources-and-references — Channel Guide**

The team's shared bookmarks. Papers, tools, diagrams, docs, videos.

**How to post:**
```
📎 [TAG] — Title or brief description
Link: ...
Why it's relevant: one or two sentences
```

**Tags:**
`[PAPER]` `[TOOL]` `[DIAGRAM]` `[ARTICLE]` `[DOCS]` `[VIDEO]` `[DECISION]`""",

    "daily-status-updates": """**#daily-status-updates — Channel Guide**

The ASTRA bot posts an automated digest here every morning at **9AM CDT**.

**Digest includes:**
→ Open tasks (count + assignees)
→ PRs awaiting review
→ Issues closed yesterday
→ Active incident count

**Optional personal updates** (not mandatory, keep to 3 sentences max):
```
Working on X today. Hit Y issue yesterday, trying Z approach.
Should have something testable by EOD.
— [Your name]
```

**Rule:** Don't have conversations here. Discussion goes in the relevant channel.""",

    "project-requirements": """**#project-requirements — Channel Guide**

Where we define what ASTRA is supposed to do. Requirements are the ground truth.

**Format:**
```
[FR/NFR]-[NUMBER] | Short Title
Description: What exactly is required. Be specific.
Acceptance Criteria: How do we know this is met?
Status: Draft / In Review / Approved / Deprecated
Owner: Who is responsible
```

**Rules:**
→ Discuss before posting — use #general-discussion first
→ Don't modify Approved requirements without flagging it
→ Never delete — mark as Deprecated instead""",

    "problem-statements": """**#problem-statements — Channel Guide**

The "why are we doing this" channel. One problem per post.

**Format:**
```
PROBLEM-[N] | Short Title
Context: Background on the situation
Problem: What specifically is wrong or missing
Impact: What happens because of this problem
What success looks like: How we know it's solved
Status: Active / Resolved
Owner: ...
```

**Rule:** Keep it focused on the problem. If you're writing about the solution, stop and take it to #system-architecture.""",

    "system-architecture": """**#system-architecture — Channel Guide**

How we build it. Diagrams, ADRs, component designs.

**Tags to use:** `[HIGH-LEVEL]` `[DATA-FLOW]` `[COMPONENT]` `[DB-SCHEMA]` `[INFRA]`

**ADR format:**
```
ADR-[N] | Decision Title
Date: ...  Status: Accepted / Rejected / Superseded
Context: Why we needed to make this decision
Decision: What we chose
Reasoning: Why
Trade-offs: What we're giving up
```

**Rules:**
→ Every significant architectural decision needs an ADR
→ When a design changes, add a new post — don't delete the old one""",

    "active-incidents": """**#active-incidents — Channel Guide**

The most critical channel. When something breaks, it gets reported here.

**Method A — Quick message:**
Just type what you see. Bot detects severity from keywords and creates a thread.
```
Severity keywords:
🔴 CRITICAL → down, outage, crash, unresponsive, failed, unreachable
🟡 WARNING  → slow, degraded, latency, high memory, high cpu
🔵 INFO     → notice, monitoring, investigating, update
```

**Method B — Slash command:**
```
/incident
```
Opens a structured form with title, severity, service, description, assignee.

**Thread format:** `INC-007 🔴 CRITICAL | EC2 Instance Unreachable — Apr 7 04:32 UTC`

**Rules:**
→ All discussion goes in the thread — not the main channel
→ Update the thread regularly during an incident
→ Never close without scheduling a post-mortem
→ Aaryan must approve any infrastructure action (restart, rollback)""",

    "sprint-board": """**#sprint-board — Channel Guide**

Central task management. All commands sync with GitHub Projects.

**CREATING TASKS**
```
/task create "title"
/task create "title" assign:Bhargav priority:high
/task create "title" assign:Bhargav,Asif priority:critical label:backend
```

**VIEWING**
```
/task list                    /task list assign:Nithish
/task list status:in-progress /task list label:ai-engine
/task overdue                 /task search "RCA"
/task report
```

**UPDATING**
```
/task status #14 in-progress  /task status #14 in-review
/task status #14 done         /task assign #14 Asif
/task priority #14 critical   /task label #14 backend
```

**CLOSING**
```
/task close #14               /task delete #14
```

**SPRINTS**
```
/sprint start "Sprint 1"      /sprint end
/sprint summary               /sprint carry "Sprint 2"
```

**LABELS:** `ai-engine` `observability` `backend` `frontend` `devops` `simulation` `incident` `research` `bug` `urgent` `blocked`
**PRIORITIES:** `critical` `high` `medium` `low`

**Rules:**
→ Always assign at least one person when creating a task
→ Update status as you move through the work
→ Run /sprint summary at the end of every sprint""",

    "pull-request-reviews": """**#pull-request-reviews — Channel Guide**

PR notifications auto-post here. Bot posts when a PR is opened, review requested, or merged.

**When you open a PR, also post here with context:**
```
PR #24 — Short description of what this does

Context: Why this change was needed (link to task/incident if applicable)
Needs review from: @name
Any notes for reviewer: ...
→ github.com/aaryan778/ASTRA/pull/24
```

**Rules:**
→ PRs should be reviewed within 24 hours during active sprints
→ Tag the reviewer here — don't rely on GitHub notifications alone
→ Approvals go in GitHub, not Discord
→ Don't merge your own PR without at least one approval""",

    "post-incident-reviews": """**#post-incident-reviews — Channel Guide**

Every incident gets a post-mortem within 48 hours. Blameless.

**Template:**
```
POST-MORTEM | INC-[N]
Incident: ...    Date: ...    Duration: ...    Author: ...

SUMMARY: What happened in 2-3 sentences
TIMELINE: Chronological events with timestamps
ROOT CAUSE: What specifically caused this
CONTRIBUTING FACTORS: What made it worse or harder to catch
WHAT WENT WELL: (yes, include this)
WHAT COULD HAVE GONE BETTER: Be honest
ACTION ITEMS: Owner | Due date | Task #
```

**Rules:**
→ Post within 48 hours of incident resolution
→ Every action item needs an owner, due date, and GitHub task
→ This is blameless — focus on system improvements, not people""",
}

# ─── BOT SETUP ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)


async def pin_message(channel, content):
    """Post a message and pin it."""
    # Discord message limit is 2000 chars — split if needed
    chunks = [content[i:i+1990] for i in range(0, len(content), 1990)]
    last_msg = None
    for chunk in chunks:
        last_msg = await channel.send(chunk)
        await asyncio.sleep(0.5)
    if last_msg:
        await last_msg.pin()
    await asyncio.sleep(0.5)


async def create_astra_server():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"[ERROR] Could not find server with ID {GUILD_ID}")
        print("  Make sure the bot is invited to the server and DISCORD_GUILD_ID is correct.")
        await client.close()
        return

    print(f"\n[ASTRA] Found server: '{guild.name}' (ID: {guild.id})")
    print("[ASTRA] Setting up ASTRA channel structure ...")

    # Delete default channels
    print("[ASTRA] Removing existing channels ...")
    for channel in guild.channels:
        try:
            await channel.delete()
            await asyncio.sleep(0.3)
        except Exception:
            pass

    everyone = guild.default_role
    await everyone.edit(permissions=discord.Permissions(
        read_messages=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True,
        add_reactions=True,
        connect=True,
        speak=True,
    ))

    # Create categories and channels
    print("[ASTRA] Creating categories and channels ...")
    for category_name, channels in SERVER_STRUCTURE.items():
        category = await guild.create_category(name=category_name)
        print(f"\n  [{category_name}]")
        await asyncio.sleep(0.5)

        for ch_name, ch_type, ch_topic in channels:
            if ch_type == "text":
                ch = await guild.create_text_channel(
                    name=ch_name,
                    category=category,
                    topic=ch_topic,
                )
                print(f"    # {ch_name}")

                # Pin channel guide if one exists
                if ch_name in CHANNEL_PINS:
                    await asyncio.sleep(1)
                    await pin_message(ch, CHANNEL_PINS[ch_name])
                    # Delete the system "pinned a message" notification
                    async for msg in ch.history(limit=5):
                        if msg.type == discord.MessageType.pins_add:
                            await msg.delete()
                            break

            else:
                await guild.create_voice_channel(
                    name=ch_name,
                    category=category,
                )
                print(f"    🔊 {ch_name}")

            await asyncio.sleep(0.5)

    # Post welcome message in announcements
    for ch in guild.text_channels:
        if ch.name == "announcements":
            await ch.send(
                "**Welcome to ASTRA — AI-Powered SRE & RCA Platform**\n\n"
                "This is the central hub for building and operating ASTRA:\n"
                "→ AI/SRE agent for automated Root Cause Analysis\n"
                "→ Custom Ollama LLM — private, no third-party data access\n"
                "→ Observability stack: CloudWatch, Datadog, Grafana, Prometheus, Splunk\n"
                "→ EC2 simulation, log ingestion pipeline, AI-generated RCA reports\n\n"
                "**Team:** Aaryan (Admin) | Bhargav | Asif | Nithish | Sai Purna\n\n"
                "Every channel has a pinned guide — read it before posting.\n"
                "Sprint board commands: `/task` and `/sprint` in #sprint-board\n"
                "Incident reporting: post in #active-incidents or use `/incident`\n\n"
                "Let's build something powerful. — Aaryan"
            )
            break

    print(f"\n[ASTRA] ✅ Server '{SERVER_NAME}' created successfully!")
    print(f"[ASTRA] Server ID: {guild.id}")
    print("[ASTRA] Invite your team and run astra_bot.py to start the bot.\n")
    await client.close()


@client.event
async def on_ready():
    print(f"[ASTRA] Bot logged in as: {client.user}")
    await create_astra_server()


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("[ERROR] Missing DISCORD_BOT_TOKEN")
        print("  export DISCORD_BOT_TOKEN=your_token_here")
    elif not GUILD_ID:
        print("[ERROR] Missing DISCORD_GUILD_ID")
        print("  export DISCORD_GUILD_ID=your_server_id_here")
        print("  (Right-click your server in Discord → Copy Server ID)")
        print("  (Requires Developer Mode: Settings → Advanced → Developer Mode)")
    else:
        client.run(BOT_TOKEN)
