# 🚀 Zalopay Enterprise Knowledge Agent System
## Executive Summary & Technical Recommendation

---

## 📋 PROJECT OVERVIEW

### Business Objective
Build a **hyper-intelligent knowledge bot** that acts as the single source of truth for 800+ Zalopay employees across 20 departments, answering questions with precision and fast response times, supporting concurrent users and continuous learning.

### Key Metrics
| Metric | Target |
|--------|--------|
| Accuracy | >95% (correct + cited source) |
| Response Time | <30 seconds (acceptable, 1min+ ok too) |
| Concurrent Users | Unlimited (auto-scaling) |
| QPS | 10 req/s typical |
| Uptime | 99.9% (PROD-grade) |
| Learning | Continuous (feedback loop) |

### Scope
```
Organization: Zalopay (Fintech)
├── 20 Departments (Tech + Non-Tech)
├── ~800 Employees
├── 500K-2M pages knowledge base
├── 4 doc types: Org, PRD, Tech, RCA, Ops
├── Multiple sources: Confluence, GitLab, Drive/SharePoint
├── Interfaces: Teams Bot (20 + central) + Web Dashboard
└── Deployment: Docker → AgentBase (VNG platform)

Timeline: 3-4 weeks full PROD
Token Budget: 590k-910k (Claude API, very affordable)
```

---

## 🏗️ ARCHITECTURE - MY RECOMMENDATIONS

### 1. MEMORY STRATEGY (Decision Made ✅)

**Chosen: Hybrid Semantic + Vector + Relational**

```
┌─────────────────────────────────────────────────────┐
│          Knowledge Layer Architecture               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐   ┌──────────────────┐      │
│  │  Confluence      │   │  GitLab + Docs   │      │
│  │  (Source Truth)  │   │  (Code + Refs)   │      │
│  │  500K-2M pages   │   │  (Incremental)   │      │
│  └────────┬─────────┘   └────────┬─────────┘      │
│           │                      │                 │
│           └──────────┬───────────┘                 │
│                      ▼                             │
│        ┌─────────────────────────────┐            │
│        │   Daily Batch Processor     │            │
│        │  (End-of-day sync, 1-2x/day)│           │
│        └──────────┬──────────────────┘            │
│                   ▼                                │
│  ┌────────────────────────────────────┐           │
│  │   Knowledge Processing Pipeline    │           │
│  │  ┌──────────┐ ┌──────────┐       │           │
│  │  │ Chunk    │ │ Classify │       │           │
│  │  │ (300tok) │ │ (doc type)       │           │
│  │  └──────────┘ └──────────┘       │           │
│  └──────────┬─────────────────────────┘           │
│             │                                     │
│  ┌──────────┴──────────────┬──────────────┐      │
│  ▼                         ▼              ▼       │
│ ┌──────────┐  ┌──────────────┐  ┌──────────┐    │
│ │ Vector DB│  │ PostgreSQL   │  │  Redis   │    │
│ │(Weaviate)│  │  (Metadata)  │  │ (Cache)  │    │
│ │Embeddings│  │  (Relations) │  │(Session) │    │
│ └──────────┘  └──────────────┘  └──────────┘    │
│                                                   │
│  Per-Department Indexes:                        │
│  ├── Vector embeddings (semantic search)        │
│  ├── Full-text index (keyword search)           │
│  ├── Department-specific context               │
│  └── Citation metadata (link + section)         │
│                                                   │
└─────────────────────────────────────────────────────┘
```

**Why This Approach?**
- ✅ **Vector DB (Weaviate)**: Semantic search + scales to millions
- ✅ **PostgreSQL**: Store metadata, relations, audit logs
- ✅ **Redis**: Session state, response cache, rate limiting
- ✅ **Batch Processing**: Cost-effective, no real-time sync overhead
- ✅ **Per-Department Indexing**: Isolation + faster queries
- ✅ **Scalable to Infinity**: Each layer independently scalable

