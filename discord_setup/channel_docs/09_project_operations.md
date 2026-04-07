# PROJECT OPERATIONS — Channel Docs

---

## #task-assignments

This is the responsibility matrix for ASTRA. Every significant piece of work that someone owns — not just sprint tasks, but ongoing responsibilities — gets documented here. Think of it as the human layer on top of the sprint board. The sprint board tracks individual tasks. This channel tracks who owns what area of the project at a higher level.

The goal is that anyone on the team can look at this channel and immediately know who to go to for any given topic, without having to guess or ask around.

**What belongs here:**
- Area ownership (who is responsible for each part of the system)
- Task handoffs when ownership changes
- Cross-team dependencies (when one person's work is blocked on another's)
- Responsibility matrix updates as the team evolves
- Long-running assignments that span multiple sprints

**Current responsibility matrix (update this as things change):**

```
AREA                        PRIMARY OWNER       BACKUP
─────────────────────────────────────────────────────
Project Lead / Admin        Aaryan              —
AI Engine / Ollama LLM      Bhargav             Asif
RCA Engine Development      Asif                Bhargav
Log Ingestion Pipeline      Bhargav             Nithish
Observability Stack         Sai Purna           Bhargav
  (CloudWatch, Grafana,
   Prometheus, Splunk)
Backend API                 Nithish             Asif
Database & Schema           Nithish             Sai Purna
Authentication / Security   Aaryan              Nithish
Frontend / UI               Sai Purna           —
Deployment / DevOps         Nithish             Sai Purna
EC2 Simulation              Bhargav             Asif
Testing / QA                Asif                Nithish
Documentation               Everyone            —
Sprint Management           Aaryan              —
```

**How to post a task handoff:**
```
HANDOFF | Log Ingestion Pipeline

From: Bhargav
To: Nithish
Effective: April 10, 2024
Reason: Bhargav shifting full focus to RCA engine for sprint 2

What's being handed over:
  - CloudWatch log fetcher service (astra-log-pipeline repo)
  - Drain3 parser configuration (see docs in #log-ingestion-pipeline)
  - 2 open tasks: Task #23 (polling interval) and Task #24 (context builder)

Current state:
  - Basic pipeline working end-to-end
  - Drain3 parser has 12 templates configured
  - Known issue: occasional duplicate log ingestion on CloudWatch retry
    (Task #23 tracks this — highest priority)

Handoff meeting: April 9 at 2PM CDT in War Room voice channel
```

**How to flag a cross-team dependency:**
```
DEPENDENCY | RCA Engine blocked on Log Pipeline

Blocked team: AI Engine (Asif)
Blocking team: Log Pipeline (Bhargav)
Blocked since: April 7

What's needed:
  The RCA engine needs the normalized log format output from the pipeline
  to be finalized before prompt engineering can continue. Currently the
  log format is changing frequently which breaks the prompts.

Resolution needed by: April 10 (sprint boundary)

Status: Bhargav to finalize log schema by April 9 — agreed in standup
```

**Rules:**
- Update the responsibility matrix whenever ownership changes. An outdated matrix is worse than none.
- If you're going to be unavailable for more than a day, make sure your backup knows and post it here.
- Cross-team dependencies should be flagged here the moment they're identified, not when they've already caused a delay.

---

## #sprint-board

This is the central task management channel for ASTRA. Every task, feature, bug fix, and research item gets created and tracked here. All tasks sync automatically with the **ASTRA Sprint Board** on GitHub Projects — what you type here creates real GitHub issues with proper assignment, labels, and status tracking.

The bot lives in this channel. Everything is command-driven.

---

**CREATING TASKS**

Basic:
```
/task create "title"
```

With assignment and priority:
```
/task create "Build RCA Engine v1" assign:Bhargav priority:high
```

With multiple assignees and label:
```
/task create "Set up CloudWatch alarms" assign:Bhargav,Sai priority:high label:observability
```

Full options:
```
/task create "title" assign:@member priority:critical|high|medium|low label:labelname
```

Bot response:
```
✅ Task #14 created
Title:    Build RCA Engine v1
Assigned: Bhargav
Priority: High
Label:    ai-engine
Status:   Backlog
→ github.com/aaryan778/ASTRA/issues/14
```

---

**VIEWING TASKS**

```
/task list                          — all open tasks
/task list assign:Nithish           — tasks assigned to one person
/task list status:in-progress       — filter by status
/task list label:backend            — filter by label
/task list priority:critical        — filter by priority
/task overdue                       — tasks past their due date
/task search "RCA"                  — search by keyword
/task report                        — full team progress summary
```

---

**UPDATING TASKS**

