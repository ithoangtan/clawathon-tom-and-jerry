import type { ReactNode } from "react";
import type { Citation } from "@/lib/types";

export interface CitationMarkerOptions {
  citations: Citation[];
  onCitationClick?: (index: number) => void;
}

/** Turn [n] citation markers in plain text into clickable links or buttons. */
export function renderCitationMarkers(
  text: string,
  { citations, onCitationClick }: CitationMarkerOptions,
): ReactNode {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (!match) return part;

    const index = parseInt(match[1], 10);
    const citation = citations[index - 1];
    if (!citation) return part;

    if (onCitationClick) {
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCitationClick(index)}
          className="citation-link"
          title={citation.title}
          aria-label={`Citation ${index}: ${citation.title}`}
        >
          {index}
        </button>
      );
    }

    return (
      <a
        key={i}
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="citation-link"
        title={citation.title}
        aria-label={`Citation ${index}: ${citation.title}`}
      >
        {index}
      </a>
    );
  });
}

/** Recursively process React children to linkify citation markers in strings. */
export function processCitationChildren(
  children: ReactNode,
  options: CitationMarkerOptions,
): ReactNode {
  if (typeof children === "string") {
    return renderCitationMarkers(children, options);
  }
  if (Array.isArray(children)) {
    return children.map((child, i) =>
      typeof child === "string" ? (
        <span key={i}>{renderCitationMarkers(child, options)}</span>
      ) : (
        child
      ),
    );
  }
  return children;
}
