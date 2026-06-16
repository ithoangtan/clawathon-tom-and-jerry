#!/usr/bin/env python3
"""Update Confluence pages for DGS_260520_585 with proper XHTML styling.

Updates:
1. Main campaign config page (ClawathonRisk, ID 2686994) — full rewrite from MD
2. ClawathonGrow pages — targeted updates with DGS_260520_585 campaign data
3. ClawathonRisk pages — updated Risk SOP / Principles with campaign context

Run:
    cd code/zalopay-knowledge
    python -m scripts.update_dgs585_full
"""
from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.adapters.confluence_writer import ConfluenceWriter
from app.config import get_settings
from app.ingestion.confluence import ConfluenceClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

RISK_SPACE = "ClawathonRisk"
GROW_SPACE = "ClawathonGrow"
MAIN_PAGE_ID = "2686994"


# ── XHTML helpers ─────────────────────────────────────────────────────────────

def h(level: int, text: str) -> str:
    return f"<h{level}>{text}</h{level}>"


def p(text: str) -> str:
    return f"<p>{text}</p>"


def s(text: str) -> str:
    return f"<strong>{text}</strong>"


def hr() -> str:
    return "<hr/>"


def ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li><p>{item}</p></li>" for item in items) + "</ul>"


def table(headers: list[str], rows: list[list[str]]) -> str:
    th_row = "".join(f"<th><p>{s(hdr)}</p></th>" for hdr in headers)
    body = "".join(
        "<tr>" + "".join(f"<td><p>{cell}</p></td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><tbody><tr>{th_row}</tr>{body}</tbody></table>"


def macro(name: str, content: str) -> str:
    return (
        f'<ac:structured-macro ac:name="{name}" ac:schema-version="1">'
        f"<ac:rich-text-body>{content}</ac:rich-text-body>"
        f"</ac:structured-macro>"
    )


def info(content: str) -> str:
    return macro("info", content)


def warning(content: str) -> str:
    return macro("warning", content)


def note(content: str) -> str:
    return macro("note", content)


def tip(content: str) -> str:
    return macro("tip", content)


# ── Main campaign config page ──────────────────────────────────────────────────

def build_main_page() -> str:
    parts: list[str] = []

    parts.append(info(
        p(f"{s('MKT Code:')} DGS_260520_585 &nbsp;|&nbsp; "
          f"{s('Ads_id (Thể lệ):')} 6828 &nbsp;|&nbsp; "
          f"{s('Live time:')} 10:00 05/06 – 23:59 26/07/2026")
    ))

    # 1. THÔNG TIN CHUNG
    parts.append(h(2, "1. THÔNG TIN CHUNG"))
    parts.append(table(
        ["Trường", "Nội dung"],
        [
            ["MKT_Name", "[20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]"],
            ["MKT_Code", "DGS_260520_585"],
            ["Tên chương trình", "Săn vé du lịch hè 0đ cùng Zalopay"],
            ["Thể lệ chương trình (Ads_id)", "6828"],
            [s("Ngân sách tổng"), s("619.300.000 đ")],
            ["Testing time", "05/06"],
            [s("Live time"), "10:00 05/06 – 23:59 26/07"],
        ]
    ))

    # 2. CẤU HÌNH CƠ BẢN
    parts.append(hr())
    parts.append(h(2, "2. YÊU CẦU CẤU HÌNH CƠ BẢN"))

    parts.append(h(3, "2.1 Cảnh báo ngân sách &amp; Email"))
    parts.append(table(
        ["Trường", "Nội dung"],
        [
            ["Mức cảnh báo (% ngân sách đã dùng)", "50% – 75% – 95%"],
            ["Email nhận Alert", "phutt2, thuyvtt4, thutla, lylt"],
        ]
    ))

    parts.append(h(3, "2.2 Danh sách UserID Testing"))
    parts.append(table(
        ["Tên", "UserID"],
        [
            ["HoaVMQ", "181211000004278"],
            ["TaiCT", "200124000486951"],
            ["ThuTLA", "181002000000026"],
            ["LyLT", "180219000003633"],
            ["TrangPY", "200807000019734"],
            ["Thuyvtt4", "190411000016472"],
            ["TrucBTT", "190514000003974"],
            ["Phutt2", "201114000014743"],
        ]
    ))

    # 3. CẤU HÌNH NÂNG CAO
    parts.append(hr())
    parts.append(h(2, "3. YÊU CẦU CẤU HÌNH NÂNG CAO"))

    parts.append(h(3, "3.1 Điều kiện tham gia"))
    parts.append(table(
        ["Điều kiện", "Lựa chọn"],
        [
            ["User cần visit landing để tham gia?", "✅ Có"],
            ["User cần bấm thực hiện task trước?", "❌ Không"],
            ["Tạo link và bật button chia sẻ landing page", "❌ Không"],
            ["Welcome turn cho user", "✅ Tự động cho 2 lượt chơi lần đầu tiên visit Gami"],
        ]
    ))

    parts.append(h(3, "3.2 User Profile / Segment"))
    parts.append(table(["Segment", "Segment ID"], [["Mass", "13155"]]))

    parts.append(h(3, "3.3 Điều kiện nhận quà"))
    parts.append(table(["Điều kiện", "Lựa chọn"], [["User cần bấm claim quà?", "❌ Không"]]))

    # 4. GAME UI
    parts.append(hr())
    parts.append(h(2, "4. GAME UI"))

    parts.append(h(3, "4.1 Thông tin thiết kế"))
    parts.append(table(
        ["Trường", "Nội dung"],
        [
            ["Game Type", "Lucky Wheel"],
            ["UI Design Type", "MKT gửi KV banner &amp; request UI design adaption"],
            ["Link KV / Asset", '<a href="https://vngms-my.sharepoint.com/:f:/g/personal/phutt2_vng_com_vn/IgDwh98FwMXtQLY8zBSfu8bwAbJDLZ89NryRxtr0T1brxx8?e=Q8ztXy">SharePoint Link</a>'],
            ["Gami Title", "Săn vé du lịch hè 0đ cùng Zalopay"],
        ]
    ))

    parts.append(h(3, "4.2 Icon trên vòng quay (8 ô)"))
    parts.append(table(
        ["STT", "Icon", "Ghi chú"],
        [
            ["1", "Nha Trang 0Đ", "Lấy từ KV"],
            ["2", "Dấu hỏi chấm", "Lấy từ folder"],
            ["3", "Đà Nẵng 0Đ", "Lấy từ KV"],
            ["4", "VinWonders", "—"],
            ["5", "Đà Lạt 0Đ", "Lấy từ KV"],
            ["6", "Vietjet Air", "—"],
            ["7", "Hải Phòng 0Đ", "Lấy từ KV"],
            ["8", "FUTA", "—"],
        ]
    ))

    parts.append(h(3, "4.3 Ads Banner bổ sung"))
    parts.append(table(
        ["Banner", "Ads ID", "Vị trí hiển thị"],
        [
            ["Banner 1", "6845", "Dưới game chính"],
            ["Banner 2", "6846", "Dưới task list"],
        ]
    ))

    # 5. ĐIỀU KIỆN PHÁT QUÀ
    parts.append(hr())
    parts.append(h(2, "5. ĐIỀU KIỆN PHÁT QUÀ"))

    parts.append(h(3, "5.1 Trigger Type &amp; Risk Rules"))
    parts.append(warning(
        h(4, "⚠️ Bắt buộc cấu hình RISK CONFIRM") +
        ul([
            "Chặn VietQR / Apple Pay / Thanh toán trực tiếp không cần liên kết",
            "Loại malicious/casual abuser theo list update của Risk",
        ])
    ))
    parts.append(table(
        ["Loại", "Nội dung"],
        [
            ["Trigger", "AUTO-TRIGGER"],
            ["Risk Confirm #1", "Chặn VietQR / Apple Pay / Thanh toán trực tiếp không cần liên kết"],
            ["Risk Confirm #2", "Loại malicious/casual abuser theo list update của Risk"],
        ]
    ))

    parts.append(h(3, "5.2 Segment &amp; Điều kiện"))
    parts.append(table(
        ["Segment", "Segment ID", "Điều kiện"],
        [["Loại Starter", "13155",
          "Tự động 2 lượt chơi lần đầu visit Gami; Hoàn thành task để nhận thêm lượt; Phải visit landing page trước"]]
    ))

    # 6. TASK LIST
    parts.append(hr())
    parts.append(h(2, "6. TASK LIST"))
    parts.append(table(
        ["#", "Segment", "Title", "Description", "Trigger Type", "Trigger Condition", "Reward", "Frequency", "CTA", "Logo", "Ghi chú"],
        [
            ["1", "Mass", "Đặt vé máy bay, tàu xe hè dùng giảm giá từ xu", "Bật Giảm giá từ Xu tại Thanh toán", "Payment",
             "69,606,612,677,678,681,2643,3568,3569,620,2843,2625,738,2942,3023,3024,3181,3751,4096,4341,759,1589,257",
             "4 lượt", "1 lần/tuần", "Đặt vé", "Xu", "Thanh toán thành công &amp; phải bật toggle giảm giá từ xu"],
            ["2", "13181", "Đặt vé máy bay, tàu xe hè dùng Tài khoản trả sau", "Dùng Tài khoản trả sau tại Thanh toán", "Payment",
             "69,606,612,677,678,681,2643,3568,3569,620,2843,2625,738,2942,3023,3024,3181,3751,4096,4341,759,1589,257",
             "4 lượt", "1 lần/tuần", "Đặt vé", "BNPL", "Thanh toán thành công &amp; phải dùng SOF BNPL"],
            ["3", "Mass", "Khám phá vé máy bay hè bao rẻ", "Tìm kiếm chuyến bất kỳ", "FE Event ID",
             "01.4700.006 / 02.4700.006", "1 lượt", "1 lần/tuần", "Tìm ngay", "Vietnam Airlines", "—"],
            ["4", "Mass", "Khám phá vé xe khách hè bao rẻ", "Tìm kiếm chuyến bất kỳ", "FE Event ID",
             "01.4731.005 / 02.4731.005", "1 lượt", "1 lần/tuần", "Tìm ngay", "Vé xe khách", "—"],
            ["5", "Mass", "Khám phá vé tàu hè bao rẻ", "Tìm kiếm chuyến bất kỳ", "FE Event ID",
             "01.4770.008 / 02.4770.008", "1 lượt", "1 lần/tuần", "Tìm ngay", "Vé tàu", "—"],
            ["6", "Mass", "Đặt vé máy bay hè", "Chuyến bất kỳ", "Payment",
             "69,606,612,3568,677,678,681,2643,3569,4096,4341", "2 lượt", "1 lần/tuần", "Đặt vé", "Vé máy bay", "—"],
            ["7", "Mass", "Đặt vé tàu, xe khách hè", "Chuyến bất kỳ", "Payment",
             "620,759,2843,1589,622,257,2625", "2 lượt", "1 lần/tuần", "Đặt vé", "Vé xe khách", "—"],
            ["8", "Mass", "Đặt vé VinWonders, SunWorld hè", "Khu VinWonders, Sunworld bất kỳ", "Payment",
             "3023, 3024, 3181", "2 lượt", "1 lần/tuần", "Đặt vé", "Vé vui chơi", "—"],
            ["9", "Mass → 11/6: 12844", "Đặt vé website/app FUTA thanh toán Zalopay", "Chuyến bất kỳ", "Payment",
             "984, 360", "2 lượt", "1 lần/tuần → 11/6: 1 lần/CT", "Đặt vé", "FUTA", "FPU appID - bật cờ save result"],
            ["10", "Mass → 11/6: 12845", "Đặt vé website/app VEXERE thanh toán Zalopay", "Chuyến bất kỳ", "Payment",
             "320,1130,225", "2 lượt", "1 lần/tuần → 11/6: 1 lần/CT", "Đặt vé", "VEXERE", "FPU appID - bật cờ save result"],
            ["11", "Mass → 11/6: 13811", "Đặt vé website Vietjet Air thanh toán Zalopay", "Chuyến bất kỳ", "Payment",
             "2942", "2 lượt", "1 lần/tuần → 11/6: 1 lần/CT", "Đặt vé", "Vietjet Air", "FPU appID - bật cờ save result"],
            ["12", "Mass", "Chơi game xuyên hè", "Chơi game H5 bất kì trên miniapp Trò chơi", "FE Event ID",
             "ACCESS_H5_GAME_KIEMVU, ACCESS_H5_GAME_NGOA_LONG, ... (37 event IDs, chỉ cần 1)",
             "1 lượt", "1 lần/tháng", "Chơi ngay", "Game", "—"],
            ["13", "Mass", "Kiểm tra hóa đơn trước khi du lịch hè", "Điện, Nước, Internet, Khoản vay", "FE Event ID",
             "01.4101.302, 02.4101.302, 01.4101.303, 02.4101.303 (chỉ cần 1)",
             "1 lượt", "1 lần/tháng", "Kiểm tra", "Bill", "—"],
            ["14", "Mass", "Thanh toán đơn TikTok Shop", "Đơn bất kỳ", "Payment",
             "1413, 4833", "1 lượt", "1 lần/tháng", "Mua ngay", "TikTok Shop", "—"],
            ["15", "Mass", "Nạp điện thoại", "Đơn bất kỳ", "CPS",
             "61,12,4609,4610,4666,4667,4668,4712,4715", "1 lượt", "1 lần/tháng", "Nạp ngay", "Điện thoại", "—"],
            ["16", "Mass", "Thanh toán di chuyển hè cùng GreenSM", "Nhập mã ZLPDULICH khi thanh toán", "Payment",
             "3095", "2 lượt", "1 lần/tuần", "Đặt ngay", "GreenSM", "—"],
            ["17", "Mass", "Đặt vé phim hot mỗi tháng trên Zalopay", "Xem phim hot bất kỳ", "Payment",
             "19", "2 lượt", "1 lần/tuần", "Đặt ngay", "Vé phim", "—"],
            ["18", "Mass", "Ghé thăm và theo dõi Fanpage Zalopay", "N/A", "—",
             "Mở link: https://www.facebook.com/Zalopay", "1 lượt", "1 lần duy nhất", "Làm ngay!", "Zalopay", "—"],
        ]
    ))

    # 7. TỈ LỆ CHIA THƯỞNG
    parts.append(hr())
    parts.append(h(2, "7. TỈ LỆ CHIA THƯỞNG"))
    parts.append(h(3, "7A. QUÀ THEO TUẦN (Pool Mass - Non Starter)"))
    parts.append(note(p("Thả lúc " + s("10:00 thứ Hai") + " mỗi tuần")))

    weekly_headers = ["Item", "Số lượng", "Tỷ trọng", "Counter"]
    counter = "1 lần/user/quà"

    weeks = [
        ("Tuần 1: 10:00 08/06 – 23:59 14/06", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "8", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
        ]),
        ("Tuần 2: 10:00 15/06 – 23:59 21/06", [
            ["Vé cứng CGV miễn phí", "3", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["Vé máy bay Đà Nẵng 0Đ (max 2.500K)", "1", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé tàu hỏa HN – Hải Phòng 0Đ (max 400K)", "1", "0,1%", counter],
            ["Vé tàu hỏa Huế – Đà Nẵng 0Đ (max 500K)", "1", "0,1%", counter],
        ]),
        ("Tuần 3: 10:00 22/06 – 23:59 28/06", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["Vé máy bay Nha Trang 0Đ (max 2.500K)", "1", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé tàu hỏa HN – Hải Phòng 0Đ (max 400K)", "1", "0,1%", counter],
            ["Vé tàu hỏa Huế – Đà Nẵng 0Đ (max 500K)", "1", "0,1%", counter],
        ]),
        ("Tuần 4: 10:00 29/06 – 23:59 05/07", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
        ]),
        ("Tuần 5: 10:00 06/07 – 23:59 12/07", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["Vé máy bay Đà Lạt 0Đ (max 2.500K)", "1", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "8", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "8", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "8", "0,1%", counter],
            ["Vé tàu hỏa HN – Hải Phòng 0Đ (max 400K)", "3", "0,1%", counter],
            ["Vé tàu hỏa Huế – Đà Nẵng 0Đ (max 500K)", "3", "0,1%", counter],
        ]),
        ("Tuần 6: 10:00 13/07 – 23:59 19/07", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "3", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["Vé máy bay Hải Phòng 0Đ (max 2.500K)", "1", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
        ]),
        ("Tuần 7: 10:00 20/07 – 23:59 26/07", [
            ["Vé cứng CGV miễn phí", "2", "0,1%", counter],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "2", "0,1%", counter],
            ["Nạp game nửa giá – Giảm đến 100K", "7", "0,1%", counter],
            ["1 đêm nghỉ dưỡng resort 0Đ (max 3.000K)", "1", "0,1%", counter],
            ["Vé xe khách HCM – Nha Trang 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HN – Hải Phòng 0Đ (max 300K)", "7", "0,1%", counter],
            ["Vé xe khách HCM – Đà Lạt 0Đ (max 300K)", "7", "0,1%", counter],
        ]),
    ]
    for week_title, rows in weeks:
        parts.append(h(4, week_title))
        parts.append(table(weekly_headers, rows))

    parts.append(hr())
    parts.append(h(3, "7B. QUÀ XUYÊN SUỐT CHƯƠNG TRÌNH"))
    parts.append(table(
        ["Item", "Số lượng", "Tỷ trọng", "Counter"],
        [
            ["Trả Khoản Vay – Giảm 1% tối đa 10K đơn từ 1 triệu", "1.000", "1%", "unlimited"],
            ["Phúc Long – Giảm 10K đơn 59K (TK Trả Sau)", "500", "1%", "unlimited"],
            ["KFC MiniApp – Giảm 30K đơn từ 160K", "100", "1%", "unlimited"],
            ["Ăn uống – Giảm 20% tối đa 25K", "200", "2%", "unlimited"],
            ["TikTok Shop – Giảm thêm 2% tối đa 50K đơn từ 300K", "400", "2%", "unlimited"],
            ["Nạp Điện thoại – Giảm 5% tối đa 5K", "2.000", "5%", "unlimited"],
            ["Mỹ phẩm – Giảm 35K đơn 600K", "143", "2%", "unlimited"],
            ["Thời trang – Giảm 80K đơn từ 1 triệu", "63", "1%", "unlimited"],
            ["Circle K – Giảm 5K đơn từ 30K", "600", "2%", "unlimited"],
            ["AEON – Giảm 25K đơn từ 990K", "200", "1%", "unlimited"],
            ["MM Mega Market – Giảm 25K đơn từ 990K", "200", "1%", "unlimited"],
            ["Bách Hóa XANH – Giảm 20K đơn từ 599K", "250", "1%", "unlimited"],
            ["GO! – Giảm 70K đơn từ 2.5 triệu (TK Trả Sau)", "71", "1%", "unlimited"],
            ["Hasaki – Giảm 30K đơn từ 300K (TK Trả Sau)", "167", "1%", "unlimited"],
            ["Siêu thị mini – Giảm 10K đơn 200K (TK Trả Sau)", "500", "2%", "unlimited"],
            ["AEON – Giảm 30K đơn từ 500K (TK Trả Sau)", "167", "1%", "unlimited"],
            ["Thời trang – Giảm 30K đơn từ 300K (TK Trả Sau)", "167", "1%", "unlimited"],
            ["Mỹ phẩm – Giảm 30K đơn từ 300K (TK Trả Sau)", "167", "1%", "unlimited"],
            ["Circle K – Giảm 5K đơn từ 10K (TK Trả Sau)", "600", "1%", "unlimited"],
            ["Nhà thuốc Long Châu – Giảm 30K đơn từ 150K (TK Trả Sau)", "167", "1%", "unlimited"],
            ["Vé xe khách – Giảm 5.000đ đơn từ 100K", "300.000", "20%", "unlimited"],
            ["Vietjet Air – Giảm 20.000đ đơn từ 100K", "10.000", "5%", "unlimited"],
            ["Vietnam Airlines – Giảm 35.000đ đơn từ 100K", "30.000", "5%", "unlimited"],
            ["Vietravel Airlines – Giảm 20.000đ đơn từ 100K", "10.000", "3%", "unlimited"],
            ["Sun PhuQuoc Airways – Giảm 35.000đ đơn từ 100K", "30.000", "5%", "unlimited"],
            ["Vinpearl – Giảm 4% tối đa 50.000đ mọi đơn khách sạn", "100.000", "5%", "unlimited"],
            ["VinWonders – Giảm 2% tối đa 100.000đ đơn từ 500K", "100.000", "5%", "unlimited"],
            ["SunWorld – Giảm 2% tối đa 100.000đ đơn từ 500K", "100.000", "2%", "unlimited"],
            ["Tàu hỏa hè – Giảm 10.000đ đơn từ 100K", "5.000", "4%", "unlimited"],
            ["Website/App FUTA – Giảm 2% tối đa 50.000đ", "20.000", "2%", "unlimited"],
            ["Website/App VEXERE – Giảm 2% tối đa 50.000đ", "20.000", "2%", "unlimited"],
            ["Mytour – Giảm 1% tối đa 100.000đ", "2.000", "1%", "unlimited"],
            ["Website Vietjet – Giảm 5.000đ đơn từ 100K", "50.000", "2%", "unlimited"],
            ["10 xu", "100.000", "5%", "unlimited"],
            ["100 xu", "100.000", "5%", "unlimited"],
        ]
    ))

    # 8. CONFIG VOUCHER CHI TIẾT
    parts.append(hr())
    parts.append(h(2, "8. CONFIG VOUCHER CHI TIẾT"))
    parts.append(note(p(f"{s('Group Name Voucher:')} Vòng quay vé du lịch hè 0đ")))

    parts.append(h(3, "8.1 Quà theo tuần – Voucher vỏ &amp; Voucher giá trị cao"))
    parts.append(table(
        ["Tên quà", "MKT Code", "SL", "Ngân sách (đ)", "% Giảm", "Giá trị (đ)", "Min order (đ)", "Max (đ)", "HSD", "Logo", "AppID áp dụng"],
        [
            ["Vé cứng CGV miễn phí (voucher vỏ)", "DGS_260520_585", "15", "—", "—", "—", "—", "—", "30 ngày", "CGV", "—"],
            ["VTVGo – 1 tháng miễn phí xem World Cup", "DGS_260520_585", "20", "800.000", "100%", "40.000", "1.000", "40.000", "30 ngày", "VTVGo", "4738 (auto apply)"],
            ["Nạp game nửa giá – Giảm đến 100K", "DGS_260520_585", "50", "5.000.000", "50%", "100.000", "1.000", "—", "7 ngày", "Game", "149,15,3677,3762,4251,4708,3011,..."],
            ["Vé máy bay Đà Lạt 0Đ", "DGS_260520_585", "1", "2.500.000", "100%", "2.500.000", "1.000", "2.500.000", "30 ngày", "Vé máy bay", "69,606,612,3568,677,678,681,2643,3569,4096,4341"],
            ["Vé máy bay Nha Trang 0Đ", "DGS_260520_585", "1", "2.500.000", "100%", "2.500.000", "1.000", "2.500.000", "30 ngày", "Vé máy bay", "69,606,612,3568,677,678,681,2643,3569,4096,4341"],
            ["Vé máy bay Đà Nẵng 0Đ", "DGS_260520_585", "1", "2.500.000", "100%", "2.500.000", "1.000", "2.500.000", "30 ngày", "Vé máy bay", "69,606,612,3568,677,678,681,2643,3569,4096,4341"],
            ["Vé máy bay Hải Phòng 0Đ", "DGS_260520_585", "1", "2.500.000", "100%", "2.500.000", "1.000", "2.500.000", "30 ngày", "Vé máy bay", "69,606,612,3568,677,678,681,2643,3569,4096,4341"],
            ["1 đêm nghỉ dưỡng resort 0Đ", "DGS_260520_585", "1", "3.000.000", "100%", "3.000.000", "1.000", "3.000.000", "30 ngày", "Khách sạn", "3751,738,595,621"],
            ["Vé xe khách HCM – Nha Trang 0Đ", "DGS_260520_585", "50", "15.000.000", "100%", "300.000", "1.000", "300.000", "30 ngày", "Xe khách", "620,759,2843,1589,622,257"],
            ["Vé xe khách HN – Hải Phòng 0Đ", "DGS_260520_585", "50", "15.000.000", "100%", "300.000", "1.000", "300.000", "30 ngày", "Xe khách", "620,759,2843,1589,622,257"],
            ["Vé xe khách HCM – Đà Lạt 0Đ", "DGS_260520_585", "50", "15.000.000", "100%", "300.000", "1.000", "300.000", "30 ngày", "Xe khách", "620,759,2843,1589,622,257"],
            ["Vé tàu hỏa HN – Hải Phòng 0Đ", "DGS_260520_585", "5", "2.000.000", "100%", "400.000", "1.000", "400.000", "30 ngày", "Tàu hỏa", "2625"],
            ["Vé tàu hỏa Huế – Đà Nẵng 0Đ", "DGS_260520_585", "5", "2.500.000", "100%", "500.000", "1.000", "500.000", "30 ngày", "Tàu hỏa", "2625"],
        ]
    ))

    parts.append(h(3, "8.2 Quà xuyên suốt – OTA &amp; Travel"))
    parts.append(table(
        ["Tên quà", "MKT Code", "SL", "Ngân sách (đ)", "Giá trị (đ)", "Min order (đ)", "HSD", "Logo", "AppID áp dụng"],
        [
            ["Vé xe khách – Giảm 5.000đ", "DGS_260520_585", "300.000", "75.000.000", "5.000", "100.000", "30 ngày", "Xe khách", "620,759,2843,1589,622,257"],
            ["Vietjet Air – Giảm 20.000đ", "DGS_260520_585", "10.000", "40.000.000", "20.000", "100.000", "30 ngày", "Vietjet", "612, 678"],
            ["Vietnam Airlines – Giảm 35.000đ", "DGS_260520_585", "30.000", "52.500.000", "35.000", "100.000", "30 ngày", "Vietnam Airlines", "3568, 3569"],
            ["Vietravel Airlines – Giảm 20.000đ", "DGS_260520_585", "10.000", "20.000.000", "20.000", "100.000", "30 ngày", "Vietravel Airlines", "4096, 4341"],
            ["Sun PhuQuoc Airways – Giảm 35.000đ", "DGS_260520_585", "30.000", "52.500.000", "35.000", "100.000", "30 ngày", "Sun PhuQuoc Airways", "4096, 4341"],
            ["Vinpearl – Giảm 4% tối đa 50.000đ", "DGS_260520_585", "100.000", "26.000.000", "50.000", "1.000", "30 ngày", "Vinpearl", "3751,738,595,621"],
            ["VinWonders – Giảm 2% tối đa 100.000đ", "DGS_260520_585", "100.000", "20.000.000", "100.000", "500.000", "30 ngày", "VinWonders", "3023,3024,3181"],
            ["SunWorld – Giảm 2% tối đa 100.000đ", "DGS_260520_585", "100.000", "20.000.000", "100.000", "500.000", "30 ngày", "SunWorld", "3023,3024,3181"],
            ["Tàu hỏa hè – Giảm 10.000đ", "DGS_260520_585", "5.000", "15.000.000", "10.000", "100.000", "30 ngày", "Đường Sắt VN", "2625"],
            ["Website/App FUTA – Giảm 2% tối đa 50.000đ", "DGS_260520_585", "20.000", "32.000.000", "50.000", "1.000", "30 ngày", "FUTA", "984, 360"],
            ["Website/App VEXERE – Giảm 2% tối đa 50.000đ", "DGS_260520_585", "20.000", "32.000.000", "50.000", "1.000", "30 ngày", "VEXERE", "320,1130,225"],
            ["Mytour – Giảm 1% tối đa 100.000đ", "DGS_260520_585", "2.000", "20.000.000", "100.000", "1.000", "30 ngày", "Mytour", "2942"],
            ["Website Vietjet – Giảm 5.000đ", "DGS_260520_585", "50.000", "75.000.000", "5.000", "100.000", "30 ngày", "Vietjet", "1996"],
        ]
    ))

    parts.append(h(3, "8.3 Quà xuyên suốt – Các BU khác &amp; BNPL"))
    parts.append(table(
        ["Tên quà", "MKT Code", "SL", "Ngân sách (đ)", "Giá trị (đ)", "Min order (đ)", "HSD", "Logo", "AppID áp dụng", "Ghi chú SOF"],
        [
            ["Trả Khoản Vay – Giảm 1% tối đa 10K", "DGS_260520_585", "1.000", "10.000.000", "10.000", "1.000.000", "30 ngày", "—", "3825,3869,3162,... (29 appIDs)", "Ví / Liên kết NH"],
            ["Phúc Long – Giảm 10K đơn 59K", "DGS_260520_585", "500", "5.000.000", "10.000", "59.000", "5 ngày", "Phúc Long", "1431,1326,1677", s("Chỉ TK Trả Sau")],
            ["KFC MiniApp – Giảm 30K đơn từ 160K", "DGS_260520_585", "100", "3.000.000", "30.000", "160.000", "5 ngày", "KFC", "4630", "Ví / Liên kết NH"],
            ["Ăn uống – Giảm 20% tối đa 25K", "DLS_260401_064", "200", "5.000.000", "25.000", "1.000", "5 ngày", "—", "(nhiều appID)", "Ví / Liên kết NH"],
            ["TikTok Shop – Giảm 2% tối đa 50K", "DGS_260520_585", "400", "20.000.000", "50.000", "300.000", "30 ngày", "TikTok Shop", "1413,4833 (auto apply)", "Ví / Liên kết NH"],
            ["Nạp Điện thoại – Giảm 5% tối đa 5K", "DGS_260520_585", "2.000", "10.000.000", "5.000", "1.000", "30 ngày", "—", "61,12,4609,4610,4666,...", "Ví / Liên kết NH"],
            ["Mỹ phẩm – Giảm 35K đơn 600K", "DLS_260401_038", "143", "5.000.000", "35.000", "600.000", "7 ngày", "—", "2383,1472,666,444,...", "Ví / Liên kết NH"],
            ["Thời trang – Giảm 80K đơn từ 1 triệu", "DLS_260401_080", "63", "5.000.000", "80.000", "1.000.000", "7 ngày", "—", "(nhiều appID)", "Ví / Liên kết NH"],
            ["Circle K – Giảm 5K đơn từ 30K", "DLS_260401_083", "600", "3.000.000", "5.000", "30.000", "7 ngày", "—", "3957", "Ví / Liên kết NH"],
            ["AEON – Giảm 25K đơn từ 990K", "DLS_260101_947", "200", "5.000.000", "25.000", "990.000", "7 ngày", "AEON", "(nhiều appID)", "Ví / Liên kết NH"],
            ["MM Mega Market – Giảm 25K đơn từ 990K", "DLS_260401_045", "200", "5.000.000", "25.000", "990.000", "7 ngày", "MM Mega Market", "1587", "Ví / Liên kết NH"],
            ["Bách Hóa XANH – Giảm 20K đơn từ 599K", "DLS_260101_951", "250", "5.000.000", "20.000", "599.000", "7 ngày", "Bách Hóa XANH", "361,1442", "Ví / Liên kết NH"],
            ["GO! – Giảm 70K đơn từ 2.5 triệu", "DLS_260401_090", "71", "5.000.000", "70.000", "2.500.000", "14 ngày", "GO!", "2839,3508,1675,3600", s("Chỉ TK Trả Sau")],
            ["Hasaki – Giảm 30K đơn từ 300K", "DGS_260520_585", "167", "5.000.000", "30.000", "300.000", "14 ngày", "Hasaki", "4536,4537", s("Chỉ TK Trả Sau")],
            ["Siêu thị mini – Giảm 10K đơn 200K", "DGS_260520_585", "500", "5.000.000", "10.000", "200.000", "14 ngày", "Minimart", "(nhiều appID)", s("Chỉ TK Trả Sau")],
            ["AEON – Giảm 30K đơn từ 500K", "DLS_260401_050", "167", "5.000.000", "30.000", "500.000", "14 ngày", "AEON", "(nhiều appID)", s("Chỉ TK Trả Sau")],
            ["Thời trang – Giảm 30K đơn từ 300K", "DGS_260520_585", "167", "5.000.000", "30.000", "300.000", "14 ngày", "—", "(nhiều appID)", s("Chỉ TK Trả Sau")],
            ["Mỹ phẩm – Giảm 30K đơn từ 300K", "DLS_260401_077", "167", "5.000.000", "30.000", "300.000", "14 ngày", "—", "2383,1472,666,...", s("Chỉ TK Trả Sau")],
            ["Circle K – Giảm 5K đơn từ 10K", "DGS_260520_585", "600", "3.000.000", "5.000", "10.000", "14 ngày", "Circle K", "3957", s("Chỉ TK Trả Sau")],
            ["Nhà thuốc Long Châu – Giảm 30K đơn từ 150K", "DGS_260520_585", "167", "5.000.000", "30.000", "150.000", "14 ngày", "Long Châu", "2236,4744", s("Chỉ TK Trả Sau")],
        ]
    ))

    return "".join(parts)


