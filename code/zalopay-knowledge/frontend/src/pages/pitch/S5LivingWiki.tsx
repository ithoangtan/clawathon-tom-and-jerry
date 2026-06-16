import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { SectionLabel } from "./S1Problem";

const eras = [
  {
    label: "Năm đầu",
    sublabel: "Foundation docs, policy, SOPs",
    height: 64,
    color: "var(--color-brand)",
    opacity: 0.4,
  },
  {
    label: "Năm tiếp theo",
    sublabel: "Post-mortems, case studies, playbooks",
    height: 112,
    color: "var(--color-brand)",
    opacity: 0.65,
  },
  {
    label: "Hôm nay & tương lai",
    sublabel: "Agent reasoning trên toàn bộ nền kiến thức",
    height: 168,
    color: "var(--color-brand)",
    opacity: 1,
    isTop: true,
  },
];

export function S5LivingWiki() {
  const sectionRef = useRef<HTMLElement>(null);
  const barsRef = useRef<(SVGRectElement | null)[]>([]);
  const labelsRef = useRef<(HTMLDivElement | null)[]>([]);

  useGSAP(
    () => {
      // Animate bars growing up
      barsRef.current.forEach((bar, i) => {
        if (!bar) return;
        const targetHeight = eras[i].height;
        gsap.fromTo(
          bar,
          { attr: { height: 0, y: 200 } },
          {
            attr: { height: targetHeight, y: 200 - targetHeight },
            duration: 0.8,
            ease: "power3.out",
            delay: i * 0.18,
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 72%",
              once: true,
            },
          },
        );
      });

      // Animate labels fading in
      labelsRef.current.forEach((label, i) => {
        if (!label) return;
        gsap.from(label, {
          opacity: 0,
          y: 10,
          duration: 0.5,
          delay: i * 0.18 + 0.6,
          ease: "power2.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 72%",
          },
        });
      });
    },
    { scope: sectionRef },
  );

  return (
    <section
      id="living-wiki"
      ref={sectionRef}
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Living Wiki</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Một Wiki sống — nơi kiến thức không bao giờ mất
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Kế thừa kho kinh nghiệm từ các thế hệ Zalopay trước — thay vì mỗi người mới lại reset
          về zero.
        </p>

        {/* SVG timeline diagram */}
        <div data-reveal className="mx-auto max-w-3xl">
          <div className="glass-panel relative overflow-hidden rounded-2xl p-8">
            {/* Background grid lines */}
            <svg
              className="pointer-events-none absolute inset-0 h-full w-full"
              preserveAspectRatio="none"
              aria-hidden
            >
              {[25, 50, 75].map((y) => (
                <line
                  key={y}
                  x1="0"
                  y1={`${y}%`}
                  x2="100%"
                  y2={`${y}%`}
                  stroke="rgba(148,163,184,0.06)"
                  strokeWidth="1"
                />
              ))}
            </svg>

            {/* Main SVG diagram */}
            <svg
              viewBox="0 0 480 220"
              className="w-full"
              style={{ overflow: "visible" }}
            >
              {/* Baseline */}
              <line
                x1="20"
                y1="200"
                x2="460"
                y2="200"
                stroke="rgba(148,163,184,0.3)"
                strokeWidth="1.5"
              />

              {/* Era bars */}
              {eras.map((era, i) => {
                const x = 60 + i * 140;
                const barWidth = 80;
                return (
                  <g key={i}>
                    <rect
                      ref={(el) => (barsRef.current[i] = el)}
                      x={x}
                      y={200}
                      width={barWidth}
                      height={0}
                      rx="6"
                      fill={`rgba(0,104,255,${era.opacity})`}
                    />
                    {/* Agent crown on last bar */}
                    {era.isTop && (
                      <g>
                        <circle
                          cx={x + barWidth / 2}
                          cy={200 - era.height - 20}
                          r={16}
                          fill="rgba(0,104,255,0.2)"
                          stroke="rgba(0,104,255,0.6)"
                          strokeWidth="1.5"
                        />
                        <text
                          x={x + barWidth / 2}
                          y={200 - era.height - 15}
                          textAnchor="middle"
                          fontSize="14"
                          fill="#0068ff"
                        >
                          ✦
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}

              {/* Arrow at end of baseline */}
              <polygon
                points="456,196 466,200 456,204"
                fill="rgba(148,163,184,0.4)"
              />
            </svg>

            {/* Era labels below chart */}
            <div className="mt-4 grid grid-cols-3 gap-2">
              {eras.map((era, i) => (
                <div
                  key={i}
                  ref={(el) => (labelsRef.current[i] = el)}
                  className="text-center"
                >
                  <div
                    className="text-sm font-bold"
                    style={{ color: `rgba(0,104,255,${era.opacity + 0.1})` }}
                  >
                    {era.label}
                  </div>
                  <div
                    className="mt-1 text-sm leading-tight"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    {era.sublabel}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Caption */}
        <p
          data-reveal
          className="mt-8 text-center text-sm italic"
          style={{ color: "var(--color-text-muted)" }}
        >
          Càng nhiều team đóng góp kiến thức → agent càng hiểu sâu hơn về Zalopay
        </p>
      </div>
    </section>
  );
}
