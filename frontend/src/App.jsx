import { useEffect, useMemo, useRef, useState } from "react";

const API = import.meta.env.VITE_API_URL || "";

const STARTERS = [
  "List powered-off VMs",
  "What is the Nutanix disk failure runbook?",
  "Reset payments-api-01",
  "Show critical Prism alerts",
];

export default function App() {
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "InfraGPT is up. Ask about mock vCenter VMs, Nutanix alerts, or the local runbooks.",
      sources: [],
      tool_calls: [],
    },
  ]);
  const bottom = useRef(null);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "down" }));
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const history = useMemo(
    () =>
      messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.content })),
    [messages]
  );

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: message }]);
    setBusy(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const body = await res.json();
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: body.answer,
          sources: body.sources || [],
          tool_calls: body.tool_calls || [],
          model: body.model,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Backend unreachable. Start the API on :8000 (${err.message}).`,
          sources: [],
          tool_calls: [],
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <header>
        <div>
          <p className="eyebrow">Infra ops RAG</p>
          <h1>InfraGPT</h1>
        </div>
        <div className={`pill ${health?.status === "ok" ? "ok" : "down"}`}>
          {health?.status === "ok"
            ? `${health.docs_indexed} runbooks · ${health.llm}`
            : "api offline"}
        </div>
      </header>

      <main>
        {messages.map((m, i) => (
          <article key={i} className={m.role}>
            <span className="who">{m.role}</span>
            <pre>{m.content}</pre>
            {m.tool_calls?.length > 0 && (
              <ul className="meta">
                {m.tool_calls.map((t, j) => (
                  <li key={j}>
                    tool <code>{t.name}</code>
                  </li>
                ))}
              </ul>
            )}
            {m.sources?.length > 0 && (
              <ul className="meta">
                {m.sources.map((s) => (
                  <li key={s.path}>
                    {s.title} · {s.path}
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
        {busy && <p className="busy">retrieving + calling tools…</p>}
        <div ref={bottom} />
      </main>

      <div className="starters">
        {STARTERS.map((s) => (
          <button key={s} type="button" onClick={() => send(s)} disabled={busy}>
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a VM, alert, or runbook"
          autoFocus
        />
        <button type="submit" disabled={busy}>
          Send
        </button>
      </form>
    </div>
  );
}