# ── Growth Enablement page updates ────────────────────────────────────────────

def build_prd_update() -> str:
    """Updated PRD with DGS_260520_585 actual icon & config data."""
    parts: list[str] = []
    parts.append(tip(
        p(f"{s('Campaign đang chạy:')} DGS_260520_585 – Săn vé du lịch hè 0đ cùng Zalopay "
          f"| Live: 10:00 05/06 – 23:59 26/07/2026")
    ))

    parts.append(h(1, "Lucky Wheel - Product Requirements Document (PRD)"))
    parts.append(p(f"{s('Owner:')} Growth Enablement Team &nbsp;|&nbsp; {s('Version:')} 2.5 "
                   f"&nbsp;|&nbsp; {s('Status:')} Production"))

    parts.append(h(2, "1. Tổng quan"))
    parts.append(p("Lucky Wheel là tính năng gamification trên ZaloPay, cho phép người dùng quay vòng xổ số ảo để nhận phần thưởng (voucher, xu, vé sự kiện). Mục tiêu tăng DAU và Transaction Volume."))

    parts.append(h(2, "2. Cấu hình UI"))
    parts.append(h(3, "2.1 Thiết kế vòng quay"))
    parts.append(ul([
        "Số ô (slot): cấu hình động, tối đa 12 ô, mặc định 8 ô",
        "Mỗi ô: hình ảnh icon (PNG, 80×80px), label tối đa 16 ký tự",
        "Animation: CSS spin với easing cubic-bezier(0.17, 0.67, 0.12, 0.99)",
        "Thời gian quay: 3–5 giây (ngẫu nhiên per session)",
        "Hỗ trợ dark/light mode",
    ]))

    parts.append(h(4, "Ví dụ icon — DGS_260520_585 (8 slot)"))
    parts.append(table(
        ["STT", "Icon", "Nguồn asset"],
        [
            ["1", "Nha Trang 0Đ", "Lấy từ KV"],
            ["2", "Dấu hỏi chấm (mystery prize)", "Lấy từ folder"],
            ["3", "Đà Nẵng 0Đ", "Lấy từ KV"],
            ["4", "VinWonders", "Logo thương hiệu"],
            ["5", "Đà Lạt 0Đ", "Lấy từ KV"],
            ["6", "Vietjet Air", "Logo thương hiệu"],
            ["7", "Hải Phòng 0Đ", "Lấy từ KV"],
            ["8", "FUTA", "Logo thương hiệu"],
        ]
    ))

    parts.append(h(3, "2.2 Ads Banner tích hợp"))
    parts.append(table(
        ["Vị trí", "Ads ID (ví dụ DGS_260520_585)", "Kích thước"],
        [
            ["Dưới game chính", "6845", "320×50px"],
            ["Dưới task list", "6846", "320×50px"],
        ]
    ))

    parts.append(h(2, "3. Cấu hình lượt quay"))
    parts.append(table(
        ["Tham số", "Mô tả", "Giá trị mặc định"],
        [
            ["welcome_turns", "Lượt quay chào mừng khi lần đầu vào Gami", "2"],
            ["max_turns_per_day", "Giới hạn lượt quay tối đa/ngày/user", "5"],
            ["max_turns_per_campaign", "Giới hạn tổng lượt quay/user/campaign", "không giới hạn"],
            ["turn_expiry_hours", "Số giờ lượt quay hết hạn sau khi nhận", "24"],
        ]
    ))

    parts.append(h(2, "4. Cấu hình quà"))
    parts.append(h(3, "4.1 Gift Pool"))
    parts.append(table(
        ["Loại pool", "Mô tả", "Thời điểm thả"],
        [
            ["Weekly pool", "Thả vào thứ Hai 10:00 hàng tuần, hết sau 7 ngày", "Thứ Hai 10:00"],
            ["Campaign pool", "Chạy xuyên suốt campaign", "Từ ngày live"],
        ]
    ))

    parts.append(h(3, "4.2 Tỉ lệ quay"))
    parts.append(ul([
        "Tổng tỉ lệ tất cả slot = 100%",
        "Hỗ trợ slot buffer (xu) với tỉ lệ cao để không vượt budget",
        "counter = 1 lần/user/quà nghĩa là mỗi user chỉ nhận loại quà đó 1 lần trong campaign",
    ]))

    parts.append(h(2, "5. Task List để nhận lượt quay"))
    parts.append(p("User hoàn thành task → nhận thêm lượt quay. DGS_260520_585 có 18 tasks trải khắp các vertical."))
    parts.append(table(
        ["Trigger Type", "Mô tả", "Ví dụ (DGS_260520_585)"],
        [
            ["Payment", "User thực hiện giao dịch thanh toán theo AppID", "Task 6: Đặt vé máy bay (AppID: 69,606,612,...)"],
            ["FE Event ID", "User thực hiện hành động trên app (click, search)", "Task 3: Tìm kiếm vé máy bay (Event: 01.4700.006)"],
            ["CPS", "Cost Per Sale – ghi nhận khi có giao dịch partner", "Task 15: Nạp điện thoại (AppID: 61,12,...)"],
        ]
    ))

    parts.append(h(2, "6. Điều kiện tham gia (Eligibility)"))
    parts.append(table(
        ["Điều kiện", "Cấu hình", "DGS_260520_585"],
        [
            ["Visit landing", "Bắt buộc vào trang campaign trước", "✅ Có"],
            ["Welcome turn", "Nhận lượt đầu khi lần đầu mở Gami", "✅ 2 lượt"],
            ["Segment", "Nhóm user áp dụng", "Mass (13155)"],
            ["Claim quà", "User bấm xác nhận để nhận quà", "❌ Không (auto)"],
        ]
    ))

    parts.append(h(2, "7. TnC (Terms &amp; Conditions)"))
    parts.append(ul([
        "Ads_id: ID bài viết TnC trên CMS (DGS_260520_585: Ads_id = 6828)",
        "Hiển thị popup lần đầu user vào campaign",
        "Bắt buộc scroll đến cuối trước khi nhấn Đồng ý",
        "Cập nhật TnC → yêu cầu user xác nhận lại",
    ]))

    return "".join(parts)


