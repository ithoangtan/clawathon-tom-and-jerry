import { useRef, useState, useEffect } from "react";
import { gsap } from "@/lib/gsap";
import {
  CheckCircle2,
  XCircle,
  Mail,
  Timer,
  RotateCcw,
  FileText,
  BookOpen,
  Scale,
  ClipboardList,
  LayoutGrid,
} from "lucide-react";
import { SectionLabel } from "./S1Problem";

const subSteps = [
  { icon: FileText, text: "Đọc ticket Jira..." },
  { icon: BookOpen, text: "Lấy Risk Playbook từ Confluence..." },
  { icon: Scale, text: "Đối chiếu policy hiện tại..." },
  { icon: ClipboardList, text: "Soạn Quick Risk Report..." },
];

const otherUseCases = [
  "Compliance review",
  "Partner due diligence",
  "Onboarding checklist",
  "Incident triage",
  "Policy Q&A",
  "và nhiều hơn nữa...",
];

export function S2Demo() {
  const [isHighRisk, setIsHighRisk] = useState(false);
  // Ref mirrors state so animation callbacks always read the latest value
  const isHighRiskRef = useRef(false);
  const hasEnteredRef = useRef(false);
  const loopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tlRef = useRef<gsap.core.Timeline | null>(null);

  const sectionRef = useRef<HTMLElement>(null);
  const node1Ref = useRef<HTMLDivElement>(null);
  const node2Ref = useRef<HTMLDivElement>(null);
  const node3Ref = useRef<HTMLDivElement>(null);
  const arrow1Ref = useRef<HTMLDivElement>(null);
  const arrow2Ref = useRef<HTMLDivElement>(null);
  const subPanelRef = useRef<HTMLDivElement>(null);
  const stepRefs = [
    useRef<HTMLDivElement>(null),
    useRef<HTMLDivElement>(null),
    useRef<HTMLDivElement>(null),
    useRef<HTMLDivElement>(null),
  ];
  const spinnerRef = useRef<HTMLDivElement>(null);
  const checkmarkRef = useRef<HTMLDivElement>(null);
  const approvedRef = useRef<HTMLDivElement>(null);
  const rejectedRef = useRef<HTMLDivElement>(null);
  const notifyCardRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<HTMLDivElement>(null);

  // All reads are from refs — safe to call from stale closures
  const playAnim = () => {
    tlRef.current?.kill();
    const hr = isHighRiskRef.current;

    if (!node1Ref.current) return;

    gsap.set(node1Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
    gsap.set(node2Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
    gsap.set(node3Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
    gsap.set([arrow1Ref.current, arrow2Ref.current], { scaleX: 0, transformOrigin: "left" });
    gsap.set(subPanelRef.current, { maxHeight: 0, opacity: 0 });
    stepRefs.forEach((r) => gsap.set(r.current, { opacity: 0, x: -10 }));
    gsap.set(spinnerRef.current, { opacity: 1 });
    gsap.set(checkmarkRef.current, { opacity: 0, scale: 0 });
    gsap.set(approvedRef.current, { opacity: 0, y: 10 });
    gsap.set(rejectedRef.current, { opacity: 0, y: 10 });
    gsap.set(notifyCardRef.current, { opacity: 0, x: 28 });
    gsap.set(timerRef.current, { opacity: 0, scale: 0.85 });

    const tl = gsap.timeline();

    tl
      .to(node1Ref.current, {
        opacity: 1,
        borderColor: "#0068ff",
        boxShadow: "0 0 0 1px rgba(0,104,255,0.25), 0 0 16px rgba(0,104,255,0.2)",
        duration: 0.45,
        ease: "power2.out",
      })
      .to(arrow1Ref.current, { scaleX: 1, duration: 0.4, ease: "power2.inOut" }, "+=0.3")
      .to(node2Ref.current, {
        opacity: 1,
        borderColor: "#0068ff",
        boxShadow: "0 0 0 1px rgba(0,104,255,0.25), 0 0 16px rgba(0,104,255,0.2)",
        duration: 0.45,
        ease: "power2.out",
      })
      .to(arrow2Ref.current, { scaleX: 1, duration: 0.4, ease: "power2.inOut" }, "+=0.3")
      .to(node3Ref.current, {
        opacity: 1,
        borderColor: "#0068ff",
        boxShadow: "0 0 0 1px rgba(0,104,255,0.25), 0 0 20px rgba(0,104,255,0.25)",
        duration: 0.45,
        ease: "power2.out",
      })
      .to(subPanelRef.current, { maxHeight: 220, opacity: 1, duration: 0.45, ease: "power2.out" }, "+=0.2")
      .to(stepRefs[0].current, { opacity: 1, x: 0, duration: 0.3, ease: "power2.out" })
      .to(stepRefs[1].current, { opacity: 1, x: 0, duration: 0.3, ease: "power2.out" }, "+=0.45")
      .to(stepRefs[2].current, { opacity: 1, x: 0, duration: 0.3, ease: "power2.out" }, "+=0.45")
      .to(stepRefs[3].current, { opacity: 1, x: 0, duration: 0.3, ease: "power2.out" }, "+=0.45")
      .to(spinnerRef.current, { opacity: 0, duration: 0.2 }, "+=0.55")
      .to(checkmarkRef.current, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.5)" }, "-=0.1")
      .to(
        node3Ref.current,
        {
          borderColor: hr ? "#f87171" : "#34d399",
          boxShadow: hr
            ? "0 0 0 1px rgba(248,113,113,0.3), 0 0 16px rgba(248,113,113,0.2)"
            : "0 0 0 1px rgba(52,211,153,0.3), 0 0 16px rgba(52,211,153,0.2)",
          duration: 0.35,
        },
        "-=0.2",
      )
      .to(
        hr ? rejectedRef.current : approvedRef.current,
        { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" },
        "+=0.2",
      )
      .to(notifyCardRef.current, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }, "+=0.25")
      .to(timerRef.current, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.5)" }, "+=0.3")
      .call(() => {
        // Schedule auto-toggle to opposite risk after a pause
        loopTimerRef.current = setTimeout(() => {
          loopTimerRef.current = null;
          const next = !isHighRiskRef.current;
          isHighRiskRef.current = next;
          setIsHighRisk(next);
          playAnim();
        }, 2200);
      });

    tlRef.current = tl;
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    // Set initial hidden states before first play
    if (node1Ref.current) {
      gsap.set(node1Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
      gsap.set(node2Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
      gsap.set(node3Ref.current, { opacity: 0.35, borderColor: "var(--color-border)", boxShadow: "none" });
      gsap.set([arrow1Ref.current, arrow2Ref.current], { scaleX: 0, transformOrigin: "left" });
      gsap.set(subPanelRef.current, { maxHeight: 0, opacity: 0 });
      stepRefs.forEach((r) => gsap.set(r.current, { opacity: 0, x: -10 }));
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasEnteredRef.current) {
          hasEnteredRef.current = true;
          playAnim();
          observer.disconnect();
        }
      },
      { threshold: 0.2 },
    );

    const section = sectionRef.current;
    if (section) observer.observe(section);

    return () => {
      observer.disconnect();
      tlRef.current?.kill();
      if (loopTimerRef.current) clearTimeout(loopTimerRef.current);
    };
  }, []); // intentionally empty — playAnim reads only from refs

  const cancelLoop = () => {
    if (loopTimerRef.current) {
      clearTimeout(loopTimerRef.current);
      loopTimerRef.current = null;
    }
  };

  const handleReplay = () => {
    cancelLoop();
    hasEnteredRef.current = true;
    playAnim();
  };

  const handleToggle = (high: boolean) => {
    cancelLoop();
    isHighRiskRef.current = high;
    setIsHighRisk(high);
    if (!hasEnteredRef.current) return;
    playAnim();
  };

  return (
    <section
      id="demo"
      ref={sectionRef}
      data-pitch-section
      className="relative py-24 px-4 sm:py-32 sm:px-6"
    >
      <div className="mx-auto max-w-6xl">
        {/* Section header */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SectionLabel>Demo</SectionLabel>
          <span
            className="rounded-full px-3 py-0.5 text-sm"
            style={{
              background: "var(--color-bg-elevated)",
              color: "var(--color-text-muted)",
              border: "1px solid var(--color-border)",
            }}
          >
            1 trong nhiều workflows
          </span>
        </div>

        <h2
          className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl"
          style={{ color: "var(--color-text-primary)" }}
        >
          Risk Review Workflow
        </h2>

        {/* Framing note */}
        <blockquote
          className="mb-10 max-w-3xl rounded-xl border-l-4 py-3 pl-5 text-base italic leading-relaxed"
          style={{
            borderColor: "var(--color-brand)",
            color: "var(--color-text-secondary)",
          }}
        >
          "Để hình dung cụ thể — đây là 1 trong những workflow đầu tiên chúng tôi xây: Risk Review
          cho campaign. Cùng kiến trúc này có thể áp dụng cho{" "}
          <span style={{ color: "var(--color-text-primary)", fontStyle: "normal", fontWeight: 600 }}>
            bất kỳ quy trình nào cần kiến thức nền để suy luận.
          </span>
          "
        </blockquote>

        {/* Risk toggle */}
        <div className="mb-10 flex flex-wrap items-center gap-3">
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Thử với:
          </span>
          <button
            onClick={() => handleToggle(false)}
            className="rounded-lg px-4 py-1.5 text-sm font-semibold transition-all duration-200"
            style={
              !isHighRisk
                ? { background: "var(--color-success)", color: "#fff", boxShadow: "0 0 12px rgba(52,211,153,0.4)" }
                : { background: "var(--color-success-muted)", color: "var(--color-success)", border: "1px solid rgba(52,211,153,0.3)" }
            }
          >
            ✓ LOW Risk
          </button>
          <button
            onClick={() => handleToggle(true)}
            className="rounded-lg px-4 py-1.5 text-sm font-semibold transition-all duration-200"
            style={
              isHighRisk
                ? { background: "var(--color-danger)", color: "#fff", boxShadow: "0 0 12px rgba(248,113,113,0.4)" }
                : { background: "var(--color-danger-muted)", color: "var(--color-danger)", border: "1px solid rgba(248,113,113,0.3)" }
            }
          >
            ✗ HIGH Risk
          </button>
        </div>

        {/* ─── MAIN WORKFLOW DIAGRAM ─── */}
        <div className="glass-panel overflow-hidden rounded-2xl p-6 sm:p-8">

          {/* Top row: 3 nodes + arrows */}
          <div className="flex items-start gap-3 overflow-x-auto pb-2 sm:gap-4">

            <WorkflowNode ref={node1Ref} icon="📋" label="TICKET TẠO" badge="NEW" badgeColor="var(--color-text-muted)" />
            <FlowArrow ref={arrow1Ref} />
            <WorkflowNode ref={node2Ref} icon="⚡" label="RISK REVIEW" badge="TRIGGERED" badgeColor="var(--color-brand)" />
            <FlowArrow ref={arrow2Ref} />

            {/* Node 3: Agent */}
            <div
              ref={node3Ref}
              className="relative flex-shrink-0 rounded-xl border px-4 py-3 transition-all duration-300"
              style={{ minWidth: 180, borderColor: "var(--color-border)", background: "var(--color-bg-elevated)" }}
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="text-base">🤖</span>
                <div ref={spinnerRef} className="h-3.5 w-3.5 flex-shrink-0">
                  <svg className="animate-spin" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="rgba(0,104,255,0.25)" strokeWidth="2" />
                    <path d="M 8 2 A 6 6 0 0 1 14 8" stroke="#0068ff" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </div>
                <div ref={checkmarkRef} className="absolute" style={{ left: 30, top: 10, opacity: 0 }}>
                  <CheckCircle2 size={16} style={{ color: isHighRisk ? "var(--color-danger)" : "var(--color-success)" }} />
                </div>
                <span className="text-sm font-bold tracking-wide" style={{ color: "var(--color-text-primary)" }}>
                  AGENT ĐANG LÀM
                </span>
              </div>

              <div ref={subPanelRef} className="overflow-hidden" style={{ maxHeight: 0, opacity: 0 }}>
                <div
                  className="mt-2 rounded-lg p-3"
                  style={{ background: "rgba(0,104,255,0.06)", border: "1px solid rgba(0,104,255,0.15)" }}
                >
                  {subSteps.map((step, i) => {
                    const Icon = step.icon;
                    return (
                      <div key={i} ref={stepRefs[i]} className="flex items-center gap-2 py-1">
                        <Icon size={12} style={{ color: "var(--color-brand)", flexShrink: 0 }} />
                        <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                          {step.text}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Outcome row */}
          <div className="mt-6 flex flex-wrap gap-4 pl-2">
            <div
              ref={approvedRef}
              className="flex items-center gap-3 rounded-xl border px-4 py-3"
              style={{ borderColor: "rgba(52,211,153,0.4)", background: "var(--color-success-muted)", opacity: 0 }}
            >
              <CheckCircle2 size={18} style={{ color: "var(--color-success)", flexShrink: 0 }} />
              <div>
                <div className="text-sm font-bold" style={{ color: "var(--color-success)" }}>LOW RISK</div>
                <div className="text-sm" style={{ color: "var(--color-text-secondary)" }}>Notify Risk PIC để approve</div>
              </div>
            </div>

            <div
              ref={rejectedRef}
              className="flex items-center gap-3 rounded-xl border px-4 py-3"
              style={{ borderColor: "rgba(248,113,113,0.4)", background: "var(--color-danger-muted)", opacity: 0 }}
            >
              <XCircle size={18} style={{ color: "var(--color-danger)", flexShrink: 0 }} />
              <div>
                <div className="text-sm font-bold" style={{ color: "var(--color-danger)" }}>HIGH RISK</div>
                <div className="text-sm" style={{ color: "var(--color-text-secondary)" }}>Trả ticket ngay, ghi rõ lý do</div>
              </div>
            </div>
          </div>

          {/* Notification + Timer row */}
          <div className="mt-6 flex flex-wrap items-start gap-4">
            <div
              ref={notifyCardRef}
              className="flex items-start gap-3 rounded-xl border px-4 py-3"
              style={{ borderColor: "var(--color-border-brand)", background: "var(--color-brand-muted)", opacity: 0 }}
            >
              <Mail size={16} style={{ color: "var(--color-brand)", flexShrink: 0, marginTop: 2 }} />
              <div>
                <div className="text-sm font-semibold" style={{ color: "var(--color-brand)" }}>
                  {isHighRisk ? "Ticket bị reject — gửi notify cho người tạo" : "Risk: LOW — Gửi notify cho Risk PIC"}
                </div>
                <div className="mt-0.5 text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  {isHighRisk ? "Ghi rõ lý do, đề xuất hướng sửa" : "Risk PIC review nhanh và approve"}
                </div>
              </div>
            </div>

            <div
              ref={timerRef}
              className="flex items-center gap-2 rounded-xl border px-4 py-3"
              style={{ borderColor: "var(--color-border-strong)", background: "var(--color-bg-elevated)", opacity: 0 }}
            >
              <Timer size={16} style={{ color: "var(--color-accent)" }} />
              <span className="text-sm font-bold" style={{ color: "var(--color-text-primary)" }}>
                ⏱ ~10–15 phút
              </span>
            </div>
          </div>
        </div>

        {/* Replay button */}
        <button
          onClick={handleReplay}
          className="mt-5 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200"
          style={{ color: "var(--color-text-secondary)", border: "1px solid var(--color-border)", background: "var(--color-bg-elevated)" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--color-text-primary)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--color-text-secondary)"; }}
        >
          <RotateCcw size={13} /> Xem lại
        </button>

        {/* Expansion: other use cases */}
        <div className="mt-14">
          <p className="mb-4 flex items-center gap-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
            <LayoutGrid size={15} style={{ color: "var(--color-brand)" }} />
            Cùng kiến trúc này có thể áp dụng cho:
          </p>
          <div className="flex flex-wrap gap-2">
            {otherUseCases.map((uc, i) => (
              <span
                key={i}
                className="rounded-full px-4 py-1.5 text-sm font-medium"
                style={
                  i === otherUseCases.length - 1
                    ? { color: "var(--color-text-muted)", border: "1px dashed var(--color-border)", fontStyle: "italic" }
                    : { background: "var(--color-brand-muted)", color: "var(--color-brand)", border: "1px solid rgba(0,104,255,0.25)" }
                }
              >
                {uc}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Sub-components ──────────────────────────────────────────────────

import { forwardRef } from "react";

interface WorkflowNodeProps {
  icon: string;
  label: string;
  badge?: string;
  badgeColor?: string;
}

const WorkflowNode = forwardRef<HTMLDivElement, WorkflowNodeProps>(
  ({ icon, label, badge, badgeColor }, ref) => (
    <div
      ref={ref}
      className="flex-shrink-0 rounded-xl border px-4 py-3 transition-all duration-300"
      style={{ minWidth: 130, borderColor: "var(--color-border)", background: "var(--color-bg-elevated)" }}
    >
      <div className="mb-1.5 text-base">{icon}</div>
      <div className="text-sm font-bold tracking-wide" style={{ color: "var(--color-text-primary)" }}>
        {label}
      </div>
      {badge && (
        <div
          className="mt-1.5 inline-block rounded-full px-2 py-0.5 text-sm font-semibold"
          style={{ background: `color-mix(in srgb, ${badgeColor} 15%, transparent)`, color: badgeColor }}
        >
          {badge}
        </div>
      )}
    </div>
  ),
);
WorkflowNode.displayName = "WorkflowNode";

const FlowArrow = forwardRef<HTMLDivElement>((_, ref) => (
  <div className="flex flex-1 items-center gap-0 pt-5" style={{ minWidth: 32 }}>
    <div
      ref={ref}
      className="h-px flex-1"
      style={{
        background: "linear-gradient(to right, var(--color-border-brand), var(--color-brand))",
        transformOrigin: "left",
        transform: "scaleX(0)",
      }}
    />
    <div
      className="h-0 w-0"
      style={{
        borderTop: "5px solid transparent",
        borderBottom: "5px solid transparent",
        borderLeft: "7px solid var(--color-brand)",
        flexShrink: 0,
      }}
    />
  </div>
));
FlowArrow.displayName = "FlowArrow";
