# SIMULATION & QUALITY ASSURANCE — Channel Docs

---

## #ec2-failure-simulation

Before ASTRA goes anywhere near a real production environment, we need to know it actually works. That means deliberately breaking things in a controlled environment and verifying that the system responds correctly. This channel is where we design, run, and document those simulations.

The core scenario we're building toward is the one from the problem statement: an EC2 instance goes unresponsive for 2 hours with no automated detection. We simulate that, run it through ASTRA, and see what happens. Then we make it better and run it again.

**What belongs here:**
- Simulation scenario designs (what failure we're simulating and how)
- Simulation run logs (what happened when we ran it)
- Results and observations
- Chaos engineering experiment designs
- Infrastructure setup for the simulation environment (separate from production)
- Post-simulation analysis (did ASTRA catch it? How long did it take? Was the RCA accurate?)

**Our simulation environment:**
We run simulations on a dedicated EC2 instance (or set of instances) that is completely isolated from anything real. This is not the production environment. Simulations can — and should — break things. That's the point.

```
Simulation Environment:
  Instance: astra-dev-ec2-simulation-01
  AMI: Amazon Linux 2
  Type: t3.medium (enough to run meaningful scenarios)
  Region: us-east-1
  Isolation: separate VPC, no connection to production
  CloudWatch: logs and metrics forwarded to dev log groups
```

**Failure scenario library (what we're building up):**

```
SCENARIO-001 | Memory Exhaustion
Description:
  Run a script that continuously allocates memory until the OOM killer
  triggers and kills the main application process.
How to trigger:
  stress --vm 1 --vm-bytes 90% --timeout 300s
Expected ASTRA behavior:
  - CloudWatch memory alarm fires within 5 minutes
  - ASTRA agent triggers investigation
  - RCA identifies memory exhaustion as root cause
  - Report posted to #rca-output-reports within 10 minutes
Status: Designed, not yet run

SCENARIO-002 | CPU Spike
Description:
  Saturate CPU to 100% for an extended period, causing application
  timeouts and degraded response times.
How to trigger:
  stress --cpu 4 --timeout 300s
Expected ASTRA behavior:
  - CPU alarm fires
  - ASTRA identifies CPU saturation
  - Report includes process list showing offending workload
Status: Designed, not yet run

SCENARIO-003 | Disk Full
Description:
  Fill the root filesystem to 100%, causing application writes to fail
  and logs to stop being written.
How to trigger:
  fallocate -l 95% /tmp/fillfile
Expected behavior:
  - Disk alarm fires
  - Application write errors appear in logs
  - ASTRA identifies disk exhaustion
  - Tricky: log collection may also fail if disk is full
Status: Designed, not yet run

SCENARIO-004 | Network Partition
Description:
  Block outbound network traffic using iptables, simulating a network
  partition or security group misconfiguration.
How to trigger:
  iptables -A OUTPUT -p tcp --dport 443 -j DROP
Expected behavior:
  - CloudWatch metrics stop appearing (no outbound to CW)
  - This is a hard case — how does ASTRA detect a silent failure?
Status: Design in progress

SCENARIO-005 | Application Process Crash Loop
Description:
  Crash the main application process repeatedly to simulate a crash loop
  (like a Kubernetes CrashLoopBackOff but on bare EC2).
How to trigger:
  Custom script that kills the process every 30 seconds
Expected behavior:
  - Repeated restart events in system logs
  - ASTRA identifies crash loop pattern across multiple events
Status: Designed, not yet run

SCENARIO-006 | Runaway Log Volume (2hr Outage Scenario)
Description:
  This is the core scenario from our problem statement. Simulate the
  exact conditions of the original 2-hour outage — memory leak in the
  log aggregation service with no alerting.
How to trigger:
  Custom memory-leaking service + disabled CloudWatch alarms for first phase
Expected behavior:
  - ASTRA catches it before 30 minutes (vs 2 hours manual)
  - Full RCA generated automatically
  - Compare against historical manual RCA quality
Status: Design in progress — this is our primary benchmark
```

**How to post a simulation run result:**
```
SIM RUN | SCENARIO-001 — Memory Exhaustion
Date: April 7, 2024
Runner: Bhargav
Environment: astra-dev-ec2-simulation-01

Run summary:
  Trigger time:              04:15:00 UTC
  CloudWatch alarm fired:    04:17:32 UTC (2m 32s)
  ASTRA agent triggered:     04:17:45 UTC (13s after alarm)
  Log collection complete:   04:19:10 UTC
  RCA report posted:         04:21:33 UTC

Total time to RCA: 6 minutes 33 seconds

RCA accuracy assessment:
  Root cause identified correctly: YES
  Contributing factors found: 2/3 (missed deployment version correlation)
  Recommendations useful: YES

Issues observed:
  - Agent took 13s to pick up the CloudWatch alarm — investigate polling interval
  - Missing deployment version in RCA — context builder needs improvement

Tasks created:
  - Task #23: Reduce agent CloudWatch alarm polling interval
  - Task #24: Add deployment history to RCA context builder

Link to full RCA report: [Discord message link]
```

**Rules:**
- Never run simulations against production infrastructure. Simulation environment only.
- Always document every run even if it failed or produced unexpected results. Failed runs are valuable.
- Create a GitHub task for every issue observed during a simulation run.
- Reset the simulation environment to a clean state after each run.

---

## #log-ingestion-pipeline

Step 1 of the ASTRA pipeline is reading and ingesting logs. Before the AI engine can do anything useful, we need logs — structured, parsed, and queryable. This channel is for building, testing, and maintaining that pipeline.

The log ingestion pipeline is the foundation everything else sits on. If it's unreliable, slow, or dropping logs, the RCA engine is working with incomplete information and its output can't be trusted.

**What the pipeline does:**
```
EC2 Instance
    ↓ (CloudWatch Agent)
AWS CloudWatch Log Groups
    ↓ (Log subscription filter or direct query)
Log Fetcher (Python service)
    ↓
Log Parser (Drain3 template extraction)
    ↓
Log Normalizer (consistent timestamp, severity, source format)
    ↓
Log Store (structured, queryable — PostgreSQL or similar)
    ↓
Available to RCA Engine
```

**What belongs here:**
- Pipeline architecture decisions and changes
- Parser configuration and template updates (Drain3 log templates)
- Performance metrics for the pipeline (throughput, latency, error rate)
- Issues with log formats from different sources
- New log sources being added to the pipeline
- Testing results for pipeline components

**Log format standard (what everything gets normalized to):**
```json
{
  "timestamp": "2024-04-07T04:15:32.123Z",
  "level": "ERROR",
  "source": "astra-dev-ec2-simulation-01",
  "service": "app-server",
  "message": "Out of memory: Kill process 1234 (python) score 892 or sacrifice child",
  "raw": "[Mon Apr  7 04:15:32 2024] Out of memory: Kill process...",
  "tags": ["oom", "memory", "kill"],
  "parsed_fields": {
    "process_name": "python",
    "pid": 1234,
    "oom_score": 892
  }
}
```

**Drain3 log parsing:**
Drain3 is a fast log template extraction library. It learns log patterns and extracts variable parts (like IP addresses, PIDs, timestamps) from fixed structure. This is how we turn unstructured log lines into something the RCA engine can reason about systematically.

Document new log templates discovered here:
```
TEMPLATE-001 | OOM Kill Event
Raw: "Out of memory: Kill process 1234 (python) score 892 or sacrifice child"
Template: "Out of memory: Kill process <*> (<*>) score <*> or sacrifice child"
Variables: pid, process_name, oom_score
Tag: oom-kill
```

**Pipeline health metrics to track:**
```
- Logs ingested per minute
- Parse success rate (% of logs successfully parsed vs raw fallback)
- Processing latency (time from log creation to availability in store)
- Error rate (logs that failed to ingest)
- Queue depth (how many logs are waiting to be processed)
```

**Rules:**
- The pipeline must never drop logs silently. Failed ingestion goes to a dead letter queue and gets flagged.
- Every new log source needs a parser configuration documented here before it goes live.
- Pipeline changes that affect the schema of stored logs need a migration plan before deployment.

---

## #rca-output-reports

This is where ASTRA posts its finished work. Every RCA report generated by the AI engine — whether from a real incident or a simulation run — gets posted here automatically by the bot.

This channel serves as a permanent record of every investigation ASTRA has conducted. It's also where the team reviews the AI's output, assesses quality, and flags issues for improvement.

**What gets posted here:**
- Every RCA report generated by ASTRA (automatically, via bot)
- Quality assessments of RCA reports (posted manually by team members after review)
- Corrections to incorrect RCA reports
- Links to the corresponding GitHub issue for each incident

**What an RCA report post looks like:**
```
═══════════════════════════════════════════
ASTRA RCA REPORT — INC-003
Generated: April 7, 2024 at 04:47 UTC
Incident: EC2 instance i-0a1b2c3d unresponsive
Investigation duration: 6 minutes 33 seconds
═══════════════════════════════════════════

ROOT CAUSE
Memory exhaustion on astra-dev-ec2-simulation-01 caused the Linux OOM
killer to terminate the primary application process (PID 1234, python).
This was triggered by a memory leak in the log aggregation service,
introduced in deployment v2.3.1 (deployed April 6 at 22:10 UTC).

CONTRIBUTING FACTORS
1. No CloudWatch memory alarm was configured for this instance
2. The log aggregation service had no memory usage cap or limit
3. No automated rollback triggered on process termination

TIMELINE
03:58 UTC  Memory usage crossed 75% — no alert configured
04:08 UTC  Memory reached 85% — application response time degraded
04:12 UTC  Memory at 95% — OOM killer activated
04:14 UTC  Application process killed — instance stops responding
04:15 UTC  ASTRA CloudWatch alarm triggered (CPU + memory spike pattern)
04:17 UTC  ASTRA agent began investigation
04:21 UTC  RCA report generated

RECOMMENDATIONS
IMMEDIATE
  → Restart EC2 instance i-0a1b2c3d
  → Roll back deployment to v2.3.0

SHORT-TERM
  → Add CloudWatch memory alarm: threshold 80%, action: notify
  → Set memory limit on log aggregation service: 512MB max

LONG-TERM
  → Implement automated rollback on OOM events
  → Add memory leak detection to CI pipeline
  → Review all services for missing resource limits

CONFIDENCE: High
Supporting evidence: 9/11 log signals consistent with memory exhaustion hypothesis

GitHub Issue: #47
Thread: Continue discussion below ↓
═══════════════════════════════════════════
```

**After a report is posted — review process:**
Within 24 hours of a report being posted, someone on the team should review it and reply in the thread with an assessment:

```
REVIEW — INC-003 RCA

Reviewed by: Aaryan
Date: April 7, 2024

Root cause: CORRECT — confirmed by checking deployment changelog
Contributing factors: PARTIAL — missed that the memory alarm was 
  disabled by a previous team member during testing and never re-enabled
Timeline: ACCURATE
Recommendations: GOOD — implementing items 1-3 as tasks

Quality score: 8/10
Issues to improve:
  - Should have checked alarm configuration history, not just current state
  - Created task #48 to improve alarm history lookup in context builder
```

**Rules:**
- Don't delete reports. Even bad ones stay — they're training data for improving ASTRA.
- Always post a review within 24 hours of a simulated incident report.
- If a report is significantly wrong, create a task to fix the underlying issue in the RCA engine.
- Use threads for all discussion about a specific report. Keep the main channel clean.

---

## #test-scenarios-and-cases

This is the QA repository for ASTRA. Every failure scenario, edge case, regression test, and acceptance test we define lives here. The goal is to have a comprehensive test suite that we can run against any version of ASTRA to know whether it's working correctly.

This is different from `#ec2-failure-simulation` — simulation is about running actual failure scenarios on real infrastructure. This channel is about defining and tracking the test cases themselves, including unit-level tests for individual pipeline components.

**What belongs here:**
- Test case definitions (what we're testing and what the expected outcome is)
- Test suite organization and coverage tracking
- Regression test results (did a change break something that was working?)
- Edge cases discovered during simulations or incidents
- Acceptance criteria for new features
- Known failing tests and their status

**Test case format:**
```
TEST-001 | Memory Exhaustion — Basic Detection

Category: Integration — Log Ingestion + RCA Engine
Priority: Critical (core scenario)

Setup:
  - Clean simulation EC2 instance
  - CloudWatch agent running and forwarding logs
  - ASTRA pipeline running in dev environment

Test steps:
  1. Start memory stress on EC2 instance
  2. Record exact time stress starts
  3. Monitor CloudWatch for alarm
  4. Wait for ASTRA to generate RCA report
  5. Compare against expected output

Expected outcome:
  - CloudWatch alarm fires within 3 minutes of memory crossing 80%
  - ASTRA RCA report generated within 10 minutes total
  - Root cause correctly identified as memory exhaustion
  - At least 2 recommendations included in report
  - Confidence score > 70%

Pass criteria: ALL expected outcomes met
Fail criteria: Any expected outcome NOT met

Current status: Passing (last run April 5)
Last runner: Bhargav
```

**Test categories:**

```
Unit Tests — individual components in isolation
  U-001 to U-099: Log parser unit tests
  U-100 to U-199: RCA prompt output parser tests
  U-200 to U-299: Agent decision logic tests

Integration Tests — components working together
  I-001 to I-099: Log ingestion pipeline end-to-end
  I-100 to I-199: RCA engine integration (log in → report out)
  I-200 to I-299: Agent full pipeline tests

Simulation Tests — real infrastructure scenarios
  S-001 to S-099: EC2 failure scenarios (links to #ec2-failure-simulation)

Regression Tests — things that broke before and must not break again
  R-001 to R-099: Known regression cases

Edge Cases — unusual or boundary conditions
  E-001 to E-099: Incomplete or corrupted logs
  E-100 to E-199: Multi-cause failures
  E-200 to E-299: Silent failures (no logs generated)
```

**Rules:**
- Every bug that gets fixed should have a regression test added so it can't silently come back.
- Test results should be posted here after every significant change to the codebase.
- Edge cases found during real incidents or simulations should be formalized as test cases here within 48 hours.
- Tests are never deleted — they can be marked deprecated but the definition stays.
