import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { ChevronDown, Play } from "lucide-react";

export function S0Hero() {
  const sectionRef = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      gsap.from("[data-hero-reveal]", {
        opacity: 0,
        y: 36,
        duration: 0.8,
        ease: "power3.out",
        stagger: 0.13,
      });
    },
    { scope: sectionRef },
  );

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section
      id="hero"
      ref={sectionRef}
      data-pitch-section
      className="relative flex min-h-screen flex-col items-center justify-center px-4 py-24 text-center sm:px-6"
    >
      {/* Glow accent */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
        aria-hidden
      >
        <div
          className="h-[480px] w-[640px] rounded-full blur-3xl opacity-20"
          style={{ background: "radial-gradient(ellipse, var(--color-brand) 0%, transparent 70%)" }}
        />
      </div>

      <div className="relative z-10 max-w-4xl">
        {/* Badge */}
        <div data-hero-reveal className="mb-6 inline-flex items-center gap-2">
          <span
            className="rounded-full border px-3 py-1 text-sm font-semibold tracking-wider uppercase"
            style={{
              borderColor: "var(--color-border-brand)",
              color: "var(--color-brand)",
              background: "var(--color-brand-muted)",
            }}
          >
            Zalopay Internal Knowledge Agent
          </span>
        </div>

        {/* Headline */}
        <h1
          data-hero-reveal
          className="text-gradient-brand mb-6 font-display font-extrabold leading-[1.25] tracking-tight"
          style={{ fontSize: "clamp(2.8rem, 8vw, 6rem)" }}
        >
          Knowledge stays.
          <br />
          Legacy grows.
        </h1>

        {/* Sub-headline */}
        <p
          data-hero-reveal
          className="mx-auto mb-12 max-w-2xl text-lg leading-relaxed sm:text-xl"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Nền tảng kiến thức sống cho Zalopay — giúp mọi team{" "}
          <span style={{ color: "var(--color-text-primary)" }}>quyết định nhanh hơn</span>,{" "}
          <span style={{ color: "var(--color-text-primary)" }}>nhất quán hơn</span>, và kế thừa
          kinh nghiệm tích lũy qua từng thế hệ.
        </p>

        {/* CTAs */}
        <div data-hero-reveal className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <button
            onClick={() => scrollTo("problem")}
            className="inline-flex items-center gap-2 rounded-xl px-7 py-3.5 text-sm font-semibold transition-all duration-200"
            style={{
              background: "var(--color-brand)",
              color: "#fff",
              boxShadow: "0 0 24px var(--color-brand-glow)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--color-brand-hover)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--color-brand)";
            }}
          >
            Xem câu chuyện <ChevronDown size={16} />
          </button>
          <button
            onClick={() => scrollTo("demo")}
            className="inline-flex items-center gap-2 rounded-xl border px-7 py-3.5 text-sm font-semibold transition-all duration-200"
            style={{
              borderColor: "var(--color-border-strong)",
              color: "var(--color-text-primary)",
              background: "var(--color-bg-glass)",
            }}
          >
            <Play size={15} /> Xem demo ngay
          </button>
        </div>
      </div>

      {/* Scroll hint */}
      <div
        data-hero-reveal
        className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce"
        style={{ color: "var(--color-text-muted)" }}
      >
        <ChevronDown size={20} />
      </div>
    </section>
  );
}
