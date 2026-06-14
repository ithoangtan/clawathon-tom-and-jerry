# Zalopay Internal Knowledge Agent

A **citation-grounded, corrective-RAG assistant** for Zalopay's internal teams.  Every answer carries at least one verifiable citation from your Confluence/Drive corpus; the agent refuses when the retrieved documents don't support an answer.  It never touches the internet.

---

## What it is / isn't

| It IS | It is NOT |
|---|---|
| An internal Q&A assistant grounded 100% in your Confluence + Drive documents | A general-purpose chatbot |
| A citation machine — every claim cites a source | A document management system |
| Cross-department (Risk / Grow Enablement / Bank Partnerships fan-out) | A compliance/legal tool (answers are informational only) |
| Deployed as a single Docker container | A multi-tenant SaaS |
| Bilingual VI + EN | A translation service |

---

## Architecture at a glance

```
React SPA ──HTTP──► FastAPI (port 8080)
                     │
                     ▼
              LangGraph supervisor
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   Risk subgraph  Grow subgraph  Bank subgraph   (parallel, per-branch timeout)
   retrieve→grade→synthesize→verify
        │            │            │
        └────────────┴────────────┘
                     ▼
               reconcile → respond

Ports (swappable):  LLMPort → VNG MaaS (Qwen/MiniMax)
                    RetrieverPort → FAISS (local)
                    CheckpointerPort → SQLite (local) / AgentBase STM (deploy)

Ingestion (triggered by Sync button):
  Confluence Cloud v2 ──► extract ──► chunk ──► embed (local) ──► FAISS partition
  Google Drive PDFs   ──► pypdf  ──► chunk ──► embed (local) ──► FAISS partition
```

---

## Credentials & where to get them

> Fill these in `.env` before running anything. `.env` is gitignored; `.env.example` shows all fields.

