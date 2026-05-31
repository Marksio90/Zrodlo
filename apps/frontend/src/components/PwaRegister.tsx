"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .then((reg) => {
        reg.addEventListener("updatefound", () => {
          const newWorker = reg.installing;
          if (!newWorker) return;
          newWorker.addEventListener("statechange", () => {
            if (
              newWorker.state === "installed" &&
              navigator.serviceWorker.controller
            ) {
              // Nowa wersja dostępna – możemy pokazać toast/reload
              console.info("[SW] Nowa wersja Źródła dostępna. Odśwież stronę.");
            }
          });
        });
      })
      .catch(() => {
        // Service worker niedostępny (np. HTTP) – ignorujemy
      });
  }, []);

  return null;
}
