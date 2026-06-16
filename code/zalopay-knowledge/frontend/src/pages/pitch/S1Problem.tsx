import { useRef } from "react";
import { useGSAP, attachPerspectiveTilt } from "@/lib/gsap";
import { HelpCircle, History, GitBranch, Sparkles } from "lucide-react";

const problems = [
  {
    icon: HelpCircle,
    title: "Hỏi ai bây giờ?",
    body: "Người nắm kiến thức đã chuyển team, đang bận, hoặc đã nghỉ khỏi Zalopay. Knowledge nằm trong đầu người — không có chỗ lưu.",
    accent: "var(--color-warning)",
  },
  {
    icon: History,
    title: "Bài học này mình đã gặp rồi...",
    body: "Post-mortem, case study, incident report năm ngoái không ai nhớ. Sai lầm cũ lặp lại ở team khác.",
    accent: "var(--color-danger)",
  },
  {
    icon: GitBranch,
    title: "Đúng process chưa? Hỏi ai để confirm?",
    body: "Team A biết mình cần risk review. Team B nghĩ mình không cần — nhưng thực ra là cần. Không biết hỏi ai để xác nhận nhanh.",
    accent: "var(--color-accent)",
  },
  {
    icon: Sparkles,
    title: "AI tốt đến đâu cũng cần 1 thứ",
    body: "Kiến thức nội bộ: policy, experience, context của Zalopay. Không có nó, AI generic không thể áp dụng đúng judgment của người đã làm việc ở đây nhiều năm.",
    accent: "var(--color-brand)",
  },
];

export function S1Problem() {
  const sectionRef = useRef<HTMLElement>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useGSAP(
    () => {
      cardRefs.current.forEach((card) => {
        if (card) attachPerspectiveTilt(card, { maxTilt: 6 });
      });
    },
    { scope: sectionRef },
  );

  return (
    <section
      id="problem"
      ref={sectionRef}
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div data-reveal className="mb-4">
          <SectionLabel>The Problem</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Dù bạn ở team nào — bạn sẽ nhận ra mình trong đây
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Risk, Tech, Operations, Finance, hay bất kỳ phòng ban nào — tất cả đều đang chạy vào
          cùng một bức tường.
        </p>

        {/* Cards */}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {problems.map((p, i) => {
            const Icon = p.icon;
            return (
              <div
                key={i}
                data-reveal
                ref={(el) => (cardRefs.current[i] = el)}
                className="glass-panel rounded-2xl p-6"
                style={{ borderLeft: `3px solid ${p.accent}` }}
              >
                <div
                  className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl"
                  style={{ background: `color-mix(in srgb, ${p.accent} 15%, transparent)` }}
                >
                  <Icon size={20} style={{ color: p.accent }} />
                </div>
                <h3
                  className="mb-2 text-sm font-bold leading-snug"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {p.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {p.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="text-sm font-bold tracking-widest uppercase"
      style={{ color: "var(--color-brand)" }}
    >
      {children}
    </span>
  );
}
