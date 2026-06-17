# Zalopay Internal Knowledge Agent

🌐 [Phiên bản Tiếng Việt → README.md](README.md)

> **"Knowledge stays. Legacy grows."**
>
> A living knowledge platform for Zalopay — helping every team make faster, more consistent decisions, and inherit accumulated experience across generations.

---

## The Problem

**Whichever team you're on — you'll recognize yourself in this.**

Risk, Tech, Operations, Finance, or any department — everyone is hitting the same wall:

| # | Problem | Symptom |
|---|---------|---------|
| 1 | **Who do I ask now?** | The person who held the knowledge has switched teams, is busy, or has left Zalopay. Knowledge lives inside people's heads — with nowhere to store it. |
| 2 | **We've hit this before...** | Last year's post-mortems, case studies, and incident reports are forgotten. Old mistakes repeat themselves in other teams. |
| 3 | **Is this the right process? Who confirms?** | Team A knows they need a risk review. Team B thinks they don't — but they actually do. No one knows who to ask for a quick confirmation. |
| 4 | **Even the best AI needs one thing** | Internal knowledge: Zalopay's policies, experience, and context. Without it, generic AI cannot apply the judgment of someone who has worked here for years. |

---

## Demo: Risk Review Workflow

> *"To make this concrete — this is one of the first workflows we built: Risk Review for campaigns. The same architecture applies to **any process that requires background knowledge to reason through**."*

**Flow:**

```
TICKET CREATED (NEW)  →  RISK REVIEW (TRIGGERED)  →  AGENT WORKING
                                                            │
                                             ┌──────────────┴──────────────┐
                                             │  1. Read Jira ticket         │
                                             │  2. Fetch Risk Playbook from │
                                             │     Confluence               │
                                             │  3. Cross-check policy       │
                                             │  4. Draft Quick Risk Report  │
                                             └─────────────────────────────┘
                                                            │
                              ┌─────────────────────────────┴─────────────────────────────┐
                              │                                                             │
                       ✅ LOW RISK                                                   ❌ HIGH RISK
                Notify Risk PIC to approve                             Return ticket immediately, explain why
                              │                                                             │
                       📧 Send notify to Risk PIC                           📧 Notify ticket creator
                          to review & approve                                  + suggest fixes
                              └────────────────────── ⏱ ~10–15 minutes ──────────────────────┘
```

**Same architecture applies to:** Compliance review · Partner due diligence · Onboarding checklist · Incident triage · Policy Q&A · and more.

---

## Why Now?

**AI isn't the bottleneck — internal knowledge is the competitive edge.**

**01 — Claude, ChatGPT, Gemini are powerful — but they don't know Zalopay**
These AIs don't know Zalopay's Risk Playbook, last year's major incidents, or which teams need to review what. Internal knowledge is a competitive advantage — whoever builds it first, wins.

**02 — Zalopay already has the assets — it just needs to unlock them**
Years of accumulated SOPs, post-mortems, playbooks, and case studies. This is knowledge no generic AI has. Wiki Agent is the layer that turns those assets into action.

**03 — Companies that build their knowledge base today will have an AI-native edge in one year**
It's not about waiting for a better AI. It's about waiting for enough knowledge for AI to work on your behalf. Start today, and in one year Zalopay will be ready for any AI-native workflow.

---

## Platform — One Platform, For Every Team

Three core concepts. No need to be a developer to understand — and no need to be a developer to build new workflows.

### 🗄️ Store Knowledge — Organized by Department
Automatically reads and syncs documents from Confluence. Knowledge is structured per department with individual access controls. Each team has its own agent — agents can communicate with each other to make multi-dimensional decisions, cross-reference sources, or generate review checklists before reaching a conclusion.

### 🧠 Understand & Reason from Internal Knowledge
When a decision is needed, the agent finds the right documents, reads the context, and applies the correct policy — without inventing answers beyond what has been recorded. This is the key differentiator: AI doesn't guess, AI applies exactly what Zalopay has accumulated.

### ⚡ Automate Processes with Reasoning
Chat to ask questions. Or run a workflow: execute repetitive steps that require knowledge — not just simple automation, but automation with reasoning. The agent thinks and acts until the task is complete.

