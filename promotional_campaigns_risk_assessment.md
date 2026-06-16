# BỘ CHƯƠNG TRÌNH KHUYẾN MÃI

## LUCKY WHEEL – NGÂN HÀNG

### Risk Assessment Evaluation Set

| Status | CTKM 1 | CTKM 2 | CTKM 3 |
|--------|--------|--------|--------|
| **Compliance** | Fully Compliant | Partially Non-Compliant | Fully Non-Compliant |
| **Decision** | **PASS** | **PARTIAL FAIL** | **FAIL** |

> Các campaign spec dưới đây được cấu hình theo **Lucky Wheel Operations Guide** (segment → lifecycle → Reward Pool → Slots → Spin Token → Tasks → TnC). Gate đánh giá ở workflow page: 0 vi phạm → PASS; 1–4 vi phạm fixable (không thuộc nhóm nghiêm trọng) → PARTIAL_FAIL; vi phạm nghiêm trọng (payment channel / abuser segment / legal) hoặc đa số rule → FAIL.

---

# CTKM 1 – Fully Compliant

## Chương trình khuyến mãi: Lucky Wheel 'Quay Vong May Man – Tieu Thu Thuong'

### 1.1 Thông tin chương trình

| Thông tin | Chi tiết |
|-----------|----------|
| **Campaign Name** | Lucky Wheel 'Quay Vong May Man – Tieu Thu Thuong' |
| **Objective** | Tăng tần suất giao dịch của KH hiện hữu trên Zalopay; khuyến khích thanh toán qua ví liên kết ngân hàng; nâng cao brand loyalty với KH tier Loyal trở lên. |
| **Target Customer** | KH Zalopay đã KYC, tài khoản hoạt động ≥ 90 ngày, tier Loyal (hạng 2 trở lên), không nằm trong danh sách malicious hoặc casual abuser. |
| **Mechanic** | Mỗi giao dịch thanh toán thành công qua Zalopay wallet tại merchant F&B/retail đối tác (giá trị ≥ 50,000 VND) → nhận 1 lượt quay Lucky Wheel. Tối đa 3 lượt/KYC ID/device ID trong toàn campaign. |
| **Offer / Benefit** | Ô thưởng Lucky Wheel gồm: Voucher F&B 30k (40%), Voucher mua sắm 50k (30%), Voucher xăng dầu 100k (20%), Voucher du lịch 150k (8%), Jackpot: Vé máy bay nội địa (2%) – giới hạn 500 vé trong toàn campaign. |
| **Eligibility** | KYC hợp lệ; tài khoản ≥ 90 ngày; tier Loyal; không trong blacklist malicious/casual; giao dịch thực tế với merchant bên thứ ba; không bao gồm top-up, chuyển tiền, nạp game. |
| **Duration** | 01/07/2026 00:00 – 31/07/2026 23:59 (giờ VN, UTC+7). Chương trình có thể kết thúc sớm khi hết ngân sách. |
| **Budget** | Tổng ngân sách KM: 2,000,000,000 VND (2 tỷ đồng). Phân bổ: Voucher F&B/mua sắm/xăng: 1,200,000,000; Vé máy bay: 800,000,000 (tối đa 500 vé × 1,600,000 VND). |
| **KPI** | - Số lượt quay phát sinh: ≥ 50,000<br>- Số KH tham gia unique: ≥ 15,000<br>- Tỷ lệ sử dụng voucher: ≥ 65%<br>- GMV tăng thêm: ≥ 10% so với baseline tháng trước<br>- Fraud rate: < 0.5% |

#### Cấu hình campaign (Lucky Wheel tool)

| Field | Giá trị |
|-------|---------|
| **Lifecycle status** | SCHEDULED (đang chờ RISK REVIEW trước khi publish) |
| **Segment / priority** | LOYAL_TIER2_PLUS · priority 5 (1 user 1 campaign tại một thời điểm) |
| **start_time / end_time** | 2026-07-01T00:00:00+07:00 → 2026-07-31T23:59:00+07:00 |
| **Reward Pool type** | NON_REPLACEABLE (voucher giới hạn — hết stock là hết, fallback sang slot MISS) |
| **guaranteed_after_N** | Không bật (đã có 2 slot MISS bảo đảm pool không cạn) |
| **Spin token** | currency_type = `lw_spin_token`; Spin 1 cost = 1; Spin 10 cost = 10 |
| **TnC display** | BOTTOM_SHEET (hiển thị khi user bấm "Điều khoản & Điều kiện") |

