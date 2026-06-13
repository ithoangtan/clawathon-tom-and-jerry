import type { ReactNode } from "react";
import { useRef } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { LanguageSwitcher } from "@/components/ui/LanguageSwitcher";
import { LocaleEffect } from "@/components/layout/LocaleEffect";
import { TutorialHelpButton } from "@/components/layout/TutorialHelpButton";
import {
  Brain,
  Database,
  LayoutDashboard,
  MessageSquare,
  Plus,
  Settings,
  Sparkles,
} from "@/components/ui/icons";
import { runBrandPulse, runHeroFloat, runNavStagger, useGSAP } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { classNames } from "@/lib/format";
import { useHealth } from "@/hooks/useHealth";
import { useUserStore } from "@/store/userStore";
import { useSessionStore } from "@/store/sessionStore";
import { NavLink } from "react-router-dom";

const NAV_ICONS = {
  "/": MessageSquare,
  "/dashboard": LayoutDashboard,
  "/admin": Database,
  "/settings": Settings,
} as const;

function BrandMark() {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const el = ref.current;
      if (!el) return;
      const cleanups = [runBrandPulse(el), runHeroFloat(el)];
      return () => cleanups.forEach((fn) => fn());
    },
    { scope: ref },
  );

  return (
    <div
      ref={ref}
      className="perspective-scene relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-accent text-white shadow-glow"
      aria-hidden
    >
      <Brain size="md" className="relative z-10" strokeWidth={2.25} />
      <Sparkles size="xs" className="absolute -right-0.5 -top-0.5 z-20 text-accent opacity-90" />
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-brand/20 to-accent/20 blur-sm" />
    </div>
  );
}

export function Header() {
  const locale = useUserStore((s) => s.locale);
  const requestNewSession = useSessionStore((s) => s.requestNewSession);
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
              <span className="text-gradient-brand font-medium">{t("knowledgeAgent", locale)}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <LanguageSwitcher className="hidden sm:inline-flex" />
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
          <TutorialHelpButton />
          <Button variant="ghost" onClick={requestNewSession} className="hidden sm:inline-flex">
            <Plus size="sm" />
            {t("newSession", locale)}
          </Button>
        </div>
      </div>
    </header>
  );
}

export function Nav() {
  const locale = useUserStore((s) => s.locale);
  const navRef = useRef<HTMLDivElement>(null);

  const links: { to: keyof typeof NAV_ICONS; label: string; end?: boolean }[] = [
    { to: "/", label: t("navChat", locale), end: true },
    { to: "/dashboard", label: t("navDashboard", locale) },
    { to: "/admin", label: t("navAdmin", locale) },
    { to: "/settings", label: t("navSettings", locale) },
  ];

  useGSAP(
    () => {
      const pills = navRef.current?.querySelectorAll("[data-nav-pill]");
      if (!pills?.length) return;
      return runNavStagger(pills);
    },
    { scope: navRef },
  );

  return (
    <nav
      className="relative z-20 border-b border-border glass-panel"
      aria-label={t("navAriaLabel", locale)}
    >
      <div ref={navRef} className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-2 sm:px-6">
        <div className="flex flex-1 gap-1">
          {links.map((link) => {
            const NavIcon = NAV_ICONS[link.to];
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                data-nav-pill
                data-tour={link.to === "/dashboard" ? "nav-dashboard" : undefined}
                className={({ isActive }) =>
                  classNames("nav-pill", isActive && "nav-pill-active")
                }
              >
                <NavIcon size="sm" className="opacity-80" />
                {link.label}
              </NavLink>
            );
          })}
        </div>
        <LanguageSwitcher className="sm:hidden" />
      </div>
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const locale = useUserStore((s) => s.locale);

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden">
      <LocaleEffect />
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