**Key Parameters**
```yaml
chunk_strategy:
  size: 300 tokens  # Optimal balance: not too small, not too large
  overlap: 50 tokens
  method: semantic (split by sentences/paragraphs, not random)

embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  # Local model, 384 dims, super fast, free, good quality
  # Or: multilingual-e5-small if Zalopay has non-English content

vector_db:
  type: "weaviate"  # Self-hosted, no vendor lock-in, scales well
  dimensions: 384 (matches embedding model)
  similarity: "cosine"
  replication_factor: 3  # High availability

cache_layer:
  ttl: 3600 seconds  # 1 hour
  max_size: 100K entries
  eviction: LRU (least recently used)
  
batch_sync:
  frequency: "daily" (end-of-day)
  fallback: "6-hourly" if major updates detected
  incremental: True (only new/modified docs)
```

---

### 2. MULTI-AGENT ARCHITECTURE (Decision Made ✅)

```
┌────────────────────────────────────────────────────────┐
│         Zalopay Knowledge Agent System                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────────────────────────────┐         │
│  │   Central Router Agent (1)                │         │
│  │  • Query classification                  │         │
│  │  • Department routing                    │         │
│  │  • Cross-dept verification               │         │
│  │  • Response aggregation                  │         │
│  │  • User context awareness               │         │
│  └────────────────┬─────────────────────────┘         │
│                   │                                    │
│     ┌─────────────┼─────────────┐                     │
│     ▼             ▼             ▼                     │
│  ┌──────┐    ┌──────┐      ┌──────┐                  │
│  │Dept 1│    │Dept 2│  ... │Dept20│                  │
│  │Agent │    │Agent │      │Agent │                  │
│  └──────┘    └──────┘      └──────┘                  │
│                                                       │
│  Each Department Agent:                             │
│  ├── Specific knowledge base (100-5000 pages)      │
│  ├── Response style (PM, Dev, Ops, Biz, Risk...)  │
│  ├── Cross-department query capability            │
│  ├── Audit trail + feedback loop                  │
│  └── Internal tools + feature documentation       │
│                                                       │
└────────────────────────────────────────────────────────┘
```

**Agent Communication Pattern**
```
User Query
    ↓
┌─────────────────────────────────────┐
│  Central Router Agent               │
│  - Parse intent & entities          │
│  - Identify required departments    │
│  - Check cache first                │
│  - Route to 1-N department agents   │
└────────┬────────────────────────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
  Dept-A    Dept-B    Dept-C
   Agent     Agent     Agent
    │         │        │
    ├─────────┼────────┤
    │   (parallel requests + timeout protection)
    │
    ▼
┌──────────────────────────────┐
│ Response Aggregator          │
│ - Merge results              │
│ - Consensus if conflicting   │
│ - Add citations              │
│ - Apply response style       │
└────────┬─────────────────────┘
         ▼
    Final Response
```

**Concurrency Handling**
```
Queue System: Redis-backed task queue
├── Separate queue per department
├── Max workers per department: 3-5
├── Max concurrent users: Unlimited (auto-queue)
├── Timeout: 30 seconds per agent
└── Fallback: Return "processing, check later" + email result

Example Flow:
- User 1-100 ask questions simultaneously
- Central router distributes to department queues
- Department agents process in order (fair scheduling)
- Responses returned as ready (FIFO per user)
```

---

### 3. RESPONSE PERSONALIZATION (Decision Made ✅)

**Audience-Aware Response Engine**

