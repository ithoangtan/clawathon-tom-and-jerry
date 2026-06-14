# TC16 — Auto-route: Cross-version slot count v1 vs v2

| Field | Value |
|-------|-------|
| **Test ID** | TC16 |
| **Mode** | Auto-route |
| **Type** | Edge — cross-version comparison |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc16-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Lucky Wheel v1 và v2 khác nhau về số lượng slot như thế nào?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **lang** | `vi` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 6 |
| **confidence** | `0.72` |

### Answer (excerpt)

```
## Sự khác biệt về số lượng slot giữa Lucky Wheel v1 và v2

| Phiên bản | Số lượng slot hỗ trợ       |
|-----------|-----------------------------|
| v1        | 8 hoặc 12 slot [4]          |
| v2        | 6 / 8 / 10 / 12 slot [1][2] |

**Tóm tắt:** Lucky Wheel v2 đã mở rộng thêm 2 kích thước slot mới là **6 slot** và
**10 slot**, bên cạnh 2 kích thước cũ (8 và 12 slot) từ phiên bản v1 [2].

Điều này giúp đội Ops có thêm sự linh hoạt trong việc thiết kế vòng quay phù hợp
với từng chiến dịch cụ thể.
```

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `answered` | `answered` | ✅ |
| v1: 8 hoặc 12 slot | ✅ trong tech doc v1 | ✅ | ✅ |
| v2: 6/8/10/12 slot | ✅ trong tech doc v2 | ✅ | ✅ |
| Nêu rõ 2 sizes mới của v2 (6 và 10) | ✅ | ✅ | ✅ |
| Không nhầm thông tin v1 vs v2 | ✅ | ✅ phân biệt rõ | ✅ |
| `citations` từ cả v1 và v2 docs | ✅ | 6 citations | ✅ |

---

## 📝 Ghi chú

- confidence = 0.72 — cao nhất trong toàn bộ các TC, phản ánh câu hỏi so sánh rõ ràng
- Agent synthesize đúng từ cả Tech Doc v1 và v2 — không confuse giữa 2 version
- Cross-document retrieval hoạt động tốt: 6 citations span nhiều docs
