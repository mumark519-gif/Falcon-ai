import React, { useEffect, useState } from "react";
import AuthScreen from "../components/AuthScreen";
import Sidebar from "../components/Sidebar";
import ChatView from "../components/ChatView";
import { getToken, getUsernameFromToken } from "../lib/api";

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  useEffect(() => {
    setAuthed(!!getToken());
  }, []);

  if (!authed) {
    return <AuthScreen onAuthed={() => setAuthed(true)} />;
  }

  const username = getUsernameFromToken() || "you";

  return (
    <div className="app-shell">
      <Sidebar
        activeChatId={activeChatId}
        onSelectChat={setActiveChatId}
        onNewChat={() => setActiveChatId(null)}
        refreshKey={sidebarRefresh}
        username={username}
        onLoggedOut={() => setAuthed(false)}
      />
      <ChatView
        chatId={activeChatId}
        onChatCreated={(id) => {
          setActiveChatId(id);
          setSidebarRefresh((k) => k + 1);
        }}
      />
    </div>
  );
}
