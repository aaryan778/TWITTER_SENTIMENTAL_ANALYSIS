# AI ENGINE — CORE — Channel Docs

---

## #llm-development

This is where we build the brain of ASTRA. The LLM is the core of everything — it's what takes raw log data, understands what went wrong, and produces something a human can actually act on. We're running this entirely on Ollama, which means it's local, private, and fully under our control. No log data ever leaves our infrastructure.

This channel is specifically for the development of the LLM itself — model selection, fine-tuning, server configuration, prompt engineering at the model level, and anything else that touches the actual language model.

**What we're building:**
A locally hosted LLM via Ollama that:
- Understands infrastructure logs (EC2, CloudWatch, system logs)
- Can reason about failure patterns and contributing causes
- Produces structured RCA reports in a consistent format
- Runs fast enough to be useful during an active incident

**What belongs here:**
- Model evaluation results (which model handles our use case best)
- Fine-tuning experiments and results
- Ollama configuration and model serving setup
- Discussions about model size vs performance trade-offs
- Prompt templates at the system/model level
- Hardware requirements and optimization (GPU memory, batch sizes, etc.)
- Version tracking — which model version we're running in each environment

**How to post a model evaluation:**
```
MODEL EVAL | Llama 3 8B vs Mistral 7B — RCA Task Performance

Test setup:
- 10 simulated EC2 failure scenarios
- Same system prompt for both models
- Running on [hardware spec]
- Ollama version: X.X.X

Results:
                    Llama 3 8B    Mistral 7B
Accuracy (RCA)         78%           71%
Avg. inference time    4.2s          2.8s
Token output quality   Higher        Lower on complex multi-cause
Memory usage           ~6GB          ~5GB

Observations:
Llama 3 produces more structured output and handles multi-cause failures
better. Mistral is faster but sometimes misses secondary contributing factors.

Recommendation: Use Llama 3 8B for now. Revisit when we have more
failure scenarios to test against.

Owner: Sai Purna
Date: April 7, 2024
```

**Current model in use:**
Always keep a pinned message at the top of this channel with the current production model, version, and any important configuration notes.

**Rules:**
- Never test against real production logs without approval. Use synthetic or simulated data in development.
- Document every model change. If you switch models, post why and what you expect to improve.
- Prompt engineering that affects how the model responds at a task level goes in `#rca-engine-development`. System-level prompt configuration (the base instructions baked into the model) goes here.

---

## #rca-engine-development

The RCA engine is the layer that sits between the log ingestion pipeline and the LLM. Its job is to take raw, parsed log data, structure it into something the LLM can reason about, send it to Ollama, and then format the response into a proper RCA report.

Think of it like this: the LLM is the analyst, and the RCA engine is the process that briefs the analyst, manages the conversation, and writes up the final report.

**What belongs here:**
- RCA pipeline architecture (how logs flow through to the final report)
- Prompt design and engineering for RCA tasks (the actual prompts we send to Ollama)
- Output format design (what does a finished RCA report look like)
- Accuracy testing against known failure scenarios
- Edge cases and failure modes (what happens when logs are incomplete or corrupted)
- Iteration history — what we tried, what worked, what didn't

