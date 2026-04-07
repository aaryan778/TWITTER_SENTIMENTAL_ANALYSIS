# OBSERVABILITY & INFRASTRUCTURE — Channel Docs

---

## #cloudwatch-monitoring

AWS CloudWatch is our primary observability layer. It's the first thing that sees when something goes wrong on our EC2 instances — before the RCA engine, before the AI agent, before any human. If CloudWatch isn't configured correctly, the whole ASTRA pipeline breaks down before it even starts. This channel is where we set up, maintain, and discuss everything related to CloudWatch.

**What CloudWatch does for us:**
- Collects logs from EC2 instances (system logs, application logs, custom logs)
- Tracks metrics (CPU, memory, disk I/O, network traffic)
- Triggers alarms when metrics cross thresholds
- Sends those alarms downstream to our ASTRA pipeline (Phase 2) and to this Discord channel (Phase 2)
- Serves as the log archive we query during RCA

**What belongs here:**
- CloudWatch setup and configuration discussions
- Alarm definitions (what thresholds we set and why)
- Log group structure (how we organize logs in CloudWatch)
- CloudWatch Insights queries we've written and reuse
- Metric math expressions for derived metrics
- Cost discussions (CloudWatch can get expensive if misconfigured)
- Issues with log ingestion (missing logs, delays, format problems)
- Phase 2: automated alert posts from CloudWatch will appear here

**Key alarms we need configured (to be set up in Phase 2):**

```
ALARM | EC2 CPU Utilization
Threshold: > 85% for 5 consecutive minutes
Action: Trigger ASTRA agent investigation
Severity: WARNING

ALARM | EC2 Instance Status Check Failed
Threshold: Status = FAILED for 1 minute
Action: Trigger ASTRA agent investigation immediately
Severity: CRITICAL

ALARM | Memory Utilization
Threshold: > 80% for 3 consecutive minutes
Action: Trigger ASTRA agent investigation
Note: Requires CloudWatch agent installed on instance
Severity: WARNING

ALARM | Disk Usage
Threshold: > 90%
Action: Post to #cloudwatch-monitoring
Severity: WARNING

ALARM | Network In/Out Anomaly
Method: Anomaly detection (not static threshold)
Action: Post to #cloudwatch-monitoring for human review
Severity: INFO
```

**Useful CloudWatch Insights queries (save these):**

Find all errors in the last hour:
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

Find memory-related log lines:
```
fields @timestamp, @message
| filter @message like /OOM/ or @message like /out of memory/ or @message like /killed/
| sort @timestamp desc
```

Track request latency over time:
```
fields @timestamp, @message
| parse @message "duration=* ms" as duration
| stats avg(duration), max(duration), min(duration) by bin(5m)
```

**Cost awareness:**
CloudWatch charges per metric, per alarm, per GB of log data ingested, and per GB queried via Insights. Always think about cost when adding new metrics or log groups. Document the estimated monthly cost of any new CloudWatch configuration here before enabling it.

**Rules:**
- All CloudWatch alarm changes need to be documented here before being applied.
- If you're adding a new log group or metric, post the estimated cost impact.
- Keep a running list of active alarms pinned in this channel.
- Phase 2: when automated alerts start coming in here, do not delete them. They're part of the incident record.

---

## #datadog-and-newrelic

Datadog and New Relic give us a different view of the system than CloudWatch. Where CloudWatch is tightly integrated with AWS, Datadog and New Relic are more flexible — they can monitor across cloud providers, give us better APM (application performance monitoring), and have stronger dashboarding and alerting capabilities.

We're evaluating both. This channel is where that evaluation happens and where ongoing configuration is discussed.

**What belongs here:**
- Datadog agent setup and configuration
- New Relic integration setup
- APM configuration (tracing, spans, service maps)
- Custom dashboards built in either tool
- Alerting policies and notification channels
- Cost comparison between the two (both can get expensive fast)
- Integration with our ASTRA pipeline
- Discussions about which tool to standardize on long-term

**Datadog vs New Relic — what we're evaluating:**

