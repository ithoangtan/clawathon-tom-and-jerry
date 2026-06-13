# ZaloPay Internal Knowledge Agent — Multi-Role Review Checklist (v3, phased)

> Self-review checklist for shipping an enterprise "knowledge brain" a demanding team will trust.
>
> **Two tags per line:**
> - Priority: **[MUST]** (load-bearing) · **[NICE]** (polish)
> - Phase: 🟢 **MVP** (in the first shippable pilot) · 🔵 **ROLLOUT** (before opening to all ~800 users / GA) · ⚪ **LATER** (continuous improvement; raises the ceiling)
>
> **Key assumption driving the phasing:** the **MVP corpus is non-sensitive, all-employee-readable content only.**
> This is what lets document-level ACL, PII classification, DLP, and the full red-team defer to ROLLOUT.
> ⚠️ **If the MVP corpus includes ANY sensitive docs (HR, contracts, Risk memos), every item marked `🔵 (corpus-conditional)` jumps back to 🟢 MVP and becomes launch-blocking for the pilot.**

---

## 0. Invariants (enforce in CODE, not prompt)

- [ ] 🟢 **[MUST]** No valid citation → no answer. Graph-level enforcement.
- [ ] 🟢 **[MUST]** No web tools / no writes (read-only), enforced by construction.
- [ ] 🟢 **[MUST]** Retrieved content treated as DATA, not instructions (basic injection hardening).
- [ ] 🟢 **[MUST]** Every factual sentence traces to ≥1 chunk in context.
- [ ] 🔵 **[MUST]** *(corpus-conditional)* LLM never sees content the user can't read. **MVP: satisfied by all-readable corpus. ROLLOUT: enforce via ACL filter.**

---

## 1. Senior AI Product Manager

- [ ] 🟢 **[MUST]** North-star metric (e.g. deflection rate) + guardrail (answered-wrong rate). Start simple.
- [ ] 🟢 **[MUST]** Conservative stance: refuse > guess (a product decision).
- [ ] 🟢 **[MUST]** Useful escalation path on refusal ("ask [person/Zalo channel]") — even a static pointer.
- [ ] 🟢 **[MUST]** Explicit out-of-scope definition; scope locked to 3 MVP departments.
- [ ] 🟢 **[MUST]** High-stakes disclaimer pattern: "verify with [owner], as of [date]".
- [ ] 🟢 **[NICE]** Rollout plan: pilot 1 friendly department → measure → expand.
- [ ] 🟢 **[NICE]** Capture thumbs up/down from day one.
- [ ] 🔵 **[MUST]** Content governance: named owner per Confluence space + stale-doc loop. *(MVP: just curate a clean, owned corpus.)*
- [ ] 🔵 **[NICE]** Feedback → triage queue with an owner and SLA.
- [ ] 🔵 **[NICE]** Discoverability / onboarding for 800 users.
- [ ] ⚪ **[NICE]** Repeat-usage / WAU tracking as the real trust signal.

---

## 2. Senior AI Engineer

### Retrieval
- [ ] 🟢 **[MUST]** Hybrid search (dense + BM25/lexical).
- [ ] 🟢 **[MUST]** Cross-encoder reranker (retrieve 30–50 → rerank → keep 5–8). bge-reranker-v2-m3 / PhoRanker / ViRanker.
- [ ] 🟢 **[MUST]** Correct E5 prefixes (`query:`/`passage:`) with an asserting test (if using E5).
- [ ] 🟢 **[MUST]** Empty-retrieval → useful refusal, never "best-effort guess."
- [ ] 🟢 **[NICE]** Decide embedding model up front (switching later = migration). Consider BGE-M3.
- [ ] ⚪ **[NICE]** Query rewriting: acronym expansion, spell-fix, VI↔EN.
- [ ] ⚪ **[NICE]** Multi-query / HyDE for hard questions.
- [ ] 🔵 **[MUST]** *(corpus-conditional)* Permission filter before rerank/generate.

### Generation & behavior
- [ ] 🟢 **[MUST]** Answer ladder (MVP: 3 tiers — full / partial+gap / useful refusal).
- [ ] 🟢 **[MUST]** Refusal always points somewhere.
- [ ] 🟢 **[MUST]** Policy/compliance: quote key clauses verbatim + "as of [date]".
- [ ] 🟢 **[MUST]** Temperature ~0 for synthesis; prompts pinned & versioned.
- [ ] 🔵 **[MUST]** Multi-turn: standalone-question rewrite before retrieval. *(MVP can ship single-turn; needed once follow-ups are in scope.)*

