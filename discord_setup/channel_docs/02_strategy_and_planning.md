# STRATEGY & PLANNING — Channel Docs

---

## #project-requirements

This is where we define what ASTRA is supposed to do — not how it does it, but what it needs to accomplish. Requirements are the ground truth. When someone disagrees about whether a feature is needed or how something should behave, this channel is where you come to settle it.

Every requirement posted here should be clear enough that someone who just joined the team can read it and understand exactly what's expected — no ambiguity, no "it depends."

**Two types of requirements we track:**

**Functional Requirements** — what the system does
These describe specific behaviors. If ASTRA is supposed to detect an EC2 failure and generate an RCA report within 5 minutes, that's a functional requirement.

```
FR-001 | Log Ingestion
The system must be able to ingest logs from AWS CloudWatch in real time.
Logs must be parsed and stored in a queryable format within 30 seconds of arrival.
Status: Approved
Owner: Bhargav
```

**Non-Functional Requirements** — how well the system does it
These describe performance, reliability, privacy, scalability constraints.

```
NFR-001 | Data Privacy
No log data or user data shall be sent to any third-party service.
All LLM inference must happen locally via Ollama.
Status: Approved
Owner: Aaryan
```

**How to post a requirement:**
```
[FR/NFR]-[NUMBER] | Short Title
Description: What exactly is required. Be specific.
Acceptance Criteria: How do we know this requirement is met?
Status: Draft / In Review / Approved / Deprecated
Owner: Who is responsible for this
```

**Statuses explained:**
- `Draft` — written but not yet reviewed by the team
- `In Review` — being discussed, may change
- `Approved` — locked in, we're building to this
- `Deprecated` — no longer applies, kept for history

**Rules:**
- Don't add a requirement without a discussion first. Bring it up in `#general-discussion` or the relevant channel, then formalize it here once there's agreement.
- Don't modify an Approved requirement without flagging it. Post a message saying what changed and why.
- Requirements live forever in this channel even if deprecated. Don't delete them.

---

## #problem-statements

Before we build anything we need to be clear about what problem we're actually solving. This channel is for writing out problem statements — structured descriptions of a specific issue or challenge the team is trying to address.

Think of it as the "why are we doing this" channel. Not the solution, not the implementation — just the problem, clearly articulated.

**Why this matters:**
It's really easy to jump straight into building something without properly defining the problem first. Then three weeks later someone asks "wait, why did we build it this way?" and nobody has a good answer. This channel prevents that.

**Format for a problem statement:**
```
PROBLEM-001 | 2-Hour EC2 Outage — No Automated Detection

Context:
During a recent incident, an EC2 instance became unresponsive for approximately
2 hours before anyone noticed. There was no automated alerting in place, and
the ops team had to manually trace through logs to identify the root cause.
This took significant time and the RCA was incomplete.

Problem:
We have no automated system that can detect infrastructure failures in real time,
correlate logs, and produce a structured root cause analysis without human
intervention. The current process is entirely manual, slow, and dependent on
individual expertise.

Impact:
- 2+ hour mean time to detection (MTTD)
- Incomplete RCAs that miss contributing factors
- Heavy reliance on a small number of people who understand the system deeply

What success looks like:
An AI agent that detects the failure, reads the relevant logs, and produces
a structured RCA report with recommendations — automatically, within minutes.

Status: Active
Owner: Aaryan
```

**Rules:**
- One problem per post. Don't combine multiple issues into one statement.
- Keep it focused on the problem. If you find yourself writing about the solution, stop and move it to `#system-architecture`.
- Link related requirements from `#project-requirements` if they exist.

---

## #system-architecture

This is the technical design channel. Once we know what we're building (requirements) and why (problem statements), this is where we figure out how. Architecture diagrams, system designs, data flow diagrams, component breakdowns — all of it lives here.

We're using eraser.io for diagrams. Export or screenshot your diagrams and post them here with explanation. Don't just post a diagram and leave — walk people through it.

**What belongs here:**
- High-level system architecture diagrams (how all components connect)
- Data flow diagrams (how logs move from EC2 → CloudWatch → AI Engine → Discord)
- Component diagrams (what each service does and how they talk to each other)
- API design decisions (REST vs GraphQL, endpoint structure, etc.)
- Database schema designs
- Infrastructure layout (which services run where, what talks to what)
- Architecture Decision Records (ADRs) — documented decisions about why we chose one approach over another

