"""
ASTRA Discord Server Setup Script
===================================
Creates a fully structured Discord server for the ASTRA project:
AI-powered SRE/RCA Analysis System with Ollama LLM (private, no third-party data access)

Usage:
    pip install discord.py
    python create_server.py

Note: Bot must be in fewer than 10 guilds to use create_guild().
      Bot needs: MANAGE_GUILD, MANAGE_CHANNELS, MANAGE_ROLES permissions.
"""

import discord
import asyncio
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
SERVER_NAME = "ASTRA | AI-SRE Platform"
# ───────────────────────────────────────────────────────────────────────────────


# ─── SERVER STRUCTURE ──────────────────────────────────────────────────────────
# Format: { "CATEGORY NAME": [ ("channel-name", "text" | "voice", "description") ] }

SERVER_STRUCTURE = {
    "WELCOME & GENERAL": [
        ("announcements",       "text",  "Official project updates, releases, and milestones"),
        ("general",             "text",  "Open team discussion"),
        ("introductions",       "text",  "Introduce yourself and your role"),
        ("resources",           "text",  "Useful links, papers, tools, eraser.io diagrams"),
        ("team-standup",        "text",  "Daily async standups and progress updates"),
    ],

    "R&D / PLANNING": [
        ("requirements",        "text",  "Functional & non-functional requirements docs"),
        ("problem-statements",  "text",  "Scope definitions and ongoing problem analysis"),
        ("architecture",        "text",  "System design diagrams (eraser.io), ADRs"),
        ("objectives-okrs",     "text",  "R&D goals, OKRs, sprint planning"),
        ("research-papers",     "text",  "Reference papers, benchmarks, competitor analysis"),
    ],

    "AI ENGINE (ASTRA CORE)": [
        ("ollama-llm-dev",      "text",  "Custom Ollama LLM development — private, no third-party access"),
        ("rca-engine",          "text",  "Root Cause Analysis logic, prompt engineering, output tuning"),
        ("ai-agent-dev",        "text",  "Agent behavior, tool use, memory contexts"),
        ("model-evals",         "text",  "LLM evaluation results, benchmarks, accuracy reports"),
        ("ai-voice-collab",     "voice", "AI team voice collaboration"),
    ],

    "OBSERVABILITY / INFRA": [
        ("cloudwatch-alerts",   "text",  "AWS CloudWatch EWS — live alert feed and analysis"),
        ("datadog-newrelic",    "text",  "Datadog / New Relic dashboards and alert discussions"),
        ("grafana-prometheus",  "text",  "Grafana dashboards, Prometheus metrics, alert rules"),
        ("splunk-logs",         "text",  "Splunk log queries and saved searches"),
        ("infra-general",       "text",  "General AWS infra: EC2, VPC, IAM, cost discussions"),
    ],

    "SIMULATION & TESTING": [
        ("ec2-simulation",      "text",  "EC2 instance failure simulations and chaos engineering"),
        ("log-ingestion",       "text",  "Step 1 — Reading & ingesting logs from CW/Splunk/Datadog"),
        ("rca-reports",         "text",  "Step 2 — AI-generated RCA reports and recommendations"),
        ("test-scenarios",      "text",  "Test case definitions, edge cases, regression suites"),
        ("simulation-voice",    "voice", "Simulation run voice channel"),
    ],

    "INCIDENTS & AUDIT": [
        ("active-incidents",    "text",  "Live incident tracking (e.g., 2hr EC2 outage scenarios)"),
        ("post-mortems",        "text",  "Post-incident reviews, learnings, corrective actions"),
        ("access-violations",   "text",  "Unauthorized access alerts — who accessed what they shouldn't"),
        ("audit-trail",         "text",  "Full audit log — costly ops flagged, compliance tracking"),
        ("cost-alerts",         "text",  "AWS cost anomaly detection and budget breach alerts"),
    ],

    "FRONTEND / DEPLOYMENT": [
        ("react-nextjs",        "text",  "UI development — React / Next.js components and PRs"),
        ("vercel-streamlit",    "text",  "Deployment pipelines — Vercel (prod) & Streamlit (demos)"),
        ("ux-feedback",         "text",  "User feedback, UI/UX reviews, accessibility"),
        ("staging-prod",        "text",  "Staging vs production environment discussions"),
    ],

    "TASK MANAGEMENT": [
        ("task-assignments",    "text",  "Responsibility matrix — who owns what (Excel-style tracking)"),
        ("sprint-board",        "text",  "Sprint tasks, blockers, velocity"),
        ("pr-reviews",          "text",  "Pull request review requests and merge notifications"),
        ("release-notes",       "text",  "Version changelogs and release summaries"),
    ],

    "VOICE ROOMS": [
        ("Team Standup",        "voice", "Daily standup call"),
        ("War Room",            "voice", "Incident response war room"),
        ("R&D Brainstorm",      "voice", "Open R&D discussion"),
        ("1-on-1",              "voice", "Private pairing / mentorship"),
    ],
}


# ─── ROLES WITH COLORS AND PERMISSIONS ─────────────────────────────────────────
ROLES = [
    # (name, color_hex, is_admin, hoist)
    ("Admin",           0xE74C3C, True,  True),   # Red    — full access
    ("AI Engineer",     0x9B59B6, False, True),   # Purple — AI Engine + Simulation
    ("SRE",             0xE67E22, False, True),   # Orange — Observability + Incidents
    ("R&D",             0x2ECC71, False, True),   # Green  — Planning + Research
    ("Frontend Dev",    0x3498DB, False, True),   # Blue   — Frontend + Deployment
    ("Viewer",          0x95A5A6, False, False),  # Grey   — read-only across public channels
]


