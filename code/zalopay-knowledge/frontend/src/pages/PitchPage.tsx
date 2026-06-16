import { useEffect } from "react";
import { ThemeEffect } from "@/components/layout/ThemeEffect";
import { gsap } from "@/lib/gsap";
import { PitchNav } from "./pitch/PitchNav";
import { S0Hero } from "./pitch/S0Hero";
import { S1Problem } from "./pitch/S1Problem";
import { S2Demo } from "./pitch/S2Demo";
import { S3WhyNow } from "./pitch/S3WhyNow";
import { S4Solution } from "./pitch/S4Solution";
import { S5LivingWiki } from "./pitch/S5LivingWiki";
import { S6Impact } from "./pitch/S6Impact";
import { S7Governance } from "./pitch/S7Governance";
import { S8MvpVsProd } from "./pitch/S8MvpVsProd";
import { S9NextSteps } from "./pitch/S9NextSteps";
import { S10Closing } from "./pitch/S10Closing";

function useSectionSnap() {
  useEffect(() => {
    const getSections = () =>
      Array.from(document.querySelectorAll("[data-pitch-section]")) as HTMLElement[];

    let locked = false;
    const lock = () => {
      locked = true;
      setTimeout(() => { locked = false; }, 950);
    };

    const getActiveIndex = (sections: HTMLElement[]) => {
      let best = 0;
      sections.forEach((s, i) => {
        if (s.getBoundingClientRect().top <= window.innerHeight * 0.45) best = i;
      });
      return best;
    };

    const goTo = (sections: HTMLElement[], index: number) => {
      const clamped = Math.max(0, Math.min(index, sections.length - 1));
      sections[clamped].scrollIntoView({ behavior: "smooth", block: "start" });
      lock();
    };

    const onWheel = (e: WheelEvent) => {
      if (locked) { e.preventDefault(); return; }
      const sections = getSections();
      const idx = getActiveIndex(sections);
      const active = sections[idx];
      const rect = active.getBoundingClientRect();
      // Tall section: let natural scroll happen until user reaches its boundary
      const isTall = active.offsetHeight > window.innerHeight * 1.1;

      if (e.deltaY > 0) {
        if (!isTall || rect.bottom <= window.innerHeight + 60) {
          e.preventDefault();
          goTo(sections, idx + 1);
        }
      } else if (e.deltaY < 0) {
        if (!isTall || rect.top >= -60) {
          e.preventDefault();
          goTo(sections, idx - 1);
        }
      }
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (locked) return;
      // Don't hijack keys while user types in an input/textarea
      if ((e.target as HTMLElement).matches("input,textarea,select,[contenteditable]")) return;
      const sections = getSections();
      const idx = getActiveIndex(sections);
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        goTo(sections, idx + 1);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        goTo(sections, idx - 1);
      }
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);
}

function useRevealOnEnter() {
  useEffect(() => {
    const sections = Array.from(
      document.querySelectorAll("[data-pitch-section]"),
    ) as HTMLElement[];

    // Hide all reveal elements upfront
    sections.forEach((s) => {
      const els = s.querySelectorAll("[data-reveal]");
      if (els.length) gsap.set(els, { opacity: 0, y: 28 });
    });

    const revealed = new Set<Element>();
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !revealed.has(entry.target)) {
            revealed.add(entry.target);
            const els = (entry.target as HTMLElement).querySelectorAll("[data-reveal]");
            if (els.length) gsap.to(els, {
              opacity: 1,
              y: 0,
              duration: 0.7,
              ease: "power3.out",
              stagger: 0.1,
              clearProps: "transform",
            });
          }
        });
      },
      { threshold: 0.15 },
    );

    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, []);
}

export default function PitchPage() {
  useSectionSnap();
  useRevealOnEnter();
  return (
    <div
      className="pitch-root relative min-h-screen overflow-x-hidden"
      style={{ background: "var(--color-bg-base)", color: "var(--color-text-primary)" }}
    >
      {/* Background layers — fixed so they cover the whole scroll */}
      <div className="pointer-events-none fixed inset-0 mesh-bg" aria-hidden />
      <div className="pointer-events-none fixed inset-0 grid-overlay opacity-20" aria-hidden />

      <ThemeEffect />
      <PitchNav />

      <main>
        <S0Hero />
        <S1Problem />
        <S2Demo />
        <S3WhyNow />
        <S4Solution />
        <S5LivingWiki />
        <S6Impact />
        <S7Governance />
        <S8MvpVsProd />
        <S9NextSteps />
        <S10Closing />
      </main>
    </div>
  );
}
