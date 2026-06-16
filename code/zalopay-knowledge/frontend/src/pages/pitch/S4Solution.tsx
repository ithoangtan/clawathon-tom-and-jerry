import { Database, Brain, Zap } from "lucide-react";
import { SectionLabel } from "./S1Problem";

const concepts = [
  {
    icon: Database,
    color: "var(--color-accent)",
    title: "Lưu kiến thức — theo từng phòng ban",
    body: "Tự động đọc và cập nhật tài liệu từ Confluence. Knowledge được tổ chức theo từng department, phân quyền riêng. Mỗi team có agent riêng — các agent có thể giao tiếp với nhau để đưa ra quyết định đa chiều, tham chiếu chéo, hoặc tạo checklist review trước khi kết luận.",
  },
  {
    icon: Brain,
    color: "var(--color-brand)",
    title: "Hiểu & suy luận từ kiến thức nội bộ",
    body: "Khi cần quyết định, tìm đúng tài liệu liên quan, đọc hiểu context, áp dụng đúng policy — không tự nghĩ ra ngoài những gì đã được ghi lại. Đây là điểm khác biệt: AI không đoán, AI áp dụng đúng những gì Zalopay đã tích lũy.",
  },
  {
    icon: Zap,
    color: "var(--color-warning)",
    title: "Tự động hóa quy trình có suy luận",
    body: "Chat để hỏi thông tin. Hoặc chạy workflow: thực hiện các bước lặp lại cần kiến thức — không chỉ automation đơn thuần, mà automation có reasoning. Agent tự suy nghĩ và hành động cho tới khi hoàn thành công việc.",
  },
];

export function S4Solution() {
  return (
    <section
      id="solution"
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Platform</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Một platform — cho mọi team
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Ba khái niệm cốt lõi. Không cần là developer để hiểu — và cũng không cần là developer để
          xây thêm workflow mới.
        </p>

        <div className="grid gap-6 sm:grid-cols-3">
          {concepts.map((c, i) => {
            const Icon = c.icon;
            return (
              <div
                key={i}
                data-reveal
                className="glass-panel group relative overflow-hidden rounded-2xl p-7 transition-all duration-300"
                style={{ borderTop: `2px solid ${c.color}` }}
              >
                {/* Background glow */}
                <div
                  className="pointer-events-none absolute -top-8 -right-8 h-32 w-32 rounded-full blur-2xl opacity-10 transition-opacity duration-300 group-hover:opacity-20"
                  style={{ background: c.color }}
                />

                <div
                  className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl"
                  style={{ background: `color-mix(in srgb, ${c.color} 18%, transparent)` }}
                >
                  <Icon size={22} style={{ color: c.color }} />
                </div>
                <h3
                  className="mb-3 text-base font-bold leading-snug"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {c.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {c.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