#### Cấu hình Slots & Reward (wheel 8 slot)

| Slot index | Label | Reward Type | Reward Value | Weight | Stock |
|------------|-------|-------------|--------------|--------|-------|
| 0 | Chúc may mắn | MISS | — | 220 | unlimited |
| 1 | F&B 30k | VOUCHER | VOUCHER_FB_30K | 120 | 20,000 |
| 2 | Mua sắm 50k | VOUCHER | VOUCHER_SHOP_50K | 90 | 12,000 |
| 3 | Chúc may mắn | MISS | — | 220 | unlimited |
| 4 | Xăng dầu 100k | VOUCHER | VOUCHER_FUEL_100K | 60 | 5,000 |
| 5 | F&B 30k | VOUCHER | VOUCHER_FB_30K | 120 | (chung pool slot 1) |
| 6 | Du lịch 150k | VOUCHER | VOUCHER_TRAVEL_150K | 24 | 1,500 |
| 7 | Vé máy bay (Jackpot) | JACKPOT | TICKET_DOMESTIC_FLIGHT | 6 | 500 |

- Jackpot (slot 7) chỉ rơi cho KH tier Loyal; khi hết 500 vé → tự fallback sang slot MISS.
- Luôn có ≥ 1 slot MISS / unlimited (slot 0 & 3) → pool không bao giờ cạn.

#### Task List (nhận thêm lượt quay)

| Task | Token reward | Reset | Action deeplink |
|------|--------------|-------|-----------------|
| Thanh toán hóa đơn qua ví ≥ 50k | 1 | DAILY | zalopay://bill |
| Liên kết thêm ngân hàng | 1 | ONE_TIME | zalopay://link-bank |
| Chia sẻ campaign cho bạn bè | 1 | DAILY | zalopay://share |

### 1.2 Key Terms & Conditions

- Chương trình áp dụng cho KH Zalopay đã KYC, tài khoản hoạt động ≥ 90 ngày, hạng Loyal trở lên.
- **Kênh thanh toán hợp lệ:** chỉ thanh toán qua Zalopay wallet đã liên kết tài khoản ngân hàng. KHÔNG áp dụng VietQR, Apple Pay, card direct, NFC, chuyển tiền, top-up, nạp game.
- **Đối tượng loại trừ:** loại trừ cả malicious abuser và casual abuser theo danh sách rủi ro của Zalopay; chỉ KH tier Loyal (hạng ≥ 2) tham gia.
- Tối đa 3 lượt quay/KYC ID/device ID trong toàn bộ thời gian campaign (giới hạn theo cả KYC ID và device ID, không chỉ user_id).
- Mỗi giao dịch chỉ được tính vào 01 CTKM có giá trị ưu đãi cao nhất. Không áp dụng đồng thời (stacking) với cashback, referral hay CTKM khác.
- **Checkpoint self-payment:** chỉ tính giao dịch thanh toán thực tế tới merchant bên thứ ba; loại trừ giao dịch nội bộ/cùng chủ, top-up, chuyển tiền, nạp game.
- Giao dịch bị refund/cancel trong vòng 7 ngày sẽ bị thu hồi lượt quay và reward tương ứng. GTV tính theo net (đã trừ refund).
- Reward: voucher có hạn sử dụng 30 ngày, không quy đổi tiền mặt, không chuyển nhượng. **KHÔNG bao gồm voucher App Store / Google Play** hoặc voucher dễ cashout.
- **Reward giá trị cao (Jackpot):** Vé máy bay nội địa giới hạn 500 vé, chỉ dành cho KH tier Loyal; khi hết vé ô Jackpot tự chuyển sang voucher du lịch 150k.
- **KYC:** sử dụng KYC platform sẵn có của Zalopay; không thêm checkpoint KYC riêng/trùng lặp.
- **Legal/brand:** tuân thủ Nghị định 81/2021/NĐ-CP về khuyến mãi; KHÔNG quảng cáo "0đ" hay "100% trúng thưởng"; công bố rõ cơ cấu giải, xác suất và số lượng có hạn; tổng giá trị KM không vượt 50% giá trị hàng hóa/dịch vụ.
- **Data & privacy:** chỉ sử dụng dữ liệu KYC và lịch sử giao dịch sẵn có trên platform; KHÔNG yêu cầu nhập thêm CMND/CCCD, địa chỉ, hay số điện thoại người thân; tuân Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
- Hệ thống phát hiện gian lận có quyền tạm hoãn/hủy reward. Quyết định của Zalopay là quyết định cuối cùng.
- Khiếu nại được xử lý trong vòng 3 ngày làm việc kể từ ngày kết thúc campaign.