Move through the pipeline:
```
/task status #14 in-progress        — start working on it
/task status #14 in-review          — ready for review
/task status #14 done               — completed
```

Change other fields:
```
/task assign #14 Asif               — reassign
/task assign #14 Bhargav,Asif       — assign to multiple people
/task priority #14 critical         — change priority
/task label #14 ai-engine           — add a label
/task due #14 2024-04-14            — set a due date
```

---

**CLOSING & DELETING**

```
/task close #14                     — close task (marks done, keeps history)
/task delete #14                    — permanently delete (use sparingly)
```

---

**SPRINT MANAGEMENT**

```
/sprint start "Sprint 2"            — kick off a new sprint
/sprint end                         — close current sprint with summary
/sprint summary                     — show what's done / in progress / remaining
/sprint carry "Sprint 3"            — move unfinished tasks to next sprint
```

Sprint summary output:
```
📊 SPRINT 1 SUMMARY — April 1 to April 14

COMPLETED (6 tasks):
  ✅ #12 Discord server setup
  ✅ #13 GitHub Projects integration
  ✅ #15 Ollama server installed
  ✅ #16 CloudWatch agent configured
  ✅ #17 Log fetcher service v1
  ✅ #18 Drain3 parser configured

IN PROGRESS (2 tasks — carrying to Sprint 2):
  🔄 #14 Build RCA Engine v1 (Bhargav, Asif)
  🔄 #19 API authentication (Nithish)

BACKLOG (4 tasks — carrying to Sprint 2):
  ⬜ #20 Frontend dashboard
  ⬜ #21 Grafana dashboard setup
  ⬜ #22 EC2 simulation SCENARIO-001
  ⬜ #23 Fix CloudWatch polling interval

Velocity: 6 tasks completed (target was 8)
```

---

**AVAILABLE LABELS**

| Label | Use it for |
|---|---|
| `ai-engine` | LLM, RCA, agent, prompt work |
| `observability` | CloudWatch, Grafana, Prometheus, Splunk |
| `backend` | API, DB, auth, server-side |
| `frontend` | React, Next.js, UI, Vercel |
| `devops` | CI/CD, Docker, infrastructure |
| `simulation` | EC2 simulation, test scenarios |
| `incident` | Linked to an active or past incident |
| `research` | R&D, exploration, evaluation |
| `bug` | Something broken that needs fixing |
| `urgent` | Needs immediate attention |
| `blocked` | Can't proceed until something else is done |

---

**PRIORITY LEVELS**

| Priority | What it means | Response |
|---|---|---|
| `critical` | Blocking the entire team or an active incident | Drop everything |
| `high` | Must be done this sprint, no negotiation | This week |
| `medium` | Important, next in line after high | This sprint |
| `low` | Nice to have, won't block anything | When capacity allows |

---

**LINKING TASKS TO INCIDENTS**

When an incident triggers a fix or improvement:
```
/task create "Add CloudWatch memory alarm to all instances" assign:Sai priority:high label:observability incident:INC-007
```

The bot links the task to the incident in GitHub, so you can trace every action item back to the incident that caused it.

---

**RULES**
- Always assign at least one person when creating a task. Unowned tasks don't get done.
- Update status as you move through the work. Backlog tasks that are actually in progress create confusion.
- Run `/sprint summary` at the end of every sprint before starting the next one.
- If a task is blocked, use `/task label #X blocked` and comment in the GitHub issue what it's waiting on.
- Critical tasks get created and assigned within the same message. Don't create critical tasks without an owner.

---

## #pull-request-reviews

Every time a pull request is opened, updated, reviewed, or merged on GitHub, the bot posts a notification here. This keeps the whole team aware of what's moving through the pipeline without having to check GitHub constantly.

This channel is for PR awareness and discussion, not for the actual code review (that happens in GitHub). Think of it as the PR notification feed with space for quick team comments.

**What the bot posts:**

PR opened:
```
📬 PULL REQUEST OPENED — #24

Title:    Add CloudWatch memory alarm configuration
Author:   Bhargav
Branch:   feature/cw-memory-alarms → main
Labels:   observability, backend
Files:    4 changed (+127 −12)

Description:
  Adds CloudWatch memory alarm for all EC2 instances as per action item
  from INC-007 post-mortem (Task #49).

→ Review: github.com/aaryan778/ASTRA/pull/24
```

PR review requested:
```
👀 REVIEW REQUESTED — PR #24

Requested from: Nithish, Aaryan
Title: Add CloudWatch memory alarm configuration
→ github.com/aaryan778/ASTRA/pull/24
```

PR merged:
```
✅ PULL REQUEST MERGED — #24

Title:    Add CloudWatch memory alarm configuration
Merged by: Aaryan
Branch:   feature/cw-memory-alarms → main
Closes:   Task #49

→ github.com/aaryan778/ASTRA/pull/24
```

