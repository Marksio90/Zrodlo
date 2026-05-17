"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  Calendar,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  Facebook,
  Globe,
  Loader2,
  MessageSquareText,
  Newspaper,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { komunikacjaApi, kalendarzeApi, liturgieApi } from "@/lib/api";
import {
  KanalOgloszenia,
  OgloszeniaResponse,
  Wydarzenie,
  WydarzenieOgloszenia,
  IntencjaOgloszenia,
  Liturgia,
} from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Stałe
// ---------------------------------------------------------------------------

const STYLE = [
  {
    key: "formalne" as const,
    label: "Formalne",
    opis: "Godny, liturgiczny",
    kolor: "text-slate-700",
    bg: "bg-slate-50",
    border: "border-slate-200",
    active: "border-b-2 border-slate-700 text-slate-700 bg-white",
  },
  {
    key: "przyjazne" as const,
    label: "Przyjazne",
    opis: "Ciepłe, wspólnotowe",
    kolor: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-100",
    active: "border-b-2 border-blue-600 text-blue-600 bg-white",
  },
  {
    key: "rodzinne" as const,
    label: "Rodzinne",
    opis: "Serdeczne, dla wszystkich",
    kolor: "text-rose-600",
    bg: "bg-rose-50",
    border: "border-rose-100",
    active: "border-b-2 border-rose-600 text-rose-600 bg-white",
  },
];

// ---------------------------------------------------------------------------
// Strona główna
// ---------------------------------------------------------------------------

