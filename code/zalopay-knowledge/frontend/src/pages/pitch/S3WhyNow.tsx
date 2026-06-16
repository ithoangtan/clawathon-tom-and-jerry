import { Cpu, Layers, Network } from "lucide-react";
import { SectionLabel } from "./S1Problem";

const reasons = [
  {
    icon: Cpu,
    title: "Claude, ChatGPT, Gemini đều rất giỏi — nhưng không biết Zalopay là ai",
    body: "Các AI này không biết Risk Playbook của Zalopay, không biết incident lớn năm ngoái, không biết team nào cần review gì. Knowledge nội bộ là lợi thế cạnh tranh — ai build trước, người đó thắng.",
    number: "01",
  },
  {
    icon: Layers,
    title: "Zalopay đã có tài sản — chỉ cần unlock",
    body: "Năm tích lũy SOP, post-mortem, playbook, case study. Đây là knowledge mà không AI generic nào có. Wiki Agent là lớp biến tài sản đó thành hành động.",
    number: "02",
  },
  {
    icon: Network,
    title: "Công ty nào build knowledge base ngay hôm nay — 1 năm sau có lợi thế AI-native",
    body: "Không phải chờ AI tốt hơn. Mà là chờ đủ kiến thức để AI có thể làm việc thay. Bắt đầu ngay hôm nay, 1 năm sau Zalopay sẽ luôn sẵn sàng cho bất kỳ AI-native workflow nào.",
    number: "03",
  },
];

export function S3WhyNow() {
  return (
    <section
      id="why-now"
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Why Now</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-14 max-w-3xl text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Tại sao bây giờ?{" "}
          <span style={{ color: "var(--color-text-secondary)", fontWeight: 400 }}>
            AI không thiếu — knowledge nội bộ mới là lợi thế
          </span>
        </h2>

        <div className="grid gap-6 sm:grid-cols-3">
          {reasons.map((r, i) => {
            const Icon = r.icon;
            return (
              <div key={i} data-reveal className="glass-panel rounded-2xl p-7">
                <div
                  className="mb-5 text-4xl font-black tracking-tighter"
                  style={{ color: "var(--color-brand-muted)", WebkitTextStroke: "1px var(--color-brand)" }}
                >
                  {r.number}
                </div>
                <div
                  className="mb-4 inline-flex h-9 w-9 items-center justify-center rounded-lg"
                  style={{ background: "var(--color-brand-muted)" }}
                >
                  <Icon size={18} style={{ color: "var(--color-brand)" }} />
                </div>
                <h3
                  className="mb-3 text-sm font-bold leading-snug"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {r.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {r.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
