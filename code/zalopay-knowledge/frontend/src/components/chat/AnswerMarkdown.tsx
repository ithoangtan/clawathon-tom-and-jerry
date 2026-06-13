import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { classNames } from "@/lib/format";
import type { Citation } from "@/lib/types";

interface AnswerMarkdownProps {
  /** Markdown answer body with optional inline [n] citation markers. */
  answer: string;
  citations: Citation[];
  onCitationClick?: (index: number) => void;
  streaming?: boolean;
}

/**
 * FR-2 grounded answer renderer.
 * Full GFM (tables, lists, blockquotes, task lists) plus syntax-highlighted
 * fenced code blocks with per-block copy via {@link CodeBlock}.
 */
export function AnswerMarkdown({
  answer,
  citations,
  onCitationClick,
  streaming,
}: AnswerMarkdownProps) {
  return (
    <MarkdownRenderer
      content={answer}
      citations={citations}
      onCitationClick={onCitationClick}
      streaming={streaming}
      className={classNames(
        "answer-markdown",
        streaming && "streaming-shimmer",
      )}
    />
  );
}
