import { Button } from "@/components/ui/Button";
import { ThumbsDown, ThumbsUp } from "@/components/ui/icons";
import { api } from "@/lib/apiClient";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { getUserContext, useUserStore } from "@/store/userStore";
import { useCallback, useState } from "react";

interface FeedbackBarProps {
  feedbackId: string;
}

export function FeedbackBar({ feedbackId }: FeedbackBarProps) {
  const locale = useUserStore((s) => s.locale);
  const [rating, setRating] = useState<"up" | "down" | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
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
        setDone(true);
      } catch (e) {
        setError(e instanceof Error ? e.message : t("errorGeneric", locale));
      } finally {
        setSubmitting(false);
      }
    },
    [comment, feedbackId, locale],
  );

  if (done) {
    return (
      <p className="text-sm text-emerald-600" role="status" aria-live="polite">
        {t("feedbackThanks", locale)}
      </p>
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
