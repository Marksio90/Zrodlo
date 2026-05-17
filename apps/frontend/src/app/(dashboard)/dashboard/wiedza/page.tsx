"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Brain,
  Check,
  ChevronDown,
  Edit2,
  Globe,
  Lock,
  Plus,
  Search,
  Sparkles,
  Tag,
  Trash2,
  X,
  Zap,
} from "lucide-react";
import { format } from "date-fns";
import { pl } from "date-fns/locale";
import { wiedzaApi } from "@/lib/api";
import {
  ETYKIETY_KATEGORII,
  KategoriaWiedzy,
  NotatkaWiedzy,
  SzukajWiedzyResponse,
  WynikSzukania,
} from "@/types";
import { cn } from "@/lib/utils";

const KATEGORIE = Object.keys(ETYKIETY_KATEGORII) as KategoriaWiedzy[];

const KOLORY_KATEGORII: Record<KategoriaWiedzy, string> = {
  liturgia: "bg-purple-100 text-purple-700",
  duszpasterstwo: "bg-blue-100 text-blue-700",
  administracja: "bg-gray-100 text-gray-700",
  prawo_kanoniczne: "bg-red-100 text-red-700",
  historia_parafii: "bg-amber-100 text-amber-700",
  katecheza: "bg-green-100 text-green-700",
  inne: "bg-slate-100 text-slate-700",
};

// ---------------------------------------------------------------------------
// Modal – Create / Edit
// ---------------------------------------------------------------------------

interface ModalFormProps {
  initial?: NotatkaWiedzy | null;
  onClose: () => void;
  onSaved: () => void;
}

