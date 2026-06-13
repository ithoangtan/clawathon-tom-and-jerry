import { classNames } from "@/lib/format";
import { runCopySuccess } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import { useCallback, useEffect, useRef, useState } from "react";

interface CopyButtonProps {
  text: string;
  label?: string;
  copiedLabel?: string;
  className?: string;
  size?: "sm" | "md";
}

export function CopyButton({
  text,
  label,
  copiedLabel,
  className,
  size = "sm",
}: CopyButtonProps) {
  const locale = useUserStore((s) => s.locale);
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const buttonRef = useRef<HTMLButtonElement>(null);

  const copyLabel = label ?? t("copy", locale);
  const copiedText = copiedLabel ?? t("copied", locale);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      if (buttonRef.current) runCopySuccess(buttonRef.current);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      if (buttonRef.current) runCopySuccess(buttonRef.current);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    }
  }, [text]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const iconSize = size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4";

  return (
    <button
      ref={buttonRef}
      type="button"
      onClick={handleCopy}
      className={classNames(
        "inline-flex items-center gap-1.5 rounded-md font-medium text-slate-500 transition-colors",
        "hover:bg-brand-light/60 hover:text-brand-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40",
        size === "sm" ? "px-2 py-1 text-xs" : "px-2.5 py-1.5 text-sm",
        copied && "text-emerald-600",
        className,
      )}
      aria-label={copied ? copiedText : copyLabel}
      title={copied ? copiedText : copyLabel}
    >
      {copied ? (
        <>
          <CheckIcon className={iconSize} />
          <span className="sr-only sm:not-sr-only">{copiedText}</span>
        </>
      ) : (
        <>
          <CopyIcon className={iconSize} />
          <span className="sr-only sm:not-sr-only">{copyLabel}</span>
        </>
      )}
    </button>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