```
                    Datadog             New Relic
APM quality         Excellent           Excellent
Log management      Good                Very good
Infrastructure      Excellent           Good
Dashboarding        Excellent           Good
Cost                High                Medium
Free tier           Trial only          Generous free tier
Learning curve      Moderate            Lower
Custom metrics      Easy                Moderate
AI/ML features      Strong              Growing
```

**Initial recommendation:**
Start with New Relic's free tier for evaluation. It's more accessible without a committed contract and the free tier is genuinely useful (100GB/month free data ingest). Migrate to Datadog if we need its specific APM features at scale.

**What to configure first:**
1. Install the New Relic infrastructure agent on EC2 instances
2. Set up log forwarding from CloudWatch to New Relic
3. Configure basic alerting policies mirroring our CloudWatch alarms
4. Build a service health dashboard

**Rules:**
- Don't commit to a paid plan without Aaryan's approval. Both tools have sales teams that push hard — be careful.
- Document every integration you set up. If you connect a new data source, write it up here.
- Compare cost monthly. These tools can quietly become expensive if log volume grows.

---

## #grafana-and-prometheus

Grafana and Prometheus are the open-source, self-hosted alternative to paying for Datadog/New Relic dashboarding. Prometheus scrapes metrics, stores them in a time-series database, and Grafana turns them into dashboards. Together they're extremely powerful and free.

The trade-off is operational overhead — we have to run and maintain them ourselves. But for a project like ASTRA where privacy and control are priorities, that trade-off is worth it.

**What belongs here:**
- Prometheus setup and configuration (scrape configs, targets, retention)
- Grafana dashboard designs and exports
- Alert rules written in Prometheus (PromQL)
- Discussion about what metrics to expose and how
- Integration with EC2 instances (node exporter setup)
- Integration with our Ollama server (custom metrics for inference performance)
- Issues with metric collection or dashboard accuracy

**Prometheus scrape targets we need:**

```yaml
# prometheus.yml — scrape config outline
scrape_configs:
  - job_name: 'ec2-node'
    static_configs:
      - targets: ['<ec2-ip>:9100']   # node_exporter

  - job_name: 'ollama-server'
    static_configs:
      - targets: ['<ollama-ip>:11434']  # custom metrics

  - job_name: 'astra-api'
    static_configs:
      - targets: ['<api-ip>:8000/metrics']  # app metrics
```

**Key dashboards to build in Grafana:**

```
Dashboard 1: EC2 Health Overview
  - CPU usage over time (all instances)
  - Memory usage over time
  - Disk I/O
  - Network traffic
  - Instance status (up/down)

Dashboard 2: ASTRA AI Engine Performance
  - Ollama inference time per request
  - RCA generation time end-to-end
  - Number of RCA reports generated
  - Error rate in RCA pipeline

Dashboard 3: Log Pipeline Health
  - Log ingestion rate (logs/sec)
  - Processing latency
  - Failed ingestion count
  - Queue depth

Dashboard 4: Incident Overview
  - Active incidents count
  - Mean time to detection
  - Mean time to RCA generation
  - Incident frequency over time
```

**PromQL examples (useful queries):**

CPU usage percentage:
```
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

Memory usage percentage:
```
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

Disk usage percentage:
```
(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100
```

**Rules:**
- Export Grafana dashboards as JSON and commit them to the repo. Don't build dashboards that only exist in the UI.
- Alert rules go in Prometheus config files (in the repo), not just in the UI.
- If you add a new scrape target, document it here with what metrics it exposes.

---

## #splunk-log-analysis

Splunk is the heavy-duty log analysis tool in our stack. While CloudWatch handles real-time log streaming and alerting, Splunk is better for deep forensic analysis — querying large volumes of historical logs, building complex search pipelines, and correlating events across multiple log sources.

Think of Splunk as the forensics lab. When we need to really dig into what happened during an incident — not just the last 5 minutes, but the last 5 days — Splunk is what we use.

