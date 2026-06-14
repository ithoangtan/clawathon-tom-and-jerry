import { Group, Panel, useDefaultLayout } from "react-resizable-panels";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { SessionSidebar, SessionSidebarPanel } from "@/components/chat/SessionSidebar";
import { SidebarResizeHandle } from "@/components/chat/SidebarResizeHandle";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { t } from "@/lib/i18n";
import { useSessionStore } from "@/store/sessionStore";
import { useSidebarStore } from "@/store/sidebarStore";
import { useUserStore } from "@/store/userStore";
import { useEffect } from "react";
import { useParams } from "react-router-dom";

const DESKTOP_MQ = "(min-width: 768px)";

/** v4 treats bare numbers as pixels, not percentages. */
const SIDEBAR_DEFAULT_PX = 310;
const SIDEBAR_MIN_PX = 180;
const SIDEBAR_MAX_PX = 420;

export function ChatPage() {
  const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();
  const currentSessionId = useUserStore((s) => s.sessionId);
  const requestSwitchSession = useSessionStore((s) => s.requestSwitchSession);

  useEffect(() => {
    if (urlSessionId && urlSessionId !== currentSessionId) {
      requestSwitchSession(urlSessionId);
    }
  }, [urlSessionId, currentSessionId, requestSwitchSession]);

  const locale = useUserStore((s) => s.locale);
  const sidebarOpen = useSidebarStore((s) => s.open);
  const setSidebarOpen = useSidebarStore((s) => s.setOpen);
  const isDesktop = useMediaQuery(DESKTOP_MQ, window.matchMedia(DESKTOP_MQ).matches);

  const { defaultLayout, onLayoutChanged } = useDefaultLayout({
    id: "chat-sidebar-layout",
    storage: localStorage,
    panelIds: ["sidebar", "main"],
  });

  return (
    <div className="relative flex min-h-0 flex-1">
      {/* Mobile drawer + desktop open button */}
      <SessionSidebar />

      <Group
        id="chat-layout"
        orientation="horizontal"
        defaultLayout={defaultLayout}
        onLayoutChanged={onLayoutChanged}
        className="min-h-0 flex-1"
      >
        {isDesktop && sidebarOpen && (
          <>
            <Panel
              id="sidebar"
              defaultSize={SIDEBAR_DEFAULT_PX}
              minSize={SIDEBAR_MIN_PX}
              maxSize={SIDEBAR_MAX_PX}
            >
              <aside
                id="session-sidebar-panel"
                className="session-sidebar flex h-full flex-col border-r border-border chat-glass"
                aria-label={t("sessionHistory", locale)}
                role="complementary"
              >
                <SessionSidebarPanel onCloseDesktop={() => setSidebarOpen(false)} />
              </aside>
            </Panel>
            <SidebarResizeHandle />
          </>
        )}
        <Panel id="main" className="flex min-h-0 flex-col">
          <ChatInterface />
        </Panel>
      </Group>
    </div>
  );
}
