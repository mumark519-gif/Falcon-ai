// Falcon AI API client.
// Talks to the FastAPI backend. In dev, VITE_API_URL defaults to "/api"
// and vite.config.ts proxies that to the backend, so no CORS setup is
// needed locally. In production, point VITE_API_URL at the deployed API.

const BASE = (import.meta as any).env?.VITE_API_URL || "/api";
const TOKEN_KEY = "falcon_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUsernameFromToken(): string | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return payload.sub || null;
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request(path: string, init: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof URLSearchParams) && init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || data.error || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  return res;
}

// ---- Auth ----

export async function register(username: string, password: string) {
  const res = await request("/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (data.error) throw new ApiError(data.error, 400);
  return data;
}

export async function login(username: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);
  const res = await request("/login", { method: "POST", body: form });
  const data = await res.json();
  if (data.error) throw new ApiError(data.error, 401);
  setToken(data.access_token);
  return data;
}

export function logout() {
  setToken(null);
}

// ---- Chats ----

export interface ChatSummary {
  id: number;
  title: string;
  created_at?: string;
}

export interface Message {
  id?: number;
  role: "user" | "assistant";
  message: string;
  routing?: { provider: string; model: string } | null;
}

export async function listChats(): Promise<ChatSummary[]> {
  const res = await request("/chats");
  return res.json();
}

export async function searchChats(q: string): Promise<ChatSummary[]> {
  const res = await request(`/search-chats?q=${encodeURIComponent(q)}`);
  return res.json();
}

export async function createChat(title: string): Promise<{ chat_id: number; title: string }> {
  const res = await request("/create_chat", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function renameChat(chat_id: number, title: string) {
  const res = await request("/rename-chat", {
    method: "PUT",
    body: JSON.stringify({ chat_id, title }),
  });
  return res.json();
}

export async function deleteChat(chat_id: number) {
  const res = await request(`/chat/${chat_id}`, { method: "DELETE" });
  return res.json();
}

export async function getChatMessages(chat_id: number): Promise<Message[]> {
  const res = await request(`/chat/${chat_id}`);
  const rows = await res.json();
  return rows.map((r: any) => ({ id: r.id, role: r.role, message: r.message }));
}

// Streams an assistant reply token-by-token. Calls onChunk for each text
// delta, onRoute once if/when a routing header arrives, and resolves with
// the full accumulated text when the stream ends.
export async function streamChat(
  chat_id: number,
  message: string,
  onChunk: (delta: string) => void,
  onRoute?: (route: { provider: string; model: string }) => void
): Promise<string> {
  const token = getToken();
  const res = await fetch(`${BASE}/chat-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ chat_id, message }),
  });
  if (!res.ok || !res.body) {
    throw new ApiError(res.statusText, res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let full = "";
  let buffer = "";
  let routeHandled = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    if (!routeHandled) {
      const newlineIdx = buffer.indexOf("\n");
      if (buffer.startsWith("__ROUTE__") && newlineIdx !== -1) {
        const header = buffer.slice("__ROUTE__".length, newlineIdx);
        buffer = buffer.slice(newlineIdx + 1);
        routeHandled = true;
        try {
          onRoute?.(JSON.parse(header));
        } catch {
          /* ignore malformed header */
        }
      } else if (!buffer.startsWith("__ROUTE__") || newlineIdx !== -1) {
        // Either no route header at all, or we now have enough to know
        // it's not one -- stop waiting.
        routeHandled = true;
      }
    }

    if (routeHandled && buffer) {
      full += buffer;
      onChunk(buffer);
      buffer = "";
    }
  }

  if (buffer) {
    full += buffer;
    onChunk(buffer);
  }

  return full;
}

export async function sendChat(chat_id: number, message: string) {
  const res = await request("/chat", {
    method: "POST",
    body: JSON.stringify({ chat_id, message }),
  });
  return res.json() as Promise<{ response: string; routing?: { provider: string; model: string } | null }>;
}