```yaml
response_profiles:
  
  engineer_dev:
    tone: "technical, detailed, code-focused"
    include: "implementation details, code examples, edge cases"
    format: "markdown with code blocks"
    cite: "link to tech docs + GitLab"
    example_output:
      - "Here's the implementation in our codebase..."
      - "See: https://confluence.zalopay.com/...#section"
  
  product_manager:
    tone: "business-focused, feature-oriented"
    include: "feature status, timeline, dependencies, metrics"
    format: "bullet points, PRD links"
    cite: "link to PRD + Confluence"
    example_output:
      - "Feature X is in beta, targeting Q3 launch"
      - "Related: https://confluence.zalopay.com/PRD-..."
  
  operator_support:
    tone: "practical, step-by-step, operational"
    include: "procedures, runbooks, troubleshooting, escalation"
    format: "numbered steps, images, links"
    cite: "link to ops guide"
    example_output:
      - "1. Check dashboard at X\n2. Run command Y\n3. If error Z, escalate"
      - "Full guide: https://confluence.zalopay.com/Ops-..."
  
  business_stakeholder:
    tone: "executive, high-level, impact-focused"
    include: "status, business impact, timeline"
    format: "executive summary, key metrics"
    cite: "link to relevant docs"
    example_output:
      - "Feature X will improve conversion by 5%, launching Q3"
      - "Details: https://confluence.zalopay.com/..."
  
  risk_compliance:
    tone: "cautious, detailed, risk-aware"
    include: "compliance requirements, edge cases, risk mitigation"
    format: "structured, with risk levels"
    cite: "link to compliance + risk docs"
    example_output:
      - "⚠️ This feature has PCI-DSS implications"
      - "See: https://confluence.zalopay.com/Compliance-..."

# Dynamic Learning
training_mechanism:
  method: "in-context learning"  # Not fine-tuning (cost-effective)
  source: "user feedback + session history"
  storage: "PostgreSQL + vector DB"
  update_frequency: "after each session (real-time)"
  retention: "rolling 90 days + monthly aggregation"
  
  feedback_types:
    - "👍 Helpful / 👎 Not helpful"
    - "⭐ Rating (1-5 stars)"
    - "💬 User comment"
    - "✂️ User edited response"
    - "🔗 User clicked link / didn't click"
```

---

### 4. DATA INTEGRATION & SYNC (Decision Made ✅)

**Daily Batch Processing Pipeline**

```
┌──────────────────────────────────────────────────┐
│       Daily Data Sync Pipeline (End-of-Day)      │
├──────────────────────────────────────────────────┤
│                                                  │
│  Trigger: 22:00 UTC (off-peak hours)            │
│  Duration: 30-60 minutes                        │
│  Frequency: Daily + on-demand if major update   │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │ 1. Fetch Changes from Sources          │    │
│  │  ├─ Confluence API: Get modified pages │    │
│  │  │  (use modified_after timestamp)     │    │
│  │  ├─ GitLab: Pull new commits (git pull)│    │
│  │  └─ Drive/SharePoint: List new files  │    │
│  └────────────────┬───────────────────────┘    │
│                   ▼                             │
│  ┌────────────────────────────────────────┐    │
│  │ 2. Process Documents                  │    │
│  │  ├─ Extract text + metadata           │    │
│  │  ├─ Parse doc type (org/PRD/tech/RCA)│    │
│  │  ├─ Map to department                 │    │
│  │  ├─ Chunk into 300-token segments    │    │
│  │  └─ Generate embeddings (batch)      │    │
│  └────────────────┬───────────────────────┘    │
│                   ▼                             │
│  ┌────────────────────────────────────────┐    │
│  │ 3. Update Knowledge Base               │    │
│  │  ├─ Upsert vectors (Weaviate)         │    │
│  │  ├─ Update metadata (PostgreSQL)      │    │
│  │  ├─ Rebuild department indexes       │    │
│  │  ├─ Clear stale cache (Redis)        │    │
│  │  └─ Version snapshot                  │    │
│  └────────────────┬───────────────────────┘    │
│                   ▼                             │
│  ┌────────────────────────────────────────┐    │
│  │ 4. Quality Assurance                  │    │
│  │  ├─ Validate embeddings              │    │
│  │  ├─ Check for duplicates             │    │
│  │  ├─ Verify citation links            │    │
│  │  ├─ Run health checks                │    │
│  │  └─ Alert on issues                  │    │
│  └────────────────┬───────────────────────┘    │
│                   ▼                             │
│  ┌────────────────────────────────────────┐    │
│  │ 5. Publish Update                      │    │
│  │  ├─ Mark as "live"                    │    │
│  │  ├─ Send notification to bots         │    │
│  │  ├─ Log to audit trail                │    │
│  │  └─ Alert ops team on success        │    │
│  └────────────────────────────────────────┘    │
│                                                  │
└──────────────────────────────────────────────────┘

Performance Targets:
- Confluence fetch: 10 minutes (for 2M pages)
- Processing: 20 minutes
- Embedding generation: 20 minutes (batch)
- DB updates: 10 minutes
- QA + publish: 5 minutes
- Total: ~65 minutes
```

**API Integration Details**

