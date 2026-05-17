"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Archive,
  BookOpen,
  Brain,
  Calendar,
  CheckCircle2,
  Church,
  FileText,
  Heart,
  Loader2,
  MessageSquare,
  Newspaper,
  Play,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { demoApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const DEMO_ITEMS = [
  { icon: Church, label: "1 Parafia", desc: "Parafia pw. Wniebowzięcia NMP w Krakowie" },
  { icon: Users, label: "1 Proboszcz + 2 Wikariuszy", desc: "Pełne profile kapłanów" },
  { icon: Users, label: "300 Parafian", desc: "Rejestr parafialny z danymi kontaktowymi" },
  { icon: Heart, label: "Intencje i Liturgie", desc: "Msze z 8 miesięcy + intencje" },
  { icon: FileText, label: "25 Dokumentów", desc: "Metryki, zaświadczenia, pisma" },
  { icon: Users, label: "6 Wspólnot", desc: "Schola, Ministranci, Caritas, Oaza, Różaniec, Krąg Biblijny" },
  { icon: Calendar, label: "35 Wydarzeń", desc: "Rekolekcje, pielgrzymki, spotkania" },
  { icon: Brain, label: "20 Notatek wiedzy", desc: "Historia, liturgia, administracja" },
  { icon: Newspaper, label: "15 Ogłoszeń", desc: "Parafialne ogłoszenia niedzielne" },
  { icon: Sparkles, label: "Powiadomienia", desc: "Kolejka do zatwierdzenia, alerty" },
];

const CREDENTIALS = [
  { rola: "Proboszcz", email: "proboszcz@nmp-krakow.pl", haslo: "Demo1234!" },
  { rola: "Wikariusz 1", email: "wikariusz1@nmp-krakow.pl", haslo: "Demo1234!" },
  { rola: "Wikariusz 2", email: "wikariusz2@nmp-krakow.pl", haslo: "Demo1234!" },
  { rola: "Administrator", email: "admin@zrodlo.pl", haslo: "Admin1234!" },
];

const MODULES = [
  { icon: Heart, label: "Intencje", href: "/dashboard/intencje", color: "text-rose-500" },
  { icon: FileText, label: "Dokumenty", href: "/dashboard/dokumenty", color: "text-blue-500" },
  { icon: Archive, label: "Archiwum", href: "/dashboard/archiwum", color: "text-orange-500" },
  { icon: Users, label: "Wspólnoty", href: "/dashboard/wspolnoty", color: "text-green-500" },
  { icon: Calendar, label: "Kalendarz", href: "/dashboard/kalendarz", color: "text-purple-500" },
  { icon: Newspaper, label: "Ogłoszenia", href: "/dashboard/ogloszenia", color: "text-amber-500" },
  { icon: Sparkles, label: "Wsparcie AI", href: "/dashboard/ai", color: "text-indigo-500" },
  { icon: MessageSquare, label: "Asystent", href: "/dashboard/asystent", color: "text-teal-500" },
  { icon: BookOpen, label: "Homilie", href: "/dashboard/homilia", color: "text-pink-500" },
  { icon: Brain, label: "Wiedza", href: "/dashboard/wiedza", color: "text-cyan-500" },
];

interface SeedResult {
  status: string;
  stats?: Record<string, number>;
  message?: string;
}

export default function DemoPage() {
  const [result, setResult] = useState<SeedResult | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: demoApi.seed,
    onSuccess: (data: SeedResult) => setResult(data),
  });

  function copyText(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 1500);
  }

  const isSeeded = result?.status === "ok" || result?.status === "already_seeded";

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="border-b bg-gradient-to-r from-primary/5 to-purple-500/5 px-6 py-5">
        <div className="flex items-center gap-3 mb-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-sm">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Tryb Demo</h1>
            <p className="text-sm text-muted-foreground">
              Wypełnij system realistycznymi danymi parafii
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 p-6 max-w-4xl mx-auto w-full space-y-6">
        {/* What gets generated */}
        <div className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Co zostanie wygenerowane
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {DEMO_ITEMS.map(({ icon: Icon, label, desc }) => (
              <div
                key={label}
                className="flex items-start gap-3 rounded-lg bg-muted/40 px-4 py-3"
              >
                <Icon className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        {!isSeeded ? (
          <div className="rounded-xl border bg-white p-6 text-center space-y-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 mx-auto">
              <Play className="h-7 w-7 text-primary ml-1" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Uruchom tryb demo</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
                Operacja jest bezpieczna i idempotentna – możesz ją uruchomić wielokrotnie.
                Dane wyglądają jak 8 miesięcy aktywnego użytkowania systemu.
              </p>
            </div>
            {mutation.isError && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive inline-block">
                {(mutation.error as Error).message}
              </div>
            )}
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-3 text-sm font-semibold text-white hover:bg-primary/90 disabled:opacity-50 transition-colors shadow-sm"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generuję dane… (kilkanaście sekund)
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Wygeneruj dane demo
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="rounded-xl border border-green-200 bg-green-50 p-6 text-center space-y-3">
            <CheckCircle2 className="h-10 w-10 text-green-600 mx-auto" />
            <div>
              <h3 className="font-semibold text-green-800">
                {result?.status === "already_seeded"
                  ? "Dane demo były już wygenerowane"
                  : "Dane demo wygenerowane pomyślnie!"}
              </h3>
              {result?.stats && (
                <div className="mt-3 flex flex-wrap gap-2 justify-center">
                  {Object.entries(result.stats).map(([k, v]) => (
                    <span
                      key={k}
                      className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700"
                    >
                      {k}: {v}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Credentials */}
        <div className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            Dane logowania demo
          </h2>
          <div className="space-y-2">
            {CREDENTIALS.map(({ rola, email, haslo }) => (
              <div
                key={email}
                className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2.5"
              >
                <div>
                  <span className="text-xs font-semibold text-primary">{rola}</span>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-sm font-mono">{email}</span>
                    <span className="text-xs text-muted-foreground">·</span>
                    <span className="text-sm font-mono text-muted-foreground">{haslo}</span>
                  </div>
                </div>
                <button
                  onClick={() => copyText(`${email}\n${haslo}`, email)}
                  className="rounded-md px-3 py-1.5 text-xs font-medium border hover:bg-muted transition-colors shrink-0"
                >
                  {copied === email ? "Skopiowano!" : "Kopiuj"}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Module links */}
        <div className="rounded-xl border bg-white p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Church className="h-4 w-4 text-primary" />
            Moduły do sprawdzenia
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {MODULES.map(({ icon: Icon, label, href, color }) => (
              <a
                key={href}
                href={href}
                className="flex flex-col items-center gap-2 rounded-lg border bg-muted/20 px-3 py-3 hover:bg-muted/50 transition-colors text-center"
              >
                <Icon className={cn("h-5 w-5", color)} />
                <span className="text-xs font-medium">{label}</span>
              </a>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <p className="text-sm text-amber-800">
            <strong>Uwaga:</strong> Dane demo są fikcyjne i służą wyłącznie prezentacji
            możliwości systemu. Wszystkie osoby, daty i dokumenty są wygenerowane losowo.
            Nie należy wykorzystywać ich w rzeczywistych procesach parafialnych.
          </p>
        </div>
      </div>
    </div>
  );
}
