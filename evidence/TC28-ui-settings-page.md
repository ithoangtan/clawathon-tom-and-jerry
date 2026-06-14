# TC28 — UI: Settings page — identity & runtime config

| Field | Value |
|-------|-------|
| **Test ID** | TC28 |
| **Mode** | UI — Browser navigation |
| **Type** | Happy case — settings page rendering & interaction |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Click "Settings" in top nav | `a[href="/settings"]` |
| 2 | Observe identity panel | User ID, Role, Language, Home dept |
| 3 | Observe runtime config panel | Read-only fields from /health |

---

## 📸 Observed UI State

**Page title:** "Settings"
**Subtitle:** "Configure your identity, sync preferences, and runtime environment for grounded answers."

**Your identity section:**

| Field | Value |
|-------|-------|
| User ID | `user-289707e3` (auto-generated) |
| Role | `Business` (dropdown) |
| Language | `EN` / `VI` toggle |
| Home department | `Risk Management` + [Change] link |
| Save button | Blue "Save" button |

**Runtime config section (read-only, grayed out):**

| Field | Value |
|-------|-------|
| small_model | `qwen/qwen3.7-plus` |
| main_model | `qwen/qwen3.7-plus` |
| embedding_model | `baai/bge-m3` |
| grade_threshold | `0.3` |
| topk | `8` |
| route_confidence_min | `0.55` |
| Version | `1.0.0` |

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| User ID editable | ✅ | ✅ text input | ✅ |
| Role dropdown | ✅ options | `Business` selected | ✅ |
| Language EN/VI toggle | ✅ | ✅ | ✅ |
| Home dept with Change link | ✅ | `Risk Management` | ✅ |
| Runtime config read-only | ✅ greyed out | ✅ disabled inputs | ✅ |
| grade_threshold = 0.3 | ✅ | `0.3` | ✅ |
| embedding_model = baai/bge-m3 | ✅ | `baai/bge-m3` | ✅ |
| Version 1.0.0 | ✅ | `Version 1.0.0` | ✅ |

---

## 📝 Ghi chú

- Runtime config is read-only in UI — matches `/health` config endpoint
- User identity (User ID, Role, Home dept) được gửi với mỗi chat request qua headers
- Language toggle trong Settings cũng thay đổi toàn bộ UI (đồng bộ với header toggle)
- Home department sẽ ảnh hưởng auto-routing khi không pin specific dept
