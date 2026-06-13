import { AnswerCard } from "@/components/chat/AnswerCard";
import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { formatMessageTime } from "@/lib/format";
import { t } from "@/lib/i18n";
import { runMessageEnter, useGSAP } from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";
import type { ChatResponse, Department } from "@/lib/types";
import { useRef } from "react";

interface AssistantMessageProps {
  response: ChatResponse;
  timestamp: string;
  streaming?: boolean;
  onClarifySelect?: (dept: Department) => void;
}

export function AssistantMessage({
  response,
  timestamp,
  streaming,
  onClarifySelect,
}: AssistantMessageProps) {
  const locale = useUserStore((s) => s.locale);
  const timeLabel = formatMessageTime(timestamp, locale);
  const articleRef = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const el = articleRef.current;
      if (!el) return;
      return runMessageEnter(el, "assistant");
    },
    { scope: articleRef },
  );

  return (
    <article ref={articleRef} className="flex gap-3" aria-label={t("assistantName", locale)}>
      <ChatAvatar role="assistant" className="avatar-assistant-glow" />
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-content-secondary">
            {t("assistantName", locale)}
          </span>
          <time
            dateTime={timestamp}
            className="text-[11px] text-content-muted tabular-nums"
          >
            {timeLabel}
          </time>
        </div>
        <div className="message-content-slot min-w-0">
          <AnswerCard
            response={response}
            onClarifySelect={onClarifySelect}
            variant="message"
            streaming={streaming}
          />
        </div>
      </div>
    </article>
  );
}