def build_ops_update() -> str:
    """Updated QA & Operation Guide with DGS_260520_585 real data."""
    parts: list[str] = []
    parts.append(info(
        p(f"{s('Campaign reference:')} DGS_260520_585 – Săn vé du lịch hè 0đ | "
          f"Testing: 05/06 | Live: 10:00 05/06 – 23:59 26/07/2026")
    ))

    parts.append(h(1, "Lucky Wheel - QA Test Cases &amp; Operation Guide"))

    parts.append(h(2, "Part 1: QA Test Cases"))
    parts.append(h(3, "1.1 Happy Path"))
    parts.append(table(
        ["ID", "Test case", "Expected"],
        [
            ["HP-01", "User mở landing page lần đầu → nhận welcome turn", "Số lượt = 2 (config DGS_260520_585)"],
            ["HP-02", "User hoàn thành task Payment (vé máy bay) → credit lượt", "Turns += reward của task"],
            ["HP-03", "User quay → nhận voucher", "Animation quay, hiện kết quả, voucher vào ví"],
            ["HP-04", "RISK CONFIRM: dùng ví/liên kết NH (không phải VietQR)", "Credit đúng lượt quay"],
            ["HP-05", "Quà weekly thả đúng thứ Hai 10:00", "Pool mới xuất hiện, quà cũ hết"],
            ["HP-06", "Budget alert 50% → email gửi đến phutt2, thuyvtt4, thutla, lylt", "Email trong 5 phút"],
        ]
    ))

    parts.append(h(3, "1.2 Edge &amp; Fraud Cases"))
    parts.append(table(
        ["ID", "Test case", "Expected"],
        [
            ["EC-01", "Double-spin cùng idempotency_key", "Trả về kết quả lần 1, không spin lại"],
            ["EC-02", "Giao dịch VietQR kích hoạt auto-trigger", "Không credit (RISK CONFIRM block)"],
            ["EC-03", "Apple Pay kích hoạt auto-trigger", "Không credit (RISK CONFIRM block)"],
            ["EC-04", "User trong blacklist Risk gửi trigger", "Block, không credit"],
            ["EC-05", "Quay khi slot hết hàng", "Tự chuyển sang slot Xu (buffer)"],
            ["FR-01", "1 user gửi 10 spin/10 giây", "Rate limit block từ request thứ 4"],
        ]
    ))

    parts.append(h(3, "1.3 UserID Testing (DGS_260520_585)"))
    parts.append(table(
        ["Tên", "UserID"],
        [
            ["HoaVMQ", "181211000004278"],
            ["TaiCT", "200124000486951"],
            ["ThuTLA", "181002000000026"],
            ["LyLT", "180219000003633"],
            ["TrangPY", "200807000019734"],
            ["Thuyvtt4", "190411000016472"],
            ["TrucBTT", "190514000003974"],
            ["Phutt2", "201114000014743"],
        ]
    ))

    parts.append(h(2, "Part 2: Operation Guide"))
    parts.append(h(3, "Bước 1: Tạo campaign mới"))
    parts.append(ul([
        "Vào https://ops.zalopay.vn/lucky-wheel-config",
        "Click [+ Tạo campaign]",
        "Điền: Campaign ID (DGS_260520_585), tên, thời gian (10:00 05/06 – 23:59 26/07), budget tổng (619.300.000đ)",
    ]))

    parts.append(h(3, "Bước 2: Cấu hình slot &amp; tỉ lệ"))
    parts.append(ul([
        "Tab [Vòng quay] → Upload 8 slot icons (PNG 80×80px) theo danh sách §4.2",
        "Tab [Tỉ lệ quà] → Nhập weight % (tổng = 100%)",
        "Tick [Counter per user = 1] cho các quà giá trị cao (vé máy bay, resort)",
    ]))

    parts.append(h(3, "Bước 3: Cấu hình budget alert"))
    parts.append(ul([
        "Ngưỡng: 50%, 75%, 95%",
        "Email alert: phutt2, thuyvtt4, thutla, lylt",
    ]))

    parts.append(h(3, "Bước 4: Cấu hình task (18 tasks)"))
    parts.append(table(
        ["#", "Title", "Trigger", "Reward", "Frequency"],
        [
            ["1", "Đặt vé + dùng Giảm giá từ xu", "Payment (Xu SOF)", "4 lượt", "1 lần/tuần"],
            ["2", "Đặt vé + dùng TK Trả Sau", "Payment (BNPL SOF)", "4 lượt", "1 lần/tuần"],
            ["3", "Search vé máy bay", "FE Event 01.4700.006", "1 lượt", "1 lần/tuần"],
            ["4", "Search vé xe khách", "FE Event 01.4731.005", "1 lượt", "1 lần/tuần"],
            ["5", "Search vé tàu", "FE Event 01.4770.008", "1 lượt", "1 lần/tuần"],
            ["6", "Đặt vé máy bay", "Payment (AppID: 69,606,...)", "2 lượt", "1 lần/tuần"],
            ["7", "Đặt vé tàu/xe khách", "Payment (AppID: 620,759,...)", "2 lượt", "1 lần/tuần"],
            ["8", "Đặt vé VinWonders/SunWorld", "Payment (AppID: 3023,3024,3181)", "2 lượt", "1 lần/tuần"],
            ["9", "Đặt vé FUTA website/app", "Payment (AppID: 984,360)", "2 lượt", "1 lần/CT (từ 11/6)"],
            ["10", "Đặt vé VEXERE website/app", "Payment (AppID: 320,1130,225)", "2 lượt", "1 lần/CT (từ 11/6)"],
            ["11", "Đặt vé Vietjet website", "Payment (AppID: 2942)", "2 lượt", "1 lần/CT (từ 11/6)"],
            ["12", "Chơi game H5", "FE Event (37 IDs)", "1 lượt", "1 lần/tháng"],
            ["13", "Kiểm tra hóa đơn", "FE Event (01.4101.302,...)", "1 lượt", "1 lần/tháng"],
            ["14", "Mua TikTok Shop", "Payment (1413,4833)", "1 lượt", "1 lần/tháng"],
            ["15", "Nạp điện thoại", "CPS (61,12,4609,...)", "1 lượt", "1 lần/tháng"],
            ["16", "GreenSM + mã ZLPDULICH", "Payment (3095)", "2 lượt", "1 lần/tuần"],
            ["17", "Đặt vé phim", "Payment (19)", "2 lượt", "1 lần/tuần"],
            ["18", "Follow Fanpage Zalopay", "FE/Link", "1 lượt", "1 lần duy nhất"],
        ]
    ))

    parts.append(h(3, "Bước 5: Preview &amp; Publish"))
    parts.append(ul([
        "Click [Preview] → Kiểm tra trên device test với UserID từ §1.3",
        "Nếu OK → Click [Publish] → Campaign active",
        "Monitor: Dashboard real-time tại https://ops.zalopay.vn/lucky-wheel-config/DGS_260520_585/dashboard",
    ]))

    return "".join(parts)


