"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

const STORAGE_KEY = "zrodlo_welcome_seen";

export function WelcomeScreen() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem(STORAGE_KEY)) {
      setVisible(true);
    }
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={dismiss}
    >
      <div
        className="relative w-full max-w-md rounded-2xl bg-white shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Gradient top */}
        <div className="bg-gradient-to-br from-primary to-primary/70 px-8 pt-10 pb-8 text-white text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 mx-auto mb-4">
            <span className="text-3xl font-bold text-white">Ź</span>
          </div>
          <h1 className="text-2xl font-bold mb-2">Witamy w Źródle</h1>
          <p className="text-primary-foreground/80 text-sm leading-relaxed">
            Mniej czasu na administrację.
            <br />
            Więcej czasu dla ludzi.
          </p>
        </div>

        {/* Content */}
        <div className="px-8 py-6 space-y-4">
          <Feature
            icon="🕊"
            title="Asystent AI do pracy parafialnej"
            desc="Przygotuj homilię, znajdź dokument, odpowiedz na pytanie parafianina – AI robi szkic, ksiądz zatwierdza."
          />
          <Feature
            icon="📋"
            title="Centrum zarządzania parafią"
            desc="Intencje, dokumenty, kalendarz, ogłoszenia, wspólnoty – wszystko w jednym miejscu."
          />
          <Feature
            icon="✨"
            title="Asystent zna Twoją parafię"
            desc="Zadaj pytanie asystentowi – odpowie na podstawie wiedzy Twojej parafii."
          />
        </div>

        <div className="px-8 pb-8">
          <button
            onClick={dismiss}
            className="w-full rounded-xl bg-primary py-3 text-sm font-semibold text-white hover:bg-primary/90 transition-colors"
          >
            Rozpocznij pracę
          </button>
          <p className="text-center text-xs text-muted-foreground mt-3">
            To okno pojawi się tylko raz
          </p>
        </div>

        <button
          onClick={dismiss}
          className="absolute top-4 right-4 rounded-lg p-1.5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Zamknij"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function Feature({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div className="flex gap-3">
      <span className="text-xl flex-shrink-0 mt-0.5">{icon}</span>
      <div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground leading-relaxed mt-0.5">{desc}</p>
      </div>
    </div>
  );
}
