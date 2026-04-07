# INCIDENT MANAGEMENT & AUDIT — Channel Docs

---

## #active-incidents

This is the most critical operational channel on the server. When something goes wrong — an EC2 instance is down, a service is unresponsive, an alarm fires — this is where it gets reported and tracked. Everything else in ASTRA exists to make this channel less necessary over time, but until then, it's the nerve center.

There are two ways to report an incident here:

---

**Method A — Quick Message (for fast reporting)**

Just type what you see. The bot reads it, detects severity from keywords, creates a thread automatically, and assigns an incident ID.

```
"EC2 instance is down, been down for 10 minutes, can't SSH in"

Bot creates thread:
INC-007 🔴 CRITICAL | EC2 Instance Unreachable — Apr 7 04:32 UTC
```

Severity keywords the bot detects:
```
🔴 CRITICAL  →  down, unresponsive, outage, critical, offline, failed, unreachable, crash
🟡 WARNING   →  slow, degraded, latency, warning, high memory, high cpu, unstable
🔵 INFO      →  notice, monitoring, watching, investigating, update, info
```

If no keywords match, it defaults to 🟡 WARNING and you can correct it in the thread.

---

**Method B — Slash Command (for formal incident declaration)**

Use this when you want a properly structured incident from the start:

```
/incident
```

The bot opens a form:

```
Title:       [_________________________________]
Severity:    [🔴 CRITICAL          ▼]
Service:     [EC2 / API / Ollama / Pipeline / Other]
Description: [_________________________________]
Assigned to: [@Bhargav              ▼]
```

This creates a thread in the format:
```
INC-008 🔴 CRITICAL | Ollama Server Unresponsive — Apr 7 09:15 UTC
```

And simultaneously creates a GitHub issue linked to the incident.

---

**Inside the incident thread — what to post:**

Once you're inside the thread, keep a running log of what's happening. Don't wait until it's resolved to write things down — post updates as you go.

```
[04:32] @Bhargav — Instance i-0a1b2c3d is not responding to pings.
        SSH attempts timing out. CloudWatch shows CPU dropped to 0%.

[04:35] @Asif — Checking CloudWatch logs. Last log entry was 04:14.
        Looks like a hard stop, not a graceful shutdown.

[04:38] @Bhargav — Memory was at 97% before last log entry.
        Possible OOM kill. Waiting for ASTRA RCA report.

[04:47] 🤖 ASTRA — RCA report generated. See #rca-output-reports INC-007.
        Root cause: Memory exhaustion. Recommendations posted.

[04:52] @Aaryan — Approved restart. Go ahead.

[04:54] @Bhargav — Instance restarted. Monitoring for stability.

[05:05] @Bhargav — Instance stable. Memory at 45%. Services running.
        Closing incident. Post-mortem to follow in #post-incident-reviews.

[05:06] /incident close INC-007
```

---

**Incident lifecycle:**
```
OPEN → IN PROGRESS → RESOLVED → POST-MORTEM SCHEDULED → CLOSED
```

**Commands inside a thread:**
```
/incident update INC-007 "restarted instance, monitoring"
/incident assign INC-007 @Nithish
/incident severity INC-007 critical
/incident resolve INC-007 "instance restored, root cause identified"
/incident close INC-007
```

**Rules:**
- Every incident gets a thread. Don't discuss incidents in the main channel — only the opening message goes there.
- Update the thread regularly during an incident. Even "still investigating, nothing new" is a useful update.
- Never close an incident without scheduling a post-mortem. Even small incidents should have a brief one.
- Aaryan must approve any action that modifies infrastructure (restart, rollback, scaling). Post the request in the thread and wait for approval before acting.
- Don't delete incident threads after resolution. They're permanent records.

---

## #post-incident-reviews

Every incident gets a post-mortem. Not to blame anyone — that's not what this is for. The point is to understand what happened well enough that either it doesn't happen again, or if it does, we catch it faster and respond better.

Post-mortems happen within 48 hours of an incident being resolved while everything is still fresh. They don't have to be long. A 10-minute incident might have a one-page post-mortem. A 2-hour outage gets a more thorough one.

