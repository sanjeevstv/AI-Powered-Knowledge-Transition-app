"use client";

import { usePathname } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { apiJson, getToken } from "@/lib/api";
import type { Me } from "@/lib/types";

type AuthContextValue = {
  me: Me | null;
  loading: boolean;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    if (pathname === "/login") {
      setMe(null);
      setLoading(false);
      return;
    }
    if (!getToken()) {
      setMe(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const m = await apiJson<Me>("/auth/me");
      setMe(m);
    } catch {
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, [pathname]);

  useEffect(() => {
    void refreshMe();
  }, [refreshMe]);

  const value = useMemo(() => ({ me, loading, refreshMe }), [me, loading, refreshMe]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