```python
# Confluence Integration
confluence_api:
  method: "REST API v2"
  auth: "Bearer token (service account)"
  incremental: "modified_after timestamp"
  batch_size: 50 pages per request
  retry: "exponential backoff, max 5 retries"
  rate_limit: 100 req/minute (Confluence limit)

# GitLab Integration
gitlab_api:
  method: "git clone + git pull (fast)"
  auth: "SSH key or token"
  shallow: false  # Need full history for context
  update_frequency: "daily"
  index: "code comments, README, docs/"

# Drive/SharePoint Integration
drive_sharepoint:
  method: "REST API"
  auth: "OAuth2 (service account)"
  search: "modified_time > last_sync"
  extract: "PDF to text (PyPDF), images (OCR)"
  support: "PDF, DOCX, XLSX, PNG, JPG"
  timeout: 60 seconds per file
```

---

### 5. VECTOR DB CHOICE (Decision Made ✅)

**Chosen: Weaviate (Self-Hosted)**

```yaml
why_weaviate:
  scalability: "Supports billions of vectors"
  performance: "Sub-100ms queries"
  features:
    - "Built-in vectorization (no separate embeddings API)"
    - "Hybrid search (vector + BM25 keyword)"
    - "Multi-tenancy (per-department isolation)"
    - "CRUD semantics"
    - "GraphQL API"
  deployment: "Docker Compose, Kubernetes, or Cloud"
  cost: "Self-hosted = no vendor lock-in"
  security: "Full control over data"

setup:
  cluster_size: 3 nodes  # High availability
  disk: 500GB initial (scales as needed)
  memory: 16GB per node
  replicas: 3 (high durability)
  shard_per_dept: 1 shard per department (faster queries)

query_pattern:
  hybrid_search: 70% vector + 30% keyword
  top_k: 5-10 results per query
  filters: "department_id, doc_type, modified_date"
  timeout: 5 seconds

indexing:
  method: "multi-tenant per department"
  structure: "one index per department"
  fields:
    content: "text (embedded)"
    metadata: "doc_type, source_url, section, updated_at"
    department: "string (filter)"
    confidence_score: "float"
```

---

### 6. DEPLOYMENT ARCHITECTURE (Decision Made ✅)

```
┌────────────────────────────────────────────────────────┐
│          Zalopay Knowledge Agent Deployment           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Development → Staging → Production                  │
│                                                        │
│  Build Pipeline:                                      │
│  ┌───────────────────────────────────────┐           │
│  │  1. Code Commit (GitLab)              │           │
│  │     └─→ CI/CD pipeline triggers       │           │
│  │                                        │           │
│  │  2. Unit Tests + Linting              │           │
│  │     └─→ docker build                  │           │
│  │                                        │           │
│  │  3. Build Docker Image                │           │
│  │     ├─ Tag: myregistry/zalopay-kb:TAG│           │
│  │     └─ Push to Container Registry     │           │
│  │                                        │           │
│  │  4. Deploy to AgentBase               │           │
│  │     └─ /agentbase-deploy build → push→deploy     │           │
│  │                                        │           │
│  │  5. Run Integration Tests             │           │
│  │     └─ Smoke test in staging          │           │
│  │                                        │           │
│  │  6. Deploy to PROD                    │           │
│  │     └─ Blue-green deployment          │           │
│  └───────────────────────────────────────┘           │
│                                                        │
│  Runtime Stack:                                       │
│  ┌────────────────────────────────────────┐          │
│  │  Kubernetes Cluster (Zalopay infra)   │          │
│  │  ├─ Central Router Agent (3 pods)     │          │
│  │  ├─ Department Agents (2-3 pods each) │          │
│  │  ├─ Weaviate (3 pods + persistent vol)│          │
│  │  ├─ PostgreSQL (HA setup)             │          │
│  │  ├─ Redis (3 node cluster)            │          │
│  │  └─ Teams Bot Connector (2 pods)      │          │
│  └────────────────┬───────────────────────┘          │
│                   ▼                                   │
│  ┌────────────────────────────────────────┐          │
│  │  External Interfaces                   │          │
│  │  ├─ Teams Webhook (incoming)           │          │
│  │  ├─ Web API (FastAPI on port 8000)    │          │
│  │  ├─ Confluence API (batch sync)        │          │
│  │  ├─ GitLab API (pull code docs)        │          │
│  │  └─ Drive/SharePoint API (sync files)  │          │
│  └────────────────────────────────────────┘          │
│                                                        │
│  Monitoring & Observability:                         │
│  ├─ Prometheus (metrics)                             │
│  ├─ ELK Stack (logs)                                 │
│  ├─ Grafana (dashboards)                            │
│  ├─ AlertManager (alerts)                           │
│  └─ Jaeger (distributed tracing)                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Container Image Spec**

```dockerfile
# Multi-stage build for minimal image size
FROM python:3.11-slim as builder
# Install deps, build wheels

