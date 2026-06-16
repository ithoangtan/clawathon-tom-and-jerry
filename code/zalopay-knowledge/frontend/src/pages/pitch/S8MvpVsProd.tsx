import { ArrowRight } from "lucide-react";
import { SectionLabel } from "./S1Problem";
import { FlowDiagram } from "./FlowDiagram";

const flowNodes = [
  { id: "docs", label: "Tài liệu", sublabel: "Confluence / GDrive" },
  { id: "knowledge", label: "Kiến thức được lưu", sublabel: "Vector index + memory" },
  { id: "action", label: "Hành động", sublabel: "Chat · Workflow · Notify" },
];

const rows = [
  { label: "Tài liệu nguồn", mvp: "Confluence cá nhân + Google Drive", prod: "Confluence công ty (toàn Zalopay)" },
  { label: "Jira", mvp: "Jira cá nhân", prod: "Jira công ty" },
  { label: "Thông báo", mvp: "Gmail", prod: "Teams / Jira & Confluence native notification" },
  { label: "Hạ tầng", mvp: "GreenNode AgentBase", prod: "Self-hosted tại Zalopay — data không ra ngoài" },
  { label: "AI Model", mvp: "VNG MaaS — Qwen", prod: "Theo từng workflow: model nhẹ cho screening, model mạnh cho reasoning" },
  { label: "Tích hợp", mvp: "Direct API call", prod: "MCP (Model Context Protocol) — thêm tool mới không cần sửa agent" },
  { label: "Security", mvp: "Auth cơ bản", prod: "SSO (Zalopay IAM) · RBAC · Audit log" },
  { label: "Sync knowledge", mvp: "Manual", prod: "Auto-sync khi Confluence thay đổi" },
];

const prodExtras = [
  "Human-in-the-loop: escalate tự động khi AI confidence thấp",
  "Audit trail: mọi reasoning AI đều được log đầy đủ",
  "Workflow versioning: policy thay đổi → workflow tự cập nhật",
  "Data residency: tất cả dữ liệu trong hạ tầng Zalopay",
];

export function S8MvpVsProd() {
  return (
    <section
      id="mvp-prod"
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        <div data-reveal className="mb-4">
          <SectionLabel>Architecture</SectionLabel>
        </div>
        <h2
          data-reveal
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          MVP → Production
        </h2>
        <p
          data-reveal
          className="mb-10 max-w-2xl text-base leading-relaxed sm:text-lg"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Cùng kiến trúc — chỉ khác về quy mô và hạ tầng. Ba bước cốt lõi không thay đổi.
        </p>

        {/* Flow */}
        <div data-reveal className="mb-12">
          <FlowDiagram nodes={flowNodes} renderer="svg" />
        </div>

        {/* Comparison table */}
        <div data-reveal className="overflow-hidden rounded-2xl border" style={{ borderColor: "var(--color-border)" }}>
          {/* Header */}
          <div
            className="grid grid-cols-3 border-b text-sm font-bold uppercase tracking-wider"
            style={{ borderColor: "var(--color-border)", background: "var(--color-bg-elevated)" }}
          >
            <div className="px-5 py-4" style={{ color: "var(--color-text-muted)" }}>Thành phần</div>
            <div
              className="border-x px-5 py-4"
              style={{ borderColor: "var(--color-border)", color: "var(--color-warning)" }}
            >
              MVP (Demo)
            </div>
            <div className="px-5 py-4" style={{ color: "var(--color-success)" }}>
              Production
            </div>
          </div>

          {/* Rows */}
          {rows.map((row, i) => (
            <div
              key={i}
              className="grid grid-cols-3 border-b text-sm transition-colors last:border-0"
              style={{
                borderColor: "var(--color-border)",
                background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)",
              }}
            >
              <div
                className="px-5 py-4 font-medium"
                style={{ color: "var(--color-text-secondary)" }}
              >
                {row.label}
              </div>
              <div
                className="border-x px-5 py-4 text-sm leading-relaxed"
                style={{ borderColor: "var(--color-border)", color: "var(--color-text-secondary)" }}
              >
                {row.mvp}
              </div>
              <div
                className="px-5 py-4 text-sm leading-relaxed"
                style={{ color: "var(--color-text-primary)" }}
              >
                {row.prod}
              </div>
            </div>
          ))}
        </div>

        {/* Prod extras */}
        <div data-reveal className="mt-6 rounded-2xl border p-6" style={{ borderColor: "var(--color-border-brand)", background: "var(--color-brand-muted)" }}>
          <p className="mb-4 text-sm font-bold uppercase tracking-wider" style={{ color: "var(--color-brand)" }}>
            Production — thêm
          </p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {prodExtras.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
                <ArrowRight size={12} className="mt-0.5 flex-shrink-0" style={{ color: "var(--color-brand)" }} />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