### 1.3 Risk Assessment Summary

| Tiêu chí | Kết quả |
|----------|---------|
| ✅ Payment channel: VietQR, Apple Pay, card direct bị loại trừ rõ ràng trong T&C. | PASS |
| ✅ Abuser segment: exclude cả malicious và casual abuser; segment giới hạn KH Loyal. | PASS |
| ✅ High-value reward: giới hạn 500 vé máy bay; segment chặt; max value 150k/lần quay thông thường. | PASS |
| ✅ High-liquidity reward: không có voucher App Store/Google Play; reward F&B/merchant thực. | PASS |
| ✅ Self-payment/khống: loại trừ top-up, nạp game, chuyển tiền + checkpoint merchant bên thứ ba. | PASS |
| ✅ Multi-account: cap theo KYC ID và device ID; 3 lượt/toàn campaign. | PASS |
| ✅ Stacking: T&C quy định rõ 1 giao dịch = 1 CTKM ưu đãi cao nhất. | PASS |
| ✅ Refund: GTV net; revoke reward trong 7 ngày nếu hoàn đơn. | PASS |
| ✅ KYC: dùng KYC platform sẵn có, không thêm checkpoint dư thừa. | PASS |
| ✅ Legal/brand: tuân Nghị định 81/2021; không quảng cáo 0đ/100%; công bố số lượng & xác suất. | PASS |
| ✅ Data privacy: chỉ dùng dữ liệu platform; không over-collection; tuân Nghị định 13/2023. | PASS |

**Vi phạm: 0/11 policy rules**

**Overall Decision: ✅ APPROVED – Risk Assessment: PASS**

### 1.4 Risk Mapping Table

| Policy / Rule | Comply / Violate | Evidence |
|---------------|------------------|----------|
| Payment channel – chặn VietQR/Apple Pay/thanh toán trực tiếp | Comply | T&C: chỉ Zalopay wallet liên kết NH; loại trừ VietQR, Apple Pay, card direct, NFC. |
| Abuser segment – exclude malicious & casual abuser | Comply | Loại trừ cả malicious và casual abuser; chỉ tier Loyal ≥ 2. |
| High-value reward – giới hạn số lượng, segment chặt | Comply | Jackpot 500 vé, chỉ tier Loyal; reward thường ≤ 150k. |
| High-liquidity reward – kiểm soát rủi ro cashout | Comply | Không voucher App Store/Google Play; chỉ voucher merchant thực. |
| Giao dịch khống / self-payment – có checkpoint | Comply | Checkpoint merchant bên thứ ba; loại trừ top-up/chuyển tiền/nạp game. |
| Multi-account farming – limit theo KYC/device | Comply | Cap 3 lượt/KYC ID/device ID toàn campaign. |
| Stacking CTKM – quy định rõ ràng | Comply | 1 giao dịch = 1 CTKM ưu đãi cao nhất; không stacking. |
| Refund / hoàn tiền nhưng vẫn giữ reward | Comply | Revoke reward nếu hoàn trong 7 ngày; GTV net. |
| KYC – không yêu cầu thêm checkpoint riêng | Comply | Dùng KYC platform sẵn có. |
| Legal / brand – không vi phạm Nghị định khuyến mãi | Comply | Tuân Nghị định 81/2021; không "0đ/100%"; công bố cơ cấu giải. |
| Data & privacy – không thu thập dữ liệu dư thừa | Comply | Chỉ dùng dữ liệu platform; không thu CMND/SĐT người thân. |

---

# CTKM 2 – Partially Non-Compliant

## Chương trình khuyến mãi: Lucky Wheel 'Quay La Trung – Hoa Don & Telco'

