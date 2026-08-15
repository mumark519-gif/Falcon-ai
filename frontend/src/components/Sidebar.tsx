import React, { useEffect, useState } from "react";
import { ChatSummary, listChats, searchChats, deleteChat, logout } from "../lib/api";

export default function Sidebar({
  activeChatId,
  onSelectChat,
  onNewChat,
  refreshKey,
  username,
  onLoggedOut,
}: {
  activeChatId: number | null;
  onSelectChat: (id: number) => void;
  onNewChat: () => void;
  refreshKey: number;
  username: string;
  onLoggedOut: () => void;
}) {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [query, setQuery] = useState("");

  const load = async () => {
    try {
      const data = query.trim() ? await searchChats(query.trim()) : await listChats();
      setChats(data);
    } catch {
      /* transient network error -- keep showing the last known list */
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("Delete this chat? This can't be undone.")) return;
    await deleteChat(id);
    if (activeChatId === id) onNewChat();
    load();
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <span className="brand-name">FALCON AI</span>
        </div>
        <button className="new-chat-btn" onClick={onNewChat}>
          + New chat
        </button>
      </div>

      <div className="search-box">
        <input
          placeholder="Search chats..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <nav className="chat-list">
        {chats.map((c) => (
          <div
            key={c.id}
            className={`chat-list-item${c.id === activeChatId ? " active" : ""}`}
            onClick={() => onSelectChat(c.id)}
          >
            <span className="title">{c.title || "Untitled chat"}</span>
            <span className="row-actions">
              <button className="icon-btn" onClick={(e) => handleDelete(e, c.id)} title="Delete chat">
                ✕
              </button>
            </span>
          </div>
        ))}
        {chats.length === 0 && (
          <div style={{ color: "var(--text-faint)", fontSize: 12, padding: "10px 10px" }}>
            No chats yet.
          </div>
        )}
      </nav>

      <div className="sidebar-footer">
        <span className="user-tag">@{username}</span>
        <button
          className="logout-btn"
          onClick={() => {
            logout();
            onLoggedOut();
          }}
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
