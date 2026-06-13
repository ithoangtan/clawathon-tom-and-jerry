import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { RefusalReason } from "@/lib/types";

interface RefusalPanelProps {
  /** Server-provided refusal body (markdown); falls back to the FR-2.2 title. */
  message?: string;
  /** Distinguishes doc-not-found refusals from department access denials (FR-7.2). */
  reason?: RefusalReason | null;
}

/** Prominent UX when the grade gate, verify step, or access control refuses to answer. */
export function RefusalPanel({ message, reason }: RefusalPanelProps) {
  const locale = useUserStore((s) => s.locale);
  const isAccessDenied = reason === "access_denied";
  const title = t(isAccessDenied ? "accessDeniedTitle" : "refusalTitle", locale);
  const hint = t(isAccessDenied ? "accessDeniedHint" : "refusalHint", locale);
  const body = message?.trim();

  return (
    <div
      role="alert"
      aria-labelledby="refusal-heading"
      className={
        isAccessDenied
          ? "refusal-panel-future mt-4 rounded-xl border border-rose-200/90 bg-gradient-to-br from-rose-50/95 to-rose-100/50 p-4 shadow-sm"
          : "refusal-panel-future mt-4 rounded-xl border border-amber-200/90 bg-gradient-to-br from-amber-50/95 to-amber-100/40 p-4 shadow-sm"
      }
    >
      <div className="relative flex gap-3">
        <span
          className={
            isAccessDenied
              ? "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-700 shadow-inner"
              : "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700 shadow-inner"
          }
          aria-hidden
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
            {isAccessDenied ? (
              <>
                <path d="M12 9v4M12 17h.01" />
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              </>
            ) : (
              <>
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </>
            )}
          </svg>
        </span>
        <div className="min-w-0 flex-1">
          <h3
            id="refusal-heading"
            className={
              isAccessDenied
                ? "text-base font-semibold text-rose-950"
                : "text-base font-semibold text-amber-950"
            }
          >
            {title}
          </h3>
          {body && body !== title && (
            <div className={isAccessDenied ? "mt-2 text-rose-900/90" : "mt-2 text-amber-900/90"}>
              <AnswerMarkdown answer={body} citations={[]} />
            </div>
          )}
          <p
            className={
              isAccessDenied
                ? "mt-2 text-sm leading-relaxed text-rose-800"
                : "mt-2 text-sm leading-relaxed text-amber-800"
            }
          >
            {hint}
          </p>
        </div>
      </div>
    </div>
  );
}
