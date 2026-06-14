import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { ExternalLink } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

interface RefusedQuestion {
  question: string;
  count: number;
  last_seen: string;
  departments: string[];
}

interface LowRatedDoc {
  title: string;
  url: string;
  up: number;
  down: number;
}

interface KnowledgeGapsData {
  refused_questions: RefusedQuestion[];
  low_rated_docs: LowRatedDoc[];
}

function useKnowledgeGaps() {
  const [data, setData] = useState<KnowledgeGapsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch("/api/knowledge-gaps")
      .then((r) => r.json())
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  function exportCsv() {
    if (!data) return;
    const rows = [
      ["Type", "Question / Document", "Count / Down Ratings", "Last Seen"],
      ...data.refused_questions.map((q) => [
        "Refused",
        q.question,
        String(q.count),
        q.last_seen,
      ]),
      ...data.low_rated_docs.map((d) => [
        "Low Rated",
        d.title,
        String(d.down),
        "",
      ]),
    ];
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "knowledge-gaps.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return { data, loading, error, exportCsv };
}

export function KnowledgeGapPanel() {
  const locale = useUserStore((s) => s.locale);
  const { data, loading, error, exportCsv } = useKnowledgeGaps();

  const isEmpty =
    !loading &&
    !error &&
    data &&
    data.refused_questions.length === 0 &&
    data.low_rated_docs.length === 0;

  return (
    <Card>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-content-primary">
            {t("knowledgeGapsTitle", locale)}
          </h3>
          <p className="mt-0.5 text-sm text-content-secondary">
            {t("knowledgeGapsSubtitle", locale)}
          </p>
        </div>
        {data && (data.refused_questions.length > 0 || data.low_rated_docs.length > 0) && (
          <button
            type="button"
            onClick={exportCsv}
            className="flex-shrink-0 rounded-lg border border-border bg-surface-glass px-3 py-1.5 text-xs font-medium text-content-secondary transition-colors hover:border-border-strong hover:text-content-primary"
          >
            {t("knowledgeGapsExport", locale)}
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 py-4 text-sm text-content-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-hidden />
          {t("knowledgeGapsLoading", locale)}
        </div>
      )}

      {error && (
        <p className="text-sm text-danger py-2">{error}</p>
      )}

      {isEmpty && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
          <span className="text-base" aria-hidden>✅</span>
          <p className="text-sm text-emerald-700 dark:text-emerald-400">
            {t("knowledgeGapsEmpty", locale)}
          </p>
        </div>
      )}

      {data && data.refused_questions.length > 0 && (
        <section className="mb-5">
          <p className="gap-section-title">
            <span aria-hidden>❓</span>
            {t("knowledgeGapsRefused", locale)}
          </p>
          <div className="space-y-2">
            {data.refused_questions.map((item, i) => (
              <div key={i} className="gap-item">
                <p className="gap-item-question">{item.question}</p>
                <span className="gap-item-badge gap-item-badge-refused">
                  {t("knowledgeGapsAskedTimes", locale, { count: item.count })}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {data && data.low_rated_docs.length > 0 && (
        <section>
          <p className="gap-section-title">
            <span aria-hidden>👎</span>
            {t("knowledgeGapsLowRated", locale)}
          </p>
          <div className="space-y-2">
            {data.low_rated_docs.map((doc, i) => (
              <div key={i} className="gap-item">
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <p className="gap-item-question truncate">{doc.title}</p>
                  {doc.url && (
                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-brand hover:underline"
                    >
                      <ExternalLink size="xs" />
                      {doc.url.replace(/^https?:\/\//, "").slice(0, 50)}
                    </a>
                  )}
                </div>
                <span className="gap-item-badge gap-item-badge-down">
                  {t("knowledgeGapsDownRating", locale, { down: doc.down, up: doc.up })}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </Card>
  );
}
