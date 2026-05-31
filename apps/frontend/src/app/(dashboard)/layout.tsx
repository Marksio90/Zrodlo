"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { PwaInstallBanner } from "@/components/PwaInstallBanner";
import { getToken, getUser } from "@/lib/auth";
import { onboardingApi } from "@/lib/api";

const ONBOARDING_DONE_KEY = "zrodlo_onboarding_done";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

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
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
      <PwaInstallBanner />
    </div>
  );
}
