import { useRef } from "react";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import { gsap, useGSAP } from "@/lib/gsap";

interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ questions, onSelect }: SuggestedQuestionsProps) {
  const locale = useUserStore((s) => s.locale);
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const el = containerRef.current;
      if (!el) return;
      const chips = el.querySelectorAll(".suggestion-chip");
      if (!chips.length) return;
      gsap.fromTo(
        chips,
        { opacity: 0, y: 8, scale: 0.96 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.3,
          stagger: 0.07,
          ease: "power2.out",
          delay: 0.1,
        },
      );
    },
    { scope: containerRef, dependencies: [questions.join("|")] },
  );

  if (!questions.length) return null;

  return (
    <div ref={containerRef} className="suggested-questions-wrap" role="complementary" aria-label={t("suggestedQuestionsAriaLabel", locale)}>
      <p className="suggested-questions-label">
        <span className="suggested-questions-icon" aria-hidden>💡</span>
        {t("suggestedQuestionsTitle", locale)}
      </p>
      <div className="suggested-questions-list">
        {questions.map((q, i) => (
          <button
            key={i}
            type="button"
            className="suggestion-chip"
            onClick={() => onSelect(q)}
            title={q}
          >
            <span className="suggestion-chip-text">{q}</span>
            <span className="suggestion-chip-arrow" aria-hidden>→</span>
          </button>
        ))}
      </div>
    </div>
  );
}
