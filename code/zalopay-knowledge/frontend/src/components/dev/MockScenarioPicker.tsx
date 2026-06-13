import { useState } from "react";
import { useLocation } from "react-router-dom";
import { CHAT_SCENARIOS, SCENARIOS, type ChatScenarioKey, type ScenarioKey } from "@/lib/mockScenarios";
import { useMockStore } from "@/store/mockStore";

type RouteContext = "chat" | "sync" | null;

function getRouteContext(pathname: string): RouteContext {
  if (pathname === "/" || pathname === "") return "chat";
  if (pathname === "/dashboard" || pathname === "/admin") return "sync";
  return null;
}

export function MockScenarioPicker() {
  const { pathname } = useLocation();
  const context = getRouteContext(pathname);
  const [open, setOpen] = useState(false);

  const { chatScenario, syncScenario, setChatScenario, setSyncScenario } = useMockStore();

  // Nothing to mock on this route
  if (!context) return null;

  const isChat = context === "chat";

  function handleSelect(key: string | null) {
    if (isChat) setChatScenario(key as ChatScenarioKey | null);
    else setSyncScenario(key as ScenarioKey | null);
    setOpen(false);
  }

  const activeKey = isChat ? chatScenario : syncScenario;
  const activeScenario = isChat
    ? CHAT_SCENARIOS.find((s) => s.key === activeKey) ?? null
    : SCENARIOS.find((s) => s.key === activeKey) ?? null;

  const routeLabel = isChat ? "Chat" : pathname === "/dashboard" ? "Dashboard" : "Admin";

  return (
    <div className="fixed bottom-4 left-1/2 z-[9999] -translate-x-1/2">
      {open ? (
        <div className="flex flex-col gap-1.5 rounded-2xl border border-white/10 bg-[#0f1117]/95 p-3 shadow-2xl backdrop-blur-md">
          <div className="mb-1 flex items-center justify-between px-1">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
              Dev · Mock · {routeLabel}
            </span>
            <button
              onClick={() => setOpen(false)}
              className="ml-4 rounded px-1.5 py-0.5 text-[10px] text-white/30 hover:text-white/60 transition-colors"
            >
              ✕
            </button>
          </div>

          <ScenarioOption
            label="Tắt mock (gọi API thật)"
            description="Kết nối backend thực"
            active={activeKey === null}
            dot="bg-white/20"
            onClick={() => handleSelect(null)}
          />

          <div className="my-0.5 h-px bg-white/10" />

          {isChat
            ? CHAT_SCENARIOS.map((s) => (
                <ScenarioOption
                  key={s.key}
                  label={s.label}
                  description={s.description}
                  active={activeKey === s.key}
                  dot={chatScenarioDot(s.key)}
                  onClick={() => handleSelect(s.key)}
                />
              ))
            : SCENARIOS.map((s) => (
                <ScenarioOption
                  key={s.key}
                  label={s.label}
                  description={s.description}
                  active={activeKey === s.key}
                  dot={syncScenarioDot(s.key)}
                  onClick={() => handleSelect(s.key)}
                />
              ))}
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 rounded-full border border-white/10 bg-[#0f1117]/90 px-4 py-2 shadow-xl backdrop-blur-md transition-all hover:border-white/20 hover:bg-[#0f1117]"
        >
          <span
            className={`h-2 w-2 flex-shrink-0 rounded-full ${
              activeScenario
                ? isChat
                  ? chatScenarioDot(activeScenario.key as ChatScenarioKey)
                  : syncScenarioDot(activeScenario.key as ScenarioKey)
                : "bg-white/20"
            }`}
          />
          <span className="text-[10px] text-white/30">{routeLabel}</span>
          <span className="max-w-[160px] truncate text-xs font-medium text-white/70">
            {activeScenario ? activeScenario.label : "Mock: tắt"}
          </span>
          <span className="text-[10px] text-white/30">▲</span>
        </button>
      )}
    </div>
  );
}

interface OptionProps {
  label: string;
  description: string;
  active: boolean;
  dot: string;
  onClick: () => void;
}

function ScenarioOption({ label, description, active, dot, onClick }: OptionProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-start gap-2.5 rounded-xl px-3 py-2 text-left transition-colors ${
        active ? "bg-white/10 ring-1 ring-white/20" : "hover:bg-white/5"
      }`}
    >
      <span className={`mt-1 h-2 w-2 flex-shrink-0 rounded-full ${dot}`} />
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold text-white/80">{label}</p>
        <p className="truncate text-[10px] text-white/40">{description}</p>
      </div>
      {active && <span className="ml-auto flex-shrink-0 text-[10px] text-white/50">✓</span>}
    </button>
  );
}

function chatScenarioDot(key: ChatScenarioKey): string {
  switch (key) {
    case "chat_answered": return "bg-emerald-400";
    case "chat_partial": return "bg-yellow-400";
    case "chat_refused": return "bg-orange-400";
    case "chat_clarifying": return "bg-blue-400";
    case "chat_error": return "bg-red-400";
    default: return "bg-white/20";
  }
}

function syncScenarioDot(key: ScenarioKey): string {
  switch (key) {
    case "healthy": return "bg-emerald-400";
    case "syncing": return "bg-blue-400 animate-pulse";
    case "errors": return "bg-red-400";
    case "fresh_install": return "bg-yellow-400";
    case "stale": return "bg-orange-400";
    default: return "bg-white/20";
  }
}