### 2.1 Thông tin chương trình

| Thông tin | Chi tiết |
|-----------|----------|
| **Campaign Name** | Lucky Wheel 'Quay La Trung – Hoa Don & Telco' |
| **Objective** | Tăng tần suất giao dịch hóa đơn và nạp điện thoại; mở rộng KH active sang nhiều tier hơn. |
| **Target Customer** | KH Zalopay đã KYC, tài khoản hoạt động ≥ 60 ngày, tier Regular trở lên. Exclude cả malicious và casual abuser. |
| **Mechanic** | Mỗi giao dịch thanh toán hóa đơn điện/nước/internet hoặc nạp điện thoại thành công ≥ 50,000 VND qua Zalopay wallet → nhận 1 lượt quay. Tối đa 5 lượt/KYC ID. |
| **Offer / Benefit** | Lucky Wheel: Voucher hóa đơn 50k (40%), Voucher Telco 30k (30%), Voucher phim CGV 100k (20%), Voucher mua sắm 200k (8%), Vé máy bay nội địa (2%) – giới hạn 300 vé. |
| **Eligibility** | KYC hợp lệ; tài khoản ≥ 60 ngày; tier Regular+; exclude malicious & casual abuser; giao dịch hóa đơn/nạp ĐT thành công qua Zalopay wallet. |
| **Duration** | 15/07/2026 00:00 – 14/08/2026 23:59 (giờ VN, UTC+7). |
| **Budget** | Tổng ngân sách: 1,500,000,000 VND (1.5 tỷ). Phân bổ: Voucher hóa đơn/Telco/phim/mua sắm: 950,000,000; Vé máy bay: 550,000,000 (300 vé). |
| **KPI** | - Lượt quay: ≥ 40,000<br>- KH unique: ≥ 12,000<br>- Tỷ lệ dùng voucher: ≥ 60%<br>- GMV hóa đơn tăng ≥ 8%<br>- Fraud rate mục tiêu: < 1% |

#### Cấu hình campaign (Lucky Wheel tool)

| Field | Giá trị |
|-------|---------|
| **Lifecycle status** | SCHEDULED (đang chờ RISK REVIEW) |
| **Segment / priority** | REGULAR_PLUS · priority 4 |
| **start_time / end_time** | 2026-07-15T00:00:00+07:00 → 2026-08-14T23:59:00+07:00 |
| **Reward Pool type** | NON_REPLACEABLE |
| **guaranteed_after_N** | Không bật (có slot MISS) |
| **Spin token** | currency_type = `lw_bill_token`; Spin 1 cost = 1; Spin 10 cost = 10 |
| **Anti-abuse cap** | 5 lượt / KYC ID. **[⚠️ chưa cấu hình giới hạn theo device ID]** |
| **TnC display** | POPUP |

#### Cấu hình Slots & Reward (wheel 8 slot)

| Slot index | Label | Reward Type | Reward Value | Weight | Stock |
|------------|-------|-------------|--------------|--------|-------|
| 0 | Chúc may mắn | MISS | — | 200 | unlimited |
| 1 | Hóa đơn 50k | VOUCHER | VOUCHER_BILL_50K | 120 | 15,000 |
| 2 | Telco 30k | VOUCHER | VOUCHER_TELCO_30K | 90 | 12,000 |
| 3 | Chúc may mắn | MISS | — | 200 | unlimited |
| 4 | CGV 100k | VOUCHER | VOUCHER_CGV_100K | 50 | 4,000 |
| 5 | Hóa đơn 50k | VOUCHER | VOUCHER_BILL_50K | 120 | (chung pool slot 1) |
| 6 | Mua sắm 200k | VOUCHER | VOUCHER_SHOP_200K | 18 | 1,000 |
| 7 | Vé máy bay (Jackpot) | JACKPOT | TICKET_DOMESTIC_FLIGHT | 6 | 300 |

#### Task List (nhận thêm lượt quay)

| Task | Token reward | Reset | Action deeplink |
|------|--------------|-------|-----------------|
| Thanh toán hóa đơn điện ≥ 50k | 1 | DAILY | zalopay://bill-electric |
| Nạp điện thoại ≥ 50k | 1 | DAILY | zalopay://topup-telco |

