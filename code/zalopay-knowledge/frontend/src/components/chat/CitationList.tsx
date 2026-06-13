import { Card } from "@/components/ui/Card";
import { StalenessBadge } from "@/components/chat/StalenessBadge";
import { formatDate } from "@/lib/format";
import { attachHoverLift, useGSAP } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Citation } from "@/lib/types";
import { useRef, useState } from "react";

interface CitationListProps {
  citations: Citation[];
  /** Map citation index (1-based) to scroll/highlight */
  onCitationClick?: (index: number) => void;
  collapsible?: boolean;
}

export function CitationList({
  citations,
  onCitationClick,
  collapsible = true,
}: CitationListProps) {
  const locale = useUserStore((s) => s.locale);
  const [expanded, setExpanded] = useState(!collapsible || citations.length <= 3);

  if (citations.length === 0) return null;

  const visible = expanded ? citations : citations.slice(0, 3);

  return (
    <section role="region" aria-label={t("citations", locale)} className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-700">
          {t("citations", locale)} ({citations.length})
        </h4>
        {collapsible && citations.length > 3 && (
          <button
            type="button"
            className="text-xs font-medium text-brand transition-colors hover:text-brand-dark"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded ? t("collapseCitations", locale) : t("expandCitations", locale)}
          </button>
        )}
      </div>
      <ol className="space-y-2 list-none p-0 m-0">
        {visible.map((citation, idx) => (
          <li key={`${citation.url}-${idx}`}>
            <CitationCard
              index={idx + 1}
              citation={citation}
              onClick={onCitationClick}
            />
          </li>
        ))}
      </ol>
    </section>
  );
}

function CitationCard({
  index,
  citation,
  onClick,
}: {
  index: number;
  citation: Citation;
  onClick?: (index: number) => void;
}) {
  const locale = useUserStore((s) => s.locale);
  const cardRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const el = cardRef.current;
      if (!el) return;
      return attachHoverLift(el, { y: -3, scale: 1.008 });
    },
    { scope: cardRef },
  );

  return (
    <div ref={cardRef}>
      <Card padding="sm" className="citation-card-future">
      <div className="flex gap-3">
        <span
          className="flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-xs font-bold text-white shadow-sm"
          aria-hidden
        >
          {index}
        </span>
        <div className="min-w-0 flex-1">
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-brand hover:text-brand-dark line-clamp-2 transition-colors"
            onClick={() => onClick?.(index)}
          >
            {citation.title}
          </a>
          <p className="mt-1 truncate text-xs text-slate-400" title={citation.url}>
            {formatCitationUrl(citation.url)}
          </p>
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
            {citation.section && (
              <span>
                <span className="text-slate-400">{t("citationSection", locale)}:</span>{" "}
                {citation.section}
              </span>
            )}
            {citation.page != null && (
              <span>
                <span className="text-slate-400">{t("citationPage", locale)}:</span>{" "}
                {citation.page}
              </span>
            )}
            {citation.source_type && (
              <span className="uppercase tracking-wide">{citation.source_type}</span>
            )}
            {citation.last_modified && (
              <span>
                <span className="text-slate-400">{t("citationUpdated", locale)}:</span>{" "}
                <time dateTime={citation.last_modified}>
                  {formatDate(citation.last_modified, locale)}
                </time>
              </span>
            )}
          </div>
          <StalenessBadge citation={citation} />
        </div>
      </div>
      </Card>
    </div>
  );
}

function formatCitationUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname.length > 48 ? `${parsed.pathname.slice(0, 45)}…` : parsed.pathname;
    return `${parsed.hostname}${path}`;
  } catch {
    return url;
  }
}
