import gsap from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

export { gsap, useGSAP };

export const CHAT_EASE = {
  enter: "power3.out",
  scroll: "power2.inOut",
  micro: "power2.out",
  send: "back.out(1.7)",
  elastic: "elastic.out(1, 0.6)",
  glow: "sine.inOut",
} as const;

export const CHAT_DURATION = {
  message: 0.52,
  scroll: 0.55,
  micro: 0.24,
  stagger: 0.08,
  pulse: 0.35,
} as const;

export const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

export type MessageRole = "user" | "assistant";

function withReducedMotion(
  cb: (reduceMotion: boolean) => void | (() => void),
): () => void {
  const mm = gsap.matchMedia();
  mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
    const reduceMotion = Boolean(context.conditions?.reduceMotion);
    return cb(reduceMotion);
  });
  return () => mm.revert();
}

/** Entrance tween for a single chat row; respects prefers-reduced-motion. */
export function runMessageEnter(
  el: HTMLElement,
  role: MessageRole,
): () => void {
  const mm = gsap.matchMedia();
  mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
    if (context.conditions?.reduceMotion) {
      gsap.set(el, { opacity: 1, x: 0, y: 0, scale: 1, filter: "none" });
      return;
    }
    gsap.from(el, {
      opacity: 0,
      x: role === "user" ? 18 : -18,
      y: role === "user" ? 12 : 20,
      scale: 0.96,
      filter: "blur(6px)",
      duration: CHAT_DURATION.message,
      ease: CHAT_EASE.enter,
      transformOrigin: role === "user" ? "bottom right" : "bottom left",
      clearProps: "filter",
    });
  }, el);
  return () => mm.revert();
}

/** Staggered entrance for a NodeList of elements. */
export function runStaggerEnter(elements: NodeListOf<Element> | Element[]): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) {
      gsap.set(elements, { opacity: 1, y: 0, scale: 1 });
      return;
    }
    gsap.from(elements, {
      opacity: 0,
      y: 16,
      scale: 0.98,
      duration: CHAT_DURATION.message,
      ease: CHAT_EASE.enter,
      stagger: CHAT_DURATION.stagger,
    });
  });
}

/** Subtle parallax drift on empty-state decorative layers. */
export function runEmptyParallax(layers: Element[]): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion || layers.length === 0) return;

    const tweens = layers.map((layer, i) =>
      gsap.to(layer, {
        y: (i + 1) * -6,
        x: i % 2 === 0 ? 4 : -4,
        duration: 4 + i * 1.2,
        ease: CHAT_EASE.glow,
        repeat: -1,
        yoyo: true,
      }),
    );

    return () => {
      tweens.forEach((tween) => tween.kill());
    };
  });
}

/** Pulse the send button when a message is dispatched. */
export function runSendPulse(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.fromTo(
      el,
      { scale: 1 },
      {
        scale: 1.15,
        duration: 0.12,
        ease: "power2.out",
        yoyo: true,
        repeat: 1,
      },
    );
    return () => tween.kill();
  });
}

/** Attach hover lift to interactive cards (citations, example prompts). */
export function attachHoverLift(
  el: HTMLElement,
  options?: { y?: number; scale?: number },
): () => void {
  const y = options?.y ?? -2;
  const scale = options?.scale ?? 1.01;

  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;

    const onEnter = () => {
      gsap.to(el, {
        y,
        scale,
        duration: CHAT_DURATION.micro,
        ease: CHAT_EASE.micro,
        overwrite: "auto",
      });
    };
    const onLeave = () => {
      gsap.to(el, {
        y: 0,
        scale: 1,
        duration: CHAT_DURATION.micro,
        ease: CHAT_EASE.micro,
        overwrite: "auto",
      });
    };

    el.addEventListener("mouseenter", onEnter);
    el.addEventListener("mouseleave", onLeave);
    el.addEventListener("focusin", onEnter);
    el.addEventListener("focusout", onLeave);

    return () => {
      el.removeEventListener("mouseenter", onEnter);
      el.removeEventListener("mouseleave", onLeave);
      el.removeEventListener("focusin", onEnter);
      el.removeEventListener("focusout", onLeave);
    };
  });
}

