"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { PwaInstallBanner } from "@/components/PwaInstallBanner";
import { getToken, getUser } from "@/lib/auth";
import { onboardingApi } from "@/lib/api";
import { useNotificationSocket } from "@/hooks/useNotificationSocket";

type ToastMsg = { id: number; tytul: string; tresc: string };
let _toastId = 0;

const ONBOARDING_DONE_KEY = "zrodlo_onboarding_done";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [ready, setReady] = useState(false);
  const [toasts, setToasts] = useState<ToastMsg[]>([]);

  const handleNotification = useCallback((n: { tytul: string; tresc: string; typ: string }) => {
    const id = ++_toastId;
    setToasts((prev) => [...prev, { id, tytul: n.tytul, tresc: n.tresc }]);
    qc.invalidateQueries({ queryKey: ["powiadomienia"] });
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 6000);
  }, [qc]);

  useNotificationSocket(handleNotification);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const user = getUser();
    const onboardingDone = typeof window !== "undefined"
      && localStorage.getItem(ONBOARDING_DONE_KEY) === "1";

    // Tylko proboszcz i tylko jeśli jeszcze nie oznaczył jako done
    if (user?.rola === "proboszcz" && !onboardingDone) {
      onboardingApi.status()
        .then((s) => {
          if (!s.gotowy) {
            router.replace("/onboarding");
          } else {
            if (typeof window !== "undefined") {
              localStorage.setItem(ONBOARDING_DONE_KEY, "1");
            }
            setReady(true);
          }
        })
        .catch(() => setReady(true)); // błąd API → nie blokuj dashboardu
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
    <div className="flex h-screen overflow-hidden bg-muted/30">
      <WelcomeScreen />
      <Sidebar />
      {/* pt-14 on mobile to clear the fixed top bar; md:pt-0 restores desktop */}
      <div className="flex flex-1 flex-col overflow-hidden pt-14 md:pt-0">
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
      <PwaInstallBanner />

      {/* WebSocket notification toasts */}
      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
          {toasts.map((t) => (
            <div
              key={t.id}
              className="flex items-start gap-3 rounded-lg border bg-white shadow-lg p-4 animate-in slide-in-from-right"
            >
              <Bell className="h-4 w-4 text-primary mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{t.tytul}</p>
                <p className="text-xs text-muted-foreground truncate">{t.tresc}</p>
              </div>
              <button
                onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
                className="text-muted-foreground hover:text-foreground ml-auto shrink-0"
                aria-label="Zamknij"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
