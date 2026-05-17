"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  AlertCircle,
  BookOpen,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Copy,
  FileText,
  Loader2,
  Sparkles,
} from "lucide-react";
import { homiliaApi } from "@/lib/api";
import {
  CytatSwietego,
  HomiliaInspiracjeResponse,
  OdniesieniKKK,
  OkresLiturgiczny,
  WariantHomilii,
} from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Stałe
// ---------------------------------------------------------------------------

const OKRESY: OkresLiturgiczny[] = [
  "Zwykły",
  "Adwent",
  "Boże Narodzenie",
  "Wielki Post",
  "Triduum Paschalne",
  "Wielkanoc",
];

const GRUPY = [
  "parafianie",
  "dzieci",
  "młodzież",
  "rodziny z dziećmi",
  "małżeństwa",
  "seniorzy",
  "chorzy i cierpiący",
  "przygotowujący się do sakramentów",
];

const WARIANTY = [
  { key: "wariant_krotki" as const, label: "Krótki", time: "~5 min", color: "text-emerald-600" },
  { key: "wariant_sredni" as const, label: "Średni", time: "~10 min", color: "text-blue-600" },
  { key: "wariant_rozbudowany" as const, label: "Rozbudowany", time: "~20 min", color: "text-violet-600" },
];

// ---------------------------------------------------------------------------
// Strona główna
// ---------------------------------------------------------------------------

type FormState = {
  ewangelia: string;
  swieto: string;
  okres_liturgiczny: OkresLiturgiczny;
  patron_dnia: string;
  grupa_odbiorcow: string;
  dodatkowe_wskazowki: string;
};

const INITIAL_FORM: FormState = {
  ewangelia: "",
  swieto: "",
  okres_liturgiczny: "Zwykły",
  patron_dnia: "",
  grupa_odbiorcow: "parafianie",
  dodatkowe_wskazowki: "",
};

