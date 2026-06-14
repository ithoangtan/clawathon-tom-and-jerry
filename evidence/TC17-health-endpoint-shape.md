# TC17 — Health endpoints shape validation

| Field | Value |
|-------|-------|
| **Test ID** | TC17 |
| **Mode** | API — `GET /health`, `/health/ready`, `/health/live` |
| **Type** | Contract — endpoint shape & required fields |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
GET http://localhost:8080/health
GET http://localhost:8080/health/ready
GET http://localhost:8080/health/live
```

No auth headers required.

---

## 📥 Response

### GET /health

| Field | Value |
|-------|-------|
| **status_code** | `200` |
| **status** | `healthy` |
| **version** | `1.0.0` |
| **index_ready** | `true` |
| **config.grade_threshold** | `0.3` |
| **config.topk** | `8` |
| **config.embedding_model** | `baai/bge-m3` |
| **config.small_model** | `qwen/qwen3.7-plus` |
| **config.main_model** | `qwen/qwen3.7-plus` |
| **config.route_confidence_min** | `0.55` |

### GET /health/ready

| Field | Value |
|-------|-------|
| **status_code** | `200` |
| **index_ready** | `true` |
| **ready** | `true` |

### GET /health/live

| Field | Value |
|-------|-------|
| **status_code** | `200` |
| **status** | `healthy` |
| **version** | `1.0.0` |

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `/health` → 200 | ✅ | 200 | ✅ |
| `status: "healthy"` | ✅ | `healthy` | ✅ |
| `version: "1.0.0"` | ✅ | `1.0.0` | ✅ |
| `config.grade_threshold: 0.3` | ✅ | `0.3` | ✅ |
| `config.topk: 8` | ✅ | `8` | ✅ |
| `config.embedding_model: "baai/bge-m3"` | ✅ | `baai/bge-m3` | ✅ |
| `/health/ready` → 200 + `ready: true` | ✅ | 200 + `true` | ✅ |
| `/health/live` → 200 | ✅ | 200 | ✅ |
| No auth required for health | ✅ | ✅ no auth needed | ✅ |

---

## 📝 Ghi chú

- `/health/ready` returns 200 khi index đã sync; 503 khi chưa (K8s readiness probe semantics)
- `config` block expose đầy đủ các runtime parameters — useful cho ops observability
- Không cần auth headers cho health endpoints — phù hợp K8s liveness/readiness probe