| Variable | Lấy ở đâu | Ghi chú |
|---|---|---|
| `LLM_API_KEY` | [VNG Cloud Console](https://dashboard.console.vngcloud.vn/) → AI Platform → API Keys | Key bắt đầu bằng `vn-` |
| `SMALL_MODEL` | Hỏi VNG MaaS admin hoặc xem model list qua API | Dùng cho routing/grading/verify. Hiện tại: `minimax/minimax-m2.5` |
| `MAIN_MODEL` | Hỏi VNG MaaS admin | Dùng cho synthesis/reconcile. Hiện tại: `qwen/qwen3.7-plus` |
| `CONFLUENCE_BASE_URL` | URL Confluence Cloud của team, dạng `https://<site>.atlassian.net/wiki` | |
| `CONFLUENCE_EMAIL` | Email Atlassian account của bạn | Dùng cho Basic auth |
| `CONFLUENCE_API_TOKEN` | [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) → Create API token | Chỉ dùng local dev. Trên AgentBase lưu vào Identity |
| `CONFLUENCE_SPACES` | Confluence → Space Settings → Space Details → **Key** (VD: `GROW`) | JSON map: `{"grow_enablement":"GROW","risk":"RISK"}` — key phải khớp với `app/common/departments.py` |
| `GDRIVE_FOLDER_ID` | URL Google Drive folder: `.../folders/<FOLDER_ID>` | Chỉ cần nếu sync PDF từ Drive |
| `GDRIVE_SA_JSON_PATH` | Download từ Google Cloud Console → Service Accounts → Keys | Hoặc dùng `GDRIVE_API_KEY` thay thế |
| `EMBEDDING_MODEL` | HuggingFace model ID | Default `baai/bge-m3` (~1.5GB, tải lần đầu mất ~5 phút) |

**Lưu ý model IDs**: Chạy lệnh sau để xem model nào đang được enable trên MaaS:
```bash
curl -s https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY" | python3 -m json.tool | grep '"id"'
```

---

## Quick-start demo loop (Docker — recommended)

> **Lưu ý**: `make up` build Docker image có cài `greennode-agent-bridge` từ private registry của GreenNode AgentBase. Trên máy local nếu không có quyền truy cập registry đó, dùng [Local dev (no Docker)](#local-dev-no-docker) thay thế.

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd code/zalopay-knowledge

# 2. Copy and fill environment variables
cp .env.example .env
#    Điền LLM_API_KEY, SMALL_MODEL, MAIN_MODEL,
#    CONFLUENCE_* và GDRIVE_* (xem bảng Credentials ở trên).

# 3. Build and start
make up
#    Lần đầu build ~3–5 phút (tải embedding model baai/bge-m3 ~1.5GB).
#    Các lần sau fast hơn nhờ Docker layer cache.

# 4. Open the portal
open http://localhost:8080

# 5. Demo loop
#    a. Settings page → chọn user/role/department
#    b. Settings → Sync → click "Sync from Confluence"
#       (Dashboard → Sync Status panel chuyển xanh khi xong)
#    c. Settings → Sync → click "Sync PDFs from Drive"
#    d. Chat → hỏi câu có trong docs (trả lời + citations)
#    e. Chat → hỏi câu ngoài corpus (refusal "not in docs")
#    f. Chat → hỏi cross-department (ConflictPanel nếu sources mâu thuẫn)
```

---

## Local dev (no Docker)

Dùng khi không build được Docker image (ví dụ: `greennode-agent-bridge` không có trên public PyPI và chỉ available trong môi trường build AgentBase).

### Yêu cầu

```bash
# Python 3.11 (hoặc 3.9+)
python3 --version

# Cài dependencies (một lần)
pip install -r requirements.txt
```

**Packages quan trọng được pin cứng** (không thay đổi version):
- `langgraph==0.2.76` — `greennode-agent-bridge` được viết cho LangGraph 0.2.x; 0.3+ đã xóa `JsonPlusSerializer.dumps()` gây crash checkpointer
- `langgraph-checkpoint-sqlite==2.0.11` — phải đồng bộ với langgraph 0.2.76

### Chạy backend

```bash
cd code/zalopay-knowledge

# Điền .env trước (LLM_API_KEY, CONFLUENCE_*, v.v.)
cp .env.example .env && vim .env

make dev-backend
# Hoặc thủ công:
# mkdir -p ./index/faiss ./index/hf-cache
# INDEX_DIR=./index python3 main.py

# Backend chạy trên http://localhost:8080 (hot-reload bật sẵn)
```

> `INDEX_DIR=./index` override `.env`'s `INDEX_DIR=/data/index` (cái đó dành cho Docker volume).  
> Lần đầu chạy sẽ tải embedding model vào `./index/hf-cache/` (~1.5GB, mất vài phút).

### Chạy frontend (terminal riêng)

```bash
cd code/zalopay-knowledge
make fe-dev
# Frontend trên http://localhost:5173 (proxy /api → :8080)
```

### Populate index (cần backend đang chạy)

```bash
make sync-confluence   # Sync Confluence → FAISS (chạy trong background)
make sync-gdrive       # Sync PDFs từ Drive
make sync-status       # Kiểm tra trạng thái
make health            # Kiểm tra /health/ready
```

> Sau khi sync xong, `index_ready` trong `/health/ready` sẽ là `true`. Chat mới hoạt động.

### Debug với curl

```bash
# Health check
curl http://localhost:8080/health/ready | python3 -m json.tool

# Chat stream
curl -N -X POST http://localhost:8080/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-User-Id: local-user" \
  -H "X-GreenNode-AgentBase-Session-Id: $(uuidgen)" \
  -H "X-GreenNode-AgentBase-Role: ops" \
  -H "X-GreenNode-AgentBase-Home-Department: grow_enablement" \
  -d '{"question":"Zalopay Lucky Wheel campaign là gì?","target_departments":["grow_enablement"]}'
```

---

## Frontend dev loop (hot-reload, Docker backend)

```bash
# Terminal 1 — backend container
docker compose up

# Terminal 2 — Vite dev server (proxies /api → :8080)
make fe-dev
# open http://localhost:5173
```

---

## Project layout

```
zalopay-knowledge/
├── app/
│   ├── api/          routes, schemas (API contract), context header parsing
│   ├── ports/        Protocols only — LLMPort, RetrieverPort, CheckpointerPort
│   ├── adapters/     Concrete implementations (MaaS LLM, FAISS retriever, SQLite/AgentBase checkpointer)
│   ├── graph/        LangGraph state, node implementations, subgraph factory
│   │   └── nodes/    8 nodes: ingest_context, router, retrieve, grade, compress,
│   │                          synthesize, verify, reconcile, respond
│   ├── ingestion/    Confluence Cloud v2 + Drive PDF sync pipeline
│   ├── store/        SQLite audit log + feedback store
│   ├── common/       Departments registry, language detection, PII masking, logging
│   └── prompts/      Versioned YAML prompt templates (edit here, not inline in code)
├── frontend/         React + Vite + TypeScript + Tailwind
├── corpus/pdfs/      Drive PDFs (gitignored; Docker named volume in prod)
├── index/            FAISS partitions + SQLite metadata (gitignored; Docker named volume in prod)
├── tests/            unit/ contract/ evals/
└── docs/             API-CONTRACT.md DEPLOY-READINESS.md RUNBOOK.md
```

### Thêm department mới

1. Đăng ký trong [`app/common/departments.py`](app/common/departments.py)
2. Thêm entry vào `CONFLUENCE_SPACES` trong `.env`: `{"new_dept":"SpaceKey",...}`
3. Thêm FAISS partition sẽ tự tạo khi sync

---

## Testing

```bash
# Backend
make test            # all tests (unit + contract)
make test-unit       # unit tests only
make test-contract   # contract / round-trip tests only

# Single test
pytest tests/unit/test_foo.py::test_bar -v

# Frontend
cd frontend && npm test
cd frontend && npm run typecheck
```

---

## Deploy to GreenNode AgentBase

Xem `docs/DEPLOY-READINESS.md` để biết checklist đầy đủ.  Tóm tắt:

1. Set `APP_ENV=agentbase` trong AgentBase Environment Config.
2. Platform auto-inject `GREENNODE_*` vars (MaaS key override, identity URL, memory URL).
3. Đăng ký **Outbound Auth** trong Access Control:
   - Confluence API key: provider name = `identity-confluence-zalopay-knowledge`
   - Google Drive OAuth: provider name = `identity-google-space`
4. `app/adapters/confluence_credentials.py` và `gdrive_credentials.py` resolve tokens lúc sync.
5. `deps.py` tự chọn `AgentBaseCheckpointer` + recall khi `APP_ENV=agentbase`.

### Build & push image

```bash
# Build cho AgentBase (linux/amd64)
make docker-build-amd64

# Sau đó push qua AgentBase CLI (xem docs/DEPLOY-READINESS.md)
```

### Lưu ý version pinning

`requirements.txt` pin cứng `langgraph==0.2.76` vì `greennode-agent-bridge` được viết cho LangGraph 0.2.x API.  Dockerfile re-pin lại sau khi cài bridge để đảm bảo bridge không tự upgrade LangGraph lên 0.3+ (phiên bản đó đã xóa `JsonPlusSerializer.dumps()` gây crash checkpointer).  Đừng bump langgraph version cho đến khi bridge được update tương ứng.

---

## Phase 2 (not built — documented stubs only)

Teams webhook, MCP server endpoint, VPC/Private mode, Policy Groups, long-term memory (LTMS), GitLab source, SharePoint source.  Xem `docs/PHASE-2-PLACEHOLDERS.md`.
