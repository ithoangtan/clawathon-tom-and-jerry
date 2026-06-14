import { AppShell } from "@/components/layout/AppShell";
import { MockScenarioPicker } from "@/components/dev/MockScenarioPicker";
import { TutorialProvider } from "@/hooks/useTutorial";
import { AdminPage } from "@/pages/AdminPage";
import { ChatPage } from "@/pages/ChatPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";

export default function App() {
  return (
    <BrowserRouter>
      <TutorialProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
        {IS_DEV && <MockScenarioPicker />}
      </TutorialProvider>
    </BrowserRouter>
  );
}
