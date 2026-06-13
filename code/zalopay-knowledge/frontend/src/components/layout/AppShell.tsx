import type { ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { t } from "@/lib/i18n";
import { classNames } from "@/lib/format";
import { useHealth } from "@/hooks/useHealth";
import { useUserStore } from "@/store/userStore";
import { NavLink } from "react-router-dom";

function BrandMark() {
  return (
    <div
      className="relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-accent font-bold text-sm text-white shadow-glow"
      aria-hidden
    >
      <span className="relative z-10">ZP</span>
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-brand/20 to-accent/20 blur-sm" />
    </div>
  );
}

export function Header() {
  const locale = useUserStore((s) => s.locale);
  const newSession = useUserStore((s) => s.newSession);
  const { health } = useHealth();

  const indexReady = health?.index_ready ?? false;

  return (
    <header className="relative z-20 glass-panel-strong border-b border-border">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <BrandMark />
          <div className="min-w-0">
            <h1 className="truncate text-base font-bold tracking-tight text-content-primary sm:text-lg">
              {t("appTitle", locale)}
            </h1>
            <p className="hidden truncate text-xs text-content-secondary sm:block">
              {t("appSubtitle", locale)}
              <span className="mx-1.5 text-content-muted" aria-hidden>
                ·
              </span>
              <span className="text-gradient-brand font-medium">Knowledge Agent</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Badge tone={indexReady ? "success" : "warning"}>
            <span
              className={classNames(
                "mr-1.5 inline-block h-1.5 w-1.5 rounded-full glow-dot",
                indexReady ? "bg-success text-success" : "bg-warning text-warning",
              )}
              aria-hidden
            />
            {indexReady ? t("healthHealthy", locale) : t("healthIndexPending", locale)}
          </Badge>
          <Button variant="ghost" onClick={newSession} className="hidden sm:inline-flex">
            {t("newSession", locale)}
          </Button>
        </div>
      </div>
    </header>
  );
}

export function Nav() {
  const locale = useUserStore((s) => s.locale);

  const links = [
    { to: "/", label: t("navChat", locale), end: true },
    { to: "/dashboard", label: t("navDashboard", locale) },
    { to: "/settings", label: t("navSettings", locale) },
  ];

  return (
    <nav
      className="relative z-20 border-b border-border glass-panel"
      aria-label="Main navigation"
    >
      <div className="mx-auto flex max-w-6xl gap-1 px-4 py-2 sm:px-6">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              classNames("nav-pill", isActive && "nav-pill-active")
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const locale = useUserStore((s) => s.locale);

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden">
      <div className="pointer-events-none fixed inset-0 mesh-bg" aria-hidden />
      <div className="pointer-events-none fixed inset-0 grid-overlay opacity-40" aria-hidden />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:text-white focus:shadow-glow"
      >
        {t("skipToContent", locale)}
      </a>

      <Header />
      <Nav />

      <main
        id="main-content"
        className="relative z-10 flex min-h-0 flex-1 flex-col"
      >
        {children}
      </main>
    </div>
  );
}
