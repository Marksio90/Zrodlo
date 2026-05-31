"use client";

import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";

export function PwaOfflineBar() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setOffline(!navigator.onLine);

    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);

    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-white">
      <div className="flex items-center justify-center gap-2 py-2 px-4 text-xs font-medium">
        <WifiOff className="h-3.5 w-3.5 shrink-0" />
        Brak połączenia z internetem – niektóre funkcje mogą być niedostępne
      </div>
    </div>
  );
}