### Citations
- [ ] 🟢 **[MUST]** Inline, claim-level citations.
- [ ] 🟢 **[MUST]** Each citation: title + link + last_modified (PDF: + page).
- [ ] 🟢 **[MUST]** Post-generation faithfulness check; unsupported sentences dropped/flagged.
- [ ] 🟢 **[MUST]** Never cite an unused doc.
- [ ] 🟢 **[MUST]** Pick a verification mechanism (MVP: LLM-judge; LATER: NLI entailment).
- [ ] ⚪ **[NICE]** Deep-anchor links to exact section.
- [ ] ⚪ **[NICE]** Quote/paraphrase distinction + "based on N sources" confidence.

### Router & meta
- [ ] 🟢 **[MUST]** Intent classification: knowledge Q vs chit-chat vs action request.
- [ ] 🟢 **[MUST]** Routing + confidence threshold; uncertain → fan-out / search-all.
- [ ] 🟢 **[MUST]** Out-of-scope detection.
- [ ] 🔵 **[MUST]** "Grade the graders": small-model nodes measured in the eval set.
- [ ] ⚪ **[NICE]** Fallback model when primary MaaS model is overloaded.
- [ ] ⚪ **[NICE]** Context-budget tuning (precision after rerank > many chunks).

### Conflict & recency
- [ ] 🟢 **[MUST]** Prefer by last_modified across versions (cheap).
- [ ] 🔵 **[MUST]** Detect & SURFACE conflicts instead of silently picking one.
- [ ] ⚪ **[NICE]** Authority weighting + stale-doc warning.

---

## 3. Senior DevOps / Platform (SRE)

- [ ] 🟢 **[MUST]** Working, idempotent sync job (build offline, tombstones for deletes).
- [ ] 🟢 **[MUST]** Atomic index swap (never serve a half-built index).
- [ ] 🟢 **[MUST]** Readiness probe = index loaded + MaaS reachable (separate from liveness).
- [ ] 🟢 **[MUST]** Retry + timeout on MaaS/LLM calls; graceful degradation if a dept subgraph fails.
- [ ] 🟢 **[MUST]** Per-stage tracing (query → rewrite → chunks+scores → grades → answer → citations → verify).
- [ ] 🔵 **[MUST]** Sync freshness SLA + alerting + dead-letter path.
- [ ] 🔵 **[MUST]** Versioned index with one-command rollback.
- [ ] 🔵 **[MUST]** Eval-as-CI-gate: golden set blocks deploy on regression.
- [ ] 🔵 **[MUST]** Canary / blue-green deploy with automated rollback.
- [ ] 🔵 **[MUST]** Rate limiting / queueing / backpressure under load.
- [ ] 🔵 **[MUST]** Runbooks: MaaS down, sync failed, bad-answer spike, index corruption.
- [ ] 🔵 **[NICE]** Latency budget per stage + cost/token per query.
- [ ] 🔵 **[NICE]** IaC + dev↔prod parity.
- [ ] 🔵 **[NICE]** Load/capacity test at ~800-user peak.
- [ ] 🔵 **[NICE]** SLOs + error budget + quality dashboard.
- [ ] ⚪ **[NICE]** Circuit breaker, private-registry fallback, semantic cache.

---

## 4. Senior Data Engineer

- [ ] 🟢 **[MUST]** Full chunk metadata: source, url/anchor, space/label, last_modified, author, doc_type, **acl field present** (even if unused in MVP).
- [ ] 🟢 **[MUST]** Basic doc_type classification rules (rule-based).
- [ ] 🟢 **[NICE]** Re-embedding / reindex migration plan documented up front.
- [ ] 🟢 **[NICE]** Start logging queries + feedback from day one.
- [ ] 🔵 **[MUST]** Corpus coverage metric: % of authoritative sources actually indexed.
- [ ] 🔵 **[MUST]** Data lineage: source → chunk → answer, auditable.
- [ ] 🔵 **[MUST]** Data contract with Confluence/Drive APIs + drift alerting.
- [ ] 🔵 **[NICE]** doc_type taxonomy governance owner.
- [ ] 🔵 **[NICE]** Golden/eval dataset versioned & governed.
- [ ] 🔵 **[NICE]** Mine query logs + feedback to grow the eval set from REAL questions.
- [ ] 🔵 **[MUST]** *(corpus-conditional)* PII / sensitivity classification at ingest.
- [ ] ⚪ **[NICE]** Near-duplicate / version detection.
- [ ] ⚪ **[NICE]** Structural / parent-child chunking; tables & code handled distinctly.
- [ ] ⚪ **[NICE]** Retrieval-quality drift monitoring.

---

## 5. Senior Cloud Architect

