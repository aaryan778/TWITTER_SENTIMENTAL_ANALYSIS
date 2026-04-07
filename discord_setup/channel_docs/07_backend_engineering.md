# BACKEND ENGINEERING — Channel Docs

---

## #api-development

The ASTRA backend API is the glue between everything. The frontend talks to it, the AI engine exposes its capabilities through it, the Discord bot calls it, and external tools integrate with it. Getting the API right matters — a messy API makes everything built on top of it harder to work with.

This channel is for designing, building, and maintaining the ASTRA API layer.

**What belongs here:**
- API endpoint design and documentation
- Breaking changes and versioning decisions
- Authentication and authorization design for API routes
- API performance benchmarks and optimization
- Integration discussions (how Discord bot calls the API, how frontend calls it)
- Error handling standards
- API testing results

**API conventions we follow:**

Base URL structure:
```
https://api.astra.internal/v1/        (production)
http://localhost:8000/v1/             (local dev)
```

Endpoint naming:
```
GET    /v1/incidents                  list all incidents
GET    /v1/incidents/{id}             get specific incident
POST   /v1/incidents                  create incident
PATCH  /v1/incidents/{id}             update incident
DELETE /v1/incidents/{id}             close/delete incident

GET    /v1/rca-reports                list RCA reports
GET    /v1/rca-reports/{id}           get specific report
POST   /v1/rca/generate               trigger RCA generation

GET    /v1/tasks                      list sprint tasks
POST   /v1/tasks                      create task
PATCH  /v1/tasks/{id}                 update task

GET    /v1/health                     service health check
GET    /v1/metrics                    Prometheus metrics endpoint
```

Standard response format:
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2024-04-07T04:47:00Z",
    "request_id": "req_abc123"
  }
}
```

Error response format:
```json
{
  "status": "error",
  "error": {
    "code": "INCIDENT_NOT_FOUND",
    "message": "Incident INC-007 does not exist",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2024-04-07T04:47:00Z",
    "request_id": "req_abc123"
  }
}
```

**How to document a new endpoint:**
```
ENDPOINT | POST /v1/rca/generate

Purpose:
  Trigger RCA generation for a specific incident. Called by the ASTRA
  agent automatically, or can be called manually for re-analysis.

Request body:
  {
    "incident_id": "INC-007",           required
    "log_window_minutes": 60,           optional, default 60
    "include_metrics": true,            optional, default true
    "force_regenerate": false           optional, default false
  }

Response (202 Accepted):
  {
    "status": "success",
    "data": {
      "job_id": "rca_job_abc123",
      "incident_id": "INC-007",
      "estimated_completion_seconds": 180,
      "status_url": "/v1/rca-jobs/rca_job_abc123"
    }
  }

Auth required: YES — API key or service token
Rate limit: 10 requests/minute per service
Side effects: Triggers Ollama inference, reads CloudWatch logs

Notes:
  RCA generation is async. Use the status_url to poll for completion.
  If force_regenerate is false and a report exists for this incident,
  returns the existing report without re-running.

Owner: Nithish
Status: In development
```

**Rules:**
- No breaking changes to the API without a version bump and at least 1 week notice.
- Every new endpoint needs to be documented in this channel before it goes to code review.
- Auth is required on all endpoints except `/v1/health`. No exceptions.

---

## #database-and-schema

Every piece of data ASTRA generates or consumes has to live somewhere. The database is one of the least glamorous parts of the system but it's also one of the most important — a bad schema is a nightmare to change later, and poor query design will make the whole system slow.

This channel is for designing, discussing, and maintaining the ASTRA database.

**What belongs here:**
- Schema designs and changes (new tables, columns, indexes, constraints)
- Migration plans (how to update schema without breaking running systems)
- Query optimization discussions
- Database performance issues (slow queries, index misses, lock contention)
- Backup and recovery procedures
- Database technology discussions (PostgreSQL configuration, connection pooling)

**Core schema overview (working design):**

```sql
-- Incidents table
CREATE TABLE incidents (
    id              SERIAL PRIMARY KEY,
    incident_id     VARCHAR(20) UNIQUE NOT NULL,   -- INC-007
    title           TEXT NOT NULL,
    severity        VARCHAR(20) NOT NULL,           -- CRITICAL, WARNING, INFO
    status          VARCHAR(20) NOT NULL,           -- OPEN, IN_PROGRESS, RESOLVED, CLOSED
    service         VARCHAR(100),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    created_by      VARCHAR(100),                   -- discord user or 'astra-agent'
    github_issue_id INTEGER,
    discord_thread_id VARCHAR(50)
);

