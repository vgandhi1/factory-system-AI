import { useState } from "react";
import { api } from "../lib/api";

interface Msg {
  role: "user" | "bot";
  text: string;
  sources?: any[];
  backend?: string;
}

const SUGGESTIONS = [
  "Why is line-1 OEE low?",
  "Which line is the bottleneck?",
  "What is the top downtime cause on line-2?",
  "What defects are we seeing on line-1?",
];

export default function Chat() {
  const [log, setLog] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setLog((l) => [...l, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const r = await api.chat(question);
      setLog((l) => [
        ...l,
        { role: "bot", text: r.answer, sources: r.sources, backend: r.backend },
      ]);
    } catch (e) {
      setLog((l) => [...l, { role: "bot", text: `Error: ${e}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Factory Copilot</h1>
      <div className="suggest">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => ask(s)} disabled={busy}>
            {s}
          </button>
        ))}
      </div>

      <div className="chat-log">
        {log.map((m, i) => (
          <div className={`msg ${m.role}`} key={i}>
            {m.text}
            {m.backend && (
              <div className="sources">
                via {m.backend}
                {m.sources && m.sources.length > 0 && (
                  <>
                    {" "}
                    · sources:{" "}
                    {m.sources
                      .map((s: any) => `${s.title} (${s.occurred_at?.slice(0, 10)})`)
                      .join("; ")}
                  </>
                )}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="msg bot">…thinking</div>}
      </div>

      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
      >
        <input
          type="text"
          placeholder="Ask about OEE, downtime, defects, root cause…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={busy}>
          Ask
        </button>
      </form>
    </>
  );
}