FROM python:3.11-slim
# Copy wheels from builder
# Install runtime deps only
# Copy source code
# Healthcheck
# Run as non-root user

# Result: ~500MB image (efficient)
```

**AgentBase Integration**

```bash
# Deploy using AgentBase Skills
/agentbase-llm api-keys create zalopay-kb-key

/agentbase-deploy build \
  --dockerfile docker/Dockerfile \
  --image-name zalopay-kb:latest \
  --registry gcr.io/zalopay/

/agentbase-deploy push \
  --image zalopay-kb:latest

/agentbase-deploy deploy \
  --runtime-name zalopay-kb-prod \
  --image zalopay-kb:latest \
  --flavor gpu-small  # 2 GPU for faster inference
  --scale 5  # 5 instances
  --region us-east-1

# Monitor
/agentbase-monitor runtime-logs zalopay-kb-prod
```

---

### 7. SECURITY & COMPLIANCE (Decision Made ✅)

```yaml
security_layers:
  
  authentication:
    method: "SAML/OAuth2 (Zalopay's existing system)"
    scope: "user_id, department, role"
    token_expiry: "1 hour"
    mfa: "Required for admin access"
  
  authorization:
    model: "RBAC (Role-Based Access Control)"
    rules:
      - "Can only query own department (default)"
      - "Can query other departments if explicitly granted"
      - "Admin can audit all queries"
    implementation: "PostgreSQL + middleware"
  
  data_encryption:
    transit: "TLS 1.3 for all APIs"
    at_rest: "AES-256 for PostgreSQL + Weaviate"
    key_management: "Zalopay's key vault"
  
  audit_logging:
    capture: "All queries, responses, user actions"
    store: "PostgreSQL with archival to S3"
    retention: "7 years (compliance requirement)"
    access: "Only audit team + admins"
  
  pii_handling:
    detection: "Regex + ML-based PII detector"
    masking: "Automatically mask in responses"
    logging: "Never log raw PII"
  
  rate_limiting:
    per_user: "100 queries/hour"
    per_department: "1000 queries/hour"
    per_ip: "1000 queries/hour"
    mechanism: "Redis-based token bucket"
  
  compliance:
    standards: "PCI-DSS, SOC2, ISO27001"
    scanning: "SAST (SonarQube), DAST, vulnerability scanning"
    penetration_test: "Quarterly"
    incident_response: "24-hour SOP"
```

---

## 📊 TECH STACK SUMMARY

```yaml
language: "Python 3.11"

core_frameworks:
  web: "FastAPI"
  async: "asyncio + aiohttp"
  queue: "Celery + Redis"
  orm: "SQLAlchemy"

llm_models:
  primary: "Qwen 3.5 (via AgentBase)"
  backup: "Mimax (via AgentBase)"
  embedding: "sentence-transformers/all-MiniLM-L6-v2 (local)"

vector_db: "Weaviate (self-hosted)"
relational_db: "PostgreSQL 15"
cache: "Redis 7"
task_queue: "Celery with Redis broker"

integrations:
  confluence: "official API v2"
  gitlab: "git + API"
  teams: "BotFramework SDK"
  drive_sharepoint: "REST API v1"

deployment:
  containerization: "Docker"
  orchestration: "Kubernetes (Zalopay)"
  platform: "AgentBase (VNG)"
  ci_cd: "GitLab CI + custom scripts"