-- RCA reports table
CREATE TABLE rca_reports (
    id              SERIAL PRIMARY KEY,
    incident_id     VARCHAR(20) REFERENCES incidents(incident_id),
    version         INTEGER DEFAULT 1,             -- increments on regeneration
    root_cause      TEXT NOT NULL,
    contributing_factors  JSONB,                   -- array of strings
    timeline        JSONB,                         -- array of {time, event}
    recommendations JSONB,                         -- array of {priority, action}
    confidence_score DECIMAL(3,2),                 -- 0.00 to 1.00
    evidence_count  INTEGER,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    model_version   VARCHAR(100),                  -- which Ollama model was used
    prompt_version  VARCHAR(20)                    -- which prompt version was used
);

-- Log entries table (parsed logs stored for RCA reference)
CREATE TABLE log_entries (
    id              BIGSERIAL PRIMARY KEY,
    source_instance VARCHAR(100),
    log_group       VARCHAR(200),
    timestamp       TIMESTAMPTZ NOT NULL,
    level           VARCHAR(20),
    service         VARCHAR(100),
    message         TEXT,
    parsed_fields   JSONB,
    tags            TEXT[],
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_log_entries_timestamp ON log_entries(timestamp DESC);
CREATE INDEX idx_log_entries_source ON log_entries(source_instance, timestamp DESC);

-- Sprint tasks table
CREATE TABLE tasks (
    id              SERIAL PRIMARY KEY,
    github_issue_id INTEGER UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    status          VARCHAR(30) DEFAULT 'backlog',  -- backlog, in_progress, in_review, done
    priority        VARCHAR(20),                    -- critical, high, medium, low
    assignees       TEXT[],                         -- array of github usernames
    labels          TEXT[],
    sprint_name     VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    created_by      VARCHAR(100)
);

-- Audit log table
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    actor           VARCHAR(100) NOT NULL,
    action          TEXT NOT NULL,
    resource        TEXT,
    details         JSONB,
    cost_estimate   DECIMAL(10,4)                  -- for costly operations
);
```

**Schema change process:**
```
SCHEMA CHANGE | Add deployment_version column to incidents

Reason:
  RCA engine needs to know what was deployed at the time of incident.
  Currently stored in log_entries but slow to query.

Proposed change:
  ALTER TABLE incidents
  ADD COLUMN deployment_version VARCHAR(50);

Migration plan:
  1. Add column as nullable (no downtime)
  2. Backfill from log_entries for existing incidents
  3. Update application to always populate on incident creation
  4. Add NOT NULL constraint after backfill complete

Rollback plan:
  ALTER TABLE incidents DROP COLUMN deployment_version;
  (safe — no dependencies yet)