### 2.2 Key Terms & Conditions

- Áp dụng cho KH Zalopay đã KYC, tài khoản hoạt động ≥ 60 ngày, tier Regular trở lên.
- **Kênh thanh toán hợp lệ:** chỉ thanh toán hóa đơn / nạp điện thoại qua Zalopay wallet đã liên kết tài khoản ngân hàng. KHÔNG áp dụng VietQR, Apple Pay, card direct.
- **Đối tượng loại trừ:** loại trừ cả malicious abuser và casual abuser theo danh sách rủi ro Zalopay.
- Tối đa 5 lượt quay/KYC ID trong toàn campaign. Chưa cấu hình giới hạn theo device ID. **[⚠️ Vi phạm multi-account: chưa cap theo device ID]**
- Không có điều khoản về stacking CTKM — chưa quy định 1 giao dịch chỉ hưởng 01 CTKM ưu đãi cao nhất. **[⚠️ Vi phạm stacking policy]**
- Chưa có checkpoint loại trừ giao dịch khống / self-payment cho giao dịch hóa đơn & nạp điện thoại. **[⚠️ Vi phạm self-payment: thiếu checkpoint]**
- Reward bị revoke nếu giao dịch bị hoàn trong 14 ngày. GTV tính theo net (đã trừ refund).
- Reward: KHÔNG bao gồm voucher App Store / Google Play; chỉ voucher merchant có hợp đồng.
- **Reward giá trị cao (Jackpot):** Vé máy bay nội địa giới hạn 300 vé, công bố rõ số lượng và xác suất 2% trên trang campaign; chỉ rơi cho KH tier Regular+.
- **KYC:** dùng KYC platform sẵn có; không thêm checkpoint KYC riêng.
- **Legal/brand:** quảng cáo tuân Nghị định 81/2021; công bố rõ cơ cấu giải & số lượng; KHÔNG dùng câu chữ "0đ" / "100% trúng".
- **Data & privacy:** chỉ dùng dữ liệu platform; không thu thập thêm thông tin cá nhân ngoài dữ liệu KYC sẵn có.

### 2.3 Risk Assessment Summary

| Tiêu chí | Kết quả |
|----------|---------|
| ✅ Payment channel: loại trừ VietQR/Apple Pay/card direct rõ ràng. | PASS |
| ✅ Abuser segment: exclude cả malicious và casual abuser. | PASS |
| ✅ High-value reward: vé máy bay 300 vé, công bố số lượng & xác suất, segment Regular+. | PASS |
| ✅ High-liquidity reward: không có voucher App Store/Google Play. | PASS |
| ⚠️ Self-payment/khống: hóa đơn & nạp ĐT dễ self-payment; thiếu checkpoint lọc. | VIOLATE (fixable) |
| ⚠️ Multi-account: cap theo KYC ID nhưng chưa áp device ID → có thể clone device. | VIOLATE (fixable) |
| ⚠️ Stacking: T&C không có điều khoản ngăn stacking với CTKM khác. | VIOLATE (fixable) |
| ✅ Refund: revoke trong 14 ngày; GTV net. | PASS |
| ✅ KYC: dùng platform KYC; không thêm checkpoint dư thừa. | PASS |
| ✅ Legal/brand: tuân Nghị định 81; công bố cơ cấu giải; không "0đ/100%". | PASS |
| ✅ Data privacy: không over-collection. | PASS |

**Vi phạm: 3/11 policy rules (đều fixable, không thuộc nhóm nghiêm trọng)**

**Overall Decision: ⚠️ PARTIAL FAIL – Cần revision trước khi approve.**

**Yêu cầu sửa:**
1. Thêm giới hạn theo device ID (ngoài KYC ID)
2. Bổ sung điều khoản stacking (1 giao dịch = 1 CTKM ưu đãi cao nhất)
3. Thêm checkpoint loại trừ self-payment cho giao dịch hóa đơn/nạp ĐT

### 2.4 Risk Mapping Table

