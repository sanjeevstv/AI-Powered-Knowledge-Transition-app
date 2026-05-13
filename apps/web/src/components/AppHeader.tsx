"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { clearToken } from "@/lib/api";

import { useAuth } from "./AuthProvider";

export function AppHeader() {
  const path = usePathname();
  const router = useRouter();
  const { me, loading } = useAuth();

  if (path === "/login") return null;

  return (
    <header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="min-w-0 flex-1 text-sm text-slate-700">
        {loading ? (
          <span className="text-slate-500">Loading account…</span>
        ) : me ? (
          <span className="truncate font-semibold text-slate-900">{me.email}</span>
        ) : (
          <span className="text-slate-500">Not signed in</span>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {me ? (
          <button
            type="button"
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Sign out
          </button>
        ) : (
          <Link
            href="/login"
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
