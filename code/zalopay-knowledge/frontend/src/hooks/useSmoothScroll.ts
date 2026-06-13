import { useRef } from "react";
import { CHAT_DURATION, CHAT_EASE, gsap, REDUCED_MOTION_QUERY, useGSAP } from "@/lib/gsap";

/**
 * Smoothly scrolls a chat container to the bottom when dependencies change.
 * Falls back to instant scroll when prefers-reduced-motion is enabled.
 */
export function useSmoothScroll(deps: unknown[]) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const container = containerRef.current;
      if (!container) return;

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        const target = container.scrollHeight - container.clientHeight;
        if (context.conditions?.reduceMotion) {
          container.scrollTop = target;
          return;
        }
        gsap.to(container, {
          scrollTop: target,
          duration: CHAT_DURATION.scroll,
          ease: CHAT_EASE.scroll,
          overwrite: true,
        });
      });

      return () => mm.revert();
    },
    { dependencies: deps, scope: containerRef },
  );

  return containerRef;
}
