# TC06 — Auto-route: Out-of-Scope Question (Tỷ giá, Cổ phiếu)

| Field | Value |
|-------|-------|
| **Test ID** | TC06 |
| **Mode** | Auto-route (Agent Center) |
| **Type** | Edge case — câu hỏi hoàn toàn ngoài scope |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "question": "Tỷ giá USD/VND hiện tại là bao nhiêu? Và cổ phiếu VNG đang ở mức nào?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ⛔ refused |
| **model_used** | `None` |
| **source_departments** | `[]` |
| **citations** | 0 |
| **confidence** | `0.000` |

### Answer

Câu hỏi này nằm ngoài phạm vi tài liệu đã lập chỉ mục (ví dụ: số liệu thời gian thực).

**Liên hệ tiếp:**
- **Quản lý Rủi ro**: Teams `teams-risk-knowledge` hoặc Nguyễn Thị Lan (trưởng bộ phận)
- **Phát triển Kinh doanh**: Teams `teams-grow-enablement-knowledge` hoặc Trần Văn Minh (trưởng bộ phận)
- **Đối tác Ngân hàng**: Teams `teams-bank-partnerships-knowledge` hoặc Lê Hoàng (trưởng bộ phận)

Phạm vi MVP: chỉ tài liệu nội bộ của Quản lý Rủi ro, Phát triển Kinh doanh, Đối tác Ngân hàng. Không tra cứu internet, dữ liệu thời gian thực, HR/pháp lý ngoài phạm vi, và không thực hiện hành động trên hệ thống.

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Expected | Actual | Kết quả |
|---|---|---|---|
| Từ chối trả lời | ✅ phải refused | ✅ `status: refused` | ✅ Đúng |
| Không hallucinate số liệu | ✅ không bịa tỷ giá | ✅ không có số liệu nào | ✅ Đúng |
| Giải thích lý do từ chối | ✅ "ngoài tài liệu indexed" | ✅ giải thích rõ | ✅ Đúng |
| Gợi ý kênh liên hệ | Nên có | ✅ cung cấp Teams channels | ✅ Tốt |

## 📝 Ghi chú

- Router nhận đúng intent là `out_of_scope` (real-time data) → từ chối ngay, không thực hiện retrieval
- Tên nhân vật trong escalation hint (Nguyễn Thị Lan, Trần Văn Minh, Lê Hoàng) là hardcoded trong product copy — không lấy từ tài liệu indexed, không gây hại nhưng cần review nếu nhân sự thay đổi