def build_tech_backend_update() -> str:
    """Updated Technical Spec Backend with DGS_260520_585 RISK CONFIRM rules."""
    parts: list[str] = []
    parts.append(h(1, "Lucky Wheel - Technical Spec Backend"))

    parts.append(h(2, "1. API Design"))
    parts.append(h(3, "POST /api/v2/lucky-wheel/spin"))
    parts.append(p("Thực hiện 1 lượt quay."))

    parts.append(h(2, "2. Database Schema"))
    parts.append(p("(Xem schema đầy đủ trong thiết kế DB — lw_campaigns, lw_gifts, lw_user_turns, lw_spin_history)"))

    parts.append(h(2, "3. Rate Limiting &amp; Fraud Prevention"))

    parts.append(h(3, "3.1 Rate limits"))
    parts.append(ul([
        "1 spin/3 giây/user (Redis token bucket)",
        "100 spins/phút/IP (circuit breaker)",
    ]))

    parts.append(h(3, "3.2 AUTO-TRIGGER + RISK CONFIRM"))
    parts.append(warning(
        h(4, "⚠️ Bắt buộc cho mọi campaign có auto-trigger dựa trên payment") +
        p("Campaign DGS_260520_585 áp dụng đầy đủ RISK CONFIRM:") +
        ul([
            s("Chặn VietQR:") + " giao dịch qua VietQR không được credit lượt quay",
            s("Chặn Apple Pay:") + " tương tự VietQR",
            s("Chặn Thanh toán trực tiếp không cần liên kết:") + " không credit",
            s("Malicious/casual abuser check:") + " user trong danh sách Risk blacklist → block auto-trigger",
        ])
    ))
    parts.append(p("Logic: " + f'<code>if payment.method in BLOCKED_METHODS or user in RISK_BLACKLIST: skip_credit()</code>'))

    parts.append(h(3, "3.3 Idempotency"))
    parts.append(ul([
        "Mỗi spin yêu cầu idempotency_key (UUID)",
        "Key lưu trong Redis 24h; duplicate request → trả về kết quả cũ",
    ]))

    parts.append(h(2, "4. Budget Control"))
    parts.append(table(
        ["Ngưỡng alert", "Hành động", "DGS_260520_585 recipients"],
        [
            ["50%", "Email alert", "phutt2, thuyvtt4, thutla, lylt"],
            ["75%", "Email alert (bắt buộc)", "phutt2, thuyvtt4, thutla, lylt"],
            ["95%", "Email alert", "phutt2, thuyvtt4, thutla, lylt"],
            ["100%", "Dừng phát quà", "—"],
        ]
    ))

    parts.append(h(2, "5. Gift Distribution"))
    parts.append(ul([
        "Weighted random selection với exclusion list per-user",
        "counter_per_user = 1: user không nhận lại quà đã có",
        "Fallback: khi tất cả quà hết → slot Xu (buffer)",
    ]))

    return "".join(parts)


