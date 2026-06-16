export function S10Closing() {
  return (
    <section
      id="closing"
      data-pitch-section
      className="relative flex min-h-screen flex-col items-center justify-center px-4 py-32 text-center sm:px-6"
    >
      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
        aria-hidden
      >
        <div
          className="h-[600px] w-[800px] rounded-full blur-3xl opacity-15"
          style={{
            background:
              "radial-gradient(ellipse, var(--color-accent) 0%, var(--color-brand) 40%, transparent 70%)",
          }}
        />
      </div>

      <div className="relative z-10 max-w-4xl">
        {/* Quote */}
        <blockquote data-reveal>
          <p
            className="text-gradient-brand mb-8 font-display font-extrabold leading-[1.1] tracking-tight"
            style={{ fontSize: "clamp(2.4rem, 6vw, 5rem)" }}
          >
            "Knowledge stays.
            <br />
            Legacy grows."
          </p>
        </blockquote>

        <p
          data-reveal
          className="mx-auto mb-12 max-w-2xl text-lg leading-relaxed sm:text-xl"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Khi knowledge càng nhiều, khi workflow hỗ trợ được nhiều team hơn — agent càng hiểu sâu
          hơn.{" "}
          <span style={{ color: "var(--color-text-primary)" }}>
            Không chỉ Zalopay hôm nay, mà cả Zalopay của nhiều năm tới.
          </span>
        </p>

        <div
          data-reveal
          className="inline-flex items-center gap-3 rounded-2xl border px-6 py-4"
          style={{
            borderColor: "var(--color-border-brand)",
            background: "var(--color-brand-muted)",
          }}
        >
          <div
            className="h-2 w-2 animate-pulse rounded-full"
            style={{ background: "var(--color-brand)" }}
          />
          <span className="text-sm font-semibold" style={{ color: "var(--color-brand)" }}>
            Risk review chỉ là workflow đầu tiên
          </span>
        </div>

        <div data-reveal className="mt-8">
          <a
            href="/"
            className="inline-flex items-center gap-2 rounded-xl px-8 py-4 text-base font-semibold transition-all duration-200"
            style={{
              background: "var(--color-brand)",
              color: "#fff",
              boxShadow: "0 0 32px var(--color-brand-glow)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--color-brand-hover)";
              (e.currentTarget as HTMLElement).style.boxShadow = "0 0 48px var(--color-brand-glow)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--color-brand)";
              (e.currentTarget as HTMLElement).style.boxShadow = "0 0 32px var(--color-brand-glow)";
            }}
          >
            Thử nghiệm ngay →
          </a>
        </div>

        {/* Footer attribution */}
        <p
          data-reveal
          className="mt-16 text-sm"
          style={{ color: "var(--color-text-muted)" }}
        >
          Built with ❤ at Clawathon — Zalopay Internal Knowledge Agent
        </p>
      </div>
    </section>
  );
}
