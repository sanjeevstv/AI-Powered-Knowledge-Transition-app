"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiJson, getToken } from "@/lib/api";
import type { ClosureReport, DashboardSummary } from "@/lib/types";

function StatCard({
  title,
  value,
  sub,
}: {
  title: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-sm text-slate-600">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [closure, setClosure] = useState<ClosureReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [s, c] = await Promise.all([
          apiJson<DashboardSummary>("/dashboard/summary"),
          apiJson<ClosureReport>("/dashboard/closure-report"),
        ]);
        if (!cancelled) {
          setSummary(s);
          setClosure(c);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load dashboard");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (error) {
    return (
      <main className="flex-1 overflow-auto p-8">
        <p className="text-red-600">{error}</p>
        <Link href="/login" className="mt-4 inline-block text-emerald-700 underline">
          Sign in
        </Link>
      </main>
    );
  }

  if (!summary || !closure) {
    return (
      <main className="flex flex-1 items-center justify-center overflow-auto p-8 text-slate-600">
        Loading metrics…
      </main>
    );
  }

  return (
    <main className="flex-1 space-y-10 overflow-auto p-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">Transition dashboard</h1>
        <p className="mt-1 text-slate-600">
          Requirements §11 Module 6 — KPIs, readiness score, and closure readiness (§16–17).
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="KT completion"
          value={`${summary.kt_completion_percent}%`}
          sub={`${summary.completed_sessions} / ${summary.total_sessions} sessions`}
        />
        <StatCard title="Pending sessions" value={summary.pending_sessions} />
        <StatCard
          title="Readiness score"
          value={summary.readiness_score}
          sub="Weighted: sessions 30%, assessments 30%, docs 20%, Q&A 20%"
        />
        <StatCard
          title="Knowledge coverage"
          value={`${summary.document_coverage_percent}%`}
          sub={`${summary.documents_uploaded} / ${summary.expected_documents} documents`}
        />
        <StatCard
          title="Assessment avg"
          value={`${summary.assessment_avg_score}%`}
          sub={`${summary.assessment_count} quiz record(s)`}
        />
        <StatCard
          title="Q&A resolution (proxy)"
          value={`${summary.question_resolution_rate_percent}%`}
          sub="From chat message ratio"
        />
      </section>

      <section className="rounded-xl border border-amber-200 bg-amber-50/80 p-6">
        <h2 className="text-lg font-semibold text-amber-950">Open risks / issues</h2>
        <p className="mt-2 text-sm text-amber-900">{summary.open_risks_placeholder}</p>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Transition closure report</h2>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              closure.all_criteria_met ? "bg-emerald-100 text-emerald-800" : "bg-slate-200 text-slate-700"
            }`}
          >
            {closure.all_criteria_met ? "All signals green" : "Action needed"}
          </span>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-slate-700">{closure.narrative}</p>
        <ul className="mt-6 space-y-3">
          {closure.checklist.map((c) => (
            <li
              key={c.name}
              className={`flex gap-3 rounded-lg border px-4 py-3 text-sm ${
                c.met ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200 bg-slate-50"
              }`}
            >
              <span className="text-lg" aria-hidden>
                {c.met ? "✓" : "○"}
              </span>
              <div>
                <p className="font-medium text-slate-900">{c.name}</p>
                <p className="mt-1 text-slate-600">{c.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <p className="text-sm text-slate-500">
        Next: run the{" "}
        <Link href="/sessions" className="font-medium text-emerald-700 underline">
          KT sessions
        </Link>{" "}
        workflow (upload transcript → process AI) and use the{" "}
        <Link href="/chat" className="font-medium text-emerald-700 underline">
          chatbot
        </Link>{" "}
        to improve Q&amp;A metrics.
      </p>
    </main>
  );
}
