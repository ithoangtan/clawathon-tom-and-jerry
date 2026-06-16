import { t } from "@/lib/i18n";
import {
  attachHoverLift,
  CHAT_DURATION,
  CHAT_EASE,
  gsap,
  REDUCED_MOTION_QUERY,
  runStaggerEnter,
  useGSAP,
} from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";
import type { ReactNode } from "react";
import { useRef } from "react";

interface ChatEmptyStateProps {
  examples: string[];
  onExampleClick: (question: string) => void;
  children: ReactNode;
  belowInput?: ReactNode;
}

export function ChatEmptyState({ examples, onExampleClick, children, belowInput }: ChatEmptyStateProps) {
  const locale = useUserStore((s) => s.locale);
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const container = containerRef.current;
      if (!container) return;

      const hero = container.querySelector("[data-empty-hero]");
      const inputSlot = container.querySelector("[data-empty-input]");
      const exampleItems = container.querySelectorAll("[data-example-question]");
      const cleanups: Array<() => void> = [];

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion) {
          if (hero) gsap.set(hero, { opacity: 1, y: 0 });
          if (inputSlot) gsap.set(inputSlot, { opacity: 1, y: 0 });
          gsap.set(exampleItems, { opacity: 1, y: 0 });
          return;
        }

        if (hero) {
          gsap.from(hero, {
            opacity: 0,
            y: 12,
            duration: CHAT_DURATION.message,
            ease: CHAT_EASE.enter,
          });
        }

        if (inputSlot) {
          gsap.from(inputSlot, {
            opacity: 0,
            y: 16,
            scale: 0.98,
            duration: CHAT_DURATION.message,
            ease: CHAT_EASE.enter,
            delay: 0.08,
          });
        }

        if (exampleItems.length > 0) {
          cleanups.push(runStaggerEnter(exampleItems));
        }

        exampleItems.forEach((item) => {
          cleanups.push(attachHoverLift(item as HTMLElement, { y: -1, scale: 1.02 }));
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
      className="flex w-full max-w-2xl flex-col items-center text-center"
    >
      <div data-empty-hero className="max-w-md">
        <h2 className="text-gradient-brand text-xl font-semibold tracking-tight sm:text-2xl">
          {t("emptyChatTitle", locale)}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-content-secondary">
          {t("emptyChat", locale)}
        </p>
      </div>

      <div data-empty-input className="mt-6 w-full">
        {children}
        {belowInput ? <div className="mt-2.5 space-y-2 text-left">{belowInput}</div> : null}
      </div>

      {examples.length > 0 && (
        <div className="mt-5 w-full" data-tour="example-questions">
          <p className="text-[11px] font-medium text-content-muted">
            {t("exampleQuestions", locale)}
          </p>
          <ul className="mt-2.5 flex flex-wrap justify-center gap-2" role="list">
            {examples.map((q) => (
              <li key={q} data-example-question>
                <button
                  type="button"
                  className="chat-prompt-ghost focus-visible:ring-2 focus-visible:ring-brand"
                  onClick={() => onExampleClick(q)}
                >
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
