import { useEffect, useState } from "react";
import { Menu, Moon, Sun, X } from "lucide-react";
import { useUserStore } from "@/store/userStore";

const navItems = [
  { id: "hero", label: "Intro" },
  { id: "problem", label: "Problem" },
  { id: "demo", label: "Demo ⭐" },
  { id: "why-now", label: "Why Now" },
  { id: "solution", label: "Platform" },
  { id: "living-wiki", label: "Vision" },
  { id: "impact", label: "Impact" },
  { id: "governance", label: "Governance" },
  { id: "mvp-prod", label: "MVP → Prod" },
  { id: "next-steps", label: "Next Steps" },
  { id: "closing", label: "Closing" },
];

export function PitchNav() {
  const [active, setActive] = useState("hero");
  const [open, setOpen] = useState(false);
  const theme = useUserStore((s) => s.theme);
  const setTheme = useUserStore((s) => s.setTheme);
  const isDark = theme === "dark";

  useEffect(() => {
    const sections = document.querySelectorAll("[data-pitch-section]");
    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.3) {
            setActive(entry.target.id);
          }
        });
      },
      { threshold: 0.3 },
    );

    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setOpen(false);
  };

  const btnStyle: React.CSSProperties = {
    background: "var(--color-bg-glass-strong)",
    border: "1px solid var(--color-border-strong)",
    backdropFilter: "blur(12px)",
    color: "var(--color-text-primary)",
  };

  return (
    <>
      {/* Theme toggle — always visible top-left */}
      <button
        onClick={() => setTheme(isDark ? "light" : "dark")}
        className="fixed left-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-full transition-colors duration-200"
        style={btnStyle}
        aria-label="Toggle theme"
      >
        {isDark ? <Sun size={15} /> : <Moon size={15} />}
      </button>

      {/* Mobile toggle */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed right-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-full sm:hidden"
        style={btnStyle}
        aria-label="Toggle navigation"
      >
        {open ? <X size={16} /> : <Menu size={16} />}
      </button>

      {/* Desktop: vertical pill on right */}
      <nav
        className="fixed right-4 top-1/2 z-40 hidden -translate-y-1/2 flex-col gap-1.5 sm:flex"
        aria-label="Pitch sections"
      >
        {navItems.map((item) => {
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="group relative flex items-center justify-end"
              title={item.label}
            >
              {/* Label tooltip on hover */}
              <span
                className="pointer-events-none absolute right-6 whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium opacity-0 transition-opacity duration-200 group-hover:opacity-100"
                style={{
                  background: "var(--color-bg-glass-strong)",
                  color: "var(--color-text-primary)",
                  border: "1px solid var(--color-border)",
                  backdropFilter: "blur(8px)",
                }}
              >
                {item.label}
              </span>
              {/* Dot indicator */}
              <div
                className="h-2 w-2 rounded-full transition-all duration-200"
                style={{
                  background: isActive ? "var(--color-brand)" : "var(--color-border-strong)",
                  boxShadow: isActive ? "0 0 6px var(--color-brand-glow)" : "none",
                  transform: isActive ? "scale(1.4)" : "scale(1)",
                }}
              />
            </button>
          );
        })}
      </nav>

      {/* Mobile: overlay menu */}
      {open && (
        <div
          className="fixed inset-0 z-40 flex items-start justify-end pt-16 pr-4 sm:hidden"
          onClick={() => setOpen(false)}
        >
          <nav
            className="flex flex-col gap-1 overflow-hidden rounded-xl p-2"
            style={{
              background: "var(--color-bg-glass-strong)",
              border: "1px solid var(--color-border-strong)",
              backdropFilter: "blur(20px)",
              minWidth: 160,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {navItems.map((item) => {
              const isActive = active === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollTo(item.id)}
                  className="rounded-lg px-3 py-2 text-left text-xs font-medium transition-colors duration-150"
                  style={{
                    background: isActive ? "var(--color-brand-muted)" : "transparent",
                    color: isActive ? "var(--color-brand)" : "var(--color-text-secondary)",
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      )}
    </>
  );
}
