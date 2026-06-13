import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { formatMessageTime } from "@/lib/format";
import { t } from "@/lib/i18n";
import { runMessageEnter, useGSAP } from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";
import { useRef } from "react";

interface UserMessageProps {
  content: string;
  timestamp: string;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
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