**Architecture Decision Record (ADR) format:**
```
ADR-001 | Use Ollama for LLM Inference Instead of OpenAI API

Date: April 7, 2024
Status: Accepted

Context:
We need an LLM to power the RCA engine. We evaluated OpenAI's API and
local inference via Ollama.

Decision:
We will use Ollama with a locally hosted model (Llama 3 or Mistral).

Reasoning:
- Privacy: no log data leaves our infrastructure
- Cost: no per-token API costs at scale
- Control: we can fine-tune the model on our own RCA data
- Dependency: no reliance on third-party API availability

Trade-offs:
- Slower inference than OpenAI API on current hardware
- Requires maintaining our own model serving infrastructure
- Model quality may be lower than GPT-4 initially

Alternatives considered:
- OpenAI API (rejected: privacy and cost concerns)
- Anthropic Claude API (rejected: same privacy concerns)
```

**Rules:**
- Every significant architectural decision should have an ADR. If you decided something, document it.
- When a design changes, don't delete the old post — add a reply or new post explaining what changed and why.
- Tag diagrams with what they represent: `[HIGH-LEVEL]`, `[DATA-FLOW]`, `[COMPONENT]`, `[DB-SCHEMA]`, `[INFRA]`

---

## #objectives-and-milestones

This is where we track the big-picture goals for ASTRA — not individual tasks (that's the sprint board), but the larger milestones that tell us whether the project is on track.

Think of this like the roadmap. Sprints are weeks, milestones are months.

**Milestone format:**
```
MILESTONE-001 | Phase 1 Complete — Core Infrastructure

Target Date: May 15, 2024
Status: In Progress

What this milestone means:
By this date, we should have:
  ✅ Discord server fully set up and operational
  ✅ GitHub Projects sprint board connected
  ⬜ AWS account created with CloudWatch configured
  ⬜ EC2 test instance running and monitored
  ⬜ Ollama server installed and serving a base model
  ⬜ Log ingestion pipeline reading from CloudWatch

Definition of Done:
A simulated EC2 failure triggers a CloudWatch alarm, which is ingested
by our pipeline and visible in the ASTRA system. The AI engine doesn't
need to work yet — just the data pipeline.

Owner: Aaryan
```

**OKR format (if we use OKRs for a quarter):**
```
OBJECTIVE: Build a working AI-powered RCA pipeline
  KR1: Mean time to RCA generation < 5 minutes for simulated incidents
  KR2: RCA accuracy validated against 10 known historical incidents
  KR3: Zero external API calls during RCA — fully local inference
```

**Rules:**
- Milestones should be updated when their status changes. If something is blocking a milestone, say so.
- Don't create a milestone for something that's really just a sprint task. Milestones represent meaningful progress on the project at a high level.
- Aaryan approves milestones. Anyone can propose them.

---

## #research-and-development

This is the exploratory channel. Not everything we're building has a clear answer or an established best practice — some of it we have to figure out ourselves. This channel is where that figuring-out happens.

If you're reading papers on RCA methodologies, experimenting with different prompt strategies for the LLM, testing how Ollama performs on different hardware, or trying to understand how Grafana and Prometheus work together — document what you're learning here.

**What belongs here:**
- Notes from research sessions ("I spent two hours reading about anomaly detection in time-series logs, here's what I found")
- Experiment results ("Tested Llama 3 vs Mistral 7B on our RCA prompts, Mistral was faster but less accurate on multi-cause failures")
- Questions the team is actively trying to answer
- Links to relevant papers with summaries (not just the link — summarize the key points)
- Proposals for new approaches we haven't tried yet
- Comparisons between tools or methods

**How to format a research note:**
```
RESEARCH | Anomaly Detection Approaches for Log Analysis

Question we're trying to answer:
What's the best way to detect anomalies in EC2 system logs before they
escalate into full failures?

What I looked at:
- [Paper] "LogAnomalyDetection using Drain3" — fast template-based parsing
- [Tool] OpenTelemetry for structured log collection
- [Approach] Statistical thresholding vs ML-based detection

Key findings:
- Drain3 is fast and works well on unstructured logs. Could pair with CW.
- ML approaches need labeled data we don't have yet — not realistic for Phase 1
- Statistical thresholding is simpler but will miss complex failure patterns

Recommendation:
Start with Drain3 for log parsing + simple threshold alerts in Phase 1,
then layer ML-based detection in Phase 2 once we have incident history data.

Next steps:
Prototype Drain3 integration with CloudWatch log stream — Bhargav to own this

Status: In Progress
Owner: Asif
```

**Rules:**
- This channel is for sharing what you've learned, not just for asking questions. If you're asking a question, include what you've already tried or read.
- Proposals made here should eventually get formalized as requirements (`#project-requirements`) or architecture decisions (`#system-architecture`) if they're adopted.
- Label posts with `[RESEARCH]`, `[EXPERIMENT]`, `[PROPOSAL]`, or `[QUESTION]` at the start.