**What belongs here:**
- Splunk data input configuration (how we get logs into Splunk)
- Saved searches and search pipelines
- Dashboard and report definitions
- Alerts configured in Splunk
- SPL (Splunk Search Processing Language) queries worth saving
- Cost discussions (Splunk licensing is based on daily ingest volume)
- Integration with ASTRA's RCA engine

**Data inputs to configure:**
```
Input 1: CloudWatch Logs → Splunk (via Splunk Add-on for AWS)
Input 2: EC2 system logs (via Splunk Universal Forwarder on each instance)
Input 3: Application logs (ASTRA API, RCA engine logs)
Input 4: Ollama server logs
```

**Useful SPL queries (save these):**

Find all error events in the last 24 hours:
```
index=astra_logs level=ERROR earliest=-24h
| stats count by source, message
| sort -count
```

Find events surrounding a specific incident window:
```
index=astra_logs earliest="04/07/2024:04:00:00" latest="04/07/2024:05:00:00"
| sort @timestamp
| table _time, host, source, message
```

Identify top error sources:
```
index=astra_logs level=ERROR
| top limit=10 source
```

Correlate EC2 metrics with log errors (using eval):
```
index=astra_logs OR index=aws_metrics
| eval event_type=if(index="astra_logs", "log", "metric")
| sort _time
| table _time, event_type, source, message, metric_name, metric_value
```

**Cost management:**
Splunk charges by daily ingest volume. Be careful about what you send to Splunk — not every log line needs to be there. Send high-value, structured logs. Use log levels wisely (DEBUG logs should not go to Splunk in production).

**Rules:**
- Save every useful SPL query here before it disappears from your search history. SPL is not always easy to write and rewriting from scratch is a waste of time.
- If you build a Splunk dashboard, export it and post it here.
- Document the daily ingest volume monthly so we track cost trends.

---

## #infrastructure-general

This is the catch-all channel for infrastructure topics that don't fit neatly into one of the observability tools above. AWS account setup, IAM permissions, VPC configuration, EC2 instance provisioning, cost management, networking — all of that lives here.

**What belongs here:**
- AWS account setup and organization
- IAM roles and policies (who/what has access to what)
- VPC and networking configuration
- EC2 instance provisioning and configuration
- Security group rules
- Cost monitoring and budget alerts
- General infrastructure questions and discussions
- Terraform or infrastructure-as-code discussions
- Any infrastructure change that doesn't have a more specific home

**Infrastructure conventions to follow:**

Naming convention for resources:
```
astra-{environment}-{service}-{resource-type}

Examples:
  astra-dev-ec2-simulation-01
  astra-prod-rca-api-server
  astra-dev-cloudwatch-log-group
```

Environment tags on all resources:
```
Project:     ASTRA
Environment: dev | staging | prod
Owner:       aaryan778
CostCenter:  astra-rd
```

**IAM principle of least privilege:**
Every IAM role gets only the permissions it needs. The RCA engine gets read access to CloudWatch logs — not write, not admin. Document every IAM role here with what it has access to and why.

```
Role: astra-rca-engine
Permissions:
  - logs:GetLogEvents (read CloudWatch logs)
  - logs:DescribeLogGroups
  - logs:DescribeLogStreams
  - ec2:DescribeInstances (read EC2 state)
  - cloudwatch:GetMetricData (read metrics)
Reason: RCA engine needs to read logs and metrics. No write access needed.
```

**Monthly cost review:**
Post a monthly cost summary in this channel. AWS costs can creep up quickly if you're not watching them. Format:
```
COST REVIEW — April 2024

EC2 instances:      $XX.XX
CloudWatch:         $XX.XX
Data transfer:      $XX.XX
Other:              $XX.XX
─────────────────────────
Total:              $XX.XX

Notable changes vs last month:
- CloudWatch increased due to new log groups added for simulation
- ...

Action items:
- ...
```

**Rules:**
- Never commit AWS credentials to the repository. Use IAM roles, environment variables, or AWS Secrets Manager.
- Every infrastructure change should be documented here before it's applied, especially in production.
- Tag every AWS resource. Untagged resources get cleaned up.
