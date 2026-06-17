# Zalopay Internal Knowledge Agent

> **"Knowledge stays. Legacy grows."**
>
> Nền tảng kiến thức sống cho Zalopay — giúp mọi team quyết định nhanh hơn, nhất quán hơn, và kế thừa kinh nghiệm tích lũy qua từng thế hệ.

---

## Bài toán

**Dù bạn ở team nào — bạn sẽ nhận ra mình trong đây.**

Risk, Tech, Operations, Finance, hay bất kỳ phòng ban nào — tất cả đều đang chạy vào cùng một bức tường:

| # | Vấn đề | Biểu hiện |
|---|--------|-----------|
| 1 | **Hỏi ai bây giờ?** | Người nắm kiến thức đã chuyển team, đang bận, hoặc đã nghỉ khỏi Zalopay. Knowledge nằm trong đầu người — không có chỗ lưu. |
| 2 | **Bài học này mình đã gặp rồi...** | Post-mortem, case study, incident report năm ngoái không ai nhớ. Sai lầm cũ lặp lại ở team khác. |
| 3 | **Đúng process chưa? Hỏi ai để confirm?** | Team A biết mình cần risk review. Team B nghĩ mình không cần — nhưng thực ra là cần. Không biết hỏi ai để xác nhận nhanh. |
| 4 | **AI tốt đến đâu cũng cần 1 thứ** | Kiến thức nội bộ: policy, experience, context của Zalopay. Không có nó, AI generic không thể áp dụng đúng judgment của người đã làm việc ở đây nhiều năm. |

---

## Demo: Risk Review Workflow

> *"Đây là 1 trong những workflow đầu tiên chúng tôi xây: Risk Review cho campaign. Cùng kiến trúc này có thể áp dụng cho **bất kỳ quy trình nào cần kiến thức nền để suy luận**."*

**Flow:**

```
TICKET TẠO (NEW)  →  RISK REVIEW (TRIGGERED)  →  AGENT ĐANG LÀM
                                                        │
                                         ┌──────────────┴──────────────┐
                                         │  1. Đọc ticket Jira          │
                                         │  2. Lấy Risk Playbook từ     │
                                         │     Confluence               │
                                         │  3. Đối chiếu policy         │
                                         │  4. Soạn Quick Risk Report   │
                                         └─────────────────────────────┘
                                                        │
                          ┌─────────────────────────────┴─────────────────────────────┐
                          │                                                             │
                   ✅ LOW RISK                                                   ❌ HIGH RISK
            Notify Risk PIC để approve                               Trả ticket ngay, ghi rõ lý do
                          │                                                             │
                   📧 Gửi notify Risk PIC                                  📧 Notify người tạo ticket
                      để review & approve                                     + đề xuất hướng sửa
                          └──────────────────────── ⏱ ~10–15 phút ─────────────────────┘
```

**Cùng kiến trúc có thể áp dụng cho:** Compliance review · Partner due diligence · Onboarding checklist · Incident triage · Policy Q&A · và nhiều hơn nữa.

---

## Tại sao bây giờ?

**AI không thiếu — knowledge nội bộ mới là lợi thế.**

**01 — Claude, ChatGPT, Gemini đều rất giỏi — nhưng không biết Zalopay là ai**
Các AI này không biết Risk Playbook của Zalopay, không biết incident lớn năm ngoái, không biết team nào cần review gì. Knowledge nội bộ là lợi thế cạnh tranh — ai build trước, người đó thắng.

**02 — Zalopay đã có tài sản — chỉ cần unlock**
Năm tích lũy SOP, post-mortem, playbook, case study. Đây là knowledge mà không AI generic nào có. Wiki Agent là lớp biến tài sản đó thành hành động.

**03 — Công ty nào build knowledge base ngay hôm nay — 1 năm sau có lợi thế AI-native**
Không phải chờ AI tốt hơn. Mà là chờ đủ kiến thức để AI có thể làm việc thay. Bắt đầu ngay hôm nay, 1 năm sau Zalopay sẽ luôn sẵn sàng cho bất kỳ AI-native workflow nào.

---

## Platform — Một nền tảng, cho mọi team

Ba khái niệm cốt lõi. Không cần là developer để hiểu — và cũng không cần là developer để xây thêm workflow mới.

### 🗄️ Lưu kiến thức — theo từng phòng ban
Tự động đọc và cập nhật tài liệu từ Confluence. Knowledge được tổ chức theo từng department, phân quyền riêng. Mỗi team có agent riêng — các agent có thể giao tiếp với nhau để đưa ra quyết định đa chiều, tham chiếu chéo, hoặc tạo checklist review trước khi kết luận.

### 🧠 Hiểu & suy luận từ kiến thức nội bộ
Khi cần quyết định, tìm đúng tài liệu liên quan, đọc hiểu context, áp dụng đúng policy — không tự nghĩ ra ngoài những gì đã được ghi lại. Đây là điểm khác biệt: AI không đoán, AI áp dụng đúng những gì Zalopay đã tích lũy.

### ⚡ Tự động hóa quy trình có suy luận
Chat để hỏi thông tin. Hoặc chạy workflow: thực hiện các bước lặp lại cần kiến thức — không chỉ automation đơn thuần, mà automation có reasoning. Agent tự suy nghĩ và hành động cho tới khi hoàn thành công việc.

