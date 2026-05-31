"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center bg-muted/30">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-bold animate-pulse">
          Ź
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-primary/10">
      <div className="flex h-14 items-center border-b bg-white/80 backdrop-blur px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white font-bold text-sm">
            Ź
          </div>
          <div>
            <p className="font-semibold text-sm leading-tight">Źródło</p>
            <p className="text-xs text-muted-foreground">Konfiguracja parafii</p>
          </div>
        </div>
      </div>
      <main className="flex min-h-[calc(100vh-56px)] items-center justify-center p-4">
        {children}
      </main>
    </div>
  );
}
