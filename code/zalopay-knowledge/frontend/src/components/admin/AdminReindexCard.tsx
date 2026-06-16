import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { AlertTriangle, Trash2 } from "@/components/ui/icons";
import { api, ApiError } from "@/lib/apiClient";
import { t } from "@/lib/i18n";
import { getUserContext, useUserStore } from "@/store/userStore";

type Phase = "idle" | "confirm" | "running" | "done" | "error";

export function AdminReindexCard() {
  const locale = useUserStore((s) => s.locale);
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<{
    cleared_sync_sources: number;
    deleted_indexes: string[];
  } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleConfirm() {
    setPhase("running");
    setErrorMsg(null);
    try {
      const res = await api.adminReindex(getUserContext());
      setResult({
        cleared_sync_sources: res.cleared_sync_sources,
        deleted_indexes: res.deleted_indexes,
      });
      setPhase("done");
    } catch (e) {
      setErrorMsg(
        e instanceof ApiError ? (e.detail ?? e.message) : t("adminReindexFailed", locale),
      );
      setPhase("error");
    }
  }

  return (
    <Card>
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600"
          aria-hidden
        >
          <Trash2 size="md" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-800">{t("adminReindexTitle", locale)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{t("adminReindexSubtitle", locale)}</p>
        </div>
      </div>

      {phase === "idle" && (
        <div className="mt-4">
          <Button
            variant="secondary"
            onClick={() => setPhase("confirm")}
            className="border-red-200 text-red-600 hover:bg-red-50"
          >
            {t("adminReindexButton", locale)}
          </Button>
        </div>
      )}

      {phase === "confirm" && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex gap-2 text-amber-800">
            <AlertTriangle size="sm" className="mt-0.5 flex-shrink-0" />
            <p className="text-sm">{t("adminReindexWarning", locale)}</p>
          </div>
          <div className="mt-3 flex gap-2">
            <Button
              variant="primary"
              onClick={handleConfirm}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-500"
            >
              {t("adminReindexConfirm", locale)}
            </Button>
            <Button variant="secondary" onClick={() => setPhase("idle")}>
              {t("adminReindexCancel", locale)}
            </Button>
          </div>
        </div>
      )}

      {phase === "running" && (
        <p className="mt-4 text-sm text-slate-500" role="status">
          {t("adminReindexRunning", locale)}
        </p>
      )}

      {phase === "done" && result && (
        <div className="mt-4 space-y-1">
          <p className="text-sm text-emerald-700" role="status">
            {t("adminReindexDone", locale)}
          </p>
          <ul className="ml-1 space-y-0.5 text-xs text-slate-500">
            <li>
              {t("adminReindexClearedRows", locale, { n: String(result.cleared_sync_sources) })}
            </li>
            {result.deleted_indexes.length > 0 && (
              <li>
                {t("adminReindexDeletedIndexes", locale, {
                  n: String(result.deleted_indexes.length),
                })}
                {": "}
                <span className="font-mono">{result.deleted_indexes.join(", ")}</span>
              </li>
            )}
          </ul>
          <Button
            variant="secondary"
            onClick={() => { setPhase("idle"); setResult(null); }}
            className="mt-2"
          >
            {t("adminReindexCancel", locale)}
          </Button>
        </div>
      )}

      {phase === "error" && (
        <div className="mt-4 space-y-2">
          <p className="text-sm text-red-600" role="alert">
            {errorMsg ?? t("adminReindexFailed", locale)}
          </p>
          <Button variant="secondary" onClick={() => setPhase("idle")}>
            {t("adminReindexCancel", locale)}
          </Button>
        </div>
      )}
    </Card>
  );
}