PR closed without merge:
```
🚫 PULL REQUEST CLOSED (not merged) — #24
Title:    Add CloudWatch memory alarm configuration
Closed by: Bhargav
Reason:   [check GitHub for details]
```

---

**PR guidelines (post your PR here too when you open it):**

When you open a PR, copy the GitHub link here and add context:
```
PR #24 — CloudWatch Memory Alarm Config

This is the action item from INC-007 post-mortem.
Added alarms for all existing instances + added it to the Terraform module
so future instances get it automatically.

Needs review from someone familiar with CloudWatch config — @Sai or @Aaryan.
Happy to walk through it on a call if easier.

→ github.com/aaryan778/ASTRA/pull/24
```

**PR review expectations:**
- PRs should be reviewed within 24 hours of being opened during active sprints
- Leave a comment in the GitHub PR, not just in Discord
- Approvals and change requests go in GitHub. Use this channel for quick pings and awareness

**Rules:**
- Tag the people you want to review when you post your PR here. Don't rely on GitHub notifications alone.
- If a PR is blocked waiting for review for more than 24 hours, post a reminder here.
- Don't merge your own PRs without at least one approval from someone else (except Aaryan for urgent hotfixes).

---

## #release-notes

Every significant release of ASTRA gets documented here. This is the changelog — what changed, what was fixed, what was added, and what it means for the team.

Release notes aren't just for external users. They're for the team. Six months from now, when something breaks and you can't figure out when it started, the release notes are where you look.

**What belongs here:**
- Release notes for every version tag
- Breaking changes (especially important)
- Migration steps required after a release
- Known issues at time of release
- Hotfix notes for critical patches

**Release note format:**

```
RELEASE | ASTRA v1.4.0
Released: April 7, 2024
Deployed to staging: April 7 at 10:15 UTC
Deployed to production: April 7 at 15:30 UTC
Released by: Aaryan

────────────────────────────────────────────

NEW FEATURES
  • Incident detail page — full incident thread, RCA report, and
    timeline now accessible at /incidents/[id]
  • Task creation from incidents — use /incident and select
    "Create Task" to auto-link tasks to incidents
  • Mobile-responsive layout for dashboard and incident list

IMPROVEMENTS
  • RCA engine prompt v3 — improved contributing factor detection
    (accuracy up from 71% to 83% on benchmark suite)
  • Ollama inference timeout increased from 60s to 120s for complex incidents
  • CloudWatch log query now includes 90-minute window (was 60 minutes)
  • Bundle size reduced by 12KB (removed unused recharts components)

BUG FIXES
  • Fixed severity badge color not appearing on dark backgrounds
  • Fixed duplicate log entries during CloudWatch connection retry
  • Fixed sprint summary not including tasks closed on the last day of sprint

BREAKING CHANGES
  ⚠️ API response format change for /v1/incidents
     Added `github_issue_id` field to incident objects.
     If you're calling this endpoint directly, update your code to handle
     the new field (it's nullable for older incidents).

KNOWN ISSUES
  • Grafana dashboard shows incorrect timezone for UTC+5:30 users — fix in v1.4.1
  • /task search is case-sensitive — fix in v1.4.1

MIGRATION STEPS
  1. Run database migration: npm run db:migrate
     (Adds github_issue_id column to incidents table)
  2. No other migration steps required

ROLLBACK INSTRUCTIONS
  If needed: Vercel instant rollback to v1.3.2
  Database: Migration is backwards-compatible, no rollback needed
```

**Versioning convention:**
```
MAJOR.MINOR.PATCH

MAJOR:  Breaking changes that require migration
MINOR:  New features, backwards-compatible
PATCH:  Bug fixes, no new features

Examples:
  v1.0.0  — Initial release
  v1.1.0  — Added sprint board bot
  v1.1.1  — Fixed sprint bot command parsing
  v2.0.0  — RCA engine v2 with new output format (breaking)
```

**Hotfix format (for urgent patches):**
```
HOTFIX | ASTRA v1.4.1
Released: April 8, 2024 at 09:45 UTC
Reason: Critical bug — RCA reports not posting to Discord after v1.4.0

Fix: Corrected Discord webhook URL environment variable name mismatch
     between backend and Discord bot service

Impact: RCA reports were silently failing to post for ~18 hours.
        All unposted reports have been retroactively delivered.

No migration steps required.
No rollback needed.
```

**Rules:**
- Every production release gets a release note here, no matter how small.
- Breaking changes must be in bold/highlighted and must include migration steps.
- Release notes should be posted here before or at the same time as the production deployment.
- Tag the team when posting release notes so everyone knows something changed.