Reviewed by: Aaryan
Status: Approved
Owner: Nithish
```

**Rules:**
- Schema changes need a documented migration plan before any code is written.
- Never ALTER or DROP columns directly in production without a migration script.
- Every new table needs appropriate indexes from day one — don't add them later as an afterthought.
- JSONB columns are fine for flexible data but don't overuse them. If something is always queried, it should be a typed column.

---

## #ollama-server-configuration

Ollama is the local LLM server that powers ASTRA's AI engine. Unlike using an external API, we're running the model ourselves — which means we're also responsible for setting it up, keeping it running, and making sure it performs well enough to be useful during an actual incident.

This channel covers everything about running and maintaining the Ollama server.

**What belongs here:**
- Ollama installation and setup
- Model downloads and version management
- Server configuration (GPU, memory allocation, concurrency)
- Performance tuning (quantization choices, context length, batch size)
- Monitoring Ollama server health and performance
- Issues with model loading or inference
- API integration (how our code calls Ollama)

**Ollama server setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull our current production model
ollama pull llama3:8b

# Start server with specific configuration
OLLAMA_HOST=0.0.0.0:11434 \
OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_NUM_PARALLEL=2 \
ollama serve
```

**Model inventory — always keep this updated:**
```
Current Production Model: llama3:8b (quantized Q4_K_M)
Size on disk: ~4.7 GB
Memory required: ~6 GB VRAM (GPU) or ~8 GB RAM (CPU)
Average inference time: 4.2s per RCA request
Last updated: April 7, 2024

Available models on server:
  llama3:8b           — PRODUCTION (current RCA model)
  mistral:7b          — STAGING (evaluation only)
  llama3:8b-instruct  — EXPERIMENTAL

Do not use experimental models in incident response.
```

**Ollama API integration:**

How our code calls Ollama:
```python
import httpx

OLLAMA_BASE_URL = "http://localhost:11434"

async def generate_rca(prompt: str, context: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": f"{context}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.1,    # low temp for consistent RCA output
                    "top_p": 0.9,
                    "num_predict": 2048,   # max tokens in response
                    "num_ctx": 8192        # context window
                }
            }
        )
    return response.json()["response"]
```

Temperature guidance:
```
0.1  — Use for RCA generation (consistent, factual output needed)
0.3  — Use for recommendations (slight creativity acceptable)
0.7+ — Don't use for anything operational. Too unpredictable.
```

**Hardware requirements:**
```
Minimum (CPU only):     16 GB RAM, 8 cores, SSD
Recommended (GPU):      8 GB VRAM GPU (RTX 3060 or better)
Our current setup:      [fill in when provisioned]
```

**Rules:**
- Never change the production model without running the full benchmark suite first (`#model-evaluation-and-benchmarks`).
- If the Ollama server goes down, post in this channel immediately with what happened.
- Temperature settings for production RCA calls should not be changed without a discussion here first.
- Keep the model inventory table above updated whenever anything changes.

---

## #authentication-and-security

Security is not an afterthought in ASTRA. We're building a system that reads infrastructure logs, has access to cloud resources, and runs an AI agent that takes automated actions. Getting auth wrong has serious consequences.

This channel is for everything related to authentication, authorization, secrets management, and security practices in the ASTRA codebase and infrastructure.

**What belongs here:**
- Authentication system design and implementation
- API key management (how we issue, rotate, and revoke keys)
- Secrets management (how we handle credentials, tokens, API keys)
- Security review findings
- Dependency vulnerability alerts
- JWT or session token design
- IAM security best practices and reviews
- Security decisions and their rationale

**Authentication architecture:**

```
External clients (Discord bot, frontend)
    ↓
API Key authentication (X-API-Key header)
    ↓
ASTRA API
    ↓
Internal services communicate via service tokens
    ↓
Ollama server (no auth — internal network only, not exposed)
CloudWatch (IAM role — no credentials in code)
GitHub API (fine-grained PAT — scoped to minimum required)
```

**Secrets management rules:**

What NEVER goes in the codebase or environment variables committed to git:
```
❌ AWS access keys or secret keys
❌ Discord bot token
❌ GitHub personal access tokens
❌ Database passwords
❌ API keys for any service
```

What goes where instead:
```
Local development:  .env file (gitignored, never committed)
CI/CD:              GitHub Actions Secrets
Production:         AWS Secrets Manager or environment variables
                    set on the server, never in code
```

Environment variable names (for consistency across the team):
```
DISCORD_BOT_TOKEN
GITHUB_PAT
ASTRA_API_KEY
DATABASE_URL
OLLAMA_HOST
AWS_REGION
```

