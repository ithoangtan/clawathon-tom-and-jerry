import { t } from "@/lib/i18n";
import {
  attachHoverLift,
  CHAT_DURATION,
  CHAT_EASE,
  gsap,
  REDUCED_MOTION_QUERY,
  runEmptyParallax,
  runHeroOrb,
  runStaggerEnter,
  useGSAP,
} from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";
import { useRef } from "react";

interface ChatEmptyStateProps {
  examples: string[];
  onExampleClick: (question: string) => void;
}

export function ChatEmptyState({ examples, onExampleClick }: ChatEmptyStateProps) {
  const locale = useUserStore((s) => s.locale);
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const container = containerRef.current;
      if (!container) return;

      const hero = container.querySelector("[data-empty-hero]");
      const orbRing = container.querySelector("[data-hero-orb]");
      const parallaxLayers = container.querySelectorAll("[data-parallax]");
      const exampleItems = container.querySelectorAll("[data-example-question]");
      const cleanups: Array<() => void> = [];

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion) {
          if (hero) gsap.set(hero, { opacity: 1, y: 0, scale: 1 });
          gsap.set(exampleItems, { opacity: 1, y: 0 });
          return;
        }

        if (hero) {
          gsap.from(hero, {
            opacity: 0,
            y: 24,
            scale: 0.9,
            duration: CHAT_DURATION.message,
            ease: CHAT_EASE.enter,
          });
        }

        if (orbRing) {
          cleanups.push(runHeroOrb(orbRing as HTMLElement));
        }

        if (parallaxLayers.length > 0) {
          cleanups.push(runEmptyParallax([...parallaxLayers]));
        }

        if (exampleItems.length > 0) {
          cleanups.push(runStaggerEnter(exampleItems));
        }

        exampleItems.forEach((item) => {
          const btn = item.querySelector("button");
          if (btn) cleanups.push(attachHoverLift(btn as HTMLElement, { y: -3, scale: 1.01 }));
        });
      });

      return () => {
        cleanups.forEach((fn) => fn());
        mm.revert();
      };
    },
    { scope: containerRef },
  );

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col items-center justify-center px-4 py-16 text-center"
    >
      <div
        data-parallax
        className="pointer-events-none absolute left-1/4 top-8 h-32 w-32 rounded-full bg-brand/5 blur-3xl"
        aria-hidden
      />
      <div
        data-parallax
        className="pointer-events-none absolute bottom-12 right-1/4 h-40 w-40 rounded-full bg-dept-grow/10 blur-3xl"
        aria-hidden
      />

      <div data-empty-hero className="chat-hero-orb mb-6 h-[4.5rem] w-[4.5rem]">
        <div data-hero-orb className="absolute inset-[-6px] rounded-2xl" aria-hidden />
        <div className="chat-hero-core h-14 w-14 text-xl">ZP</div>
      </div>

      <h2 className="text-gradient-brand text-2xl font-semibold tracking-tight">
        {t("emptyChatTitle", locale)}
      </h2>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-content-secondary">
        {t("emptyChat", locale)}
      </p>

      <div className="mt-10 w-full max-w-lg">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-content-muted">
          {t("exampleQuestions", locale)}
        </p>
        <ul className="space-y-2.5" role="list">
          {examples.map((q) => (
            <li key={q} data-example-question>
              <button
                type="button"
                className="chat-prompt-chip text-content-primary focus-visible:ring-2 focus-visible:ring-brand"
                onClick={() => onExampleClick(q)}
              >
                <span className="mr-2 text-brand" aria-hidden>
                  →
                </span>
                {q}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
