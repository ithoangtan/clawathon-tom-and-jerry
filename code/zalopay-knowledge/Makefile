.PHONY: up down logs build fe-dev fe-build test sync-confluence sync-gdrive

# ── Docker Compose ──────────────────────────────────────────────────────────

## Start the full stack (build image first)
up:
	docker compose up --build

## Stop the stack (preserves the faiss-index named volume)
down:
	docker compose down

## Tail logs for the agent service
logs:
	docker compose logs -f agent

## Build the image without starting
build:
	docker compose build

# ── Frontend ────────────────────────────────────────────────────────────────

## Start Vite dev server (hot-reload; proxies /api → localhost:8080)
fe-dev:
	cd frontend && npm run dev

## Build the frontend to frontend/dist
fe-build:
	cd frontend && npm run build

# ── Tests ───────────────────────────────────────────────────────────────────

## Run backend unit + contract tests
test:
	pytest

## Run only unit tests
test-unit:
	pytest tests/unit

## Run only contract tests
test-contract:
	pytest tests/contract

# ── Sync (requires a running container) ─────────────────────────────────────

## Trigger a Confluence sync (pass USER_ID and SESSION_ID env vars or edit below)
sync-confluence:
	curl -s -X POST http://localhost:8080/sync/confluence \
	  -H "X-GreenNode-AgentBase-User-Id: $${USER_ID:-local-user}" \
	  -H "X-GreenNode-AgentBase-Session-Id: $${SESSION_ID:-local-session}" \
	  -H "X-GreenNode-AgentBase-Role: $${ROLE:-ops}" \
	  -H "X-GreenNode-AgentBase-Home-Department: $${HOME_DEPT:-risk}" \
	  | python3 -m json.tool

## Trigger a Google Drive / PDF sync
sync-gdrive:
	curl -s -X POST http://localhost:8080/sync/gdrive \
	  -H "X-GreenNode-AgentBase-User-Id: $${USER_ID:-local-user}" \
	  -H "X-GreenNode-AgentBase-Session-Id: $${SESSION_ID:-local-session}" \
	  -H "X-GreenNode-AgentBase-Role: $${ROLE:-ops}" \
	  -H "X-GreenNode-AgentBase-Home-Department: $${HOME_DEPT:-risk}" \
	  | python3 -m json.tool

## Show current sync status
sync-status:
	curl -s http://localhost:8080/sync/status | python3 -m json.tool

## Show health
health:
	curl -s http://localhost:8080/health | python3 -m json.tool
