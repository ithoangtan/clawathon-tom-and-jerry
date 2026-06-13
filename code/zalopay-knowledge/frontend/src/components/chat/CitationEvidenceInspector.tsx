import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ExternalLink, X } from "@/components/ui/icons";
import {
  docTypeLabel,
  formatExcerpt,
  isCitationDeprecated,
  lifecycleLabel,
  lifecycleTone,
  openSourceLabel,
} from "@/lib/citations";
import { formatDate } from "@/lib/format";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Citation } from "@/lib/types";
import { useEffect, useRef } from "react";

export interface CitationInspectorState {
  citations: Citation[];
  selectedIndex: number;
}

interface CitationEvidenceInspectorProps {
  state: CitationInspectorState;
  open: boolean;
  variant: "panel" | "sheet";
  onClose: () => void;
  onSelectIndex: (index: number) => void;
}

export function CitationEvidenceInspector({
  state,
  open,
  variant,
  onClose,
  onSelectIndex,
}: CitationEvidenceInspectorProps) {
  const locale = useUserStore((s) => s.locale);
  const panelRef = useRef<HTMLDivElement>(null);
  const isSheet = variant === "sheet";

  useFocusTrap(open && isSheet, panelRef);

  const { citations, selectedIndex } = state;
  const citation = citations[selectedIndex - 1];

  useEffect(() => {
    if (!open || isSheet) return;
    panelRef.current?.focus();
  }, [open, isSheet, selectedIndex]);

  if (!open || !citation) return null;

  const excerpt = formatExcerpt(citation.excerpt);
  const deprecated = isCitationDeprecated(citation);

  const body = (
    <div
      ref={panelRef}
      role="dialog"
      aria-modal={isSheet}
      aria-label={t("evidenceInspectorAriaLabel", locale, { index: selectedIndex })}
      tabIndex={-1}
      className={
        isSheet
          ? "citation-inspector-sheet glass-panel-strong flex max-h-[85dvh] flex-col rounded-t-2xl outline-none"
          : "citation-inspector-panel glass-panel-strong flex h-full flex-col outline-none"
      }
    >
      <header className="flex flex-shrink-0 items-start justify-between gap-3 border-b border-border px-4 py-3 sm:px-5">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-content-muted">
            {t("evidenceInspectorTitle", locale)} [{selectedIndex}]
          </p>
          <h2 className="mt-1 line-clamp-2 text-base font-semibold text-content-primary">
            {citation.title}
          </h2>
        </div>
        <Button
          variant="ghost"
          className="flex-shrink-0 px-2 py-2"
          onClick={onClose}
          aria-label={t("closeInspector", locale)}
        >
          <X size="sm" />
        </Button>
      </header>

      <div className="flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5">
        {deprecated && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-warning/30 bg-warning-muted px-3 py-2.5 text-sm text-warning"
          >
            <p className="font-medium">{t("deprecatedWarning", locale)}</p>
            {citation.successor_url && (
              <a
                href={citation.successor_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-flex items-center gap-1 font-medium text-brand hover:underline"
              >
                <ExternalLink size="xs" />
                {t("successorDoc", locale)}
              </a>
            )}
          </div>
        )}

        <div className="mb-4 flex flex-wrap gap-2">
          <Badge tone="info">{docTypeLabel(citation.source_type, locale)}</Badge>
          <Badge tone={lifecycleTone(citation)}>{lifecycleLabel(citation, locale)}</Badge>
        </div>

        <section aria-labelledby="evidence-excerpt-heading">
          <h3
            id="evidence-excerpt-heading"
            className="text-xs font-semibold uppercase tracking-wide text-content-muted"
          >
            {t("evidenceExcerpt", locale)}
          </h3>
          <blockquote className="mt-2 rounded-lg border border-border bg-surface-glass/60 px-3 py-3 text-sm leading-relaxed text-content-primary">
            {excerpt ?? (
              <span className="italic text-content-muted">{t("evidenceExcerptMissing", locale)}</span>
            )}
          </blockquote>
        </section>

        <dl className="mt-4 space-y-2 text-sm">
          {citation.section && (
            <div className="flex gap-2">
              <dt className="text-content-muted">{t("citationSection", locale)}</dt>
              <dd className="text-content-primary">{citation.section}</dd>
            </div>
          )}
          {citation.page != null && (
            <div className="flex gap-2">
              <dt className="text-content-muted">{t("citationPage", locale)}</dt>
              <dd className="text-content-primary">{citation.page}</dd>
            </div>
          )}
          {citation.last_modified && (
            <div className="flex gap-2">
              <dt className="text-content-muted">{t("citationUpdated", locale)}</dt>
              <dd>
                <time dateTime={citation.last_modified} className="text-content-primary">
                  {formatDate(citation.last_modified, locale)}
                </time>
              </dd>
            </div>
          )}
          {citation.chunk_id && (
            <div className="flex gap-2">
              <dt className="text-content-muted">{t("evidenceChunkId", locale)}</dt>
              <dd className="truncate font-mono text-xs text-content-secondary" title={citation.chunk_id}>
                {citation.chunk_id}
              </dd>
            </div>
          )}
        </dl>
      </div>

      <footer className="flex flex-shrink-0 flex-col gap-2 border-t border-border px-4 py-3 sm:px-5">
        {citations.length > 1 && citations.length <= 9 && (
          <p className="text-center text-xs text-content-muted">{t("citationKeyboardHint", locale)}</p>
        )}
        <div className="flex flex-wrap gap-2">
          {citations.slice(0, 9).map((_, i) => {
            const idx = i + 1;
            const active = idx === selectedIndex;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectIndex(idx)}
                aria-label={t("evidenceSelectSource", locale, { index: idx })}
                aria-current={active ? "true" : undefined}
                className={
                  active
                    ? "citation-inspector-pill citation-inspector-pill-active"
                    : "citation-inspector-pill"
                }
              >
                {idx}
              </button>
            );
          })}
        </div>
        <Button
          variant="primary"
          className="w-full"
          onClick={() => window.open(citation.url, "_blank", "noopener,noreferrer")}
        >
          <ExternalLink size="sm" />
          {openSourceLabel(citation.source_type, locale)}
        </Button>
      </footer>
    </div>
  );

  if (isSheet) {
    return (
      <div className="citation-inspector-overlay fixed inset-0 z-50 flex flex-col justify-end md:hidden">
        <button
          type="button"
          className="absolute inset-0 bg-black/50 citation-inspector-backdrop"
          aria-label={t("closeInspector", locale)}
          onClick={onClose}
        />
        <div className="relative z-10">{body}</div>
      </div>
    );
  }

  return (
    <aside className="hidden h-full min-h-0 w-[40%] flex-shrink-0 border-l border-border md:flex">
      {body}
    </aside>
  );
}
