import { Button } from "@/components/ui/Button";
import { ThumbsDown, ThumbsUp } from "@/components/ui/icons";
import { api } from "@/lib/apiClient";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { getUserContext, useUserStore } from "@/store/userStore";
import { useCallback, useState } from "react";

const STORAGE_PREFIX = "feedback:";

function loadPersistedRating(feedbackId: string): "up" | "down" | null {
  try {
    const v = localStorage.getItem(STORAGE_PREFIX + feedbackId);
    if (v === "up" || v === "down") return v;
  } catch {
    // ignore
  }
  return null;
}

function persistRating(feedbackId: string, rating: "up" | "down") {
  try {
    localStorage.setItem(STORAGE_PREFIX + feedbackId, rating);
  } catch {
    // ignore
  }
}

interface FeedbackBarProps {
  feedbackId: string;
  modelUsed?: string;
}

export function FeedbackBar({ feedbackId, modelUsed }: FeedbackBarProps) {
  const locale = useUserStore((s) => s.locale);
  const persisted = loadPersistedRating(feedbackId);
  const [rating, setRating] = useState<"up" | "down" | null>(persisted);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(persisted !== null);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (selected: "up" | "down", el?: HTMLButtonElement) => {
      if (el) runChipPop(el);

      setSubmitting(true);
      setError(null);
      setRating(selected);
      try {
        await api.feedback(
          {
            feedback_id: feedbackId,
            rating: selected,
            comment: comment.trim() ? comment.trim() : null,
          },
          getUserContext(),
        );
        persistRating(feedbackId, selected);
        setDone(true);
      } catch (e) {
        setError(e instanceof Error ? e.message : t("errorGeneric", locale));
      } finally {
        setSubmitting(false);
      }
    },
    [comment, feedbackId, locale],
  );

  if (done && rating !== null) {
    return (
      <div
        className="mt-4 border-t border-slate-100/80 pt-3"
        role="status"
        aria-live="polite"
      >
        <p className="text-xs text-slate-500 mb-2">{t("feedbackPrompt", locale)}</p>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant={rating === "up" ? "primary" : "secondary"}
            disabled
            aria-pressed={rating === "up"}
            aria-label={t("feedbackUp", locale)}
            className={rating !== "up" ? "opacity-30" : ""}
          >
            <ThumbsUp size="sm" />
          </Button>
          <Button
            variant={rating === "down" ? "primary" : "secondary"}
            disabled
            aria-pressed={rating === "down"}
            aria-label={t("feedbackDown", locale)}
            className={rating !== "down" ? "opacity-30" : ""}
          >
            <ThumbsDown size="sm" />
          </Button>
          <span className="text-xs text-emerald-600 ml-1">{t("feedbackThanks", locale)}</span>
          {modelUsed && (
            <span className="ml-auto text-[11px] text-slate-400">
              {t("modelUsedLabel", locale)}: <span className="font-medium text-slate-500">{modelUsed}</span>
            </span>
          )}
        </div>
      </div>
    );
  }

  const commentId = `feedback-comment-${feedbackId}`;

  return (
    <div
      data-feedback-bar
      className="mt-4 border-t border-slate-100/80 pt-3"
      role="group"
      aria-label={t("feedbackPrompt", locale)}
      aria-busy={submitting}
    >
      <p id={`${feedbackId}-prompt`} className="text-sm text-slate-600 mb-2">
        {t("feedbackPrompt", locale)}
      </p>

      {rating !== null && (
        <div className="mb-3">
          <label htmlFor={commentId} className="block text-xs text-slate-500 mb-1">
            {t("feedbackComment", locale)}
          </label>
          <textarea
            id={commentId}
            className="w-full rounded-lg border border-slate-200/80 bg-white/80 p-2 text-sm resize-y min-h-[60px] transition-shadow focus:border-brand focus:ring-1 focus:ring-brand/30"
            placeholder={t("feedbackCommentPlaceholder", locale)}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={2000}
            disabled={submitting}
            aria-describedby={`${feedbackId}-prompt`}
          />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant={rating === "up" ? "primary" : "secondary"}
          onClick={(e) => submit("up", e.currentTarget)}
          disabled={submitting}
          loading={submitting && rating === "up"}
          aria-pressed={rating === "up"}
          aria-label={t("feedbackUp", locale)}
        >
          <ThumbsUp size="sm" />
        </Button>
        <Button
          variant={rating === "down" ? "primary" : "secondary"}
          onClick={(e) => submit("down", e.currentTarget)}
          disabled={submitting}
          loading={submitting && rating === "down"}
          aria-pressed={rating === "down"}
          aria-label={t("feedbackDown", locale)}
        >
          <ThumbsDown size="sm" />
        </Button>
        {modelUsed && (
          <span className="ml-auto text-[11px] text-slate-400">
            {t("modelUsedLabel", locale)}: <span className="font-medium text-slate-500">{modelUsed}</span>
          </span>
        )}
      </div>

      {error && (
        <div className="mt-2 flex flex-wrap items-center gap-2" role="alert">
          <p className="text-sm text-red-600">{error}</p>
          {rating && (
            <Button
              variant="ghost"
              className="text-sm py-1 px-2"
              onClick={(e) => submit(rating, e.currentTarget)}
              disabled={submitting}
            >
              {t("retry", locale)}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
