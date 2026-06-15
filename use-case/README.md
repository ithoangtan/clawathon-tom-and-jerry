# Use Case Catalog — Zalopay Internal Knowledge Agent

---

## Tổng Quan

| ID | Use Case | Role | Demo nhanh nhất |
|---|---|---|---|
| [UC01](UC01-campaign-risk-review-agent.md) | Campaign Risk Review Agent | **Application** — use case cụ thể đầu tiên | 1.5 ngày (minimal) / 4 ngày (full) |
| [UC02](UC02-workflow-registry-platform.md) | Workflow Registry & Execution Platform | **Platform** — nền tảng scale 100+ workflows | 2 ngày (minimal) / 6 ngày (full) |

## Mối Quan Hệ

```
UC02 = Platform (Workflow Registry + Executor Engine)
UC01 = Use case đầu tiên CHẠY TRÊN platform đó

Demo UC01 = bằng chứng UC02 hoạt động
Demo UC02 = lý do UC01 scale được mà không cần code thêm
```

## Thứ Tự Build Đề Xuất

**Phase 1 — Proof of concept (2 ngày):**
Tạo 1 workflow page trên Confluence (Campaign Risk Review). Sync vào OpenSearch. Agent fetch + hiển thị từng step trong chat. User tick checklist. Không cần Jira, không cần executor phức tạp.

**Phase 2 — Full UC01 (thêm 2 ngày):**
Thêm Jira client (read ticket + write comment). Agent thực thi workflow tự động từ Jira key.

**Phase 3 — UC02 Platform (thêm 2 ngày):**
Workflow discovery (tìm đúng workflow cho bất kỳ task nào). Workflow executor chạy multi-step với cross-department assignment.

## Config Đã Xác Nhận ✅

| Item | Giá trị |
|---|---|
| Confluence space key (workflow registry) | `Workflow` |
| Jira API token (read + write comment) | ✅ Sẵn sàng |
| Workflow page mẫu (Risk team viết) | ⏳ Chờ cung cấp |

## Blockers Còn Lại

- [ ] **Workflow page mẫu** — Risk team cung cấp sau. Đây là prerequisite duy nhất trước khi chạy Phase 1.
