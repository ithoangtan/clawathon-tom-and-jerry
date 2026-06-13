import { useRef } from "react";
import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { t } from "@/lib/i18n";
import {
  gsap,
  REDUCED_MOTION_QUERY,
  runMessageEnter,
  runThinkingGlow,
  useGSAP,
} from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";

export function TypingIndicator({ statusText }: { statusText?: string | null }) {
  const locale = useUserStore((s) => s.locale);
  const rowRef = useRef<HTMLDivElement>(null);
  const avatarWrapRef = useRef<HTMLDivElement>(null);
  const barsRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const row = rowRef.current;
      const avatarWrap = avatarWrapRef.current;
      const bars = barsRef.current;
      if (!row) return;

      const cleanupEnter = runMessageEnter(row, "assistant");
      const cleanups: Array<() => void> = [cleanupEnter];

      if (avatarWrap) {
        cleanups.push(runThinkingGlow(avatarWrap));
      }

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion || !bars) return;
        const barEls = bars.querySelectorAll("[data-typing-bar]");
        gsap.fromTo(
          barEls,
          { scaleY: 0.3, opacity: 0.4 },
          {
            scaleY: 1,
            opacity: 1,
            duration: 0.45,
            ease: "power1.inOut",
            stagger: { each: 0.12, repeat: -1, yoyo: true },
            transformOrigin: "center bottom",
          },
        );
      });

      return () => {
        cleanups.forEach((fn) => fn());
        mm.revert();
      };
    },
    { scope: rowRef, dependencies: [] },
  );

  const label = statusText ?? t("assistantName", locale);

  return (
    <div ref={rowRef} className="flex gap-3" role="status" aria-live="polite">
      <div ref={avatarWrapRef} className="rounded-full">
        <ChatAvatar role="assistant" className="avatar-assistant-glow" />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <span className="text-xs font-medium text-content-secondary">{label}</span>
        <div className="typing-shell">
          <span className="sr-only">{t("sending", locale)}</span>
          <div ref={barsRef} className="typing-wave" aria-hidden>
            <span data-typing-bar className="typing-bar" />
            <span data-typing-bar className="typing-bar" />
            <span data-typing-bar className="typing-bar" />
            <span data-typing-bar className="typing-bar" />
          </div>
          <div className="typing-shimmer" aria-hidden />
        </div>
      </div>
    </div>
  );
}
