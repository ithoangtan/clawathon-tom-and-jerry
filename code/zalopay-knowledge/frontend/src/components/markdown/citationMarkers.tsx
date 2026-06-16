import type { ReactNode } from "react";
import type { Citation } from "@/lib/types";

export interface CitationMarkerOptions {
  citations: Citation[];
  onCitationClick?: (index: number) => void;
}

function renderSingleCitation(
  index: number,
  citation: Citation,
  key: string | number,
  onCitationClick?: (index: number) => void,
): ReactNode {
  if (onCitationClick) {
    return (
      <button
        key={key}
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
      key={key}
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
}

/** Turn [n] or [n,m,...] citation markers in plain text into clickable links or buttons. */
export function renderCitationMarkers(
  text: string,
  { citations, onCitationClick }: CitationMarkerOptions,
): ReactNode {
  // Match both [n] and [n,m,...] patterns
  const parts = text.split(/(\[\d+(?:,\s*\d+)*\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+(?:,\s*\d+)*)\]$/);
    if (!match) return part;

    const indices = match[1].split(",").map((s) => parseInt(s.trim(), 10));

    const buttons = indices.flatMap((index, j) => {
      const citation = citations[index - 1];
      if (!citation) return [];
      return [renderSingleCitation(index, citation, `${i}-${j}`, onCitationClick)];
    });

    return buttons.length > 0 ? buttons : part;
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
