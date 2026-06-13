## Learned User Preferences

- Communicates in Vietnamese; prefers concise, technically complete answers.
- Use parallel sub-agents for independent work streams (BE, FE, AI, per-feature FR-1–FR-7).
- `2-requirements/` is the implementation source of truth; BE and FE must stay aligned with it.
- Chat UI should match ChatGPT/Claude quality: GFM markdown, syntax highlighting, copy buttons, premium UX, optional GSAP polish.
- Iterate with local tests (`pytest`, `npm test`) until prod-ready; expect at least 2 quality-review loops.
- Frontend should feel modern and polished ("wow", futuristic AI aesthetic).
- Integrate `greennode-agentbase-skills` only when strongly justified against goals in `01-PROBLEM-AND-GOALS.md`.
- Expect feature-by-feature reviews with short flow explanations tied to FR-1–FR-7.
- Docker deploy: one public URL serves the web UI at `/`; API calls (`POST /chat`, `/invocations`, etc.) share the same host.
- Add unit tests across modules; parallel agents for test writing are welcome.
- When asking for stack overviews, focus on BE/AI/core only—skip test and UI unless requested.
- Frontend UI should support English and Vietnamese (labels/chrome only; Q&A follows the user's language).

## Learned Workspace Facts

- Primary app: `code/zalopay-knowledge/` — Zalopay Internal Knowledge Agent (RAG Q&A from internal docs only, no web search).
- Canonical product spec: `2-requirements/` (derived from `requirements-fable-5`; preferred over `requirement-opus`).
- `requirements/` documents GreenNode AgentBase platform capabilities, not the Zalopay product.
- MVP departments: Risk, Grow Enablement, Bank Partnerships; sources are Confluence spaces plus GDrive PDFs (SharePoint in production).
- Backend stack: Python 3.11, FastAPI, LangGraph, FAISS (MVP), VNG MaaS/Qwen; deploy via `code/greennode-agentbase-skills/`.
- Dashboard metrics API is `GET /api/dashboard` (not `/dashboard`) to avoid SPA route collision.
- MVP sync is manual; pipeline is designed for Phase 2 scheduled runs.
- Refusal when evidence is insufficient is a success path, not a failure.
- Engineering checklist for MVP MUST items: `2-requirements/08-KNOWLEDGE_AI_AGENT_CHECKLIST_AGAIN.md`.
- `GATEWAY_TRUST_*` env vars are app-owned security config, not AgentBase platform defaults; set via runtime env.
- `MEMORY_ID` is the AgentBase Memory store ID for STM checkpointer and LTMS recall when `APP_ENV=agentbase`.
- MVP index target ~1000 pages; production PDFs on SharePoint (MVP simulates via GDrive).
- GDrive on AgentBase: Outbound Auth OAuth `identity-google-space` (`app/adapters/gdrive_credentials.py`). Confluence: apikey `identity-confluence-zalopay-knowledge` (`app/adapters/confluence_credentials.py`). Local dev: `CONFLUENCE_API_TOKEN`, `GDRIVE_*` env.
