import React, { useEffect, useRef, useState } from "react";
import { Message, getChatMessages, streamChat, createChat, ApiError } from "../lib/api";

const PROVIDER_COLOR: Record<string, string> = {
  openai: "var(--provider-openai)",
  anthropic: "var(--provider-anthropic)",
  gemini: "var(--provider-gemini)",
  kimi: "var(--provider-kimi)",
};

const SUGGESTIONS = [
  { label: "CODE", text: "Review this function for bugs and suggest a cleaner version." },
  { label: "RESEARCH", text: "What are the tradeoffs between SQLite and Postgres for a small app?" },
  { label: "BUSINESS", text: "Help me think through pricing for a B2B SaaS tool." },
  { label: "GENERAL", text: "Explain how Falcon decides which model answers a question." },
];

function RoutePill({ route }: { route: { provider: string; model: string } }) {
  const color = PROVIDER_COLOR[route.provider] || "var(--provider-default)";
  return (
    <span className="route-pill">
      <span className="dot" style={{ background: color }} />
      {route.provider} · {route.model}
    </span>
  );
}

function renderBody(text: string) {
  // Minimal, dependency-free rendering: fenced code blocks become <pre>,
  // everything else stays as plain wrapped text.
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```")) {
      const code = part.replace(/^```[a-zA-Z0-9]*\n?/, "").replace(/```$/, "");
      return (
        <pre key={i}>
          <code>{code}</code>
        </pre>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

export default function ChatView({
  chatId,
  onChatCreated,
}: {
  chatId: number | null;
  onChatCreated: (id: number) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [streamRoute, setStreamRoute] = useState<{ provider: string; model: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatId == null) {
      setMessages([]);
      return;
    }
    getChatMessages(chatId).then(setMessages).catch(() => setMessages([]));
  }, [chatId]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, streamText]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || streaming) return;
    setError(null);

    let targetChatId = chatId;
    if (targetChatId == null) {
      try {
        const created = await createChat(trimmed.slice(0, 60));
        targetChatId = created.chat_id;
        onChatCreated(targetChatId);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Couldn't start a new chat.");
        return;
      }
    }

    setMessages((prev) => [...prev, { role: "user", message: trimmed }]);
    setDraft("");
    setStreaming(true);
    setStreamText("");
    setStreamRoute(null);

    try {
      let capturedRoute: { provider: string; model: string } | null = null;
      const full = await streamChat(
        targetChatId,
        trimmed,
        (delta) => setStreamText((prev) => prev + delta),
        (route) => {
          capturedRoute = route;
          setStreamRoute(route);
        }
      );
      setMessages((prev) => [...prev, { role: "assistant", message: full, routing: capturedRoute }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falcon couldn't respond. Try again.");
    } finally {
      setStreaming(false);
      setStreamText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(draft);
    }
  };

  const showEmpty = chatId == null && messages.length === 0 && !streaming;

  return (
    <div className="chat-column">
      {showEmpty ? (
        <div className="empty-state">
          <div className="glyph">FALCON // READY</div>
          <h1>Ask Falcon to research, code, analyze, or execute</h1>
          <p>
            Each request is routed to the model built for it -- Anthropic for code,
            OpenAI for cited research, and so on. You'll see which one answered
            under each reply.
          </p>
          <div className="suggestion-grid">
            {SUGGESTIONS.map((s) => (
              <button key={s.label} className="suggestion-chip" onClick={() => send(s.text)}>
                <span className="label">{s.label}</span>
                <span className="text">{s.text}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="message-list" ref={listRef}>
          {messages.map((m, i) => (
            <div className="message-row" key={m.id ?? i}>
              <div className="message-meta">
                <span className={`role-tag ${m.role}`}>
                  {m.role === "user" ? "YOU" : "FALCON"}
                </span>
                {m.role === "assistant" && m.routing && <RoutePill route={m.routing} />}
              </div>
              <div className="message-body">{renderBody(m.message)}</div>
            </div>
          ))}

          {streaming && (
            <div className="message-row">
              <div className="message-meta">
                <span className="role-tag assistant">FALCON</span>
                {streamRoute && <RoutePill route={streamRoute} />}
              </div>
              <div className="message-body">
                {renderBody(streamText)}
                <span className="stream-cursor" />
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{ padding: "0 24px 8px", maxWidth: 720, margin: "0 auto", width: "100%" }}>
          <div className="auth-error">{error}</div>
        </div>
      )}

      <div className="composer">
        <div className="composer-inner">
          <textarea
            rows={1}
            placeholder="Ask Falcon to research, code, analyze or execute a task..."
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={streaming}
          />
          <button className="send-btn" onClick={() => send(draft)} disabled={streaming || !draft.trim()}>
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