| Policy / Rule | Comply / Violate | Evidence |
|---------------|------------------|----------|
| Payment channel – chặn VietQR/Apple Pay/thanh toán trực tiếp | Comply | T&C loại trừ rõ VietQR, Apple Pay, card direct. |
| Abuser segment – exclude malicious & casual abuser | Comply | Exclude cả malicious và casual abuser; tier Regular+. |
| High-value reward – giới hạn số lượng, segment chặt | Comply | Vé máy bay 300 vé, công bố số lượng/xác suất, segment Regular+. |
| High-liquidity reward – kiểm soát rủi ro cashout | Comply | Không voucher App Store/Google Play. |
| Giao dịch khống / self-payment – có checkpoint | Violate | Hóa đơn & nạp ĐT dễ self-payment; T&C không có checkpoint loại trừ giao dịch cùng chủ. |
| Multi-account farming – limit theo KYC/device | Violate | Cap 5 lượt/KYC ID nhưng chưa áp device ID → bypass bằng device clone. |
| Stacking CTKM – quy định rõ ràng | Violate | T&C không có điều khoản 1 giao dịch = 1 CTKM ưu đãi cao nhất. |
| Refund / hoàn tiền nhưng vẫn giữ reward | Comply | Revoke reward nếu hoàn trong 14 ngày; GTV net. |
| KYC – không yêu cầu thêm checkpoint riêng | Comply | Dùng KYC platform sẵn có. |
| Legal / brand – không vi phạm Nghị định khuyến mãi | Comply | Tuân Nghị định 81/2021; công bố cơ cấu giải; không "0đ/100%". |
| Data & privacy – không thu thập dữ liệu dư thừa | Comply | Chỉ dùng dữ liệu platform; không yêu cầu nhập thêm thông tin. |

---

# CTKM 3 – Fully Non-Compliant

## Chương trình khuyến mãi: Lucky Wheel 'Sieu Quay – Sieu Trung – Khong Gioi Han'

### 3.1 Thông tin chương trình

| Thông tin | Chi tiết |
|-----------|----------|
| **Campaign Name** | Lucky Wheel 'Sieu Quay – Sieu Trung – Khong Gioi Han' |
| **Objective** | Tăng trưởng GTV tối đa trong tháng cao điểm; thu hút người dùng mới nạp ví và thanh toán nhiều lần; viral qua cơ chế thưởng không giới hạn và giải thưởng giá trị lớn. |
| **Target Customer** | Toàn bộ user Zalopay (kể cả tài khoản mới tạo, chưa KYC đầy đủ). Không exclude malicious hoặc casual abuser. Mở rộng tối đa để tăng participation rate. |
| **Mechanic** | Mỗi lần nạp ví Zalopay thành công (bất kỳ giá trị) → nhận 1 lượt quay. Không giới hạn số lượt/ngày/user (chỉ 1 lượt/user_id/ngày theo user_id). Mở toàn bộ kênh bao gồm VietQR, Apple Pay. |
| **Offer / Benefit** | Lucky Wheel: Voucher F&B 50k (30%), Voucher Google Play 500k (15%), Voucher du lịch 1 triệu (20%), Voucher mua sắm 200k (25%), Jackpot: Gói du lịch 5 triệu (10%) – không giới hạn số lượng Jackpot. |
| **Eligibility** | Tất cả user Zalopay. Không yêu cầu KYC hoàn chỉnh. Bổ sung điều kiện: nhập CMND, địa chỉ, số điện thoại người thân để nhận thêm lượt quay bonus. Không loại trừ bất kỳ abuser nào. |
| **Duration** | 01/08/2026 00:00 – 31/08/2026 23:59 (giờ VN, UTC+7). |
| **Budget** | Tổng ngân sách: 5,000,000,000 VND (5 tỷ). Không có cơ chế daily cap hay budget ceiling per user. |
| **KPI** | - Lượt quay tổng: ≥ 200,000<br>- KH tham gia: ≥ 50,000<br>- GMV nạp ví tăng ≥ 30%<br>- Không đặt KPI fraud rate (coi abuse là chấp nhận được để tăng volume) |

#### Cấu hình campaign (Lucky Wheel tool)

