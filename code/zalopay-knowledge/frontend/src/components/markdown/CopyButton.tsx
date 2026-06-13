import { classNames } from "@/lib/format";
import { Check, Copy } from "@/components/ui/icons";
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
          <Check size={size === "sm" ? "sm" : "md"} />
          <span className="sr-only sm:not-sr-only">{copiedText}</span>
        </>
      ) : (
        <>
          <Copy size={size === "sm" ? "sm" : "md"} />
          <span className="sr-only sm:not-sr-only">{copyLabel}</span>
        </>
      )}
    </button>
  );
}
