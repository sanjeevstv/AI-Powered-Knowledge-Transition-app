"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getToken } from "@/lib/api";

import { useAuth } from "./AuthProvider";

const allLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/planning", label: "KT planning" },
  { href: "/sessions", label: "Sessions" },
  { href: "/repository", label: "Repository" },
  { href: "/chat", label: "Chatbot" },
] as const;

export function Nav() {
  const path = usePathname();
  const { me, loading } = useAuth();
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(!!getToken());
  }, [path]);

  if (path === "/login") return null;

  const links =
    me?.ui_access === "limited"
      ? allLinks.filter((l) => l.href !== "/planning")
      : [...allLinks];

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-slate-900 text-slate-100">
      <div className="border-b border-slate-700 px-4 py-5">
        <Link href="/" className="text-lg font-semibold tracking-tight text-white">
          KT Platform
        </Link>
        <p className="mt-1 text-xs text-slate-400">Vendor transition prototype</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {loading && hasToken ? (
          <p className="px-3 py-2 text-xs text-slate-400">Loading navigation…</p>
        ) : (
          links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                path === l.href || path.startsWith(l.href + "/")
                  ? "bg-slate-700 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              {l.label}
            </Link>
          ))
        )}
      </nav>
      <div className="border-t border-slate-700 p-3">
        {!hasToken ? (
          <Link
            href="/login"
            className="block w-full rounded-lg bg-emerald-600 px-3 py-2 text-center text-sm font-medium text-white hover:bg-emerald-500"
          >
            Sign in
          </Link>
        ) : (
          <p className="px-2 text-center text-xs text-slate-500">Use the top bar to sign out</p>
        )}
      </div>
    </aside>
  );
}
