import Link from "next/link";

export default function HomePage() {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const docsUrl = `${apiBase.replace(/\/$/, "")}/docs`;
  return (
    <main className="mx-auto max-w-3xl flex-1 space-y-8 px-8 py-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          AI-Powered Knowledge Transition
        </h1>
        <p className="mt-3 text-lg text-slate-600">
          End-to-end prototype aligned with the capstone requirements: KT planning, transcript
          processing (summaries, actions, FAQs), semantic repository search, RAG chatbot, and
          transition readiness / closure reporting.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/login"
          className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-emerald-500"
        >
          Sign in
        </Link>
        <Link
          href="/dashboard"
          className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-50"
        >
          Open dashboard
        </Link>
        <Link
          href={docsUrl}
          className="rounded-lg border border-dashed border-slate-400 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          target="_blank"
          rel="noopener noreferrer"
        >
          API docs (Swagger)
        </Link>
      </div>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Demo sign-in
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Use <code className="rounded bg-slate-100 px-1">manager@example.com</code> /{" "}
          <code className="rounded bg-slate-100 px-1">demo123</code> after the API has seeded the
          database (first startup).
        </p>
      </section>
    </main>
  );
}
