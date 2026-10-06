import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppHeader } from "./components/AppHeader";
import { IssueDetailPage } from "./pages/IssueDetailPage";
import { IssuesListPage } from "./pages/IssuesListPage";
import { LogIssuePage } from "./pages/LogIssuePage";
import type { Tweaks } from "./types";

export default function App() {
  const [tweaks, setTweaks] = useState<Tweaks>({ analyze: "normal" });

  return (
    <div className="shell">
      <AppHeader tweaks={tweaks} onTweaksChange={setTweaks} />
      <main className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/log" replace />} />
          <Route path="/log" element={<LogIssuePage tweaks={tweaks} />} />
          <Route path="/issues" element={<IssuesListPage />} />
          <Route path="/issues/:id" element={<IssueDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