**The RCA pipeline (what we're building):**
```
CloudWatch Logs
      ↓
Log Parser (Drain3 or similar)
      ↓
Log Summarizer (reduce noise, extract key events)
      ↓
Context Builder (add system state, timeline, related metrics)
      ↓
Ollama LLM (RCA prompt)
      ↓
Output Parser (extract structured RCA from LLM response)
      ↓
Report Formatter
      ↓
Discord Post (#rca-output-reports) + GitHub Issue (linked to incident)
```

**RCA output format (what we're targeting):**
```
RCA REPORT — INC-001
Generated: April 7, 2024 04:47 UTC
Incident: EC2 instance i-0a1b2c3d unresponsive

ROOT CAUSE:
Memory exhaustion on the instance caused the kernel OOM killer to terminate
the primary application process. This was triggered by an uncontrolled
memory leak in the log aggregation service introduced in deployment v2.3.1.

CONTRIBUTING FACTORS:
1. No memory usage alerting was configured for this instance
2. The log aggregation service had no memory cap set
3. The deployment rollback procedure was not initiated automatically

TIMELINE:
03:58 UTC — Memory usage crosses 80% threshold (no alert triggered)
04:12 UTC — Memory reaches 95%, OOM killer activates
04:14 UTC — Application process terminated, instance stops responding
04:32 UTC — Incident detected manually

RECOMMENDATIONS:
1. Immediate: Restart instance and roll back to v2.3.0
2. Short-term: Add CloudWatch memory alarms with 80% threshold
3. Long-term: Add memory limits to log aggregation service container
   and implement automated rollback on memory threshold breach

CONFIDENCE: High (8 of 10 log signals consistent with this conclusion)
```

**How to post a prompt iteration:**
```
PROMPT v3 — RCA Generation

Change from v2:
Added explicit instruction to list contributing factors separately from root cause.
Also added confidence scoring instruction.

Prompt:
"""
You are an SRE expert analyzing infrastructure logs to determine the root
cause of a system failure. You will be given a timeline of log events...
[full prompt]
"""

Test results vs v2:
- Contributing factors section improved significantly
- Confidence scoring adds useful signal
- Still struggles with multi-service failure correlation — working on it

Status: Testing
Owner: Asif
```

**Rules:**
- Version your prompts. Don't just overwrite v2 with v3 — keep the history.
- Every prompt change needs test results. Don't deploy a new prompt without running it against the test scenarios in `#test-scenarios-and-cases`.
- If an RCA report comes out wrong or incomplete, document it here as a known edge case and create a task to fix it.

---

## #agent-framework

The agent is what makes ASTRA autonomous. It's not just an LLM that answers questions — it's a system that watches for incidents, decides when to investigate, gathers context, calls the RCA engine, and takes action. This channel is for building and discussing that agent layer.

**What the agent does (target behavior):**
1. Monitors for incident signals (CloudWatch alarm, Discord post in `#active-incidents`)
2. Decides whether to trigger an investigation
3. Collects relevant logs, metrics, and context automatically
4. Calls the RCA engine with that context
5. Posts the RCA report to Discord and GitHub
6. Optionally suggests actions (restart instance, roll back deployment, etc.)

**What belongs here:**
- Agent architecture and state machine design
- Tool use design (what tools does the agent have access to: log reader, metric fetcher, GitHub API, Discord API, etc.)
- Memory context design for the agent (what does it remember between steps)
- Decision logic (when does it trigger, when does it wait, when does it escalate)
- Agent evaluation results (does it make the right decision given a scenario)
- Discussions about autonomous action boundaries (what can it do on its own vs what requires human approval)

**Agent tool inventory (what we're building):**
```
Tool: read_cloudwatch_logs(instance_id, time_range)
Tool: get_ec2_instance_state(instance_id)
Tool: get_cloudwatch_metrics(instance_id, metric_name, time_range)
Tool: call_rca_engine(log_data, context)
Tool: post_to_discord(channel, message)
Tool: create_github_issue(title, body, assignees)
Tool: notify_on_call(message)  [Phase 2]
```

**Important design constraint:**
The agent should never take destructive action autonomously. It can read, analyze, and report. Any action that modifies infrastructure (restart, rollback, scaling) requires explicit human approval. Design every autonomous action with this in mind.

**Rules:**
- Document every change to the agent's decision logic. If you change when it triggers or what it does, write it down here.
- Anything involving the agent taking real action (not just reading/reporting) needs a discussion and Aaryan's approval before implementation.
- Keep memory context design discussions here. The actual implementation goes in the codebase, but the design reasoning lives in this channel.

---

## #model-evaluation-and-benchmarks

We need to know if ASTRA is actually getting better over time. This channel is where we track that systematically. Every time we change something significant — model, prompt, pipeline — we run it against our benchmark suite and post the results here.

The goal is to have a clear record that shows whether changes are improvements or regressions. Without this, we're flying blind.

**What belongs here:**
- Benchmark suite definition (the set of scenarios we test against)
- Evaluation results after every significant change
- Accuracy metrics over time
- Performance metrics (inference time, memory usage, throughput)
- Comparison between model versions
- Known failure cases and edge cases

**Evaluation metrics we track:**
```
Accuracy Metrics:
  - Root cause identification accuracy (did it get the right cause?)
  - Contributing factor completeness (did it catch secondary causes?)
  - False positive rate (does it trigger on non-incidents?)
  - False negative rate (does it miss real incidents?)

Performance Metrics:
  - Mean time from log ingestion to RCA report (target: < 5 min)
  - Inference time per request
  - Memory usage during inference
  - Throughput (requests per minute under load)
```

**How to post evaluation results:**
```
EVAL RUN — April 7, 2024
Change being tested: Prompt v3 + Llama 3 8B (upgraded from 7B)
Previous baseline: Prompt v2 + Mistral 7B

Test suite: 15 scenarios (10 EC2, 3 network, 2 database)

Results:
                      Baseline    New
Root cause accuracy    71%        83%
Contributing factors   58%        74%
False positive rate    12%        8%
Mean RCA time          6.2 min    4.8 min
Inference time         2.8s       4.2s (slower but more accurate)
Memory usage           5.2 GB     7.1 GB

Verdict: Improvement on accuracy metrics, acceptable performance trade-off.
Recommending for staging deployment.

Owner: Bhargav
```

**Benchmark suite:**
We maintain a set of reference scenarios in `#test-scenarios-and-cases`. Every eval run should use the same core scenarios so results are comparable over time. New scenarios can be added but never removed from the core suite.

**Rules:**
- Never declare a change "better" without running the benchmark suite. Intuition isn't enough.
- Post results even when they show a regression. That's valuable information.
- Keep a running pinned message with the current production model performance numbers so everyone knows the baseline.

---

## #memory-context-design

One of the more interesting design challenges in ASTRA is memory. The LLM doesn't inherently remember anything between calls — every RCA request starts fresh. But real incidents often have history. An EC2 instance that crashed today may have been flaky for the past week. The agent needs to know that.

This channel is specifically for designing how ASTRA maintains and uses context across time — both within a single investigation and across multiple incidents.

**What we're thinking about:**

**Short-term memory (within an incident):**
How does the agent maintain context as it gathers information across multiple tool calls during a single investigation? It starts by reading logs, then fetches metrics, then looks at deployment history — how does it keep all of that coherent?

**Long-term memory (across incidents):**
How do we store and retrieve historical incident data so the agent can say "this is the third time this instance has had a memory issue in 30 days"? What database? What schema? How do we avoid the context window filling up with irrelevant history?

**Episodic memory:**
When a past RCA was wrong and we corrected it, can the agent learn from that correction? How do we feed that back into the system without full fine-tuning every time?

**What belongs here:**
- Design proposals for memory architecture
- Database schema proposals for incident history storage
- Context window management strategies (how to summarize long histories)
- Retrieval-augmented generation (RAG) design for incident history lookup
- Discussions about what the agent should and shouldn't remember
- Implementation approaches and trade-offs

**Example discussion post:**
```
PROPOSAL | RAG-based Incident History Retrieval

Problem:
We want the agent to know when a similar incident has happened before,
but we can't put 6 months of incident history in the context window.

Proposed approach:
Store all past incidents + their RCAs in a vector database (ChromaDB or
similar). When a new incident triggers, embed the current log summary and
query for the top-3 most similar past incidents. Include those summaries
in the LLM context.

Trade-offs:
+ Gives the agent relevant history without blowing the context window
+ Similarity search is fast
- Requires maintaining a vector DB (operational overhead)
- Embedding quality affects retrieval quality

Alternative: Just use keyword search over a Postgres table of past incidents.
Simpler but less semantically aware.

Request for feedback: Does anyone have experience with ChromaDB at this scale?
Is the operational overhead worth it vs the simpler keyword approach?

Owner: Asif
```

**Rules:**
- This is a design channel, not an implementation channel. Write the reasoning here, put the code in the repo.
- Every design decision made here that gets implemented should link back to the relevant ADR in `#system-architecture`.
- If you're proposing something, include trade-offs. Don't just advocate for one approach without acknowledging the downsides.