**Post-mortem template:**
```
POST-MORTEM | INC-007
Incident: EC2 instance i-0a1b2c3d unresponsive
Date: April 7, 2024
Duration: 04:14 UTC to 04:54 UTC (40 minutes)
Severity: CRITICAL
Author: Bhargav
Reviewers: Aaryan, Asif

─────────────────────────────────────────────

SUMMARY
A memory leak in the log aggregation service (introduced in v2.3.1)
caused the EC2 instance to exhaust available memory, triggering the OOM
killer and terminating the application process. The instance was
unresponsive for 40 minutes. ASTRA detected the issue via CloudWatch
alarm and generated an RCA report in under 7 minutes.

─────────────────────────────────────────────

TIMELINE
22:10 UTC (Apr 6)  — v2.3.1 deployed to astra-dev-ec2-simulation-01
03:58 UTC (Apr 7)  — Memory crossed 75%. No alert configured.
04:08 UTC          — Memory at 85%. Application response time degraded.
04:12 UTC          — Memory at 95%. OOM killer activated.
04:14 UTC          — Application killed. Instance stops responding.
04:15 UTC          — ASTRA CloudWatch alarm triggered.
04:17 UTC          — ASTRA agent began investigation.
04:21 UTC          — ASTRA RCA report generated. Team notified.
04:32 UTC          — Team acknowledged, Bhargav began investigation.
04:52 UTC          — Aaryan approved restart.
04:54 UTC          — Instance restarted. Services restored.

─────────────────────────────────────────────

ROOT CAUSE
Memory leak in log aggregation service v2.3.1. The service was
continuously buffering parsed log entries without flushing, causing
memory usage to grow linearly over approximately 6 hours.

─────────────────────────────────────────────

CONTRIBUTING FACTORS
1. No memory utilization CloudWatch alarm was configured
2. v2.3.1 was not load tested before deployment
3. The log aggregation service had no memory cap
4. No automated rollback triggered on process termination

─────────────────────────────────────────────

WHAT WENT WELL
- ASTRA detected and diagnosed the issue in under 7 minutes
- RCA was accurate — confirmed root cause and contributing factors
- Team response once notified was fast
- ASTRA's recommendation to roll back to v2.3.0 was correct

─────────────────────────────────────────────

WHAT COULD HAVE GONE BETTER
- 11-minute gap between ASTRA alarm and team acknowledgement
  (happened at 4AM — on-call process needed)
- Memory alarm should have been standard for all instances
- No pre-deployment memory testing

─────────────────────────────────────────────

ACTION ITEMS
Item 1: Add CloudWatch memory alarm to all EC2 instances (default config)
  Owner: Sai Purna | Due: April 10 | Task: #49

Item 2: Add memory leak test to CI pipeline for log aggregation service
  Owner: Nithish | Due: April 14 | Task: #50

Item 3: Set 512MB memory limit on log aggregation service
  Owner: Bhargav | Due: April 10 | Task: #51

Item 4: Define on-call rotation so incidents at odd hours get picked up
  Owner: Aaryan | Due: April 12 | Task: #52

─────────────────────────────────────────────

BLAMELESS NOTE
This post-mortem is blameless. The memory leak was a software defect,
not a human error. The focus is on system improvements, not on who
deployed v2.3.1. We improve the process, not punish the person.
```

**Rules:**
- Post-mortems are blameless. If a review starts feeling like blame, redirect it to system improvements.
- Every action item must have an owner, a due date, and a linked GitHub task before the post-mortem is closed.
- Post-mortems are posted here within 48 hours of incident resolution. No exceptions.
- After all action items are completed, reply to the post-mortem with a close-out summary.

---

## #access-violation-alerts

This channel tracks unauthorized access attempts — situations where someone tried to access a resource they don't have permission for, or where access patterns look suspicious. This is primarily a security monitoring channel.

In Phase 2, CloudWatch and our security tooling will automatically post alerts here. For now, it's where the team manually reports and discusses any access anomalies.

**What gets posted here:**
- Failed authentication attempts (multiple failures from same IP, odd hours, unusual accounts)
- IAM permission denied events from CloudWatch
- Attempts to access restricted channels or resources
- Unusual API call patterns
- Any access event that looks wrong even if it didn't technically fail

**Alert format (manual):**
```
ACCESS ALERT | IAM Permission Denied — S3 Bucket

Time: April 7, 2024 at 11:23 UTC
Resource: arn:aws:s3:::astra-prod-logs
Action attempted: s3:GetObject
Identity: arn:aws:iam::123456789:user/test-user-01
Result: DENIED (correct — this user shouldn't have access)
Source IP: 203.0.113.45

Context:
test-user-01 is a dev account that shouldn't have access to prod buckets.
This might be a misconfigured script or a genuine mistake. Investigating.

Status: Under investigation
Owner: Aaryan
```

**Automated alert format (Phase 2):**
```
🚨 ACCESS VIOLATION DETECTED
Time: 2024-04-07 11:23:45 UTC
Type: IAM_PERMISSION_DENIED
Resource: astra-prod-logs (S3)
Identity: test-user-01
Action: s3:GetObject
Source IP: 203.0.113.45
Risk Level: MEDIUM
→ Investigate in thread below
```

**Rules:**
- Only Aaryan and the SRE-designated team members can see this channel. It contains sensitive security information.
- Every alert gets investigated. Don't dismiss alerts as "probably fine" without actually checking.
- If an alert represents a real unauthorized access, escalate immediately and document the full investigation here.
- Access violation records are kept permanently. Never delete from this channel.

