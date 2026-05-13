"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { apiJson, getToken } from "@/lib/api";
import type { KTSession, UserPublic } from "@/lib/types";

export default function SessionsPage() {
  const router = useRouter();
  const { me, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<KTSession[]>([]);
  const [users, setUsers] = useState<UserPublic[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [externalId, setExternalId] = useState("");
  const [topic, setTopic] = useState("");
  const [ownerId, setOwnerId] = useState<string>("");

  const canCreate = me?.ui_access === "full";

  const load = useCallback(async () => {
    const s = await apiJson<KTSession[]>("/sessions");
    setSessions(s);
    if (me?.ui_access === "full") {
      try {
        const u = await apiJson<UserPublic[]>("/auth/users");
        setUsers(u);
      } catch {
        setUsers([]);
      }
    } else {
      setUsers([]);
    }
  }, [me?.ui_access]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (authLoading) return;
    load().catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [router, authLoading, load]);

  async function createSession(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const body: Record<string, unknown> = {
        external_id: externalId.trim(),
        topic: topic.trim(),
        status: "pending",
      };
      if (ownerId) body.owner_id = Number(ownerId);
      await apiJson("/sessions", { method: "POST", body: JSON.stringify(body) });
      setExternalId("");
      setTopic("");
      setOwnerId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setCreating(false);
    }
  }

  if (error && !sessions.length) {
    return (
      <main className="flex-1 p-8">
        <p className="text-red-600">{error}</p>
      </main>
    );
  }

  return (
    <main className="flex-1 space-y-8 overflow-auto p-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">KT session management</h1>
        <p className="mt-1 text-slate-600">
          Requirements §11 Module 2 — create sessions, assign topics/owners, upload transcripts, track
          completion (see detail for AI processing).
        </p>
      </header>

      {canCreate && (
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Create session</h2>
          <form className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" onSubmit={createSession}>
            <div>
              <label className="block text-xs font-medium text-slate-600">Session ID</label>
              <input
                className="mt-1 w-full rounded border border-slate-300 px-2 py-2 text-sm"
                placeholder="KT-203"
                value={externalId}
                onChange={(e) => setExternalId(e.target.value)}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-600">Topic</label>
              <input
                className="mt-1 w-full rounded border border-slate-300 px-2 py-2 text-sm"
                placeholder="e.g. API documentation handover"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600">Owner (optional)</label>
              <select
                className="mt-1 w-full rounded border border-slate-300 px-2 py-2 text-sm"
                value={ownerId}
                onChange={(e) => setOwnerId(e.target.value)}
              >
                <option value="">—</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name || u.email} ({u.role})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={creating}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                {creating ? "Creating…" : "Create"}
              </button>
            </div>
          </form>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </section>
      )}

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Topic</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Scheduled</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sessions.map((row) => {
              const owner = users.find((u) => u.id === row.owner_id);
              const ownerLabel =
                owner != null
                  ? owner.full_name || owner.email
                  : row.owner_id != null
                    ? `User #${row.owner_id}`
                    : "—";
              return (
                <tr key={row.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono text-xs">{row.external_id}</td>
                  <td className="px-4 py-3 text-slate-800">{row.topic}</td>
                  <td className="px-4 py-3 text-slate-600">{ownerLabel}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        row.status === "completed"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-amber-100 text-amber-900"
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {row.scheduled_date?.slice(0, 10) ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/sessions/${row.id}`}
                      className="font-medium text-emerald-700 hover:underline"
                    >
                      Open
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sessions.length === 0 && (
          <p className="p-6 text-center text-sm text-slate-500">No sessions yet.</p>
        )}
      </section>
    </main>
  );
}
