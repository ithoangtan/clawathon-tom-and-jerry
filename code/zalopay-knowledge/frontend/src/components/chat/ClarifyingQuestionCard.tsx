import { Button } from "@/components/ui/Button";
import { DepartmentChip } from "@/components/chat/Badges";
import { departmentLabel } from "@/lib/departments";
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
      className="clarify-card-future"
      role="region"
      aria-label={t("clarifyPrompt", locale)}
    >
      <p className="mb-3 text-sm font-medium text-brand-dark">{question.prompt}</p>
      <div className="flex flex-wrap gap-2">
        {question.options.map((dept) => (
          <Button
            key={dept}
            variant="secondary"
            onClick={(e) => handleSelect(dept, e.currentTarget)}
            aria-label={departmentLabel(dept, locale)}
            className="border-brand/20 bg-white/80 hover:border-brand/40 hover:shadow-glow"
          >
            <DepartmentChip deptKey={dept} interactive />
          </Button>
        ))}
      </div>
    </div>
  );
}
