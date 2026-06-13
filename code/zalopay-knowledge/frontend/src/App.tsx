import { AppShell } from "@/components/layout/AppShell";
import { TutorialProvider } from "@/hooks/useTutorial";
import { AdminPage } from "@/pages/AdminPage";
import { ChatPage } from "@/pages/ChatPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

export default function App() {
  return (
    <BrowserRouter>
      <TutorialProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </TutorialProvider>
    </BrowserRouter>
  );
}