**How to report a security concern:**
If you find a potential security issue — exposed credential, vulnerable dependency, logic flaw in auth — post it here immediately. Don't wait. Don't file a normal task. Post here first.

Format:
```
SECURITY CONCERN | Exposed API Key in Commit

Severity: HIGH
Found by: Asif
Date: April 7, 2024

Description:
Commit abc1234 in the rca-engine branch appears to contain a hardcoded
GitHub PAT in config.py line 34.

Immediate action needed:
1. Revoke the exposed token on GitHub immediately
2. Generate a new token
3. Remove from git history (contact Aaryan)

Status: OPEN — awaiting action
```

**Rules:**
- Never store credentials in code. Not even "temporary" or "just for testing."
- Rotate all tokens every 90 days. Put it in the calendar.
- All API endpoints require authentication except `/v1/health`.
- Security concerns get priority above all other work until resolved.
- If you're unsure whether something is a security issue, assume it is and post here.

---

## #devops-and-ci-cd

Code that doesn't ship doesn't matter. This channel covers everything that gets code from a developer's laptop into a running environment — CI/CD pipelines, containerization, deployment processes, and the infrastructure that runs it all.

**What belongs here:**
- CI/CD pipeline configuration and changes (GitHub Actions workflows)
- Docker and containerization setup
- Deployment processes and runbooks
- Environment configuration (dev, staging, prod)
- Build failures and pipeline issues
- Deployment history for significant releases
- Infrastructure-as-code (Terraform, CloudFormation) discussions

**CI/CD pipeline overview:**

```
Developer pushes to feature branch
    ↓
GitHub Actions: Run linting + unit tests
    ↓
PR opened
    ↓
GitHub Actions: Run integration tests
    ↓ (tests pass)
PR reviewed and merged to main
    ↓
GitHub Actions: Build Docker image + push to ECR
    ↓
Auto-deploy to staging environment
    ↓
Manual approval gate (Aaryan)
    ↓
Deploy to production
```

**Deployment checklist (run before every production deploy):**
```
PRE-DEPLOYMENT
  ☐ All tests passing on main
  ☐ CHANGELOG updated
  ☐ Database migrations reviewed and tested on staging
  ☐ Ollama model version confirmed unchanged (or upgrade planned)
  ☐ Environment variables checked for new additions
  ☐ Rollback plan documented

DEPLOYMENT
  ☐ Deploy to staging and smoke test
  ☐ Monitor staging for 15 minutes
  ☐ Get approval from Aaryan
  ☐ Deploy to production during low-traffic window
  ☐ Monitor production for 30 minutes post-deploy

POST-DEPLOYMENT
  ☐ Verify all services healthy (check #service-status)
  ☐ Post deployment note in #release-notes
  ☐ Update incident channel if this is a hotfix deployment
```

**Docker setup:**
```
Services containerized:
  astra-api:          FastAPI backend
  astra-rca-engine:   RCA generation service
  astra-log-pipeline: Log ingestion pipeline
  astra-bot:          Discord bot

NOT containerized:
  Ollama server:      Runs directly on host (GPU driver access needed)
  PostgreSQL:         Managed RDS in production, local Docker in dev
```

**Environment tiers:**
```
development:  Local laptop. Runs everything via docker-compose.
              Ollama on host machine. Dev Discord server.

staging:      Mirrored EC2 setup. Used for integration testing and
              pre-production validation. Dev Discord server.
              Automatic deploys from main branch.

production:   Production EC2 setup. Separate AWS account.
              Production Discord server. Manual deploy with approval.
```

**Rules:**
- Never deploy directly to production without going through staging first.
- Every deployment to production needs Aaryan's explicit approval in this channel.
- Failed CI builds block merges. Don't skip CI.
- All infrastructure-as-code changes go through code review just like application code.
- Post a brief note in this channel every time you deploy to production, even for small changes.
