import { UserCheck, FileSearch, AlertCircle } from "lucide-react";
import { SectionLabel } from "./S1Problem";

const points = [
  {
    icon: UserCheck,
    color: "var(--color-success)",
    title: "Human-in-the-loop luôn luôn",
    body: "Với mọi workflow, AI làm vòng đầu. Quyết định cuối luôn do con người. LOW risk → reviewer nhận notify và approve. HIGH risk → trả lại ngay để sửa. AI không bao giờ là người ký duyệt cuối.",
  },
  {
    icon: FileSearch,
    color: "var(--color-brand)",
    title: "Audit trail đầy đủ",
    body: "Mọi reasoning của AI đều được log: dùng tài liệu nào, confidence bao nhiêu, kết quả là gì. Compliance và management có thể audit bất kỳ quyết định nào, bất kỳ lúc nào.",
  },
  {
    icon: AlertCircle,
    color: "var(--color-warning)",
    title: "Khi không chắc → escalate, không block",
    body: "AI confidence thấp thì tự escalate lên human. Workflow không bao giờ bị stuck vì AI không chắc chắn. Không có gì bị mất hay bị bỏ qua.",
  },
];

export function S7Governance() {
  return (
    <section
      id="governance"
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Governance</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          AI hỗ trợ — con người quyết định
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Đây không phải AI tự động hoàn toàn. Đây là AI làm việc cùng con người — có trách nhiệm,
          có kiểm soát, có thể audit.
        </p>

        <div className="grid gap-6 sm:grid-cols-3">
          {points.map((p, i) => {
            const Icon = p.icon;
            return (
              <div key={i} data-reveal className="glass-panel rounded-2xl p-7">
                <div
                  className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl"
                  style={{ background: `color-mix(in srgb, ${p.color} 15%, transparent)` }}
                >
                  <Icon size={22} style={{ color: p.color }} />
                </div>
                <h3
                  className="mb-3 text-sm font-bold"
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