---

## Living Wiki — Where Knowledge Never Gets Lost

Inherit the accumulated experience from previous Zalopay generations — instead of every new person starting from zero.

```
Year One          Following Years      Today & Beyond
    ▓                 ▓▓▓▓               ▓▓▓▓▓▓▓▓  ✦
    │                  │                     │
Foundation docs    Post-mortems,       Agent reasoning
policies, SOPs     case studies,       across the entire
                   playbooks           knowledge base
```

> *The more teams contribute knowledge → the deeper the agent understands Zalopay*

---

## Impact

**Saving time for both sides.**

Not replacing people — enabling people to focus on decisions that truly require human judgment.

| Metric | Result |
|--------|--------|
| ⏱ Time to receive AI review feedback | **~15 minutes** (instead of waiting days) |
| 🤖 LOW risk tickets — reviewer only needs to approve | **~50%** of tickets |

> *"Saves time for both the ticket creator and the reviewer. Risk team focuses on decisions that truly require human judgment."*

---

## Governance — AI Assists, Humans Decide

This is not fully autonomous AI. This is AI working alongside humans — accountable, controllable, auditable.

### ✅ Human-in-the-Loop Always
For every workflow, AI handles the first pass. Final decisions always belong to humans. LOW risk → reviewer gets notified and approves. HIGH risk → returned immediately for correction. AI is never the final approver.

### 🔍 Complete Audit Trail
Every AI reasoning step is logged: which documents were used, confidence levels, and the outcome. Compliance and management can audit any decision at any time.

### 🚨 When Uncertain → Escalate, Don't Block
Low AI confidence triggers automatic escalation to a human. Workflows never get stuck because the AI isn't sure. Nothing gets lost or overlooked.

---

## Architecture — MVP → Production

Same architecture — only scale and infrastructure differ. The three core steps remain unchanged:

```
Documents  →  Stored Knowledge  →  Action
(Confluence    (Vector index +      (Chat · Workflow
 / GDrive)      memory)             · Notify)
```

| Component | MVP (Demo) | Production |
|-----------|-----------|------------|
| Document source | Personal Confluence + Google Drive | Company Confluence (all of Zalopay) |
| Jira | Personal Jira | Company Jira |
| Notifications | Gmail | Teams / Jira & Confluence native notification |
| Infrastructure | GreenNode AgentBase | Self-hosted at Zalopay — data stays internal |
| AI Model | VNG MaaS — Qwen | Per workflow: lightweight model for screening, powerful model for reasoning |
| Integration | Direct API call | MCP (Model Context Protocol) — add new tools without modifying the agent |
| Security | Basic auth | SSO (Zalopay IAM) · RBAC · Audit log |
| Knowledge sync | Manual | Auto-sync when Confluence changes |

**Production — additionally:**
- Human-in-the-loop: automatic escalation when AI confidence is low
- Audit trail: all AI reasoning fully logged
- Workflow versioning: policy changes → workflow updates automatically
- Data residency: all data stays within Zalopay infrastructure

---

## Next Steps — From Demo to Zalopay-Wide

Three steps to turn the hackathon demo into a system that genuinely serves the entire company.

**01 — Validate with a Real Team**
Run with real ticket volume, measure AI review accuracy against human review. Calibrate and improve before scaling.

**02 — Connect Company Systems**
Switch from personal accounts to company Confluence + Jira. Deploy on Zalopay infrastructure — data stays internal, security compliant.

**03 — Every Team Starts Building Their Knowledge Base Today**
No need to wait for a perfect AI. Start storing knowledge, start building workflows. In one year, Zalopay will be ready for any AI-native workflow. Adding a new workflow = adding one Confluence page.

---

## Closing

> *"Knowledge stays. Legacy grows."*
>
> The more knowledge accumulates, the more workflows support teams — and the deeper the agent understands Zalopay. Not just Zalopay today, but Zalopay for many years to come.

**Risk review is just the first workflow.**

---

*Built with ❤ at Clawathon — Zalopay Internal Knowledge Agent*
