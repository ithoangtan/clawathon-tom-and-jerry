import { CodeBlock } from "@/components/markdown/CodeBlock";
import { processCitationChildren } from "@/components/markdown/citationMarkers";
import { classNames } from "@/lib/format";
import type { Citation } from "@/lib/types";
import type { ReactNode } from "react";
import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

export interface MarkdownRendererProps {
  content: string;
  /** When provided, [n] markers in text become citation links. */
  citations?: Citation[];
  /** Opens the evidence inspector instead of navigating when set. */
  onCitationClick?: (index: number) => void;
  className?: string;
  streaming?: boolean;
}

/**
 * Full GFM markdown renderer for chat messages.
 * Re-renders incrementally as `content` grows — suitable for SSE streaming.
 */
export function MarkdownRenderer({
  content,
  citations = [],
  onCitationClick,
  className,
  streaming,
}: MarkdownRendererProps) {
  const withCitations = citations.length > 0;
  const citationOptions = useMemo(
    () => ({ citations, onCitationClick }),
    [citations, onCitationClick],
  );

  const components = useMemo<Components>(() => {
    const wrap = (children: ReactNode) =>
      withCitations ? processCitationChildren(children, citationOptions) : children;

    return {
      h1: ({ children }) => (
        <h1 className="mb-3 mt-6 text-xl font-semibold first:mt-0">
          {wrap(children)}
        </h1>
      ),
      h2: ({ children }) => (
        <h2 className="mb-2 mt-5 text-lg font-semibold first:mt-0">
          {wrap(children)}
        </h2>
      ),
      h3: ({ children }) => (
        <h3 className="mb-2 mt-4 text-base font-semibold first:mt-0">
          {wrap(children)}
        </h3>
      ),
      h4: ({ children }) => (
        <h4 className="mb-1.5 mt-3 text-sm font-semibold first:mt-0">
          {wrap(children)}
        </h4>
      ),
      p: ({ children }) => (
        <p className="my-3 leading-7 first:mt-0 last:mb-0">
          {wrap(children)}
        </p>
      ),
      ul: ({ children }) => (
        <ul className="my-3 list-disc space-y-1.5 pl-6">{children}</ul>
      ),
      ol: ({ children }) => (
        <ol className="my-3 list-decimal space-y-1.5 pl-6">{children}</ol>
      ),
      li: ({ children }) => (
        <li className="leading-7 [&>p]:my-1">{wrap(children)}</li>
      ),
      blockquote: ({ children }) => (
        <blockquote className="my-4">{children}</blockquote>
      ),
      hr: () => <hr className="my-6 border-slate-200/80" />,
      strong: ({ children }) => (
        <strong className="font-semibold text-slate-900">{wrap(children)}</strong>
      ),
      em: ({ children }) => <em className="italic">{wrap(children)}</em>,
      del: ({ children }) => (
        <del className="text-slate-500 line-through">{wrap(children)}</del>
      ),
      a: ({ href, children }) => (
        <a href={href} target="_blank" rel="noopener noreferrer">
          {wrap(children)}
        </a>
      ),
      table: ({ children }) => (
        <div className="my-4 overflow-x-auto rounded-lg border border-slate-200/80">
          <table className="min-w-full divide-y divide-slate-200 text-sm">{children}</table>
        </div>
      ),
      thead: ({ children }) => <thead className="bg-slate-50/80">{children}</thead>,
      tbody: ({ children }) => <tbody className="divide-y divide-slate-100 bg-white/80">{children}</tbody>,
      tr: ({ children }) => <tr>{children}</tr>,
      th: ({ children }) => (
        <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
          {wrap(children)}
        </th>
      ),
      td: ({ children }) => (
        <td className="px-4 py-2.5 text-slate-800">{wrap(children)}</td>
      ),
      input: ({ checked, disabled, type }) => {
        if (type === "checkbox") {
          return (
            <input
              type="checkbox"
              checked={checked}
              disabled={disabled ?? true}
              readOnly
              className="mr-2 rounded border-slate-300 text-brand focus:ring-brand"
            />
          );
        }
        return <input type={type} checked={checked} disabled={disabled} readOnly />;
      },
      pre: ({ children }) => <>{children}</>,
      code: ({ className: codeClassName, children }) => {
        const text = String(children).replace(/\n$/, "");
        const match = /language-(\w+)/.exec(codeClassName ?? "");
        if (match) {
          return <CodeBlock code={text} language={match[1]} />;
        }
        return <code>{wrap(children)}</code>;
      },
    };
  }, [citationOptions, withCitations]);

  if (!content.trim()) return null;

  return (
    <div
      className={classNames(
        "prose-chat streaming-text",
        streaming && "is-streaming",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