/** Brief success pop when copy-to-clipboard succeeds. */
export function runCopySuccess(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.fromTo(
      el,
      { scale: 1 },
      { scale: 1.12, duration: 0.15, ease: CHAT_EASE.send, yoyo: true, repeat: 1 },
    );
    return () => tween.kill();
  });
}

/** Animate a chip or button selection toggle. */
export function runChipPop(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.fromTo(
      el,
      { scale: 0.92 },
      { scale: 1, duration: 0.38, ease: CHAT_EASE.send },
    );
    return () => tween.kill();
  });
}

/** Pulsing glow ring for the assistant avatar while thinking. */
export function runThinkingGlow(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.to(el, {
      boxShadow: "0 0 0 4px rgba(0, 104, 255, 0.25), 0 0 20px rgba(0, 104, 255, 0.35)",
      duration: 0.9,
      ease: CHAT_EASE.glow,
      repeat: -1,
      yoyo: true,
    });
    return () => tween.kill();
  });
}

/** Orbital rotation for empty-state hero decoration. */
export function runHeroOrb(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.to(el, {
      rotation: 360,
      duration: 24,
      ease: "none",
      repeat: -1,
    });
    return () => tween.kill();
  });
}

/** Gentle float for hero core / brand mark. */
export function runHeroFloat(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.to(el, {
      y: -6,
      duration: 2.8,
      ease: CHAT_EASE.glow,
      repeat: -1,
      yoyo: true,
    });
    return () => tween.kill();
  });
}

/** Staggered nav pill entrance on shell load. */
export function runNavStagger(elements: NodeListOf<Element> | Element[]): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) {
      gsap.set(elements, { opacity: 1, y: 0 });
      return;
    }
    gsap.from(elements, {
      opacity: 0,
      y: 10,
      duration: CHAT_DURATION.micro,
      ease: CHAT_EASE.enter,
      stagger: 0.06,
    });
  });
}

/** Subtle brand mark glow pulse in header. */
export function runBrandPulse(el: HTMLElement): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;
    const tween = gsap.to(el, {
      boxShadow: "0 0 28px rgba(0, 104, 255, 0.45), 0 0 0 1px rgba(0, 201, 183, 0.2)",
      duration: 2.2,
      ease: CHAT_EASE.glow,
      repeat: -1,
      yoyo: true,
    });
    return () => tween.kill();
  });
}

/** Mouse-follow 3D tilt for metric cards and glass panels. */
export function attachPerspectiveTilt(
  el: HTMLElement,
  options?: { maxTilt?: number },
): () => void {
  const maxTilt = options?.maxTilt ?? 7;

  return withReducedMotion((reduceMotion) => {
    if (reduceMotion) return;

    gsap.set(el, { transformPerspective: 900, transformStyle: "preserve-3d" });

    const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      gsap.to(el, {
        rotationY: x * maxTilt * 2,
        rotationX: -y * maxTilt * 2,
        duration: 0.35,
        ease: CHAT_EASE.micro,
        overwrite: "auto",
      });
    };

    const onLeave = () => {
      gsap.to(el, {
        rotationY: 0,
        rotationX: 0,
        duration: 0.55,
        ease: CHAT_EASE.enter,
        overwrite: "auto",
      });
    };

    el.addEventListener("mousemove", onMove);
    el.addEventListener("mouseleave", onLeave);

    return () => {
      el.removeEventListener("mousemove", onMove);
      el.removeEventListener("mouseleave", onLeave);
      gsap.set(el, { rotationY: 0, rotationX: 0 });
    };
  });
}

/** Layered 3D depth float for hero orb rings. */
export function runHero3DDepth(layers: Element[]): () => void {
  return withReducedMotion((reduceMotion) => {
    if (reduceMotion || layers.length === 0) return;

    const tweens = layers.map((layer, i) =>
      gsap.to(layer, {
        z: (i + 1) * 8,
        y: i % 2 === 0 ? -4 : 4,
        duration: 3 + i * 0.8,
        ease: CHAT_EASE.glow,
        repeat: -1,
        yoyo: true,
      }),
    );

    return () => {
      tweens.forEach((tween) => tween.kill());
    };
  });
}
