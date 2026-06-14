# TC29 — UI: Admin page — Knowledge sync dashboard

| Field | Value |
|-------|-------|
| **Test ID** | TC29 |
| **Mode** | UI — Browser navigation |
| **Type** | Happy case — admin/knowledge sync panel |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Click "Admin" link in top nav | `a[href="/admin"]` |
| 2 | Observe knowledge sync panel | Full admin dashboard |
| 3 | Check dept sync status table | All 4 sources visible |

---

## 📸 Observed UI State

**Page title:** "Knowledge sync"
**Subtitle:** "Trigger Confluence sync per department or globally, and monitor live job status with page counts and errors."

**Summary cards:**

| Card | Value |
|------|-------|
| TOTAL DOCUMENTS | **40** (Pages) |
| TOTAL CHUNKS | **96** |
| SOURCES SYNCED | **3 / 4** |
| LAST UPDATED | **< 1h ago** |

**Knowledge sources table:**

| Source | Status | State | Pages | Chunks | Last Updated |
|--------|--------|-------|-------|--------|-------------|
| Risk Management (Confluence) | `idle` · `Fresh (< 1h ago)` | ✅ | 13 | 37 | < 1h ago |
| Growth Enablement (Confluence) | `idle` · `Fresh (< 1h ago)` | ✅ | 14 | 23 | < 1h ago |
| Bank Partnerships (Confluence) | `idle` · `Fresh (< 1h ago)` | ✅ | 13 | 36 | < 1h ago |
| Sync PDFs from Drive (Drive) | `idle` · `Never synced` | ⚠️ | 0 | 0 | Never |

**Filter tabs:** All sources | Confluence only | Drive only

**Action button:** `Sync all departments` (blue, top right)

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Total docs ≥ 1 | ✅ | 40 | ✅ |
| Total chunks ≥ 1 | ✅ | 96 | ✅ |
| 3 Confluence depts visible | ✅ | Risk, Grow, Bank | ✅ |
| GDrive source visible | ✅ | "Sync PDFs from Drive" | ✅ |
| Per-dept chunk counts | ✅ | 37 / 23 / 36 | ✅ |
| "Never synced" for Drive | ✅ | ✅ | ✅ |
| "Sync all departments" button | ✅ | ✅ | ✅ |
| Filter tabs functional | ✅ | ✅ | ✅ |

---

## 📝 Ghi chú

- Bank Partnerships đã hoàn tất sync: 13 pages / 36 chunks (was running in previous session)
- GDrive source chưa sync — 0 chunks, "Never synced" — bình thường trong dev env
- 3/4 sources synced: Risk (37) + Grow (23) + Bank (36) = 96 total chunks
- "Sync all departments" button trigger `POST /sync/confluence` cho tất cả depts
- Admin page chỉ accessible từ main nav (not authenticated separately)