| Field | Giá trị |
|-------|---------|
| **Lifecycle status** | SCHEDULED (đang chờ RISK REVIEW) |
| **Segment / priority** | ALL_USERS (gồm NEW_USER chưa KYC) · priority 9 |
| **start_time / end_time** | 2026-08-01T00:00:00+07:00 → 2026-08-31T23:59:00+07:00 |
| **Reward Pool type** | REPLACEABLE (reward tái sử dụng — không giới hạn) **[🚨 không có pool giới hạn cho reward cao]** |
| **guaranteed_after_N** | guaranteed_after_5 (đảm bảo trúng sau 5 lần quay — không có slot MISS) |
| **Spin token** | currency_type = `lw_topup_token`; Spin 1 cost = 1; Spin 10 cost = 8 (giảm để khuyến khích quay) |
| **Anti-abuse cap** | 1 lượt / user_id / ngày. **[🚨 không cap theo KYC ID hay device ID]** |
| **Bonus task** | Nhập CMND + SĐT người thân → +10 lượt quay **[🚨 over-collection]** |
| **TnC display** | POPUP |

#### Cấu hình Slots & Reward (wheel 8 slot)

| Slot index | Label | Reward Type | Reward Value | Weight | Stock |
|------------|-------|-------------|--------------|--------|-------|
| 0 | F&B 50k | VOUCHER | VOUCHER_FB_50K | 90 | unlimited |
| 1 | Google Play 500k | VOUCHER | VOUCHER_GOOGLE_PLAY_500K | 45 | unlimited |
| 2 | Du lịch 1 triệu | VOUCHER | VOUCHER_TRAVEL_1M | 60 | unlimited |
| 3 | Mua sắm 200k | VOUCHER | VOUCHER_SHOP_200K | 75 | unlimited |
| 4 | Google Play 500k | VOUCHER | VOUCHER_GOOGLE_PLAY_500K | 45 | (chung pool slot 1) |
| 5 | Du lịch 1 triệu | VOUCHER | VOUCHER_TRAVEL_1M | 60 | unlimited |
| 6 | Jackpot 5 triệu | JACKPOT | PACKAGE_TRAVEL_5M | 30 | unlimited |
| 7 | Jackpot 5 triệu | JACKPOT | PACKAGE_TRAVEL_5M | 30 | unlimited |

- Không có slot MISS; mọi slot đều trúng (guaranteed) → "100% trúng thưởng".
- Jackpot 5 triệu stock = unlimited → budget exposure không kiểm soát.

#### Task List (nhận thêm lượt quay)

| Task | Token reward | Reset | Action deeplink |
|------|--------------|-------|-----------------|
| Nạp ví bất kỳ giá trị | 1 | (không reset, không giới hạn) | zalopay://topup |
| Nhập CMND + địa chỉ + SĐT người thân | 10 | ONE_TIME | zalopay://kyc-bonus |
| Mời bạn (referral) — cộng dồn với CTKM khác | 5 | DAILY | zalopay://invite |

### 3.2 Key Terms & Conditions

- Áp dụng cho TẤT CẢ user Zalopay, kể cả tài khoản mới tạo, chưa KYC đầy đủ. **[🚨 Vi phạm: không exclude abuser segment]**
- Kênh áp dụng: tất cả kênh bao gồm VietQR, Apple Pay, card direct, NFC, chuyển tiền. **[🚨 Vi phạm: high-risk payment channels không bị chặn]**
- Giới hạn 1 lượt quay/user_id/ngày – KHÔNG áp KYC ID hoặc device ID. **[🚨 Vi phạm: multi-account farming không bị kiểm soát]**
- Reward bao gồm voucher Google Play 500k. **[🚨 Vi phạm: high-liquidity reward dễ cashout]**
- Nạp ví = 1 lượt quay; nạp từ tài khoản ngân hàng cùng chủ không bị lọc. **[🚨 Vi phạm: self-payment/giao dịch khống không có checkpoint]**
- Không có điều khoản về stacking CTKM. CTKM có thể áp dụng đồng thời với cashback, referral. **[🚨 Vi phạm: stacking không được kiểm soát]**
- Không có cơ chế revoke reward sau hoàn tiền. GTV tính gross (chưa trừ refund). **[🚨 Vi phạm: refund-and-keep reward]**
- Thêm checkpoint KYC ngân hàng riêng với threshold >50,000 VND – trùng với platform KYC, đồng thời không yêu cầu KYC đầy đủ để tham gia. **[🚨 Vi phạm: KYC policy redundant và mâu thuẫn]**
- Quảng cáo: '100% trúng thưởng – Không giới hạn lượt quay – Jackpot 5 triệu không giới hạn số lượng'. **[🚨 Vi phạm: quảng cáo không trung thực, vi phạm Nghị định khuyến mãi]**
- Yêu cầu nhập CMND, địa chỉ, số điện thoại người thân để nhận lượt quay bonus. **[🚨 Vi phạm: data over-collection, privacy risk]**

