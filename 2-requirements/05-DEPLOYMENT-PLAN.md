# 05 — Deployment Plan (GreenNode AgentBase)

## Phase 0 — Prerequisites (start immediately; some have lead time)

1. IAM service account with AgentBase policies; export `GREENNODE_CLIENT_ID` / `GREENNODE_CLIENT_SECRET`; verify with `get_token.sh` (the skills do this in `/agentbase-wizard` Step 1).
2. **Request VPC peering with GreenNode support** (blocks Phase 2 Private mode — longest lead item). Deploy on Flavor runtime-s2-general-4x8 4 CPU8 GB RAM.
3. Confluence: 3 personal spaces + Outbound Auth apikey `identity-confluence-zalopay-knowledge`; **Google Drive:** PDF folder + OAuth `identity-google-space` (Included Google, M2M `drive.readonly`); share folder with Google client. (Teams app registration — Phase 2.)
4. Install skills bundle; Docker running; Python ≥3.10.

## Phase 1 — MVP

Day 1 — scaffold + grounded RAG loop:

```text
/agentbase-wizard init zalopay-knowledge --langgraph    # SDK-correct skeleton, CWD
/agentbase-llm api-keys create zalopay-kb-key           # LLM_API_KEY + LLM_BASE_URL + pick ENABLED model
/agentbase-memory create                                 # STM store (eventExpiryDuration=30) → MEMORY_ID
/agentbase-identity                                      # Outbound Auth: identity-confluence-zalopay-knowledge + identity-google-space; bind to agent identity
# implement: sync job (cursor → hash-skip → chunk-diff → local embed) → FAISS partitions (Risk, Grow Enablement, Bank Partnerships ≈1,000 pages total)
#            index is PRE-BUILT offline and baked into the image / loaded at boot — never built per-request
# implement: retrieve → grade → synthesize+cite → verify nodes for one department
/agentbase-wizard test validate && test local           # contract + smoke
```

Day 2 — supervisor + channels + deploy:

```text
# implement: router node, 3 dept subgraphs (Risk, Grow Enablement, Bank Partnerships), parallel fan-out + reconcile, role styles
# implement: Web UI portal (Chat + Dashboard), /chat alias, /feedback   # /webhooks/teams is Phase 2
/agentbase-wizard test docker                            # containerized contract tests (linux/amd64)
/agentbase-deploy                                        # build → push to vcr.vngcloud.vn → create runtime → ACTIVE
   # runtime: flavor 1x1-general (resize if OOMKilled), minReplicas=1, maxReplicas=1, PUBLIC
/agentbase-monitor runtime-logs <runtime-id>
curl <endpoint>/health   # 200 gate
```

MVP exit gate (also in `06`): grounded answer + citation for in-corpus question; refusal for out-of-corpus question; cross-dept question consults the relevant subgraphs; Web UI portal round-trip works (chat + citation rendering + dashboard).

## Phase 2 — Production (≈4 weeks, parallel tracks)

| Week | Track A — knowledge | Track B — platform/govern | Track C — channels/UX |
|---|---|---|---|
| 1 | Sync job (incremental + tombstones); index in VPC (Weaviate/pgvector); hybrid search | VPC peering confirmed; deploy index + MCP servers in VPC | Teams bot registration completed |
| 2 | Onboard depts 3–10 (space mapping, doc-type classifier, eval set per dept) | MCP Gateway (Private) + routes; `/agentbase-policy` per-dept Policy Group; move Confluence creds to `/agentbase-identity` | Role profiles tuned with pilot users |
| 3 | Onboard depts 11–20; weekly reconcile job; deprecation/sunset lifecycle | Runtime → Private mode, min 2 / max 10, CPU 50%; JWT inbound; budget alert at 80% | Feedback loop live; LTMS `USER_PREFERENCE` + `CUSTOM` enabled |
| 4 | Eval set pass + citation audit | Load test 10 rps; DR/runbook; `/agentbase-monitor` dashboard reviewed | Pilot → org-wide rollout |

## Release engineering

- **Versioning:** every image `vcr.vngcloud.vn/<repo>/zalopay-knowledge:<semver>`; every deploy = `PATCH /agent-runtimes/{id}` → new immutable version.
- **Canary:** create endpoint `canary` pinned to the new version; route pilot traffic there (portal pilot users in MVP, Teams pilot in Phase 2); promote by letting DEFAULT track latest.
- **Rollback:** `PATCH .../endpoints/{DEFAULT}?version=<previous>` — instant, no rebuild.
- **Config changes** (env vars, flavor, autoscaling) are also PATCHes → versioned and rollbackable the same way.
- **Health gating:** a version that fails `GET /health` never serves; poll status `CREATING→ACTIVE`, on `ERROR` read `statusReason` + `/agentbase-monitor runtime-logs`.

## Operations

- Monitoring: `/agentbase-monitor` metrics (CPU/RAM vs 25–75% thresholds), endpoint logs for latency/error rates; alert on health-check failures, sync-job failure, staleness > 24h, budget 80%.
- Capacity: start `1x1-general`; flavor up on OOM before scaling out (the ≈1,000-page FAISS index across 3 partitions + embedding model — measure in `test docker`, resize if needed); expect scale-out at CPU > 50%.
- Cost saving between demo/pilot sessions: **STOP the runtime** (state `STOPPED` = no compute cost, config + endpoints preserved; START to resume) — confirmed in live Runtime docs.
- Credential rotation: per `/agentbase-identity` rotation reference; emergency: `reset-service-account` (restarts runtime).
- Teardown of any environment: `/agentbase-teardown zalopay-knowledge --dry-run` → review → real run.

## Deliberate deviations from earlier drafts

- No Kubernetes/ELK/Jaeger/Celery/Redis self-managed stack — replaced by Runtime + Monitor + Memory + scheduled sync job (see `../brainstrom/synthesis-fable-5/03-RECOMMENDATION.md` D1–D8).
- Earlier `--flavor gpu-small --region us-east-1` examples were not platform-valid; flavors are CPU/RAM classes like `1x1-general`, region is HCM.
- SQLite session storage from the old MVP plan replaced by AgentBase Memory (containers must be stateless).
