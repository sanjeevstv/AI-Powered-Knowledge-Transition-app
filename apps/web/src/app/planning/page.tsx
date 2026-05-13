"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { apiJson, getToken, uploadDocument } from "@/lib/api";
import type { KTSession } from "@/lib/types";

export default function PlanningPage() {
  const router = useRouter();
  const { me, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<KTSession[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (authLoading) return;
    if (me?.ui_access === "limited") {
      router.replace("/dashboard");
      return;
    }
    apiJson<KTSession[]>("/sessions")
      .then(setSessions)
      .catch(() => setSessions([]));
  }, [router, authLoading, me?.ui_access]);

  async function uploadSchedule(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      await uploadDocument(file, "kt_schedule,planning");
      e.target.value = "";
    } finally {
      setBusy(false);
    }
  }

  const topics = Array.from(new Set(sessions.map((s) => s.topic)));

  return (
    <main className="flex-1 space-y-8 overflow-auto p-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">KT planning</h1>
        <p className="mt-1 text-slate-600">
          Requirements §7 Phase 1 — schedules and topics, assign owners, track completion (sessions
          table +{" "}
          <Link href="/repository" className="font-medium text-emerald-700 underline">
            repository
          </Link>{" "}
          for schedule files).
        </p>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Upload KT schedule</h2>
          <p className="mt-2 text-sm text-slate-600">
            Upload a PDF or text schedule; files are tagged <code className="rounded bg-slate-100 px-1">kt_schedule</code>{" "}
            for traceability. Manage all files under{" "}
            <Link href="/repository" className="text-emerald-700 underline">
              Repository
            </Link>
            .
          </p>
          <input
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            className="mt-4 block text-sm"
            disabled={busy}
            onChange={uploadSchedule}
          />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">KT topics in flight</h2>
          <p className="mt-2 text-sm text-slate-600">
            Distinct topics from current sessions (add or edit topics via{" "}
            <Link href="/sessions" className="text-emerald-700 underline">
              Sessions
            </Link>
            ).
          </p>
          <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {topics.length ? (
              topics.map((t) => <li key={t}>{t}</li>)
            ) : (
              <li className="text-slate-500">No sessions yet.</li>
            )}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Phase checklist (from requirements)</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-slate-700">
          <li>Phase 1 — Planning: schedules, topics, owners, completion tracking.</li>
          <li>Phase 2 — Documentation automation: transcripts → summaries, actions, FAQs.</li>
          <li>Phase 3 — Repository: store, tag, semantic search.</li>
          <li>Phase 4 — AI assistant: RAG chatbot over uploaded material.</li>
          <li>Phase 5 — Effectiveness: dashboard scores and closure readiness.</li>
        </ol>
      </section>
    </main>
  );
}
