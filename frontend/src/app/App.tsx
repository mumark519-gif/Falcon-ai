import React, { useEffect, useState } from "react";
import AuthScreen from "../components/AuthScreen";
import Sidebar from "../components/Sidebar";
import ChatView from "../components/ChatView";
import Workspace from "../components/Workspace";
import { getToken, getUsernameFromToken } from "../lib/api";

type WorkspaceMode =
  | "agents"
  | "intelligence"
  | "research"
  | "business"
  | "documents"
  | "memory"
  | "multimodal"
  | "plugins";

type ActiveView =
  | { type: "chat" }
  | { type: "workspace"; mode: WorkspaceMode };

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  const [activeView, setActiveView] = useState<ActiveView>({
    type: "chat",
  });

  useEffect(() => {
    setAuthed(!!getToken());
  }, []);

  if (!authed) {
    return <AuthScreen onAuthed={() => setAuthed(true)} />;
  }

  const username = getUsernameFromToken() || "you";

  const openChat = (id: number | null = null) => {
    setActiveChatId(id);
    setActiveView({ type: "chat" });
  };

  const openWorkspace = (mode: WorkspaceMode) => {
    setActiveView({
      type: "workspace",
      mode,
    });
  };

  return (
    <div className="app-shell">
      <Sidebar
        activeChatId={activeView.type === "chat" ? activeChatId : null}
        onSelectChat={(id) => openChat(id)}
        onNewChat={() => openChat()}
        refreshKey={sidebarRefresh}
        username={username}
        onLoggedOut={() => setAuthed(false)}
        onOpenWorkspace={openWorkspace}
      />

      {activeView.type === "chat" ? (
        <ChatView
          chatId={activeChatId}
          onChatCreated={(id) => {
            setActiveChatId(id);
            setSidebarRefresh((k) => k + 1);
          }}
        />
      ) : (
        <Workspace mode={activeView.mode} />
      )}
    </div>
  );
}