export default function OgloszeniaPage() {
  const [formOpen, setFormOpen] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  // Dane formularza
  const [dataNiedzieli, setDataNiedzieli] = useState("");
  const [swietoLiturgiczne, setSwietoLiturgiczne] = useState("");
  const [infoKsiędza, setInfoKsiędza] = useState("");
  const [dodatkowe, setDodatkowe] = useState("");

  // Zaznaczone pozycje z kalendarza
  const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set());
  const [selectedLiturgies, setSelectedLiturgies] = useState<Set<string>>(new Set());

  // Ręcznie dodane pozycje
  const [extraEvents, setExtraEvents] = useState<WydarzenieOgloszenia[]>([]);
  const [extraIntencje, setExtraIntencje] = useState<IntencjaOgloszenia[]>([]);

  // Pobierz nadchodzące wydarzenia
  const dzis = new Date().toISOString();
  const zaFortnasc = new Date(Date.now() + 14 * 86400_000).toISOString();

  const { data: dbEvents = [] } = useQuery<Wydarzenie[]>({
    queryKey: ["wydarzenia", "dla-ogloszen"],
    queryFn: () => kalendarzeApi.list({ limit: 15 }),
    staleTime: 120_000,
  });

  const { data: dbLiturgie = [] } = useQuery<Liturgia[]>({
    queryKey: ["liturgie", "dla-ogloszen"],
    queryFn: () => liturgieApi.list({ limit: 10 }),
    staleTime: 120_000,
  });

  const mutation = useMutation<OgloszeniaResponse, Error>({
    mutationFn: () => {
      const wydarzenia: WydarzenieOgloszenia[] = [
        ...dbEvents
          .filter((e) => selectedEvents.has(e.id))
          .map((e) => ({
            tytul: e.tytul,
            kiedy: formatKiedy(e.data_od),
            miejsce: e.miejsce ?? undefined,
            opis: e.opis ?? undefined,
          })),
        ...extraEvents,
      ];

      const intencje: IntencjaOgloszenia[] = [
        ...dbLiturgie
          .filter((l) => selectedLiturgies.has(l.id))
          .map((l) => ({
            kiedy: `${formatData(l.data)} godz. ${l.godzina.slice(0, 5)}`,
            tresc: l.uwagi ?? `Msza ${l.typ}`,
          })),
        ...extraIntencje,
      ];

      return komunikacjaApi.generuj({
        data_niedzieli: dataNiedzieli || undefined,
        swieto_liturgiczne: swietoLiturgiczne || undefined,
        informacje_od_ksiedza: infoKsiędza || undefined,
        wydarzenia,
        intencje,
        dodatkowe_info: dodatkowe || undefined,
      });
    },
    onSuccess: () => setFormOpen(false),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  const result = mutation.data;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Nagłówek */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Newspaper className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Ogłoszenia Źródła</h1>
            <p className="text-sm text-muted-foreground">
              3 style × 3 kanały — gotowe do publikacji po weryfikacji kapłana
            </p>
          </div>
        </div>
        {result && (
          <button
            onClick={() => { mutation.reset(); setFormOpen(true); setActiveTab(0); }}
            className="text-xs border rounded-lg px-3 py-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            Nowe ogłoszenie
          </button>
        )}
      </div>

      {/* Formularz */}
      <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
        <button
          type="button"
          onClick={() => setFormOpen((v) => !v)}
          className="flex w-full items-center justify-between px-6 py-4 hover:bg-muted/20 transition-colors"
        >
          <span className="text-sm font-semibold text-foreground">Dane do ogłoszenia</span>
          {formOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>

        {formOpen && (
          <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-6">
            {/* Wiersz 1: data + święto */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Pole label="Data niedzieli">
                <input
                  value={dataNiedzieli}
                  onChange={(e) => setDataNiedzieli(e.target.value)}
                  placeholder="Np. 18 maja 2025"
                  className={inputCls}
                />
              </Pole>
              <Pole label="Święto / Okres liturgiczny">
                <input
                  value={swietoLiturgiczne}
                  onChange={(e) => setSwietoLiturgiczne(e.target.value)}
                  placeholder="Np. Zesłanie Ducha Świętego"
                  className={inputCls}
                />
              </Pole>
            </div>

            {/* Informacje od księdza */}
            <Pole label="Informacje od księdza">
              <textarea
                value={infoKsiędza}
                onChange={(e) => setInfoKsiędza(e.target.value)}
                placeholder={`Np.\n- Zbiórka na remont dachu\n- Rekolekcje letnie 10–15 lipca\n- Dziękujemy za pomoc przy parafiadzie`}
                rows={4}
                className={`${inputCls} resize-none`}
              />
            </Pole>

            {/* Sekcja: Wydarzenia */}
            <div className="space-y-3">
              <SectionLabel icon={<Calendar className="h-3.5 w-3.5" />} label="Wydarzenia tygodnia" />

              {dbEvents.length > 0 && (
                <div className="rounded-lg border bg-gray-50 divide-y max-h-48 overflow-y-auto">
                  {dbEvents.map((e) => (
                    <label
                      key={e.id}
                      className="flex items-start gap-3 px-4 py-2.5 cursor-pointer hover:bg-white transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedEvents.has(e.id)}
                        onChange={() =>
                          setSelectedEvents((prev) => {
                            const next = new Set(prev);
                            next.has(e.id) ? next.delete(e.id) : next.add(e.id);
                            return next;
                          })
                        }
                        className="mt-0.5 accent-primary"
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{e.tytul}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatKiedy(e.data_od)}
                          {e.miejsce && ` · ${e.miejsce}`}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              )}

              {/* Ręcznie dodane wydarzenia */}
              {extraEvents.map((ev, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <div className="flex-1 grid grid-cols-2 gap-2">
                    <input
                      value={ev.tytul}
                      onChange={(e) => {
                        const copy = [...extraEvents];
                        copy[i] = { ...copy[i], tytul: e.target.value };
                        setExtraEvents(copy);
                      }}
                      placeholder="Nazwa wydarzenia"
                      className={inputCls}
                    />
                    <input
                      value={ev.kiedy}
                      onChange={(e) => {
                        const copy = [...extraEvents];
                        copy[i] = { ...copy[i], kiedy: e.target.value };
                        setExtraEvents(copy);
                      }}
                      placeholder="Kiedy (np. wt 20 maja, 18:00)"
                      className={inputCls}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => setExtraEvents((prev) => prev.filter((_, j) => j !== i))}
                    className="p-1.5 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}

              <button
                type="button"
                onClick={() => setExtraEvents((prev) => [...prev, { tytul: "", kiedy: "" }])}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border border-dashed rounded-lg px-3 py-2 hover:bg-muted/30 transition-colors w-full justify-center"
              >
                <Plus className="h-3.5 w-3.5" />
                Dodaj wydarzenie ręcznie
              </button>
            </div>

            {/* Sekcja: Intencje */}
            <div className="space-y-3">
              <SectionLabel icon={<span className="text-xs">✝</span>} label="Intencje mszalne" />

              {dbLiturgie.length > 0 && (
                <div className="rounded-lg border bg-gray-50 divide-y max-h-40 overflow-y-auto">
                  {dbLiturgie.map((l) => (
                    <label
                      key={l.id}
                      className="flex items-start gap-3 px-4 py-2.5 cursor-pointer hover:bg-white transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedLiturgies.has(l.id)}
                        onChange={() =>
                          setSelectedLiturgies((prev) => {
                            const next = new Set(prev);
                            next.has(l.id) ? next.delete(l.id) : next.add(l.id);
                            return next;
                          })
                        }
                        className="mt-0.5 accent-primary"
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {formatData(l.data)} · {l.godzina.slice(0, 5)}
                        </p>
                        <p className="text-xs text-muted-foreground capitalize">{l.typ}</p>
                      </div>
                    </label>
                  ))}
                </div>
              )}

              {/* Ręcznie dodane intencje */}
              {extraIntencje.map((int, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <div className="flex-1 grid grid-cols-3 gap-2">
                    <input
                      value={int.kiedy}
                      onChange={(e) => {
                        const copy = [...extraIntencje];
                        copy[i] = { ...copy[i], kiedy: e.target.value };
                        setExtraIntencje(copy);
                      }}
                      placeholder="Kiedy (niedz. 9:00)"
                      className={inputCls}
                    />
                    <input
                      value={int.tresc}
                      onChange={(e) => {
                        const copy = [...extraIntencje];
                        copy[i] = { ...copy[i], tresc: e.target.value };
                        setExtraIntencje(copy);
                      }}
                      placeholder="Treść intencji"
                      className={`${inputCls} col-span-2`}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => setExtraIntencje((prev) => prev.filter((_, j) => j !== i))}
                    className="p-1.5 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}

              <button
                type="button"
                onClick={() => setExtraIntencje((prev) => [...prev, { kiedy: "", tresc: "" }])}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border border-dashed rounded-lg px-3 py-2 hover:bg-muted/30 transition-colors w-full justify-center"
              >
                <Plus className="h-3.5 w-3.5" />
                Dodaj intencję ręcznie
              </button>
            </div>

            {/* Dodatkowe */}
            <Pole label="Dodatkowe informacje (opcjonalnie)">
              <textarea
                value={dodatkowe}
                onChange={(e) => setDodatkowe(e.target.value)}
                placeholder="Np. Komunikaty dot. budowy, podziękowania, przypomnienia..."
                rows={2}
                className={`${inputCls} resize-none`}
              />
            </Pole>

            {/* Przycisk */}
            <div className="flex items-center gap-4 pt-1">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary/90 transition-colors disabled:opacity-60"
              >
                {mutation.isPending ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Generuję ogłoszenia…</>
                ) : (
                  <><Sparkles className="h-4 w-4" /> Generuj ogłoszenia</>
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
            <Newspaper className="h-12 w-12 text-primary/20" />
            <Loader2 className="h-6 w-6 animate-spin text-primary absolute -bottom-1 -right-1" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">
              Generuję 3 style × 3 kanały…
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Formalne · Przyjazne · Rodzinne — To zajmuje ~10–15 sekund
            </p>
          </div>
        </div>
      )}

      {/* Wyniki */}
      {result && !mutation.isPending && (
        <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
          {/* Zakładki stylów */}
          <div className="flex border-b bg-gray-50/50">
            {STYLE.map((s, i) => (
              <button
                key={s.key}
                onClick={() => setActiveTab(i)}
                className={cn(
                  "flex-1 flex flex-col items-center gap-0.5 px-4 py-4 transition-colors",
                  activeTab === i ? s.active : "text-muted-foreground hover:text-foreground hover:bg-white/60"
                )}
              >
                <span className="text-sm font-semibold">{s.label}</span>
                <span className={cn("text-[11px]", activeTab === i ? s.kolor : "text-muted-foreground/60")}>
                  {s.opis}
                </span>
              </button>
            ))}
          </div>

          {/* Zawartość aktywnego stylu */}
          <StyleView kanal={result[STYLE[activeTab].key]} styl={STYLE[activeTab]} />

          {/* Zastrzeżenie */}
          <div className="border-t px-6 py-3 bg-amber-50/60 flex gap-2 items-start">
            <AlertCircle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700">{result.zastrzezenie}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Widok stylu
// ---------------------------------------------------------------------------

function StyleView({
  kanal,
  styl,
}: {
  kanal: KanalOgloszenia;
  styl: (typeof STYLE)[number];
}) {
  return (
    <div className="p-6 space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* WWW – szerszy */}
        <div className="lg:col-span-3">
          <KanalCard
            icon={<Globe className="h-4 w-4" />}
            label="Wersja WWW"
            sublabel="Strona parafii / tablica ogłoszeń"
            tresc={kanal.www}
            accentClass={styl.border}
            bgClass={styl.bg}
          />
        </div>

        {/* Facebook + SMS – węższe, w stosie */}
        <div className="lg:col-span-2 flex flex-col gap-5">
          <KanalCard
            icon={<Facebook className="h-4 w-4" />}
            label="Facebook"
            sublabel="Post na profilu parafii"
            tresc={kanal.facebook}
            accentClass={styl.border}
            bgClass={styl.bg}
          />
          <SMSCard tresc={kanal.sms} accentClass={styl.border} bgClass={styl.bg} />
        </div>
      </div>

      {/* Kopiuj wszystkie */}
      <div className="flex justify-end pt-2 border-t gap-2">
        <CopyButton
          text={`WWW:\n${kanal.www}\n\nFACEBOOK:\n${kanal.facebook}\n\nSMS:\n${kanal.sms}`}
          label="Kopiuj wszystkie wersje"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Karta kanału
// ---------------------------------------------------------------------------

function KanalCard({
  icon,
  label,
  sublabel,
  tresc,
  accentClass,
  bgClass,
}: {
  icon: React.ReactNode;
  label: string;
  sublabel: string;
  tresc: string;
  accentClass: string;
  bgClass: string;
}) {
  return (
    <div className={cn("rounded-xl border flex flex-col overflow-hidden", accentClass)}>
      <div className={cn("flex items-center justify-between px-4 py-3 border-b", bgClass)}>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{icon}</span>
          <div>
            <p className="text-xs font-semibold text-foreground">{label}</p>
            <p className="text-[11px] text-muted-foreground">{sublabel}</p>
          </div>
        </div>
        <CopyButton text={tresc} label="Kopiuj" compact />
      </div>
      <div className="p-4 flex-1 bg-white">
        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{tresc}</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Karta SMS
// ---------------------------------------------------------------------------

function SMSCard({
  tresc,
  accentClass,
  bgClass,
}: {
  tresc: string;
  accentClass: string;
  bgClass: string;
}) {
  const len = tresc.length;
  const pct = Math.min(len / 160, 1);
  const counterColor =
    len > 160 ? "text-destructive" : len > 130 ? "text-amber-600" : "text-emerald-600";

  return (
    <div className={cn("rounded-xl border flex flex-col overflow-hidden", accentClass)}>
      <div className={cn("flex items-center justify-between px-4 py-3 border-b", bgClass)}>
        <div className="flex items-center gap-2">
          <MessageSquareText className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs font-semibold text-foreground">SMS</p>
            <p className="text-[11px] text-muted-foreground">Do parafian w bazie</p>
          </div>
        </div>
        <CopyButton text={tresc} label="Kopiuj" compact />
      </div>
      <div className="p-4 bg-white flex-1 space-y-3">
        <p className="text-sm text-foreground leading-relaxed">{tresc}</p>
        {/* Pasek postępu */}
        <div className="space-y-1">
          <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                len > 160 ? "bg-destructive" : len > 130 ? "bg-amber-400" : "bg-emerald-500"
              )}
              style={{ width: `${pct * 100}%` }}
            />
          </div>
          <p className={cn("text-[11px] font-medium text-right", counterColor)}>
            {len} / 160 znaków{len > 160 ? " ⚠ przekroczono limit" : ""}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Małe komponenty
// ---------------------------------------------------------------------------

function Pole({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      {children}
    </div>
  );
}

function SectionLabel({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{icon}</span>
      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
    </div>
  );
}

function CopyButton({
  text,
  label,
  compact = false,
}: {
  text: string;
  label: string;
  compact?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback silent
    }
  }

  return (
    <button
      onClick={copy}
      className={cn(
        "flex items-center gap-1.5 rounded-lg border transition-colors",
        compact
          ? "px-2.5 py-1 text-[11px]"
          : "px-3 py-1.5 text-xs font-medium",
        copied
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "text-muted-foreground hover:text-foreground hover:bg-muted"
      )}
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {copied ? "Skopiowano" : label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Helpers formatowania dat
// ---------------------------------------------------------------------------

function formatKiedy(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("pl-PL", {
      weekday: "short",
      day: "numeric",
      month: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatData(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("pl-PL", {
      weekday: "short",
      day: "numeric",
      month: "numeric",
    });
  } catch {
    return dateStr;
  }
}

// ---------------------------------------------------------------------------
// Style
// ---------------------------------------------------------------------------

const inputCls =
  "w-full rounded-lg border bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/50";
