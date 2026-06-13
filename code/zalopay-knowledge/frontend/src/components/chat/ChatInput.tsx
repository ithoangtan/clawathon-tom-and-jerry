import { useEffect, useRef, type KeyboardEvent } from "react";
import { Loader2, Send } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { classNames } from "@/lib/format";
import {
  CHAT_DURATION,
  CHAT_EASE,
  gsap,
  REDUCED_MOTION_QUERY,
  runSendPulse,
  useGSAP,
} from "@/lib/gsap";
import { useUserStore } from "@/store/userStore";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSubmit, loading, disabled }: ChatInputProps) {
  const locale = useUserStore((s) => s.locale);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const sendRef = useRef<HTMLButtonElement>(null);
  const canSend = !loading && !disabled && value.trim().length > 0;

  useGSAP(
    (_, contextSafe) => {
      if (!contextSafe) return;
      const shell = shellRef.current;
      const textarea = textareaRef.current;
      const send = sendRef.current;
      if (!shell || !textarea || !send) return;

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion) return;

        const onFocus = contextSafe(() => {
          gsap.to(shell, {
            scale: 1.006,
            y: -2,
            duration: CHAT_DURATION.micro,
            ease: CHAT_EASE.micro,
            overwrite: true,
          });
        });
        const onBlur = contextSafe(() => {
          gsap.to(shell, {
            scale: 1,
            y: 0,
            duration: CHAT_DURATION.micro,
            ease: CHAT_EASE.micro,
            overwrite: true,
          });
        });

        const onSendEnter = contextSafe(() => {
          if (send.disabled) return;
          gsap.to(send, { scale: 1.12, duration: 0.14, ease: CHAT_EASE.micro });
        });
        const onSendLeave = contextSafe(() => {
          gsap.to(send, { scale: 1, duration: 0.2, ease: CHAT_EASE.send });
        });
        const onSendDown = contextSafe(() => {
          if (send.disabled) return;
          gsap.to(send, { scale: 0.9, duration: 0.08, ease: "power2.in" });
        });
        const onSendUp = contextSafe(() => {
          if (send.disabled) return;
          gsap.to(send, { scale: 1.08, duration: 0.22, ease: CHAT_EASE.send });
        });

        textarea.addEventListener("focus", onFocus);
        textarea.addEventListener("blur", onBlur);
        send.addEventListener("mouseenter", onSendEnter);
        send.addEventListener("mouseleave", onSendLeave);
        send.addEventListener("mousedown", onSendDown);
        send.addEventListener("mouseup", onSendUp);

        return () => {
          textarea.removeEventListener("focus", onFocus);
          textarea.removeEventListener("blur", onBlur);
          send.removeEventListener("mouseenter", onSendEnter);
          send.removeEventListener("mouseleave", onSendLeave);
          send.removeEventListener("mousedown", onSendDown);
          send.removeEventListener("mouseup", onSendUp);
        };
      });

      return () => mm.revert();
    },
    { scope: shellRef, dependencies: [canSend, disabled, loading] },
  );

  useGSAP(
    () => {
      const send = sendRef.current;
      if (!send || !canSend) return;

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion) return;
        gsap.fromTo(
          send,
          { scale: 0.82, opacity: 0.7 },
          { scale: 1, opacity: 1, duration: 0.4, ease: CHAT_EASE.send },
        );
      });
      return () => mm.revert();
    },
    { scope: sendRef, dependencies: [canSend], revertOnUpdate: true },
  );

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  useEffect(() => {
    if (!loading) {
      textareaRef.current?.focus();
    }
  }, [loading]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) handleSubmit();
    }
  }

  function handleSubmit() {
    if (!canSend) return;
    const send = sendRef.current;
    if (send) runSendPulse(send);
    onSubmit();
  }

  return (
    <div className="w-full">
      <div
        ref={shellRef}
        data-tour="chat-input"
        className={classNames(
          "chat-input-shell flex items-end gap-2 p-2",
          disabled && "opacity-60",
        )}
      >
        <label htmlFor="chat-input" className="sr-only">
          {t("askPlaceholder", locale)}
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          rows={1}
          className="max-h-[200px] min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm leading-relaxed text-content-primary placeholder:text-content-muted focus:outline-none disabled:cursor-not-allowed"
          placeholder={t("askPlaceholder", locale)}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          maxLength={4000}
          aria-disabled={disabled || loading}
          aria-describedby="chat-input-hint"
        />
        <button
          ref={sendRef}
          type="button"
          onClick={handleSubmit}
          disabled={!canSend}
          className={classNames(
            "mb-1 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl transition-colors",
            canSend
              ? "bg-gradient-to-br from-brand to-brand-dark text-white shadow-md shadow-brand/25 hover:shadow-lg hover:shadow-brand/30"
              : "bg-white/5 text-content-muted cursor-not-allowed",
          )}
          aria-label={loading ? t("sending", locale) : t("send", locale)}
        >
          {loading ? <Loader2 size="md" /> : <Send size="md" />}
        </button>
      </div>
      <p id="chat-input-hint" className="mt-2 text-center text-[11px] text-content-muted">
        {t("inputHint", locale)}
      </p>
    </div>
  );
}