function ModalForm({ initial, onClose, onSaved }: ModalFormProps) {
  const qc = useQueryClient();
  const [tytul, setTytul] = useState(initial?.tytul ?? "");
  const [tresc, setTresc] = useState(initial?.tresc ?? "");
  const [kategoria, setKategoria] = useState<KategoriaWiedzy>(
    initial?.kategoria ?? "inne"
  );
  const [tagi, setTagi] = useState<string[]>(initial?.tagi ?? []);
  const [tagInput, setTagInput] = useState("");
  const [publiczna, setPubliczna] = useState(initial?.publiczna ?? false);

  const mutation = useMutation({
    mutationFn: (data: object) =>
      initial
        ? wiedzaApi.update(initial.id, data)
        : wiedzaApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wiedza"] });
      onSaved();
    },
  });

  function addTag(value: string) {
    const t = value.trim().toLowerCase();
    if (t && !tagi.includes(t)) setTagi((prev) => [...prev, t]);
  }

  function handleTagKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(tagInput);
      setTagInput("");
    }
  }

  function removeTag(t: string) {
    setTagi((prev) => prev.filter((x) => x !== t));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (tagInput.trim()) addTag(tagInput);
    mutation.mutate({ tytul, tresc, kategoria, tagi, publiczna });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">
            {initial ? "Edytuj notatkę" : "Nowa notatka wiedzy"}
          </h2>
          <button onClick={onClose} className="rounded-md p-1.5 hover:bg-muted">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium mb-1.5">Tytuł *</label>
            <input
              value={tytul}
              onChange={(e) => setTytul(e.target.value)}
              required
              minLength={3}
              maxLength={400}
              placeholder="Krótki, opisowy tytuł notatki"
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Treść *</label>
            <textarea
              value={tresc}
              onChange={(e) => setTresc(e.target.value)}
              required
              minLength={10}
              rows={8}
              placeholder="Opisz wydarzenie, decyzję, informację… Im więcej szczegółów, tym lepsze wyniki wyszukiwania."
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Kategoria</label>
              <select
                value={kategoria}
                onChange={(e) => setKategoria(e.target.value as KategoriaWiedzy)}
                className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                {KATEGORIE.map((k) => (
                  <option key={k} value={k}>
                    {ETYKIETY_KATEGORII[k]}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col justify-end">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <div
                  onClick={() => setPubliczna((p) => !p)}
                  className={cn(
                    "h-5 w-5 rounded flex items-center justify-center border-2 transition-colors",
                    publiczna
                      ? "bg-primary border-primary"
                      : "border-input"
                  )}
                >
                  {publiczna && <Check className="h-3 w-3 text-white" />}
                </div>
                <span className="text-sm font-medium">Publiczna (widoczna dla parafian)</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Tagi</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {tagi.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                >
                  {t}
                  <button
                    type="button"
                    onClick={() => removeTag(t)}
                    className="hover:text-primary/70"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagKeyDown}
              onBlur={() => {
                if (tagInput.trim()) {
                  addTag(tagInput);
                  setTagInput("");
                }
              }}
              placeholder="Wpisz tag i naciśnij Enter lub przecinek"
              className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </form>

        <div className="border-t px-6 py-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-medium border hover:bg-muted transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={() => {
              if (tagInput.trim()) addTag(tagInput);
              mutation.mutate({ tytul, tresc, kategoria, tagi, publiczna });
            }}
            disabled={mutation.isPending || tytul.length < 3 || tresc.length < 10}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? "Zapisuję…" : initial ? "Zapisz zmiany" : "Dodaj notatkę"}
          </button>
        </div>
        {mutation.isError && (
          <p className="px-6 pb-4 text-sm text-destructive">
            {(mutation.error as Error).message}
          </p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Note card
// ---------------------------------------------------------------------------

interface NoteCardProps {
  note: NotatkaWiedzy;
  onEdit: () => void;
  onDelete: () => void;
}

function NoteCard({ note, onEdit, onDelete }: NoteCardProps) {
  const kat = note.kategoria as KategoriaWiedzy;
  return (
    <div className="rounded-xl border bg-white p-5 flex flex-col gap-3 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <span
          className={cn(
            "inline-block rounded-full px-2.5 py-0.5 text-xs font-medium shrink-0",
            KOLORY_KATEGORII[kat] ?? "bg-slate-100 text-slate-700"
          )}
        >
          {ETYKIETY_KATEGORII[kat] ?? kat}
        </span>
        <div className="flex items-center gap-1 shrink-0">
          {note.publiczna ? (
            <span title="Publiczna"><Globe className="h-3.5 w-3.5 text-muted-foreground" /></span>
          ) : (
            <span title="Wewnętrzna"><Lock className="h-3.5 w-3.5 text-muted-foreground" /></span>
          )}
          {note.qdrant_id && (
            <span title="Osadzona w Qdrant"><Zap className="h-3.5 w-3.5 text-amber-500" /></span>
          )}
        </div>
      </div>

      <h3 className="font-semibold text-sm leading-snug">{note.tytul}</h3>

      <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
        {note.tresc}
      </p>

      {note.tagi.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {note.tagi.slice(0, 4).map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-0.5 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
            >
              <Tag className="h-2.5 w-2.5" />
              {t}
            </span>
          ))}
          {note.tagi.length > 4 && (
            <span className="text-xs text-muted-foreground">+{note.tagi.length - 4}</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between pt-1 border-t">
        <span className="text-xs text-muted-foreground">
          {format(new Date(note.updated_at), "d MMM yyyy", { locale: pl })}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            className="rounded p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <Edit2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={onDelete}
            className="rounded p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Search result panel
// ---------------------------------------------------------------------------

function SearchResultPanel({
  result,
  pytanie,
  onClose,
}: {
  result: SzukajWiedzyResponse;
  pytanie: string;
  onClose: () => void;
}) {
  return (
    <div className="rounded-xl border bg-white overflow-hidden mb-6">
      <div className="flex items-center justify-between border-b bg-primary/5 px-5 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold text-primary">Odpowiedź AI</span>
          <span className="text-xs text-muted-foreground">· {result.model_uzyty}</span>
        </div>
        <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1.5 font-medium">Pytanie: {pytanie}</p>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.odpowiedz}</p>
        </div>

        {result.wyniki.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              Źródła ({result.wyniki.length})
            </p>
            <div className="space-y-2">
              {result.wyniki.map((w: WynikSzukania) => (
                <div
                  key={w.id}
                  className="rounded-lg border bg-muted/30 px-4 py-3 text-sm"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{w.tytul}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          KOLORY_KATEGORII[w.kategoria as KategoriaWiedzy] ??
                            "bg-slate-100 text-slate-700"
                        )}
                      >
                        {ETYKIETY_KATEGORII[w.kategoria as KategoriaWiedzy] ?? w.kategoria}
                      </span>
                      {w.score !== null && (
                        <span className="text-xs text-muted-foreground tabular-nums">
                          {Math.round(w.score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-muted-foreground text-xs line-clamp-2">{w.fragment}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function WiedzaPage() {
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editNote, setEditNote] = useState<NotatkaWiedzy | null>(null);
  const [kategoria, setKategoria] = useState<KategoriaWiedzy | "">("");
  const [szukajText, setSzukajText] = useState("");
  const [semantyczneQuery, setSemantozneQuery] = useState("");
  const [semantyczneResult, setSemantozneResult] =
    useState<SzukajWiedzyResponse | null>(null);
  const [expandedEmbed, setExpandedEmbed] = useState(false);

  const { data: notatki = [], isLoading } = useQuery<NotatkaWiedzy[]>({
    queryKey: ["wiedza", kategoria, szukajText],
    queryFn: () =>
      wiedzaApi.list({
        ...(kategoria ? { kategoria } : {}),
        ...(szukajText ? { szukaj: szukajText } : {}),
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: wiedzaApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wiedza"] }),
  });

  const embedWszystkieMutation = useMutation({
    mutationFn: wiedzaApi.embedWszystkie,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wiedza"] });
      setExpandedEmbed(false);
    },
  });

  const szukajMutation = useMutation({
    mutationFn: wiedzaApi.szukaj,
    onSuccess: (data: SzukajWiedzyResponse) => {
      setSemantozneResult(data);
    },
  });

  function handleDelete(id: string) {
    if (confirm("Usunąć tę notatkę?")) deleteMutation.mutate(id);
  }

  function handleSemantyczneSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!semantyczneQuery.trim()) return;
    szukajMutation.mutate({ pytanie: semantyczneQuery, limit: 5 });
  }

  const nieosadzone = notatki.filter((n) => !n.qdrant_id).length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">Baza Wiedzy Parafii</h1>
              <p className="text-xs text-muted-foreground">
                Notatki, historia, decyzje z wyszukiwaniem semantycznym
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {nieosadzone > 0 && (
              <button
                onClick={() => setExpandedEmbed((p) => !p)}
                className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium text-amber-600 border-amber-200 bg-amber-50 hover:bg-amber-100 transition-colors"
              >
                <Zap className="h-3.5 w-3.5" />
                {nieosadzone} bez embeddingu
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 transition-transform",
                    expandedEmbed && "rotate-180"
                  )}
                />
              </button>
            )}
            <button
              onClick={() => {
                setEditNote(null);
                setModalOpen(true);
              }}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Nowa notatka
            </button>
          </div>
        </div>

        {expandedEmbed && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 flex items-center justify-between">
            <p className="text-sm text-amber-800">
              {nieosadzone} notatek nie jest osadzonych w Qdrant – nie pojawią się w wynikach
              wyszukiwania semantycznego.
            </p>
            <button
              onClick={() => embedWszystkieMutation.mutate()}
              disabled={embedWszystkieMutation.isPending}
              className="ml-4 shrink-0 rounded-md bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-50 transition-colors"
            >
              {embedWszystkieMutation.isPending ? "Osadzam…" : "Osadź wszystkie"}
            </button>
          </div>
        )}
        {embedWszystkieMutation.isSuccess && (
          <p className="mt-2 text-xs text-green-700">
            Osadzono: {(embedWszystkieMutation.data as { osadzone: number }).osadzone} notatek.
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Semantic search bar */}
        <form onSubmit={handleSemantyczneSearch} className="mb-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                value={semantyczneQuery}
                onChange={(e) => setSemantozneQuery(e.target.value)}
                placeholder={'Zadaj pytanie... "Kiedy była ostatnia pielgrzymka?", "Kto organizował rekolekcje?"'}
                className="w-full rounded-lg border pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <button
              type="submit"
              disabled={szukajMutation.isPending || !semantyczneQuery.trim()}
              className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {szukajMutation.isPending ? "Szukam…" : "Szukaj"}
            </button>
            {semantyczneResult && (
              <button
                type="button"
                onClick={() => {
                  setSemantozneResult(null);
                  setSemantozneQuery("");
                }}
                className="rounded-lg border px-3 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </form>

        {/* Search results */}
        {szukajMutation.isError && (
          <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {(szukajMutation.error as Error).message}
          </div>
        )}
        {semantyczneResult && (
          <SearchResultPanel
            result={semantyczneResult}
            pytanie={semantyczneQuery}
            onClose={() => setSemantozneResult(null)}
          />
        )}

        {/* Filters */}
        <div className="flex items-center gap-2 mb-5 flex-wrap">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={szukajText}
              onChange={(e) => setSzukajText(e.target.value)}
              placeholder="Szukaj w tytule i treści…"
              className="rounded-md border pl-8 pr-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setKategoria("")}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                kategoria === ""
                  ? "bg-primary text-white"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              Wszystkie
            </button>
            {KATEGORIE.map((k) => (
              <button
                key={k}
                onClick={() => setKategoria(kategoria === k ? "" : k)}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                  kategoria === k
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                )}
              >
                {ETYKIETY_KATEGORII[k]}
              </button>
            ))}
          </div>
        </div>

        {/* Note grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="h-48 rounded-xl border bg-muted/40 animate-pulse"
              />
            ))}
          </div>
        ) : notatki.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Brain className="h-12 w-12 text-muted-foreground/40 mb-4" />
            <p className="text-muted-foreground font-medium">
              {szukajText || kategoria
                ? "Brak wyników dla wybranych filtrów"
                : "Baza wiedzy jest pusta"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {szukajText || kategoria
                ? "Spróbuj zmienić kryteria wyszukiwania"
                : "Dodaj pierwszą notatkę, by zacząć budować bazę wiedzy parafii"}
            </p>
            {!szukajText && !kategoria && (
              <button
                onClick={() => {
                  setEditNote(null);
                  setModalOpen(true);
                }}
                className="mt-4 flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Dodaj pierwszą notatkę
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {notatki.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onEdit={() => {
                  setEditNote(note);
                  setModalOpen(true);
                }}
                onDelete={() => handleDelete(note.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <ModalForm
          initial={editNote}
          onClose={() => {
            setModalOpen(false);
            setEditNote(null);
          }}
          onSaved={() => {
            setModalOpen(false);
            setEditNote(null);
          }}
        />
      )}
    </div>
  );
}