---

## Living Wiki — Nơi kiến thức không bao giờ mất

Kế thừa kho kinh nghiệm từ các thế hệ Zalopay trước — thay vì mỗi người mới lại reset về zero.

```
Năm đầu          Năm tiếp theo        Hôm nay & tương lai
    ▓                 ▓▓▓▓               ▓▓▓▓▓▓▓▓  ✦
    │                  │                     │
Foundation docs    Post-mortems,       Agent reasoning
policy, SOPs       case studies,       trên toàn bộ
                   playbooks           nền kiến thức
```

> *Càng nhiều team đóng góp kiến thức → agent càng hiểu sâu hơn về Zalopay*

---

## Impact

**Tiết kiệm thời gian cho cả hai phía.**

Không phải thay thế con người — mà để con người tập trung vào những quyết định thật sự cần judgment.

| Chỉ số | Kết quả |
|--------|---------|
| ⏱ Thời gian nhận phản hồi từ AI review | **~15 phút** (thay vì chờ nhiều ngày) |
| 🤖 Ticket LOW risk — reviewer chỉ cần approve | **~50%** ticket |

> *"Tiết kiệm thời gian cho cả người tạo ticket lẫn người đi review. Risk team tập trung vào những quyết định thật sự cần con người."*

---

## Governance — AI hỗ trợ, con người quyết định

Đây không phải AI tự động hoàn toàn. Đây là AI làm việc cùng con người — có trách nhiệm, có kiểm soát, có thể audit.

### ✅ Human-in-the-loop luôn luôn
Với mọi workflow, AI làm vòng đầu. Quyết định cuối luôn do con người. LOW risk → reviewer nhận notify và approve. HIGH risk → trả lại ngay để sửa. AI không bao giờ là người ký duyệt cuối.

### 🔍 Audit trail đầy đủ
Mọi reasoning của AI đều được log: dùng tài liệu nào, confidence bao nhiêu, kết quả là gì. Compliance và management có thể audit bất kỳ quyết định nào, bất kỳ lúc nào.

### 🚨 Khi không chắc → escalate, không block
AI confidence thấp thì tự escalate lên human. Workflow không bao giờ bị stuck vì AI không chắc chắn. Không có gì bị mất hay bị bỏ qua.

---

## Architecture — MVP → Production

Cùng kiến trúc — chỉ khác về quy mô và hạ tầng. Ba bước cốt lõi không thay đổi:

```
Tài liệu  →  Kiến thức được lưu  →  Hành động
(Confluence    (Vector index +        (Chat · Workflow
 / GDrive)      memory)               · Notify)
```

| Thành phần | MVP (Demo) | Production |
|------------|-----------|------------|
| Tài liệu nguồn | Confluence cá nhân + Google Drive | Confluence công ty (toàn Zalopay) |
| Jira | Jira cá nhân | Jira công ty |
| Thông báo | Gmail | Teams / Jira & Confluence native notification |
| Hạ tầng | GreenNode AgentBase | Self-hosted tại Zalopay — data không ra ngoài |
| AI Model | VNG MaaS — Qwen | Theo từng workflow: model nhẹ cho screening, model mạnh cho reasoning |
| Tích hợp | Direct API call | MCP (Model Context Protocol) — thêm tool mới không cần sửa agent |
| Security | Auth cơ bản | SSO (Zalopay IAM) · RBAC · Audit log |
| Sync knowledge | Manual | Auto-sync khi Confluence thay đổi |

**Production — thêm:**
- Human-in-the-loop: escalate tự động khi AI confidence thấp
- Audit trail: mọi reasoning AI đều được log đầy đủ
- Workflow versioning: policy thay đổi → workflow tự cập nhật
- Data residency: tất cả dữ liệu trong hạ tầng Zalopay

---

## Next Steps — Từ demo đến Zalopay-wide

Ba bước để biến hackathon demo thành hệ thống thật sự phục vụ toàn công ty.

**01 — Validate với team thật**
Chạy thử với volume ticket thật, đo độ chính xác của AI review so với human review. Calibrate và cải thiện trước khi mở rộng.

**02 — Kết nối systems công ty**
Đổi từ tài khoản cá nhân sang Confluence + Jira công ty. Deploy trên hạ tầng Zalopay — data không ra ngoài, security compliant.

**03 — Mọi team bắt đầu build knowledge base ngay hôm nay**
Không cần chờ AI hoàn hảo. Bắt đầu lưu kiến thức, bắt đầu xây workflow. 1 năm sau Zalopay sẽ luôn sẵn sàng cho bất kỳ AI-native workflow nào. Thêm workflow mới = thêm 1 Confluence page.

---

## Closing

> *"Knowledge stays. Legacy grows."*
>
> Khi knowledge càng nhiều, khi workflow hỗ trợ được nhiều team hơn — agent càng hiểu sâu hơn. Không chỉ Zalopay hôm nay, mà cả Zalopay của nhiều năm tới.

**Risk review chỉ là workflow đầu tiên.**

---

*Built with Tôm and Jerry ❤ at Clawathon — Zalopay Internal Knowledge Agent*