---

## #audit-and-compliance

Everything that happens in ASTRA that has a cost, a compliance implication, or that changes system state gets logged here. This is the audit trail — the record that answers "who did what, when, and why?"

This channel is not for day-to-day work discussion. It's a log. Posts here are structured records, not conversations.

**What gets logged here:**
- Infrastructure changes (new resource created, resource deleted, configuration changed)
- IAM role or permission changes
- Production deployments
- Cost anomalies or significant spending events
- Data access events for sensitive data
- ASTRA agent actions (what the agent did automatically and when)
- Any manual override of automated processes

**Audit entry format:**
```
AUDIT | Infrastructure Change

Timestamp: 2024-04-07 14:33:00 UTC
Actor: Aaryan (manual action)
Action: Created CloudWatch alarm — EC2 memory threshold 80%
Resource: astra-dev-ec2-simulation-01
Reason: Action item from INC-007 post-mortem (Task #49)
Change reference: Terraform commit abc1234
Approved by: N/A (Aaryan is Admin)
Reversible: YES — alarm can be deleted or modified
```

```
AUDIT | ASTRA Agent Action

Timestamp: 2024-04-07 04:21:00 UTC
Actor: ASTRA AI Agent (automated)
Action: Read CloudWatch logs for instance i-0a1b2c3d
        Queried CloudWatch metrics for the past 24 hours
        Generated and posted RCA report INC-007
Resource: CloudWatch log group astra-dev-logs
Triggered by: CloudWatch alarm astra-dev-ec2-memory-alarm
No infrastructure modified — read-only actions only
```

**What "costly operations" means here:**
Some things cost real money — CloudWatch Insights queries on large datasets, Splunk queries on months of logs, large S3 data transfers. Flag them here so we can track spending patterns.

```
AUDIT | Costly Operation

Timestamp: 2024-04-07 15:00:00 UTC
Actor: Asif
Operation: CloudWatch Insights query across 90 days of logs
Estimated cost: ~$2.40 (based on data scanned)
Reason: Investigating historical failure pattern for RCA benchmark
Result: Found 6 prior similar events — documented in #research-and-development
```

**Rules:**
- This channel is append-only. Post entries, never edit or delete them.
- ASTRA agent actions are logged automatically (bot does this). Manual actions are logged by the person who took them.
- If you make a significant change and don't log it here, someone will ask you to retroactively. Just do it upfront.
- This is not a discussion channel. Conversation goes in the relevant technical channel. This is just the record.

---

## #cost-anomaly-alerts

AWS costs can sneak up on you fast. This channel is specifically for tracking unexpected or unusually high spending — whether it's a CloudWatch query that scanned too much data, an EC2 instance left running overnight, or a data transfer bill that came out of nowhere.

In Phase 2, AWS Cost Anomaly Detection will post here automatically when it detects spending that's outside normal patterns. For now, this is where we post manual cost observations.

**What belongs here:**
- AWS Cost Anomaly Detection alerts (Phase 2, automated)
- Monthly cost summaries (posted at the start of each month)
- One-off observations about unexpectedly high spending
- Budget alerts when we approach defined thresholds
- Cost optimization recommendations

**Monthly budget summary format:**
```
COST SUMMARY — March 2024

Budget: $150/month (dev/testing phase)

Actual spend:
  EC2 compute:          $42.30
  CloudWatch:           $18.50  ⚠️ Higher than expected
  Data transfer:        $8.20
  S3 storage:           $3.10
  Splunk (free tier):   $0.00
  New Relic (free):     $0.00
  Other:                $5.80
  ─────────────────────────────
  Total:                $77.90 (52% of budget)

Notes:
  CloudWatch costs jumped because we added 4 new log groups during
  simulation testing. Review whether all of them need to stay.

Action items:
  - Remove temporary simulation log groups from February (Sai Purna)
  - Review CloudWatch Insights query frequency in RCA engine (Asif)
```

**Cost anomaly alert format:**
```
⚠️ COST ANOMALY DETECTED

Service: AWS CloudWatch
Expected daily spend: ~$0.60
Actual daily spend: $4.20 (7x normal)
Detection time: April 7, 2024

Likely cause: High volume of CloudWatch Insights queries during simulation
testing — investigation needed.

Action: Review CloudWatch query logs and identify source.
Owner: Aaryan
```

**Rules:**
- Check this channel at least weekly. Costs don't fix themselves.
- Every cost anomaly gets investigated and explained, even if it's benign.
- If you ran something that you know cost more than usual, post about it here proactively. Don't wait for the bill.
- Monthly summaries are posted by Aaryan on the first of each month.
