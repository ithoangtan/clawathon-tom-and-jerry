import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { formatMessageTime } from "@/lib/format";
import { t } from "@/lib/i18n";
import { runMessageEnter, useGSAP } from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";
import { useRef } from "react";

interface UserMessageProps {
  content: string;
  timestamp: string;
  isWebhookTrigger?: boolean;
}

export function UserMessage({ content, timestamp, isWebhookTrigger }: UserMessageProps) {
  const locale = useUserStore((s) => s.locale);
  const timeLabel = formatMessageTime(timestamp, locale);
  const articleRef = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const el = articleRef.current;
      if (!el) return;
      return runMessageEnter(el, "user");
    },
    { scope: articleRef },
  );

  if (isWebhookTrigger) {
    return (
      <article ref={articleRef} aria-label={content}>
        <div className="flex items-start gap-2.5 rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
          <span className="mt-0.5 flex-shrink-0 text-base leading-none">⚡</span>
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-brand">
                Webhook Trigger
              </span>
              <time dateTime={timestamp} className="text-[11px] text-content-muted tabular-nums">
                {timeLabel}
              </time>
            </div>
            <MarkdownRenderer content={content} className="text-sm text-content-secondary [&_a]:text-brand [&_strong]:text-content-primary" />
          </div>
        </div>
      </article>
    );
  }

  return (
    <article
      ref={articleRef}
      className="flex flex-row-reverse gap-3"
      aria-label={`${t("you", locale)}: ${content}`}
    >
      <ChatAvatar role="user" />
      <div className="flex min-w-0 max-w-[85%] flex-col items-end gap-1 sm:max-w-prose">
        <div className="flex items-center gap-2">
          <time
            dateTime={timestamp}
            className="text-[11px] text-content-muted tabular-nums"
          >
            {timeLabel}
          </time>
          <span className="text-xs font-medium text-content-secondary">{t("you", locale)}</span>
        </div>
        <div className="user-bubble">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    </article>
  );
}