# ─── CHANNEL ACCESS MATRIX ─────────────────────────────────────────────────────
# Maps category → which roles get WRITE access (all roles can read public channels)
CATEGORY_WRITE_ACCESS = {
    "WELCOME & GENERAL":        ["Admin", "AI Engineer", "SRE", "R&D", "Frontend Dev", "Viewer"],
    "R&D / PLANNING":           ["Admin", "R&D", "AI Engineer"],
    "AI ENGINE (ASTRA CORE)":   ["Admin", "AI Engineer"],
    "OBSERVABILITY / INFRA":    ["Admin", "SRE"],
    "SIMULATION & TESTING":     ["Admin", "SRE", "AI Engineer"],
    "INCIDENTS & AUDIT":        ["Admin", "SRE"],
    "FRONTEND / DEPLOYMENT":    ["Admin", "Frontend Dev"],
    "TASK MANAGEMENT":          ["Admin", "AI Engineer", "SRE", "R&D", "Frontend Dev"],
    "VOICE ROOMS":              ["Admin", "AI Engineer", "SRE", "R&D", "Frontend Dev"],
}

# Channels locked to Admin + SRE only (no public read)
RESTRICTED_CHANNELS = {"access-violations", "audit-trail", "active-incidents"}


# ─── BOT SETUP ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def create_astra_server():
    print(f"\n[ASTRA] Creating server: '{SERVER_NAME}' ...")
    guild = await client.create_guild(name=SERVER_NAME)
    await asyncio.sleep(2)  # let Discord propagate

    # Fetch the newly created guild with full data
    guild = client.get_guild(guild.id)

    print("[ASTRA] Cleaning up default channels ...")
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception:
            pass

    # ── Create Roles ──────────────────────────────────────────────────────────
    print("[ASTRA] Creating roles ...")
    role_objects = {}

    for role_name, color_hex, is_admin, hoist in ROLES:
        perms = discord.Permissions.all() if is_admin else discord.Permissions.none()

        if not is_admin:
            # Base permissions for non-admin roles
            perms = discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                add_reactions=True,
                use_slash_commands=True,
                connect=True,       # voice
                speak=True,         # voice
            )

        role = await guild.create_role(
            name=role_name,
            color=discord.Color(color_hex),
            permissions=perms,
            hoist=hoist,
            mentionable=True,
        )
        role_objects[role_name] = role
        print(f"  + Role: {role_name}")
        await asyncio.sleep(0.5)

    everyone = guild.default_role

    # ── Create Categories & Channels ─────────────────────────────────────────
    print("[ASTRA] Creating categories and channels ...")

    for category_name, channels in SERVER_STRUCTURE.items():
        write_roles    = CATEGORY_WRITE_ACCESS.get(category_name, [])
        is_restricted  = category_name in ("INCIDENTS & AUDIT",)

        # Category-level overwrites
        category_overwrites = {
            everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        }
        for role_name in write_roles:
            role = role_objects.get(role_name)
            if role:
                category_overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                )

        category = await guild.create_category(
            name=category_name,
            overwrites=category_overwrites,
        )
        print(f"\n  [{category_name}]")

        for ch_name, ch_type, ch_topic in channels:
            # Restricted channels: hide from everyone except Admin + SRE
            if ch_name in RESTRICTED_CHANNELS:
                ch_overwrites = {
                    everyone:                   discord.PermissionOverwrite(read_messages=False),
                    role_objects["Admin"]:       discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    role_objects["SRE"]:         discord.PermissionOverwrite(read_messages=True, send_messages=True),
                }
            else:
                ch_overwrites = {}  # inherit from category

            if ch_type == "text":
                ch = await guild.create_text_channel(
                    name=ch_name,
                    category=category,
                    topic=ch_topic,
                    overwrites=ch_overwrites,
                )
            else:
                ch = await guild.create_voice_channel(
                    name=ch_name,
                    category=category,
                    overwrites=ch_overwrites,
                )

            print(f"    {'#' if ch_type == 'text' else '🔊'} {ch_name}")
            await asyncio.sleep(0.3)

    # ── Send Welcome Message ──────────────────────────────────────────────────
    for ch in guild.text_channels:
        if ch.name == "announcements":
            await ch.send(
                "**Welcome to ASTRA — AI-Powered SRE & RCA Platform**\n\n"
                "This server is the central hub for building and operating the ASTRA system:\n"
                "• AI/SRE Agent for automated Root Cause Analysis\n"
                "• Custom Ollama LLM — private, no third-party data access\n"
                "• Observability stack: CloudWatch, Datadog, Grafana, Prometheus, Splunk\n"
                "• EC2 simulation, log ingestion pipeline, and AI-generated RCA reports\n\n"
                "**Roles:** Admin | AI Engineer | SRE | R&D | Frontend Dev | Viewer\n"
                "Ask an Admin to assign your role. Let's build something powerful."
            )
            break

    print(f"\n[ASTRA] Server '{SERVER_NAME}' created successfully!")
    print(f"[ASTRA] Server ID: {guild.id}")
    print("[ASTRA] Invite your team and assign roles. Shutting down bot ...\n")
    await client.close()


@client.event
async def on_ready():
    print(f"[ASTRA] Bot logged in as: {client.user}")
    await create_astra_server()


# ─── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("[ERROR] Set your bot token: export DISCORD_BOT_TOKEN=your_token_here")
    else:
        client.run(BOT_TOKEN)
