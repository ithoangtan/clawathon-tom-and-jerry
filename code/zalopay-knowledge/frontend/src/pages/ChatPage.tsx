import { ChatInterface } from "@/components/chat/ChatInterface";
import { SessionSidebar } from "@/components/chat/SessionSidebar";

export function ChatPage() {
  return (
    <div className="relative flex min-h-0 flex-1">
      <SessionSidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <ChatInterface />
      </div>
    </div>
  );
}
