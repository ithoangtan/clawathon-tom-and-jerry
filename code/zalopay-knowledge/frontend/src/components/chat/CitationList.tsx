import { StalenessBadge } from "@/components/chat/StalenessBadge";
import { formatDate } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Citation } from "@/lib/types";
import { useState } from "react";

interface CitationListProps {
  citations: Citation[];
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
    <section role="region" aria-label={t("citations", locale)} className="mt-0">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-medium text-content-muted uppercase tracking-wide">
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
      <ol className="space-y-1 list-none p-0 m-0">
        {visible.map((citation, idx) => (
          <li key={`${citation.url}-${idx}`}>
            <CitationRow
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

function CitationRow({
  index,
  citation,
  onClick,
}: {
  index: number;
  citation: Citation;
  onClick?: (index: number) => void;
}) {
  const locale = useUserStore((s) => s.locale);
  const interactive = Boolean(onClick);

  const content = (
    <div className="flex items-start gap-2 py-1.5 px-1 rounded-lg transition-colors hover:bg-surface-glass group/row">
      <span className="flex-shrink-0 mt-0.5 flex h-4 w-4 items-center justify-center rounded text-[10px] font-bold text-content-muted bg-border/40">
        {index}
      </span>
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium text-content-secondary group-hover/row:text-brand transition-colors line-clamp-1">
          {citation.title}
        </span>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-content-muted truncate">{formatCitationUrl(citation.url)}</span>
          {citation.source_type && (
            <span className="text-[10px] uppercase tracking-wide text-content-muted/60 flex-shrink-0">{citation.source_type}</span>
          )}
          {citation.last_modified && (
            <time className="text-xs text-content-muted/60 flex-shrink-0" dateTime={citation.last_modified}>
              {formatDate(citation.last_modified, locale)}
            </time>
          )}
          <StalenessBadge citation={citation} />
        </div>
      </div>
    </div>
  );

  if (interactive) {
    return (
      <button
        type="button"
        className="w-full text-left"
        onClick={() => onClick?.(index)}
        aria-label={`${t("evidenceSelectSource", locale, { index })}: ${citation.title}`}
      >
        {content}
      </button>
    );
  }

  return (
    <a href={citation.url} target="_blank" rel="noopener noreferrer" className="block">
      {content}
    </a>
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