- [ ] 🟢 **[MUST]** Egress deny-all + allowlist — enforces "no internet by construction" at the network layer.
- [ ] 🟢 **[MUST]** TLS in transit everywhere.
- [ ] 🔵 **[MUST]** Private endpoints inside ZaloPay VPC; nothing public except authenticated gateway.
- [ ] 🔵 **[MUST]** Data residency: confirm MaaS / embeddings / vector store / logs run in-country.
- [ ] 🔵 **[MUST]** Compliance gate: PDPL 2026 (Law 91/2025/QH15) + Decree 356/2025; localization under Decree 53/2022 (≥24-mo retention). DPIA + DPO sign-off. *(Verify scope with legal — not engineering's call.)*
- [ ] 🔵 **[MUST]** Encryption at rest with KMS-managed keys.
- [ ] 🔵 **[MUST]** Least-privilege IAM between services.
- [ ] 🔵 **[NICE]** DR: backup + restore drill for index & metadata DB; defined RPO/RTO.
- [ ] ⚪ **[NICE]** Multi-AZ HA.
- [ ] ⚪ **[NICE]** Cost architecture (vector store sizing, embedding compute, token model, scale-to-zero sync).

---

## 6. Senior Security Engineer

- [ ] 🟢 **[MUST]** `X-GreenNode-AgentBase-*` headers set ONLY by trusted gateway; rejected if client-supplied. Verify early — retrofitting auth is painful.
- [ ] 🟢 **[MUST]** Audit log: who asked what, what was retrieved, what was returned (basic in MVP).
- [ ] 🟢 **[MUST]** Kill-switch / feature flag to disable the agent instantly.
- [ ] 🟢 **[MUST]** Secrets not in image (AgentBase Identity); no hardcoded credentials.
- [ ] 🟢 **[NICE]** Pin dependencies.
- [ ] 🔵 **[MUST]** Red-team pass (injection, jailbreak, ACL bypass, PII leak) = hard GA gate.
- [ ] 🔵 **[MUST]** Threat-model + red-team the RAG confused-deputy / IDOR.
- [ ] 🔵 **[MUST]** Prompt-injection → exfiltration chain tested.
- [ ] 🔵 **[MUST]** Compliance-grade audit trail (fintech requirements).
- [ ] 🔵 **[MUST]** Incident-response runbook for "agent leaked sensitive info" + index quarantine.
- [ ] 🔵 **[MUST]** Secrets rotation.
- [ ] 🔵 **[NICE]** Supply chain: SCA + image scan + SBOM + registry integrity.
- [ ] 🔵 **[NICE]** Rate-limit / abuse detection (corpus-scraping via Q&A).
- [ ] 🔵 **[MUST]** *(corpus-conditional)* Document-level ACL enforced at retrieval.
- [ ] 🔵 **[NICE]** *(corpus-conditional)* DLP on outputs.
- [ ] ⚪ **[NICE]** Cross-department leakage tests as a standing regression suite.

---

## 7. Evaluation (shared gate)

- [ ] 🟢 **[MUST]** Golden set (MVP: ~30–50 questions → expected answer → expected citation).
- [ ] 🟢 **[MUST]** Retrieval metrics: context recall & precision @k.
- [ ] 🟢 **[MUST]** Generation metrics: faithfulness + answer relevance.
- [ ] 🟢 **[MUST]** Refusal precision/recall (over-refusal AND hallucination).
- [ ] 🔵 **[MUST]** Golden set re-runs in CI on every model/prompt/chunking change.
- [ ] 🔵 **[NICE]** LLM-as-judge offline eval; injection + out-of-scope test suites.
- [ ] ⚪ **[NICE]** Periodic thumbs-down analysis → patch retrieval gaps.

---

## MVP cut at a glance (everything 🟢)

**Retrieval & answers:** hybrid + reranker · claim-level citations + faithfulness check · refuse-without-evidence invariant · 3-tier answer ladder · basic intent routing + out-of-scope detection · temp-0 + versioned prompts.
**Trust & product:** north-star + guardrail metric · conservative refusal stance · useful escalation pointer · high-stakes disclaimer · thumbs capture.
**Platform:** working idempotent sync · atomic index swap · readiness probe · retry/timeout · per-stage tracing.
**Security:** header trust verified · basic audit log · kill-switch · no creds in image · pinned deps · "no web / no writes" + egress deny-all + TLS.
**Eval:** ~30–50 golden questions measuring faithfulness + refusal precision/recall.
**Data:** full chunk metadata (acl field present) · basic doc_type rules · query/feedback logging on · reindex plan documented.

## Defers to ROLLOUT (before opening to all ~800)

Document-level ACL · PII classification + DLP · full red-team + threat model · data residency / PDPL / DPIA sign-off · private endpoints + encryption-at-rest · CI eval-gate + canary deploy + rollback · freshness SLA + runbooks + load test · content-governance loop · conflict surfacing · multi-turn rewrite · data lineage + contracts + coverage metric.

## ⚠️ Conditional reminder

Every `🔵 (corpus-conditional)` item becomes 🟢 **MVP-blocking** the moment any sensitive document enters the MVP corpus. Keep the MVP corpus all-readable to keep them deferred.