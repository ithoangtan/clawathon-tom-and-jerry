# Network policy — Zalopay Knowledge Agent (AgentBase VPC)

MVP security checklist requires **egress deny-all + allowlist** at the network
layer so the runtime cannot reach the public internet by construction.

## Principle

- **Default deny** all outbound traffic from the agent runtime.
- **Allowlist only** destinations the agent must call to function.
- **TLS required** for every allowed destination (enforced in app config too).

## Required egress allowlist (MVP)

| Destination | Port | Purpose |
|---|---|---|
| `maas-llm-aiplatform-hcm.api.vngcloud.vn` | 443 | VNG MaaS LLM inference |
| `*.atlassian.net` (Confluence sync job only) | 443 | Confluence REST API during sync |
| `www.googleapis.com` / `drive.googleapis.com` (sync only) | 443 | Google Drive PDF sync |
| AgentBase platform endpoints (`agentbase.api.vngcloud.vn`, identity, memory) | 443 | Platform services |

Sync jobs run inside the same container; if sync is moved to a separate job,
tighten the runtime allowlist to **MaaS + AgentBase platform only**.

## AgentBase runtime configuration

When deploying in **VPC / PRIVATE** mode (Phase 2):

1. Set runtime `networkMode` to VPC with **egress deny-all**.
2. Add explicit routes for each allowlisted CIDR or service endpoint.
3. Expose the runtime only via **Resource Gateway** with JWT/IAM inbound auth.
4. Set runtime env:
   - `APP_ENV=agentbase`
   - `GATEWAY_TRUST_REQUIRED=true`
   - `AGENT_ENABLED=true` (flip to `false` for kill-switch)

PUBLIC MVP (Phase 1) may use PUBLIC network mode for demo; document the
egress/TLS posture before GA and migrate to VPC deny-all.

## TLS in transit

- User → Gateway → Runtime: HTTPS terminated at AgentBase edge.
- Runtime → MaaS / Confluence / Drive: HTTPS only (`https://` URLs enforced in
  `app.config.Settings`).
- No plaintext HTTP for external service calls.

## Verification checklist

- [ ] Runtime security group / VPC route table has no `0.0.0.0/0` egress except via allowlist
- [ ] `curl https://example.com` from inside the container fails (deny-all)
- [ ] MaaS health/inference call succeeds over 443
- [ ] `.env` and credential files are **not** in the built image (`docker history` / inspect)
- [ ] `GATEWAY_TRUST_REQUIRED=true` in production with gateway injecting trust headers

## Reference

- `deploy/agentbase-runtime.env.example` — production env template (kill-switch, gateway trust)
- `2-requirements/08-KNOWLEDGE_AI_AGENT_CHECKLIST_AGAIN.md` §5–6
- `greennode-agentbase-skills/.claude/skills/agentbase-gateway/references/inbound-auth.md`
- `greennode-agentbase-skills/.claude/skills/agentbase-deploy` (VPC network mode)
