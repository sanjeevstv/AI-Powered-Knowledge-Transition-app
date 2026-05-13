"use client";

import { AppHeader } from "@/components/AppHeader";
import { AuthProvider } from "@/components/AuthProvider";
import { Nav } from "@/components/Nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <div className="flex min-h-screen">
        <Nav />
        <div className="flex min-h-0 flex-1 flex-col">
          <AppHeader />
          {children}
        </div>
      </div>
    </AuthProvider>
  );
}
