# TC13 — EN query: Campaign statuses in Lucky Wheel

| Field | Value |
|-------|-------|
| **Test ID** | TC13 |
| **Mode** | Auto-route — English question |
| **Type** | Happy case — EN language detection |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc13-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "What are the campaign statuses in Lucky Wheel?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **lang** | `en` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 5 |
| **confidence** | `0.368` |
| **model_used** | `minimax/minimax-m2.5` |
| **feedback_id** | `8769084e-2c8e-42b9-9e31-4ac7bbe7308a` |

### Answer (excerpt)

```
## Campaign Statuses in Lucky Wheel

DRAFT → SCHEDULED → ACTIVE → ENDED

1. DRAFT – Campaign is being created or edited
2. SCHEDULED – Campaign is set up with start/end times but not yet running
3. ACTIVE – Campaign is currently live and accepting spins
4. ENDED – Campaign has passed its end date/time
```

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `answered` | `answered` | ✅ |
| `lang` | `en` | `en` | ✅ |
| Route đến `grow_enablement` | ✅ | `['grow_enablement']` | ✅ |
| 4 trạng thái DRAFT/SCHEDULED/ACTIVE/ENDED | ✅ trong ops guide | ✅ liệt kê đủ 4 | ✅ |
| `citations` ≥ 1 | ✅ | 5 | ✅ |

---

## 📝 Ghi chú

- EN question → EN answer (`lang: en`) — bilingual detection bidirectional
- Auto-route nhận diện đúng `grow_enablement` không cần explicit `target_departments`
- confidence = 0.368 > GRADE_THRESHOLD (0.3) → answer được chấp nhận
- Model `minimax/minimax-m2.5` (auto-fallback từ `qwen/qwen3.7-plus` daily quota)
