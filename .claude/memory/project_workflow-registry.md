---
name: project-workflow-registry
description: UC01/UC02 confirmed config — Confluence space, Jira token, workflow content status
metadata:
  type: project
---

UC01 Campaign Risk Review + UC02 Workflow Registry platform đang được thiết kế.

**Confirmed config:**
- Confluence space key cho workflow registry: `Workflow`
- Jira API token: có sẵn, có quyền read ticket + write comment
- Workflow page mẫu (Campaign Risk Review): Risk team sẽ cung cấp — chưa có, là blocker duy nhất cho Phase 1

**Why:** Hai UC này target Risk/BAU team, giải quyết bài toán review campaign thủ công không đồng nhất.

**How to apply:** Khi bắt đầu build, Confluence space = `Workflow`, cần check workflow page đã có chưa trước khi code Workflow Discovery Node.
