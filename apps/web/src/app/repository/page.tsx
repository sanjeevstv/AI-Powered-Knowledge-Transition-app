"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiJson, getToken, uploadDocument } from "@/lib/api";
import type { DocumentRow, SemanticHit } from "@/lib/types";

export default function RepositoryPage() {
  const router = useRouter();
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [tags, setTags] = useState("runbook,sop");
  const [q, setQ] = useState("deployment Jenkins");
  const [hits, setHits] = useState<SemanticHit[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDocs() {
    const d = await apiJson<DocumentRow[]>("/documents");
    setDocs(d);
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    loadDocs().catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [router]);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy("upload");
    setError(null);
    try {
      await uploadDocument(file, tags);
      e.target.value = "";
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(null);
    }
  }

  async function indexDoc(docId: number) {
    setBusy(`idx-${docId}`);
    setError(null);
    try {
      await apiJson(`/documents/${docId}/index`, { method: "POST" });
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Index failed");
    } finally {
      setBusy(null);
    }
  }

  async function runSearch() {
    setBusy("search");
    setError(null);
    try {
      const res = await apiJson<{ hits: SemanticHit[] }>(
        `/search/semantic?q=${encodeURIComponent(q)}`,
      );
      setHits(res.hits);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="flex-1 space-y-8 overflow-auto p-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">Knowledge repository</h1>
        <p className="mt-1 text-slate-600">
          Requirements §11 Module 4 — upload documents (PDF/TXT), tagging, semantic search across the
          vector index.
        </p>
      </header>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Upload</h2>
        <p className="mt-1 text-sm text-slate-600">
          Tags are comma-separated (e.g. <code className="rounded bg-slate-100 px-1">runbook</code>,{" "}
          <code className="rounded bg-slate-100 px-1">kt_schedule</code> for planning artifacts).
        </p>
        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600">Tags</label>
            <input
              className="mt-1 w-56 rounded border border-slate-300 px-2 py-2 text-sm"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600">File (.pdf or .txt)</label>
            <input
              type="file"
              accept=".pdf,.txt,text/plain,application/pdf"
              className="mt-1 block text-sm"
              disabled={busy !== null}
              onChange={onUpload}
            />
          </div>
        </div>
        {busy === "upload" && <p className="mt-2 text-sm text-slate-500">Uploading…</p>}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Semantic search</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <input
            className="min-w-[240px] flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ask in natural language…"
          />
          <button
            type="button"
            onClick={runSearch}
            disabled={busy !== null}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {busy === "search" ? "Searching…" : "Search"}
          </button>
        </div>
        <ul className="mt-6 space-y-4">
          {hits.map((h, i) => (
            <li key={i} className="rounded-lg border border-slate-100 bg-slate-50/80 p-4 text-sm">
              <p className="whitespace-pre-wrap text-slate-800">{h.snippet}</p>
              <pre className="mt-2 overflow-x-auto text-xs text-slate-500">
                {JSON.stringify(h.metadata, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
        {hits.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">
            No results yet — index documents and run KT session AI so Chroma has embeddings.
          </p>
        )}
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 className="font-semibold text-slate-900">Stored documents</h2>
        </div>
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="text-left text-xs font-semibold uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Tags</th>
              <th className="px-4 py-3">Uploaded</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {docs.map((d) => (
              <tr key={d.id}>
                <td className="px-4 py-3 font-medium text-slate-900">{d.filename}</td>
                <td className="px-4 py-3 text-slate-600">{d.tags || "—"}</td>
                <td className="px-4 py-3 text-slate-500">{d.created_at?.slice(0, 19) ?? ""}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    className="text-sm font-medium text-emerald-700 hover:underline disabled:opacity-50"
                    disabled={busy !== null}
                    onClick={() => indexDoc(d.id)}
                  >
                    {busy === `idx-${d.id}` ? "Indexing…" : "Index to vector store"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {docs.length === 0 && (
          <p className="p-6 text-center text-sm text-slate-500">No documents uploaded yet.</p>
        )}
      </section>
    </main>
  );
}