monitoring:
  metrics: "Prometheus"
  logs: "ELK Stack"
  tracing: "Jaeger"
  alerting: "AlertManager + PagerDuty"
  dashboard: "Grafana"

testing:
  unit: "pytest"
  integration: "pytest-asyncio"
  load: "locust"
  e2e: "Playwright"
```

---

## 🎯 IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1)
- [ ] Setup project structure + Docker
- [ ] Core agent base classes
- [ ] Basic Confluence integration
- [ ] Single department agent (test)
- [ ] Local development environment

### Phase 2: Knowledge System (Week 2)
- [ ] Weaviate setup + indexing
- [ ] PostgreSQL schemas + migrations
- [ ] Batch sync pipeline
- [ ] Vector embedding generation
- [ ] Semantic search implementation

### Phase 3: Multi-Agent System (Week 3)
- [ ] Central router agent
- [ ] 20 department sub-agents
- [ ] Agent communication protocol
- [ ] Response aggregation
- [ ] Cross-department verification

### Phase 4: Integration & UX (Week 3-4)
- [ ] Teams Bot connector
- [ ] Web Dashboard API
- [ ] Response personalization
- [ ] Feedback loop system
- [ ] User testing

### Phase 5: Security & Monitoring (Week 4)
- [ ] Security hardening
- [ ] Audit logging
- [ ] Monitoring setup
- [ ] Load testing
- [ ] Performance optimization

### Phase 6: PROD Deploy (Week 4)
- [ ] AgentBase deployment
- [ ] Staging validation
- [ ] PROD cutover
- [ ] Team training
- [ ] Support handoff

---

## 💰 COST ESTIMATE

```
Infrastructure (Monthly):
├─ Kubernetes (3 nodes): ~$500
├─ PostgreSQL (managed): ~$300
├─ Redis (managed): ~$200
├─ Weaviate (self-hosted on K8s): $0 (included)
├─ AgentBase usage: ~$100-200 (varies)
└─ Monitoring (ELK): ~$200
   Total Infrastructure: ~$1300-1400/month

LLM API Cost (Monthly, 10 req/s × 24h):
├─ Qwen 3.5 (cheapest): ~$200-400
├─ Inference batching: -50% savings
├─ Cache hits: -70% savings (real-world)
└─ Estimated actual: ~$50-100/month
   Total LLM: ~$50-100/month

TOTAL MONTHLY COST: ~$1400/month (~$17K/year)

Cost vs. Human Solution:
├─ 5 Knowledge Engineers @ $5K/month = $25K/month
├─ System automation saves: ~90% of manual work
└─ Bot cost: 5% of human cost ✅
```

---

## ✅ READINESS CHECKLIST

Before Launch:
- [ ] All 20 departments trained on bot
- [ ] Confluence documentation up-to-date
- [ ] GitLab repos indexed and ready
- [ ] Teams integration tested with 100+ users
- [ ] Web dashboard UI/UX validated
- [ ] Security audit passed
- [ ] Load testing passed (10 req/s)
- [ ] Disaster recovery plan tested
- [ ] On-call rotation established
- [ ] Documentation complete
- [ ] Monitoring dashboards live
- [ ] Alert thresholds calibrated

---

## 🚀 NEXT STEPS

**You're ready to:**
1. ✅ Review this architecture
2. ✅ Confirm tech stack choices
3. ✅ Start Phase 1 (project setup + first agent)
4. ✅ Iterate with feedback

**My recommendations are:**
- Solid for 5-10 year scale
- Enterprise-grade security
- Cost-optimized (cheap models + smart caching)
- Production-ready deployment
- Continuous improvement built-in

---

## 📞 QUESTIONS TO CONFIRM

Before I start coding the implementation:

1. **Zalopay Infrastructure**: K8s already setup? Or use managed service (AWS EKS, GCP GKE)?
2. **Confluence URL**: Point me to your Confluence instance (for API testing)?
3. **Teams Setup**: Who creates the bot accounts? You have Teams admin access?
4. **Deployment**: AgentBase prod environment already setup? What's the API endpoint?
5. **Timeline**: Hard deadline? Or flexible?
6. **Budget**: Any cost constraints I should respect?

Once you confirm, I'll start with **Phase 1: Foundation** and deliver working code! 🎯
