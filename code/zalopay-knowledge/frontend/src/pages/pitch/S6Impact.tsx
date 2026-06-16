import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { Timer, TrendingDown } from "lucide-react";
import { SectionLabel } from "./S1Problem";

export function S6Impact() {
  const sectionRef = useRef<HTMLElement>(null);
  const minutesRef = useRef<HTMLSpanElement>(null);
  const percentRef = useRef<HTMLSpanElement>(null);

  useGSAP(
    () => {
      // Count-up animations
      const countUpTrigger = {
        trigger: sectionRef.current,
        start: "top 72%",
        once: true,
      };

      gsap.fromTo(
        minutesRef.current,
        { innerText: 0 },
        {
          innerText: 15,
          duration: 1.4,
          ease: "power2.out",
          snap: { innerText: 1 },
          scrollTrigger: countUpTrigger,
        },
      );

      gsap.fromTo(
        percentRef.current,
        { innerText: 0 },
        {
          innerText: 50,
          duration: 1.6,
          ease: "power2.out",
          snap: { innerText: 1 },
          scrollTrigger: countUpTrigger,
        },
      );
    },
    { scope: sectionRef },
  );

  return (
    <section
      id="impact"
      ref={sectionRef}
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Impact</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Tiết kiệm thời gian cho cả hai phía
        </h2>
        <p
          data-reveal
          className="mb-14 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Không phải thay thế con người — mà để con người tập trung vào những quyết định thật sự
          cần judgment.
        </p>

        {/* Big number cards */}
        <div className="mb-10 grid gap-6 sm:grid-cols-2">
          {/* Card 1: Time */}
          <div data-reveal className="glass-panel rounded-2xl p-8">
            <div className="mb-2 flex items-start justify-between">
              <div>
                <div
                  className="mb-1 flex items-end gap-1 font-display font-extrabold leading-[1.1]"
                  style={{ color: "var(--color-brand)" }}
                >
                  <span
                    className="text-gradient-brand"
                    style={{ fontSize: "clamp(3rem, 8vw, 5rem)" }}
                  >
                    ~<span ref={minutesRef}>15</span>
                  </span>
                  <span
                    className="mb-2 text-2xl"
                    style={{ color: "var(--color-brand)" }}
                  >
                    phút
                  </span>
                </div>
                <p
                  className="text-sm font-semibold"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  nhận phản hồi từ AI review
                </p>
              </div>
              <div
                className="mt-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl"
                style={{ background: "var(--color-brand-muted)" }}
              >
                <Timer size={20} style={{ color: "var(--color-brand)" }} />
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
              Thay vì chờ nhiều ngày không biết kết quả. HIGH risk → biết ngay để sửa; LOW risk →
              reviewer nhận notify để approve.
            </p>
            <div
              className="mt-4 rounded-lg px-3 py-2 text-sm"
              style={{
                background: "var(--color-brand-muted)",
                color: "var(--color-brand)",
              }}
            >
              * Ví dụ đo với Risk Review workflow
            </div>
          </div>

          {/* Card 2: Automation */}
          <div data-reveal className="glass-panel rounded-2xl p-8">
            <div className="mb-2 flex items-start justify-between">
              <div>
                <div
                  className="mb-1 flex items-end gap-1 font-display font-extrabold leading-[1.1]"
                >
                  <span
                    className="text-gradient-brand"
                    style={{ fontSize: "clamp(3rem, 8vw, 5rem)" }}
                  >
                    ~<span ref={percentRef}>50</span>%
                  </span>
                </div>
                <p
                  className="text-sm font-semibold"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  ticket LOW risk — reviewer chỉ cần approve
                </p>
              </div>
              <div
                className="mt-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl"
                style={{ background: "var(--color-accent-muted)" }}
              >
                <TrendingDown size={20} style={{ color: "var(--color-accent)" }} />
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
              Những ticket lặp lại cùng cấu trúc suy nghĩ được xử lý ở vòng đầu. Con người chỉ
              handle exception và quyết định thật sự cần judgment.
            </p>
          </div>
        </div>

        {/* Quote */}
        <blockquote
          data-reveal
          className="rounded-2xl border-l-4 px-6 py-5"
          style={{
            borderColor: "var(--color-accent)",
            background: "var(--color-accent-muted)",
          }}
        >
          <p className="text-sm italic leading-relaxed" style={{ color: "var(--color-text-primary)" }}>
            "Tiết kiệm thời gian cho cả người tạo ticket lẫn người đi review. Risk team tập trung
            vào những quyết định thật sự cần con người."
          </p>
        </blockquote>
      </div>
    </section>
  );
}
