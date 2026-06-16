import { FlaskConical, Building2, Users } from "lucide-react";
import { SectionLabel } from "./S1Problem";

const steps = [
  {
    icon: FlaskConical,
    number: "01",
    title: "Validate với team thật",
    body: "Chạy thử với volume ticket thật, đo độ chính xác của AI review so với human review. Calibrate và cải thiện trước khi mở rộng.",
    color: "var(--color-accent)",
  },
  {
    icon: Building2,
    number: "02",
    title: "Kết nối systems công ty",
    body: "Đổi từ tài khoản cá nhân sang Confluence + Jira công ty. Deploy trên hạ tầng Zalopay — data không ra ngoài, security compliant.",
    color: "var(--color-brand)",
  },
  {
    icon: Users,
    number: "03",
    title: "Mọi team bắt đầu build knowledge base ngay hôm nay",
    body: "Không cần chờ AI hoàn hảo. Bắt đầu lưu kiến thức, bắt đầu xây workflow. 1 năm sau Zalopay sẽ luôn sẵn sàng cho bất kỳ AI-native workflow nào. Thêm workflow mới = thêm 1 Confluence page.",
    color: "var(--color-warning)",
  },
];

export function S9NextSteps() {
  return (
    <section
      id="next-steps"
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Next Steps</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Từ demo đến Zalopay-wide
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Ba bước để biến hackathon demo thành hệ thống thật sự phục vụ toàn công ty.
        </p>

        <div className="grid gap-6 sm:grid-cols-3">
          {steps.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} data-reveal className="glass-panel rounded-2xl p-7">
                <div className="mb-5 flex items-center justify-between">
                  <div
                    className="text-5xl font-black tracking-tighter"
                    style={{ color: "transparent", WebkitTextStroke: `1px ${s.color}` }}
                  >
                    {s.number}
                  </div>
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                    style={{ background: `color-mix(in srgb, ${s.color} 15%, transparent)` }}
                  >
                    <Icon size={18} style={{ color: s.color }} />
                  </div>
                </div>
                <h3
                  className="mb-3 text-sm font-bold leading-snug"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {s.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {s.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
