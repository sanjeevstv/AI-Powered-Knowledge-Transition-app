"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { apiJson, getToken } from "@/lib/api";

type Msg = { role: "user" | "assistant"; text: string };

export default function ChatPage() {
  const router = useRouter();
  const [input, setInput] = useState("What is the deployment rollback process?");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    try {
      const res = await apiJson<{ answer: string; retrieved_chunks: number; sources: unknown[] }>(
        "/chat",
        { method: "POST", body: JSON.stringify({ message: text }) },
      );
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: `${res.answer}\n\n— Retrieved ${res.retrieved_chunks} chunk(s).`,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: e instanceof Error ? e.message : "Request failed",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col overflow-hidden p-8">
      <header className="shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">KT chatbot (RAG)</h1>
        <p className="mt-1 text-slate-600">
          Requirements §11 Module 5 — retrieval-based answers from indexed transcripts and documents.
        </p>
      </header>

      <div className="mt-6 flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <p className="text-sm text-slate-500">
              Try: “How does incident escalation work?”, “Where are logs monitored?”, or “How is the
              app deployed?”
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                msg.role === "user"
                  ? "ml-auto bg-emerald-600 text-white"
                  : "mr-auto border border-slate-200 bg-slate-50 text-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          ))}
          <div ref={bottom} />
        </div>
        <div className="shrink-0 border-t border-slate-200 p-4">
          <div className="flex gap-2">
            <textarea
              className="min-h-[48px] flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              placeholder="Type a KT question…"
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => void send()}
              className="self-end rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {busy ? "…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
