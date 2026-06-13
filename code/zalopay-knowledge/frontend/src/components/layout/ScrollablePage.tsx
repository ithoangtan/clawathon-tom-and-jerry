import type { ReactNode } from "react";

/** Scroll region for non-chat routes inside AppShell (main uses overflow-hidden). */
export function ScrollablePage({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain chat-scroll">
      {children}
    </div>
  );
}