def build_risk_sop_update() -> str:
    """Updated Risk SOP with DGS_260520_585 as worked example."""
    parts: list[str] = []
    parts.append(h(1, "Risk SOP - Campaign Review"))
    parts.append(p(f"{s('Phiên bản:')} 3.2 &nbsp;|&nbsp; {s('Hiệu lực từ:')} 01/01/2026 &nbsp;|&nbsp; {s('Owner:')} Risk Management Team"))

    parts.append(h(2, "1. Mục đích"))
    parts.append(p("Quy trình này xác định các bước review và phê duyệt rủi ro cho tất cả campaign khuyến mãi trước khi launch, đảm bảo tuân thủ chính sách Risk và kiểm soát chi phí."))

    parts.append(h(2, "2. Phạm vi áp dụng"))
    parts.append(p("Áp dụng cho tất cả campaign có phát quà/voucher/xu cho người dùng ZaloPay:"))
    parts.append(ul(["Lucky Wheel, Scratch Card, Mini Game", "Cashback campaign", "Partnership promotion", "OTA (One-Time Award) campaign"]))

    parts.append(h(2, "3. Quy trình"))
    parts.append(table(
        ["Bước", "Người thực hiện", "Mô tả", "SLA"],
        [
            [s("Bước 1"), "Biz Team", "Tạo Jira ticket (status = TO DO), attach Confluence Campaign Request Document đầy đủ 8 mục", "T-5 ngày làm việc"],
            [s("Bước 2"), "Biz/PM", "Chuyển ticket sang RISK REVIEW", "—"],
            [s("Bước 3"), "Risk Reviewer", "Đánh giá theo checklist 10 điểm (xem §4)", "T+1 ngày làm việc"],
            [s("Bước 4"), "Risk Reviewer", "Ra quyết định: PASS / PARTIAL_FAIL / FAIL → update ticket", "—"],
            [s("Bước 5"), "Risk Lead", "Escalation nếu ngân sách &gt; 500M VND hoặc category mới", "T+0.5 ngày"],
        ]
    ))

    parts.append(h(2, "4. Checklist 10 điểm"))
    parts.append(table(
        ["#", "Tiêu chí", "Mức độ"],
        [
            ["1", "Ngân sách có FA approve", "Critical"],
            ["2", "Giá trị quà/user theo policy (≤ 1M/user/campaign)", "Critical"],
            ["3", "Không có restricted/prohibited merchant", "High"],
            ["4", "RISK CONFIRM rules đã khai báo (VietQR, Apple Pay, blacklist)", "High"],
            ["5", "KYC tier requirement rõ ràng", "High"],
            ["6", "Thời gian campaign xác định (ngày bắt đầu và kết thúc)", "Medium"],
            ["7", "Budget alert đã cấu hình (ít nhất 75%)", "Medium"],
            ["8", "Task list và reward pool không vi phạm chính sách", "Medium"],
            ["9", "Voucher config có điều kiện đầy đủ (SOF, min order, HSD)", "Medium"],
            ["10", "Campaign có danh sách UserID testing", "Low"],
        ]
    ))

    parts.append(h(2, "5. Quyết định"))
    parts.append(table(
        ["Quyết định", "Điều kiện", "Action"],
        [
            [s("PASS"), "Tất cả 10 mục Comply", "Chuyển ticket → Review done"],
            [s("PARTIAL_FAIL"), "1–2 mục Chưa rõ, không có Violate", "Chuyển ticket → Review done, comment yêu cầu clarify trong 24h"],
            [s("FAIL"), "Bất kỳ mục Critical/High nào Violate", "Chuyển ticket → REJECT, Biz phải sửa và gửi lại"],
        ]
    ))

    parts.append(h(2, "6. Ví dụ thực tế — DGS_260520_585"))
    parts.append(info(
        h(4, "Campaign: Săn vé du lịch hè 0đ cùng Zalopay") +
        table(
            ["Tiêu chí", "Kết quả", "Ghi chú"],
            [
                ["Ngân sách FA approve", "✅ Comply", "619.300.000đ — FA đã phê duyệt"],
                ["Giá trị quà/user", "✅ Comply", "Tối đa 3M (resort) — trong ngưỡng cho phép"],
                ["Merchant category", "✅ Comply", "OTA + F&B + Retail — all approved categories"],
                ["RISK CONFIRM", "✅ Comply", "Chặn VietQR/Apple Pay/direct; loại malicious users"],
                ["KYC tier", "✅ Comply", "Segment Mass 13155 = Basic verified"],
                ["Thời gian campaign", "✅ Comply", "10:00 05/06 – 23:59 26/07"],
                ["Budget alert", "✅ Comply", "50%/75%/95% — đủ 3 ngưỡng"],
                ["Task list &amp; reward", "✅ Comply", "18 tasks, tất cả approved categories"],
                ["Voucher config", "✅ Comply", "Đầy đủ SOF, min order, HSD"],
                ["UserID testing", "✅ Comply", "8 testing users đã khai báo"],
            ]
        )
    ))

    return "".join(parts)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    settings = get_settings()
    writer = ConfluenceWriter(settings)
    reader = ConfluenceClient(settings)

    if not writer.is_ready():
        log.error("Confluence credentials not configured — check .env")
        sys.exit(1)

    # ── Step 1: Update main campaign page (known ID) ─────────────────────────
    log.info("=== Updating main campaign page (ID: %s) ===", MAIN_PAGE_ID)
    main_title = "[20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]"
    try:
        result = writer.update_page(
            page_id=MAIN_PAGE_ID,
            title=main_title,
            body_storage=build_main_page(),
        )
        log.info("Main page updated → version %s", result.get("version"))
    except Exception as exc:
        log.error("Failed to update main page: %s", exc)

    # ── Step 2: Find ClawathonGrow page IDs ──────────────────────────────────
    log.info("=== Finding ClawathonGrow pages ===")
    try:
        grow_pages = reader.list_pages(GROW_SPACE)
        grow_by_title: dict[str, str] = {}
        for pg in grow_pages:
            pid = str(pg.get("id", ""))
            title = pg.get("title", "")
            if pid and title:
                grow_by_title[title] = pid
        log.info("Found %d pages in %s", len(grow_by_title), GROW_SPACE)
    except Exception as exc:
        log.error("Failed to list ClawathonGrow pages: %s", exc)
        grow_by_title = {}

    # ── Step 3: Update ClawathonGrow pages ───────────────────────────────────
    grow_updates = [
        ("Lucky Wheel - Product Requirements Document (PRD)", build_prd_update()),
        ("Lucky Wheel - Technical Spec Backend", build_tech_backend_update()),
        ("Lucky Wheel - QA Test Cases & Operation Guide", build_ops_update()),
    ]

    for title, xhtml in grow_updates:
        pid = grow_by_title.get(title)
        if not pid:
            log.warning("Page %r not found in %s — skipping", title, GROW_SPACE)
            continue
        try:
            result = writer.update_page(page_id=pid, title=title, body_storage=xhtml)
            log.info("Updated %r → version %s", title[:50], result.get("version"))
        except Exception as exc:
            log.error("Failed to update %r: %s", title, exc)

    # ── Step 4: Find ClawathonRisk pages ─────────────────────────────────────
    log.info("=== Finding ClawathonRisk pages ===")
    try:
        risk_pages = reader.list_pages(RISK_SPACE)
        risk_by_title: dict[str, str] = {}
        for pg in risk_pages:
            pid = str(pg.get("id", ""))
            title = pg.get("title", "")
            if pid and title:
                risk_by_title[title] = pid
        log.info("Found %d pages in %s", len(risk_by_title), RISK_SPACE)
    except Exception as exc:
        log.error("Failed to list ClawathonRisk pages: %s", exc)
        risk_by_title = {}

    # ── Step 5: Update ClawathonRisk pages ───────────────────────────────────
    risk_updates = [
        ("Risk SOP - Campaign Review", build_risk_sop_update()),
    ]

    for title, xhtml in risk_updates:
        pid = risk_by_title.get(title)
        if not pid:
            log.warning("Page %r not found in %s — skipping", title, RISK_SPACE)
            continue
        try:
            result = writer.update_page(page_id=pid, title=title, body_storage=xhtml)
            log.info("Updated %r → version %s", title[:50], result.get("version"))
        except Exception as exc:
            log.error("Failed to update %r: %s", title, exc)

    log.info("=== Done ===")


if __name__ == "__main__":
    main()