### 3.3 Risk Assessment Summary

| Tiêu chí | Kết quả |
|----------|---------|
| 🚨 Payment channel: VietQR, Apple Pay, card direct, chuyển tiền đều được phép → abuse tràn lan. | FAIL |
| 🚨 Abuser segment: không exclude malicious hay casual abuser; mở cho tất cả kể cả tài khoản mới. | FAIL |
| 🚨 High-value reward: Jackpot 5 triệu không giới hạn số lượng, mở cho toàn bộ user. | FAIL |
| 🚨 High-liquidity reward: Voucher Google Play 500k dễ cashout/resell. | FAIL |
| 🚨 Self-payment/khống: nạp ví từ TK cùng chủ không bị lọc → giao dịch khống farm lượt quay. | FAIL |
| 🚨 Multi-account: giới hạn chỉ theo user_id → bypass dễ bằng multi-SIM/device farm. | FAIL |
| 🚨 Stacking: không có điều khoản → stack với cashback, referral, loyalty trên cùng giao dịch. | FAIL |
| 🚨 Refund: không revoke reward → giao dịch, lấy reward, sau đó hoàn tiền. | FAIL |
| 🚨 KYC: thêm checkpoint KYC riêng trùng platform + không yêu cầu KYC đầy đủ. | FAIL |
| 🚨 Legal/brand: '100% trúng thưởng', 'không giới hạn Jackpot' – vi phạm Nghị định khuyến mãi. | FAIL |
| 🚨 Data privacy: yêu cầu nhập CMND, địa chỉ, SĐT người thân → over-collection. | FAIL |

**Vi phạm: 11/11 policy rules**

**Overall Decision: ❌ REJECTED – Risk Assessment: FAIL**

**Không thể approve ở cấu trúc hiện tại. Yêu cầu thiết kế lại toàn bộ cơ chế campaign.**

### 3.4 Risk Mapping Table

| Policy / Rule | Comply / Violate | Evidence |
|---------------|------------------|----------|
| Payment channel – chặn VietQR/Apple Pay/thanh toán trực tiếp | Violate | CTKM áp dụng cho tất cả kênh bao gồm VietQR và Apple Pay mà không giới hạn. |
| Abuser segment – exclude malicious & casual abuser | Violate | Mở cho toàn bộ user kể cả tài khoản mới (NPU). Không exclude abuser. |
| High-value reward – giới hạn số lượng, segment chặt | Violate | Jackpot 5,000,000 VND stock unlimited; không thu hẹp segment. |
| High-liquidity reward – kiểm soát rủi ro cashout | Violate | Reward gồm voucher Google Play 500k – high-liquidity dễ cashout/resell. |
| Giao dịch khống / self-payment – có checkpoint | Violate | 1 lần nạp ví = 1 lượt quay; nạp từ TK cùng chủ không có filter self-payment. |
| Multi-account farming – limit theo KYC/device | Violate | Chỉ cap theo user_id (1 lượt/ngày). Không áp KYC ID/device ID. |
| Stacking CTKM – quy định rõ ràng | Violate | Không có điều khoản; cộng dồn với cashback, referral, CTKM song song. |
| Refund / hoàn tiền nhưng vẫn giữ reward | Violate | Không revoke reward sau hoàn tiền; GTV tính gross. |
| KYC – không yêu cầu thêm checkpoint riêng | Violate | Thêm checkpoint KYC ngân hàng riêng trùng platform; lại không yêu cầu KYC đầy đủ. |
| Legal / brand – không vi phạm Nghị định khuyến mãi | Violate | Quảng cáo '100% trúng – không giới hạn'; Jackpot 5 triệu không khai báo giới hạn. |
| Data & privacy – không thu thập dữ liệu dư thừa | Violate | Yêu cầu nhập CMND, địa chỉ, SĐT người thân – over-collection dữ liệu cá nhân. |
