import { useMemo } from "react";
import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { ConfidenceBadge, DepartmentChip } from "@/components/chat/Badges";
import { CitationList } from "@/components/chat/CitationList";
import { ClarifyingQuestionCard } from "@/components/chat/ClarifyingQuestionCard";
import { ConflictPanel } from "@/components/chat/ConflictPanel";
import { FeedbackBar } from "@/components/chat/FeedbackBar";
import { MessageCopyButton } from "@/components/chat/MessageCopyButton";
import { RefusalPanel } from "@/components/chat/RefusalPanel";
import { Card } from "@/components/ui/Card";
import { classNames } from "@/lib/format";
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

  return (
    <Card
      padding={isMessage ? "sm" : "md"}
      className={classNames(
        isMessage ? "assistant-card-future" : "max-w-3xl",
      )}
    >
      {departmentChips.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {departmentChips.map((dept) => (
            <DepartmentChip key={dept} deptKey={dept} interactive />
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <ConfidenceBadge
          confidence={confidence}
          status={status}
          refusalReason={refusal_reason}
        />
        {status !== "refused" && answer.trim() && !streaming && (
          <MessageCopyButton text={answer} />
        )}
      </div>

      {clarifying_question && onClarifySelect ? (
        <div className="mt-4">
          <ClarifyingQuestionCard
            question={clarifying_question}
            onSelect={onClarifySelect}
          />
        </div>
      ) : status === "refused" ? (
        <>
          <RefusalPanel message={answer} reason={refusal_reason} />
          {feedback_id && <FeedbackBar feedbackId={feedback_id} />}
        </>
      ) : (
        <>
          <div className="mt-4">
            <AnswerMarkdown
              answer={answer}
              citations={citations}
              onCitationClick={onCitationClick}
              streaming={streaming}
            />
          </div>
          {!streaming && (
            <CitationList citations={citations} onCitationClick={onCitationClick} />
          )}
          {!streaming && conflicts && conflicts.length > 0 && (
            <ConflictPanel conflicts={conflicts} />
          )}
          {!streaming && feedback_id && <FeedbackBar feedbackId={feedback_id} />}
        </>
      )}
    </Card>
  );
}