export default function HomiliaPage() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [activeTab, setActiveTab] = useState(0);
  const [formOpen, setFormOpen] = useState(true);

  const mutation = useMutation<HomiliaInspiracjeResponse, Error, FormState>({
    mutationFn: (data) =>
      homiliaApi.generujInspiracje({
        ...data,
        swieto: data.swieto || undefined,
        patron_dnia: data.patron_dnia || undefined,
        dodatkowe_wskazowki: data.dodatkowe_wskazowki || undefined,
      }),
    onSuccess: () => setFormOpen(false),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.ewangelia.trim()) return;
    mutation.mutate(form);
  }

  function handleNowy() {
    mutation.reset();
    setForm(INITIAL_FORM);
    setActiveTab(0);
    setFormOpen(true);
  }

  const result = mutation.data;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Nagłówek */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Inspiracje Homilii</h1>
            <p className="text-sm text-muted-foreground">
              Trzy warianty szkiców — kapłan przemyśla, adaptuje i głosi
            </p>
          </div>
        </div>
        {result && (
          <button
            onClick={handleNowy}
            className="text-xs text-muted-foreground hover:text-foreground border rounded-lg px-3 py-1.5 hover:bg-muted transition-colors"
          >
            Nowa homilia
          </button>
        )}
      </div>

      {/* Formularz */}
      <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
        <button
          type="button"
          onClick={() => setFormOpen((v) => !v)}
          className="flex w-full items-center justify-between px-6 py-4 hover:bg-muted/30 transition-colors"
        >
          <span className="text-sm font-semibold text-foreground">Dane liturgiczne</span>
          {formOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>

        {formOpen && (
          <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-5">
            {/* Ewangelia */}
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide">
                Ewangelia / Perykopa *
              </label>
              <textarea
                value={form.ewangelia}
                onChange={(e) => setForm({ ...form, ewangelia: e.target.value })}
                placeholder={`Np. J 3,16–21\n\n„Tak bowiem Bóg umiłował świat, że Syna swego Jednorodzonego dał, aby każdy, kto w Niego wierzy, nie zginął, ale miał życie wieczne."`}
                rows={5}
                required
                className="w-full rounded-lg border bg-gray-50 px-4 py-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/50 resize-none"
              />
            </div>

            {/* Święto + Okres */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Święto / Uroczystość">
                <input
                  value={form.swieto}
                  onChange={(e) => setForm({ ...form, swieto: e.target.value })}
                  placeholder="Np. Wniebowstąpienie Pańskie"
                  className={inputClass}
                />
              </FormField>
              <FormField label="Okres liturgiczny">
                <select
                  value={form.okres_liturgiczny}
                  onChange={(e) =>
                    setForm({ ...form, okres_liturgiczny: e.target.value as OkresLiturgiczny })
                  }
                  className={inputClass}
                >
                  {OKRESY.map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </FormField>
            </div>

            {/* Patron + Grupa */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Patron dnia">
                <input
                  value={form.patron_dnia}
                  onChange={(e) => setForm({ ...form, patron_dnia: e.target.value })}
                  placeholder="Np. Św. Tomasz z Akwinu"
                  className={inputClass}
                />
              </FormField>
              <FormField label="Grupa odbiorców">
                <select
                  value={form.grupa_odbiorcow}
                  onChange={(e) => setForm({ ...form, grupa_odbiorcow: e.target.value })}
                  className={inputClass}
                >
                  {GRUPY.map((g) => (
                    <option key={g}>{g}</option>
                  ))}
                </select>
              </FormField>
            </div>

            {/* Wskazówki */}
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide">
                Wskazówki kapłana{" "}
                <span className="normal-case font-normal">(opcjonalne)</span>
              </label>
              <textarea
                value={form.dodatkowe_wskazowki}
                onChange={(e) => setForm({ ...form, dodatkowe_wskazowki: e.target.value })}
                placeholder="Np. Parafia przeżywa 100-lecie. Minął tydzień od tragedii lokalnej. Homilia na Mszę szkolną."
                rows={2}
                className="w-full rounded-lg border bg-gray-50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/50 resize-none"
              />
            </div>

            {/* Przycisk */}
            <div className="flex items-center gap-4 pt-1">
              <button
                type="submit"
                disabled={!form.ewangelia.trim() || mutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generuję 3 warianty…
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generuj inspiracje
                  </>
                )}
              </button>
              {mutation.isError && (
                <div className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  {mutation.error.message}
                </div>
              )}
            </div>
          </form>
        )}
      </div>

      {/* Ładowanie */}
      {mutation.isPending && (
        <div className="rounded-xl border bg-white shadow-sm p-12 flex flex-col items-center gap-4">
          <div className="relative">
            <BookOpen className="h-12 w-12 text-primary/20" />
            <Loader2 className="h-6 w-6 animate-spin text-primary absolute -bottom-1 -right-1" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">
              Generuję 3 warianty inspiracji homiletycznych…
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Cytaty świętych · KKK · Kontekst · Szkice · To zajmuje ~20–30 sekund
            </p>
          </div>
        </div>
      )}

      {/* Wyniki */}
      {result && !mutation.isPending && (
        <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
          {/* Zakładki */}
          <div className="flex border-b bg-gray-50/50">
            {WARIANTY.map((v, i) => (
              <button
                key={v.key}
                onClick={() => setActiveTab(i)}
                className={cn(
                  "flex-1 flex flex-col items-center gap-0.5 px-4 py-4 text-sm transition-colors",
                  activeTab === i
                    ? "border-b-2 border-primary bg-white text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/60"
                )}
              >
                <span className="font-semibold">{v.label}</span>
                <span
                  className={cn(
                    "text-xs font-medium",
                    activeTab === i ? v.color : "text-muted-foreground/60"
                  )}
                >
                  {v.time}
                </span>
              </button>
            ))}
          </div>

          {/* Zawartość wariantu */}
          <WariantView
            variant={result[WARIANTY[activeTab].key]}
            label={WARIANTY[activeTab].label}
            accentColor={WARIANTY[activeTab].color}
          />

          {/* Zastrzeżenie */}
          <div className="border-t px-6 py-3 bg-amber-50/60 flex gap-2">
            <AlertCircle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700 leading-relaxed">{result.zastrzezenie}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Komponent wariantu
// ---------------------------------------------------------------------------

function WariantView({
  variant,
  label,
  accentColor,
}: {
  variant: WariantHomilii;
  label: string;
  accentColor: string;
}) {
  const [szkicOpen, setSzkicOpen] = useState(false);

  return (
    <div className="p-6 space-y-7">
      {/* Tytuł i myśl przewodnia */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-foreground">{variant.tytul}</h2>
        <p className="text-base text-muted-foreground italic leading-relaxed">
          „{variant.mysl_przewodnia}"
        </p>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>~{variant.dlugosc_min} minut</span>
        </div>
      </div>

      {/* Siatka: Struktura + Pytania */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <InfoCard title="Struktura homilii" icon="📋">
          <ol className="space-y-2.5">
            {variant.struktura.map((punkt, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-primary/10 text-primary text-[11px] flex items-center justify-center font-bold">
                  {i + 1}
                </span>
                <span className="text-foreground leading-snug">{punkt}</span>
              </li>
            ))}
          </ol>
        </InfoCard>

        <InfoCard title="Pytania do refleksji" icon="🤔">
          <ul className="space-y-2">
            {variant.pytania_do_refleksji.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground leading-snug">
                <span className="text-primary font-bold flex-shrink-0">›</span>
                {q}
              </li>
            ))}
          </ul>
        </InfoCard>
      </div>

      {/* Cytaty Świętych */}
      {variant.cytaty_swietych.length > 0 && (
        <section>
          <SectionHeader icon="✝" title="Cytaty Świętych" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {variant.cytaty_swietych.map((c, i) => (
              <QuoteCard key={i} cytat={c} />
            ))}
          </div>
        </section>
      )}

      {/* Katechizm */}
      {variant.katechizm_kk.length > 0 && (
        <section>
          <SectionHeader icon="📖" title="Katechizm Kościoła Katolickiego" />
          <div className="space-y-3">
            {variant.katechizm_kk.map((k, i) => (
              <KKKCard key={i} odniesienie={k} />
            ))}
          </div>
        </section>
      )}

      {/* Kontekst + Zastosowanie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <InfoCard title="Kontekst historyczny" icon="🏛">
          <p className="text-sm text-foreground leading-relaxed">
            {variant.kontekst_historyczny}
          </p>
        </InfoCard>
        <InfoCard title="Praktyczne zastosowanie" icon="🌱">
          <p className="text-sm text-foreground leading-relaxed">
            {variant.praktyczne_zastosowanie}
          </p>
        </InfoCard>
      </div>

      {/* Pełny szkic */}
      <div className="rounded-xl border-2 border-dashed border-primary/25 overflow-hidden">
        <button
          onClick={() => setSzkicOpen((v) => !v)}
          className="flex w-full items-center justify-between px-5 py-4 hover:bg-muted/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-foreground">Pełny szkic homilii</span>
            <span className="text-xs text-muted-foreground">
              (~{Math.ceil(variant.pelny_szkic.split(" ").length / 130)} min czytania)
            </span>
          </div>
          {szkicOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {szkicOpen && (
          <div className="px-5 pb-5 pt-1">
            <div className="rounded-lg border bg-white p-5 text-sm leading-loose text-foreground whitespace-pre-wrap font-serif">
              {variant.pelny_szkic}
            </div>
            <div className="flex justify-end mt-3">
              <CopyButton text={variant.pelny_szkic} label="Kopiuj szkic" />
            </div>
          </div>
        )}
      </div>

      {/* Kopiuj wszystko */}
      <div className="flex justify-end pt-1 border-t">
        <CopyButton
          text={formatujCalyWariant(variant, label)}
          label="Kopiuj cały wariant"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Małe komponenty
// ---------------------------------------------------------------------------

function FormField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      {children}
    </div>
  );
}

function SectionHeader({ icon, title }: { icon: string; title: string }) {
  return (
    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
      <span>{icon}</span>
      {title}
    </h3>
  );
}

function InfoCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border bg-gray-50/80 p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
        <span>{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function QuoteCard({ cytat }: { cytat: CytatSwietego }) {
  return (
    <blockquote className="rounded-xl border-l-4 border-primary/40 bg-primary/5 px-4 py-3 space-y-2">
      <p className="text-sm italic text-foreground leading-relaxed">„{cytat.tresc}"</p>
      <footer className="text-xs font-semibold text-primary/80">— {cytat.autor}</footer>
    </blockquote>
  );
}

function KKKCard({ odniesienie }: { odniesienie: OdniesieniKKK }) {
  return (
    <div className="flex gap-3 items-start rounded-xl border bg-gray-50/80 px-4 py-3">
      <span className="flex-shrink-0 text-xs font-bold text-primary bg-primary/10 rounded-lg px-2.5 py-1 mt-0.5">
        {odniesienie.numer}
      </span>
      <p className="text-sm text-foreground leading-relaxed">{odniesienie.tresc}</p>
    </div>
  );
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable in some browser contexts
    }
  }

  return (
    <button
      onClick={copy}
      className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-emerald-600" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
      {copied ? "Skopiowano!" : label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Formatowanie do schowka
// ---------------------------------------------------------------------------

function formatujCalyWariant(v: WariantHomilii, label: string): string {
  const sep = "─".repeat(60);
  const lines: string[] = [
    `HOMILIA – WARIANT ${label.toUpperCase()} (~${v.dlugosc_min} MINUT)`,
    sep,
    `TYTUŁ: ${v.tytul}`,
    `MYŚL PRZEWODNIA: ${v.mysl_przewodnia}`,
    "",
    "STRUKTURA:",
    ...v.struktura.map((p, i) => `  ${i + 1}. ${p}`),
    "",
    "CYTATY ŚWIĘTYCH:",
    ...v.cytaty_swietych.map((c) => `  „${c.tresc}"\n  — ${c.autor}`),
    "",
    "KATECHIZM KOŚCIOŁA KATOLICKIEGO:",
    ...v.katechizm_kk.map((k) => `  ${k.numer}: ${k.tresc}`),
    "",
    "KONTEKST HISTORYCZNY:",
    `  ${v.kontekst_historyczny}`,
    "",
    "PRAKTYCZNE ZASTOSOWANIE:",
    `  ${v.praktyczne_zastosowanie}`,
    "",
    "PYTANIA DO REFLEKSJI:",
    ...v.pytania_do_refleksji.map((q) => `  • ${q}`),
    "",
    sep,
    "PEŁNY SZKIC HOMILII:",
    sep,
    v.pelny_szkic,
  ];
  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const inputClass =
  "w-full rounded-lg border bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/50";
