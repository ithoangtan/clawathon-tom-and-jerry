import { useMemo } from "react";
import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { ConfidenceBadge, DepartmentChip } from "@/components/chat/Badges";
import { CitationList } from "@/components/chat/CitationList";
import { ClarifyingQuestionCard } from "@/components/chat/ClarifyingQuestionCard";
import { ConflictPanel } from "@/components/chat/ConflictPanel";
import { FeedbackBar } from "@/components/chat/FeedbackBar";
import { MessageCopyButton } from "@/components/chat/MessageCopyButton";
import { PartialGapBanner } from "@/components/chat/PartialGapBanner";
import { RefusalPanel } from "@/components/chat/RefusalPanel";
import { Card } from "@/components/ui/Card";
import { classNames } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { ChatResponse, Department } from "@/lib/types";

interface AnswerCardProps {
  response: ChatResponse;
  onClarifySelect?: (dept: Department) => void;
  onCitationClick?: (index: number) => void;
  variant?: "card" | "message";
  streaming?: boolean;
}

export function AnswerCard({
  response,
  onClarifySelect,
  onCitationClick,
  variant = "card",
  streaming,
}: AnswerCardProps) {
  const locale = useUserStore((s) => s.locale);
  const {
    answer,
    citations,
    source_departments,
    confidence,
    status,
    conflicts,
    clarifying_question,
    feedback_id,
    refusal_reason,
    refusals,
    model_used,
  } = response;

  const isMessage = variant === "message";

  const departmentChips = useMemo(() => {
    const depts = new Set<Department>(source_departments);
    for (const conflict of conflicts ?? []) {
      for (const side of conflict.sides) {
        depts.add(side.department);
      }
    }
    return [...depts];
  }, [conflicts, source_departments]);

  const isClarifying = Boolean(clarifying_question && onClarifySelect);

  return (
    <Card
      padding={isMessage ? "sm" : "md"}
      className={classNames(
        isMessage ? "assistant-card-future" : "max-w-3xl",
      )}
    >
      {/* Agent action: compact progress/status render — no dept chips, no feedback */}
      {status === "agent_action" ? (
        <>
          <div className="mb-2">
            <ConfidenceBadge confidence={confidence} status={status} />
          </div>
          <AnswerMarkdown answer={answer} citations={[]} />
        </>
      ) : (
        <>
          {departmentChips.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {departmentChips.map((dept) => (
                <DepartmentChip key={dept} deptKey={dept} interactive />
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <ConfidenceBadge
                confidence={confidence}
                status={status}
                refusalReason={refusal_reason}
                clarifying={isClarifying}
              />
              {model_used && (
                <span
                  className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] font-medium text-slate-500"
                  title={`${t("modelUsedLabel", locale)}: ${model_used}`}
                >
                  <span className="opacity-60">⚙</span>
                  {model_used}
                </span>
              )}
            </div>
            {status !== "refused" && !isClarifying && answer.trim() && !streaming && (
              <MessageCopyButton text={answer} />
            )}
          </div>
        </>
      )}

      {status !== "agent_action" && (
        isClarifying ? (
          <div className="mt-4">
            <ClarifyingQuestionCard
              question={clarifying_question!}
              onSelect={onClarifySelect!}
            />
            {!streaming && feedback_id && <FeedbackBar feedbackId={feedback_id} modelUsed={model_used ?? undefined} />}
          </div>
        ) : status === "refused" ? (
          <>
            <RefusalPanel message={answer} reason={refusal_reason} />
            {feedback_id && <FeedbackBar feedbackId={feedback_id} />}
          </>
        ) : (
          <>
            {status === "partial" && <PartialGapBanner refusals={refusals} />}
            <div className="mt-4" data-tour="response-answer">
              <AnswerMarkdown
                answer={answer}
                citations={citations}
                onCitationClick={onCitationClick}
                streaming={streaming}
              />
            </div>
            {!streaming && citations.length > 0 && (
              <div className="mt-5 border-t border-border pt-4" data-tour="response-citations">
                <CitationList citations={citations} onCitationClick={onCitationClick} />
              </div>
            )}
            {!streaming && conflicts && conflicts.length > 0 && (
              <ConflictPanel conflicts={conflicts} />
            )}
            {!streaming && feedback_id && <FeedbackBar feedbackId={feedback_id} modelUsed={model_used ?? undefined} />}
          </>
        )
      )}
    </Card>
  );
}
