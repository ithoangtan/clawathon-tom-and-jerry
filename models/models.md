# GreenNode AI Platform — Model Catalog Reference

> **Mục đích:** Tài liệu tham chiếu nội bộ cho Zalopay Knowledge Agent — chọn model theo vai trò (router / grade / synthesize / embed / rerank / OCR / STT).
>
> **Nguồn dữ liệu:**
> - Danh sách model + trạng thái ENABLED/DISABLED: screenshot console AI Platform (2026-06-13)
> - Platform API schema: `code/greennode-agentbase-skills/.claude/skills/agentbase-llm/SKILL.md`, `aip.sh models list|get|metadata`
> - Billing công khai (mức giá theo **provider/family**, không phải từng model): [GreenNode MaaS Pricing](https://greennode.ai/product/model-as-a-service), [VNG docs — Connect OpenAI-compatible to MaaS](https://docs.vngcloud.vn/vng-cloud-document/ai-stack/agent-base/ai-coding/connect-openai-compatible-to-maas)
> - Kiến trúc sử dụng model trong dự án: `2-requirements/04-SKILLS-TOOLS-INTEGRATIONS.md`, `03-ARCHITECTURE.md`
>
> **⚠️ Giới hạn nguồn (đọc trước khi dùng):**
> 1. **Không có IAM credentials** tại thời điểm tạo file → chưa gọi được `aip.sh models list/get` để lấy `uuid`, `path`, `description`, `inputPrice`, `outputPrice`, `useCases` chính xác từng model.
> 2. Skill `/agentbase-llm` ghi rõ: **không hiển thị pricing** vì có thể theo hợp đồng doanh nghiệp — giá thực tế xem **AI Platform Console → Usage / Billing**.
> 3. Giá công khai trên greennode.ai chỉ liệt kê theo **nhóm provider** (DeepSeek, Qwen, GreenMind, BGE, Whisper…), **không map 1:1** với tên model trong console (vd. `Qwen 3.5 27B`).
> 4. Cột **"Làm tốt việc gì"** dưới đây suy luận từ: (a) loại model trên console, (b) tài liệu GreenNode theo category, (c) đặc tính công khai của model family — **chưa verify bằng API detail từng model**.
> 5. Một số tên model (GPT-5, DeepSeek V4, Gemma 4, Qwen 3.7…) có thể là **bản preview / đặt tên nội bộ platform** — không tìm thấy spec độc lập trên web công khai.

**Endpoint inference (OpenAI-compatible):** `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`  
**Tham số `model` khi gọi API:** dùng field `path` từ model detail (fallback `code` nếu không có `path`).

---

## Tóm tắt nhanh cho Zalopay Knowledge Agent

| Vai trò (LangGraph node) | Model type cần | ENABLED hiện tại (screenshot) | Gợi ý |
|---|---|---|---|
| Router, grade, verify | CHAT — nhỏ/rẻ | `GPT-OSS 20B`, có thể thử `MiniMax M2.5` | Tier `LLM_MODEL_SMALL` |
| Synthesize, reconcile | CHAT — mid/lớn | `Qwen 3.5 27B`, `Gemma 4 31B-IT`, `MiniMax M2.5` | Tier `MAIN_MODEL` |
| Hybrid retrieval — rerank | RERANK | **`Qwen 3 Reranker 8B`** ✅ | Thay local cross-encoder ở prod nếu muốn MaaS |
| Embeddings (MVP đang local) | EMBEDDING | Tất cả DISABLED | MVP giữ `multilingual-e5-small` local; phase 2 thử `Qwen 3 Embedding 8B` / `GreenNode Embedding Large 1007` |
| PDF / scan OCR | OCR | `GreenNode IDP` DISABLED | Phase 2 — bật khi cần extract PDF phức tạp |
| Audio transcript | SPEECH TO TEXT | **`Whisper Large V3`** ✅ | Không thuộc MVP text Q&A |

**Model ENABLED trên account (7/54):** MiniMax M2.5, Qwen 3.5 27B, Gemma 4 31B-IT, Whisper Large V3, GPT-OSS 20B, Qwen 3 Reranker 8B (+ các model khác nếu account khác).

---

## Giá cả (public reference — **ước lượng theo provider**)

Billing thực tế: **credit-token (1 credit = 1 VND)**, prepaid hoặc postpaid — xem console.

| Provider / family | Giá công khai (GreenNode MaaS page) | Áp dụng cho model nào trong catalog |
|---|---|---|
| DeepSeek (R1, Coder, …) | **$0.3 / triệu tokens** | DeepSeek V4*, DeepSeek Reasoner, DeepSeek Chat, DeepSeek R1 Qwen 3 8B |
| Alibaba Qwen | **$0.8 / triệu tokens** | Toàn bộ Qwen 3.x chat/coder/thinking |
| GreenMind (GreenNode) | **$0.3 / triệu tokens** | GreenMind Medium 14B R1 Chat |
| GreenNode embedding | **$0.02 / triệu tokens** | GreenNode Embedding Large 1007 |
| BAAI bge (embedding + reranker) | **$0.02 / triệu tokens** | Qwen 3 Reranker 8B (nếu billing theo nhóm reranker) |
| OpenAI Whisper | **$0.018 / phút** | Whisper Large V3 |
| OpenAI GPT-4o class | *Không có trên trang public* | GPT-4o, GPT-4o Mini, GPT-3.5 Turbo |
| Google Gemini | *Không có trên trang public* | Gemini 2.5*, Gemini 3.1*, Gemini Embedding 001 |
| MiniMax | *Không có trên trang public* | MiniMax M2.5 |
| OpenAI GPT-5*, GPT-OSS*, GPT Image | *Không có trên trang public* | Các model tương ứng |
| Zalo TTS | **$10 / triệu ký tự** | (không có trong screenshot list) |

> **Per-model `inputPrice` / `outputPrice`:** cần chạy `bash aip.sh models get <uuid>` sau khi có IAM — **chưa có trong file này**.

---

## Filter metadata (từ sidebar console)

### Model Type
`Chat` · `Image Generation` · `Speech to text` · `Text to Speech` · `Embedding` · `Completion` · `Rerank` · `OCR` · `Gemini generate content` · `Responses` · `Messages`

### Use Case (một phần visible)
`Vietnamese` — lọc model tối ưu tiếng Việt (chi tiết model nào thuộc use case này: **cần `aip.sh models metadata`**).

---

## Danh sách model đầy đủ

Chú thích cột:
- **Status:** trạng thái trên account lúc chụp màn hình
- **Types:** capability tags trên console
- **Giá:** chỉ ghi khi map được provider family từ nguồn public; còn lại `⚠️ chưa xác minh`
- **Làm tốt:** ghi chú use-case — **suy luận**, cần validate bằng eval

---

### CHAT — General purpose

| Model | Status | Types | Giá (public) | Làm tốt việc gì | Ghi chú / nguồn |
|---|---|---|---|---|---|
| **MiniMax M2.5** | ENABLED | CHAT, RESPONSES, MESSAGES | ⚠️ chưa xác minh | Hội thoại đa lượt, agent có tool/responses API; thường mạnh tiếng Trung/Việt trong các deployment MiniMax | Có RESPONSES + MESSAGES → phù hợp agent phức tạp hơn chat đơn giản |
| **Qwen 3.5 27B** | ENABLED | CHAT, MESSAGES | ~$0.8/M tokens (Qwen family) | **Ứng viên MAIN_MODEL** — synthesis, reconcile; đa ngôn ngữ VI+EN; cân bằng chất lượng/chi phí | Khớp kiến trúc `04-SKILLS` (Qwen mid tier) |
| **Gemma 4 31B-IT** | ENABLED | CHAT, MESSAGES | ⚠️ chưa xác minh | Instruction-tuned Google Gemma — Q&A, reasoning vừa; thay thế/alternative cho Qwen main | IT = instruction tuned |
| **Qwen 3.7 Plus** | DISABLED | CHAT, MESSAGES | ~$0.8/M tokens | Phiên bản Plus — reasoning/chat nâng cao hơn 3.5 | Cần enable + eval trước khi thay 3.5 |
| **DeepSeek V4 Flash** | DISABLED | CHAT, MESSAGES | ~$0.3/M tokens (DeepSeek) | Chat nhanh, rẻ — **ứng viên SMALL_MODEL** (router/grade/verify) | "Flash" → latency/cost ưu tiên |
| **DeepSeek V4 Pro** | DISABLED | CHAT, MESSAGES | ~$0.3/M tokens | Chat chất lượng cao hơn Flash — synthesis | So sánh với Qwen 3.5 trên golden set |
| **Qwen 3.6 27B** | DISABLED | CHAT, MESSAGES | ~$0.8/M tokens | Tương đương 3.5 — generation trước 3.7 | |
| **Gemini 3.1 Pro Preview** | DISABLED | CHAT | ⚠️ chưa xác minh | Preview Google — reasoning dài, đa modal (nếu hỗ trợ) | Preview — API có thể thay đổi |
| **Gemma 3 27B-IT** | DISABLED | CHAT | ⚠️ chưa xác minh | Thế hệ trước Gemma 4 — IT chat | Gemma 4 đang ENABLED — ưu tiên 4 |
| **Nemotron 3 Nano 30B-A3B** | DISABLED | CHAT | ⚠️ chưa xác minh | NVIDIA efficient MoE — chat nhẹ, throughput cao | Nano → small tier candidate |
| **ByteDance Seed 1.6 Flash** | DISABLED | CHAT | ⚠️ chưa xác minh | Chat nhanh ByteDance | |
| **ByteDance Seed 1.6** | DISABLED | CHAT | ⚠️ chưa xác minh | Chat chất lượng ByteDance | |
| **GPT-5 Nano** | DISABLED | CHAT, RESPONSES | ⚠️ chưa xác minh | Tier cực nhỏ OpenAI — routing/classification | Không có spec public độc lập |
| **GPT-5 Mini** | DISABLED | CHAT, RESPONSES | ⚠️ chưa xác minh | Tier nhỏ — grade/verify | |
| **GPT-5** | DISABLED | CHAT, RESPONSES, MESSAGES | ⚠️ chưa xác minh | Tier lớn — synthesis premium | Chi phí cao — chỉ khi eval chứng minh |
| **GPT-OSS 20B** | ENABLED | CHAT | ⚠️ chưa xác minh | Open-weight ~20B — **ứng viên SMALL_MODEL** rẻ, chạy trên MaaS | Đang ENABLED — thử router/grade trước |
| **GPT-OSS 120B** | DISABLED | CHAT | ⚠️ chưa xác minh | Open-weight lớn — chất lượng cao, chậm/đắt hơn 20B | |
| **Gemini 2.5 Pro** | DISABLED | CHAT, GENERATE CONTENT, MESSAGES | ⚠️ chưa xác minh | Reasoning + long context; generate content (Gemini native API) | Có nút "View detail" trên console |
| **Gemini 2.5 Flash** | DISABLED | CHAT, GENERATE CONTENT | ⚠️ chưa xác minh | Nhanh, rẻ hơn Pro — small/mid tasks | VNG docs ví dụ `gemini/gemini-2.5-flash` |
| **Gemini 2.5 Flash Lite** | DISABLED | CHAT, GENERATE CONTENT | ⚠️ chưa xác minh | Lite = rẻ nhất dòng 2.5 Flash | |
| **DeepSeek R1 Qwen 3 8B** | DISABLED | CHAT | ~$0.3/M tokens | Reasoning/distilled — câu hỏi logic, multi-step nhỏ | R1 style — chậm hơn Flash |
| **Qwen 3 235B-A22B Thinking 2507** | DISABLED | CHAT | ~$0.8/M tokens | MoE thinking — câu hỏi khó, cần suy luận sâu | Overkill cho MVP; token cao |
| **Qwen 3 30B-A3B Thinking 2507** | DISABLED | CHAT | ~$0.8/M tokens | Thinking nhỏ hơn 235B — tradeoff cost/reasoning | |
| **DeepSeek Reasoner** | DISABLED | CHAT | ~$0.3/M tokens | Chain-of-thought reasoning (DeepSeek R1 class) | Không dùng cho verify node nhẹ |
| **DeepSeek Chat** | DISABLED | CHAT | ~$0.3/M tokens | Chat general DeepSeek | |
| **GreenMind Medium 14B R1 Chat** | DISABLED | CHAT | ~$0.3/M tokens (GreenMind) | Model nội bộ GreenNode — chat VI/enterprise | R1 trong tên → reasoning |
| **GPT-3.5 Turbo** | DISABLED | CHAT | ⚠️ chưa xác minh | Legacy OpenAI — rẻ, baseline | Không khuyến nghị vs Qwen/OSS |
| **GPT-4o Mini** | DISABLED | CHAT | ⚠️ chưa xác minh | OpenAI small — grade/route | |
| **GPT-4o** | DISABLED | CHAT | ⚠️ chưa xác minh | OpenAI flagship — chất lượng cao, đắt | VNG docs ví dụ `openai/gpt-4o` |

---

### CHAT — Code specialized

| Model | Status | Types | Giá (public) | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **Qwen 3 Coder 480B-A35B Instruct** | DISABLED | CHAT | ~$0.8/M tokens | Code generation/review — repo lớn | Không cần cho KB Q&A nội bộ |
| **Qwen 3 Coder Plus** | DISABLED | CHAT, MESSAGES | ~$0.8/M tokens | Coding agent — inline edit, tools | |
| **Qwen 3 Coder Plus (2025-07-22)** | DISABLED | CHAT, MESSAGES | ~$0.8/M tokens | Snapshot dated — pin version cho reproducibility | Chọn 1 bản, không mix |

---

### COMPLETION (legacy completion API)

| Model | Status | Types | Giá | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **GPT-3.5 Turbo Instruct** | DISABLED | COMPLETION | ⚠️ | Prompt-completion kiểu cũ (không chat messages) | Không dùng cho LangGraph chat nodes |

---

### EMBEDDING

| Model | Status | Types | Giá (public) | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **Qwen 3 Embedding 8B** | DISABLED | EMBEDDING | ~$0.8/M tokens hoặc $0.02/M (BGE class) ⚠️ | Vector hóa query/passage cho semantic search | **Phase 2** thay local E5 nếu muốn MaaS |
| **Gemini Embedding 001** | DISABLED | EMBEDDING | ⚠️ | Google embedding — đa ngôn ngữ | |
| **OpenAI Text Embedding Ada 002** | DISABLED | EMBEDDING | ⚠️ | Legacy 1536-dim | |
| **OpenAI Text Embedding 3 Large** | DISABLED | EMBEDDING | ⚠️ | Chất lượng cao, dim lớn | |
| **OpenAI Text Embedding 3 Small** | DISABLED | EMBEDDING | ⚠️ | Cân bằng cost/quality | |
| **GreenNode Embedding Large 1007** | DISABLED | EMBEDDING | ~$0.02/M tokens | Embedding nội bộ GreenNode — semantic search enterprise | Tên "1007" có thể là version/date |

> **MVP Zalopay:** embeddings **local** (`intfloat/multilingual-e5-small`) — zero MaaS token trên sync path (`01-PROBLEM-AND-GOALS` G4).

---

### RERANK

| Model | Status | Types | Giá (public) | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **Qwen 3 Reranker 8B** | **ENABLED** | RERANK | ~$0.02/M tokens (BAAI bge reranker class) | **Cross-encoder rerank** sau hybrid retrieve (top 30–50 → keep 5–8) | Khớp checklist `08` — thay bge-reranker-v2-m3 hosted |

---

### OCR / Document

| Model | Status | Types | Giá | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **GreenNode IDP** | DISABLED | OCR | ⚠️ | Intelligent Document Processing — scan PDF, bảng biểu, form | Phase 2 PDF pipeline; không thay pypdf đơn giản |

---

### SPEECH

| Model | Status | Types | Giá (public) | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **Whisper Large V3** | **ENABLED** | SPEECH TO TEXT | **$0.018 / phút** | Transcribe audio → text; đa ngôn ngữ gồm VI | Ngoài scope MVP text Q&A |
| **Gemini 2.5 Flash Preview TTS** | DISABLED | TEXT TO SPEECH | ⚠️ | Text → giọng nói | Voice channel phase 3+ |

---

### IMAGE

| Model | Status | Types | Giá | Làm tốt việc gì | Ghi chú |
|---|---|---|---|---|---|
| **GPT Image 1** | DISABLED | IMAGE GENERATION | ⚠️ (Stable Diffusion ref $0.3/image trên MaaS page) | Sinh ảnh từ prompt | Out of scope KB agent |

---

## API fields cần lấy khi có credentials

Chạy từ `code/greennode-agentbase-skills/`:

```bash
# Metadata filters (providers, types, useCases)
bash .claude/skills/agentbase/scripts/aip.sh models metadata

# Full catalog (paginate: --page 1 --size 50)
bash .claude/skills/agentbase/scripts/aip.sh models list --size 100

# Detail một model
bash .claude/skills/agentbase/scripts/aip.sh models get <MODEL_UUID>
```

Fields quan trọng từ API (`agentbase-llm` skill):
`uuid`, `name`, `code`, `path`, `description`, `modelStatus`, `isEnabled`, `isFree`, `provider`, `types`, `inputPrice`, `outputPrice`, rate limits.

Sau khi có output, cập nhật file này với:
- `path` chính xác cho `.env` (`SMALL_MODEL`, `MAIN_MODEL`)
- Giá `inputPrice`/`outputPrice` per model
- `useCases` chính thức (vd. `Vietnamese`)

---

## Khuyến nghị bước tiếp theo (improve hệ thống)

1. **Cung cấp IAM** (`GREENNODE_CLIENT_ID` / `GREENNODE_CLIENT_SECRET`) → chạy `models list` + `get` để điền UUID, path, giá chính xác.
2. **Eval A/B trên golden set** (`evals/`): so sánh `Qwen 3.5 27B` vs `Gemma 4 31B-IT` vs `MiniMax M2.5` cho synthesize; `GPT-OSS 20B` vs `DeepSeek V4 Flash` (khi enable) cho grade/verify.
3. **Bật `Qwen 3 Reranker 8B`** trong pipeline thay reranker local nếu latency/chất lượng chấp nhận được.
4. **Lọc `useCases=Vietnamese`** qua metadata API — ưu tiên model được platform gắn tag VI cho corpus Zalopay.
5. **Không hard-code tên model** trong code — discover lúc build/deploy (`04-SKILLS`).

---

## Changelog

| Date | Author | Note |
|---|---|---|
| 2026-06-13 | Agent | Tạo file từ console screenshots + GreenNode/VNG public docs. Chưa có live API dump. |
