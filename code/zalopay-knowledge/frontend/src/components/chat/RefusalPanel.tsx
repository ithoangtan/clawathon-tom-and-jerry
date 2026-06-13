import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { AlertCircle, ShieldAlert } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { RefusalReason } from "@/lib/types";

interface RefusalPanelProps {
  message?: string;
  reason?: RefusalReason | null;
}

function stripDuplicateLead(body: string, title: string): string {
  const normalized = body.trim();
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const stripped = normalized.replace(new RegExp(`^${escaped}\\.?\\s*`, "i"), "").trim();
  return stripped || normalized;
}

export function RefusalPanel({ message, reason }: RefusalPanelProps) {
  const locale = useUserStore((s) => s.locale);
  const isAccessDenied = reason === "access_denied";
  const isOutOfScope = reason === "out_of_scope";
  const title = t(
    isAccessDenied ? "accessDeniedTitle" : isOutOfScope ? "outOfScopeTitle" : "refusalTitle",
    locale,
  );
  const hint = t(
    isAccessDenied ? "accessDeniedHint" : isOutOfScope ? "outOfScopeHint" : "refusalHint",
    locale,
  );
  const rawBody = message?.trim();
  const body =
    rawBody && rawBody !== title && !isOutOfScope
      ? stripDuplicateLead(rawBody, title)
      : rawBody;

  const accentColor = isAccessDenied ? "var(--color-danger)" : "var(--color-warning)";

  return (
    <div
      role="alert"
      aria-labelledby="refusal-heading"
      className="mt-4 rounded-xl border border-border p-4"
      style={{ borderLeftWidth: "3px", borderLeftColor: accentColor }}
    >
      <div className="flex gap-3">
        <span
          className="mt-0.5 flex-shrink-0"
          style={{ color: accentColor }}
          aria-hidden
        >
          {isAccessDenied ? <ShieldAlert size="lg" /> : <AlertCircle size="lg" />}
        </span>
        <div className="min-w-0 flex-1">
          <h3 id="refusal-heading" className="text-sm font-semibold text-content-primary">
            {title}
          </h3>
          {body && body !== title && (
            <div className="mt-1.5 text-content-secondary">
              <AnswerMarkdown answer={body} citations={[]} />
            </div>
          )}
          <p className="mt-1.5 text-xs leading-relaxed text-content-muted">{hint}</p>
        </div>
      </div>
    </div>
  );
}
