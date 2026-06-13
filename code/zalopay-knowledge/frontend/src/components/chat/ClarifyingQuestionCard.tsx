import { departmentLabel, getDepartment } from "@/lib/departments";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { ClarifyingQuestion, Department } from "@/lib/types";

interface ClarifyingQuestionCardProps {
  question: ClarifyingQuestion;
  onSelect: (dept: Department) => void;
}

export function ClarifyingQuestionCard({ question, onSelect }: ClarifyingQuestionCardProps) {
  const locale = useUserStore((s) => s.locale);

  function handleSelect(dept: Department, el: HTMLButtonElement) {
    runChipPop(el);
    onSelect(dept);
  }

  return (
    <div
      className="mt-4 rounded-xl border border-border p-4"
      role="region"
      aria-label={t("clarifyPrompt", locale)}
    >
      <p className="mb-3 text-sm text-content-secondary">{question.prompt}</p>
      <div className="flex flex-wrap gap-2">
        {question.options.map((dept) => {
          const meta = getDepartment(dept);
          return (
            <button
              key={dept}
              type="button"
              onClick={(e) => handleSelect(dept, e.currentTarget)}
              aria-label={departmentLabel(dept, locale)}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-content-primary transition-colors hover:bg-surface-glass hover:border-border-strong"
            >
              <span
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: meta.accent_color }}
              />
              {departmentLabel(dept, locale)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
