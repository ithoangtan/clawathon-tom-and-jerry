import { ArrowRight } from "lucide-react";

export interface FlowNode {
  id: string;
  label: string;
  sublabel?: string;
  color?: string;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
}

interface FlowDiagramProps {
  nodes: FlowNode[];
  edges?: FlowEdge[];
  renderer?: "svg" | "reactflow" | "mermaid";
  className?: string;
}

/**
 * Abstracted flow diagram. renderer="svg" is built-in.
 * Swap to "reactflow" or "mermaid" by installing the lib and returning
 * the appropriate renderer — the nodes/edges data stays the same.
 */
export function FlowDiagram({ nodes, renderer = "svg", className = "" }: FlowDiagramProps) {
  if (renderer !== "svg") {
    return (
      <div className="rounded-lg border border-dashed border-[var(--color-border)] p-4 text-sm text-[var(--color-text-muted)]">
        Renderer &ldquo;{renderer}&rdquo; not installed yet.
      </div>
    );
  }

  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      {nodes.map((node, i) => (
        <div key={node.id} className="flex items-center gap-3">
          {i > 0 && (
            <ArrowRight
              size={16}
              className="flex-shrink-0"
              style={{ color: "var(--color-text-muted)" }}
            />
          )}
          <div
            className="glass-panel rounded-xl px-5 py-3 text-sm font-semibold text-center min-w-[130px]"
            style={{ borderColor: node.color ?? "var(--color-border-brand)" }}
          >
            <div style={{ color: "var(--color-text-primary)" }}>{node.label}</div>
            {node.sublabel && (
              <div className="mt-1 text-sm" style={{ color: "var(--color-text-muted)" }}>
                {node.sublabel}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
