"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { apiJson, getToken } from "@/lib/api";
import type { ActionItem, KTSessionDetail } from "@/lib/types";

export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [data, setData] = useState<KTSessionDetail | null>(null);
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const d = await apiJson<KTSessionDetail>(`/sessions/${id}`);
    setData(d);
    setTranscript(d.transcript_text);
  }, [id]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!Number.isFinite(id)) return;
    load().catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [id, load, router]);

  async function saveTranscript() {
    setBusy("save");
    setError(null);
    try {
      await apiJson(`/sessions/${id}/transcript`, {
        method: "PUT",
        body: JSON.stringify({ transcript_text: transcript }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(null);
    }
  }

  async function runAi() {
    setBusy("ai");
    setError(null);
    try {
      await apiJson(`/sessions/${id}/process-ai`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "AI processing failed");
    } finally {
      setBusy(null);
    }
  }

  async function toggleAction(item: ActionItem) {
    try {
      await apiJson(`/sessions/${id}/action-items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_done: !item.is_done }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    }
  }

  if (error && !data) {
    return (
      <main className="flex-1 p-8">
        <p className="text-red-600">{error}</p>
        <Link href="/sessions" className="mt-4 inline-block text-emerald-700 underline">
          Back to sessions
        </Link>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="flex flex-1 items-center justify-center p-8 text-slate-600">
        Loading session…
      </main>
    );
  }

  return (
    <main className="flex-1 space-y-8 overflow-auto p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/sessions" className="text-sm font-medium text-emerald-700 hover:underline">
            ← Sessions
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-slate-900">
            {data.external_id}{" "}
            <span className="text-lg font-normal text-slate-600">— {data.topic}</span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Requirements §7 Phase 2 — transcript upload, GenAI summary, action items, FAQs, missing
            knowledge.
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            data.status === "completed"
              ? "bg-emerald-100 text-emerald-800"
              : "bg-amber-100 text-amber-900"
          }`}
        >
          {data.status}
        </span>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Transcript / meeting notes</h2>
        <textarea
          className="mt-3 min-h-[180px] w-full rounded-lg border border-slate-300 p-3 font-mono text-sm text-slate-900"
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={saveTranscript}
            disabled={busy !== null}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-50"
          >
            {busy === "save" ? "Saving…" : "Save transcript"}
          </button>
          <button
            type="button"
            onClick={runAi}
            disabled={busy !== null}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {busy === "ai" ? "Running AI…" : "Run AI (summarize, actions, FAQs, index)"}
          </button>
        </div>
      </section>

      {(data.summary_text || data.key_decisions || data.risks || data.missing_knowledge_notes) && (
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="font-semibold text-slate-900">Summary</h3>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{data.summary_text}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="font-semibold text-slate-900">Key decisions</h3>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{data.key_decisions}</p>
            <h3 className="mt-6 font-semibold text-slate-900">Risks</h3>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{data.risks}</p>
            <h3 className="mt-6 font-semibold text-amber-900">Missing knowledge</h3>
            <p className="mt-2 whitespace-pre-wrap text-sm text-amber-950/90">
              {data.missing_knowledge_notes}
            </p>
          </div>
        </section>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Action items</h2>
        <ul className="mt-4 space-y-2">
          {data.action_items.map((a) => (
            <li key={a.id} className="flex items-start gap-3 text-sm">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-slate-400"
                checked={a.is_done}
                onChange={() => toggleAction(a)}
              />
              <span className={a.is_done ? "text-slate-400 line-through" : "text-slate-800"}>
                {a.text}
              </span>
            </li>
          ))}
        </ul>
        {data.action_items.length === 0 && (
          <p className="mt-2 text-sm text-slate-500">No action items yet — run AI after adding a transcript.</p>
        )}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Generated FAQs</h2>
        <dl className="mt-4 space-y-4">
          {data.faq_items.map((f) => (
            <div key={f.id} className="border-b border-slate-100 pb-4 last:border-0">
              <dt className="font-medium text-slate-900">{f.question}</dt>
              <dd className="mt-1 text-sm text-slate-700">{f.answer}</dd>
            </div>
          ))}
        </dl>
        {data.faq_items.length === 0 && (
          <p className="mt-2 text-sm text-slate-500">No FAQs yet — run AI on the transcript.</p>
        )}
      </section>
    </main>
  );
}
