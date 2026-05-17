"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Archive,
  ArchiveRestore,
  Calendar,
  Check,
  Copy,
  Download,
  FileImage,
  FileText,
  Filter,
  Loader2,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Search,
  Tag,
  Trash2,
  Upload,
  User,
  X,
} from "lucide-react";
import { archiwumApi } from "@/lib/api";
import { SkanListItem, SkanRead, TypDokumentuSkan } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Konfiguracja typów dokumentów
// ---------------------------------------------------------------------------

const TYP_CFG: Record<TypDokumentuSkan, { label: string; kolor: string }> = {
  metryka_chrztu: { label: "Metryka chrztu", kolor: "bg-blue-100 text-blue-700 border-blue-200" },
  metryka_slubu: { label: "Metryka ślubu", kolor: "bg-rose-100 text-rose-700 border-rose-200" },
  metryka_bierzmowania: { label: "Metryka bierzmowania", kolor: "bg-violet-100 text-violet-700 border-violet-200" },
  metryka_komunii: { label: "Metryka komunii", kolor: "bg-amber-100 text-amber-700 border-amber-200" },
  zaswiadczenie: { label: "Zaświadczenie", kolor: "bg-green-100 text-green-700 border-green-200" },
  formularz: { label: "Formularz", kolor: "bg-teal-100 text-teal-700 border-teal-200" },
  akt_zgonu: { label: "Akt zgonu", kolor: "bg-slate-100 text-slate-700 border-slate-200" },
  pismo_urzedowe: { label: "Pismo urzędowe", kolor: "bg-indigo-100 text-indigo-700 border-indigo-200" },
  korespondencja: { label: "Korespondencja", kolor: "bg-cyan-100 text-cyan-700 border-cyan-200" },
  inne: { label: "Inne", kolor: "bg-gray-100 text-gray-600 border-gray-200" },
};

const TYPY_LIST = Object.entries(TYP_CFG) as [TypDokumentuSkan, { label: string; kolor: string }][];
const MAX_SIZE = 10 * 1024 * 1024;
const ALLOWED = ["application/pdf", "image/jpeg", "image/png", "image/jpg"];

// ---------------------------------------------------------------------------
// Strona główna
// ---------------------------------------------------------------------------

export default function ArchiwumPage() {
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [typFilter, setTypFilter] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [activeTag, setActiveTag] = useState("");
  const [draggingOver, setDraggingOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  // Lista dokumentów
  const { data: lista = [], isLoading: loadingLista } = useQuery<SkanListItem[]>({
    queryKey: ["archiwum-lista", debouncedSearch, typFilter, showArchived, activeTag],
    queryFn: () =>
      archiwumApi.list({
        q: debouncedSearch || undefined,
        typ: typFilter || undefined,
        zarchiwizowany: showArchived,
        tag: activeTag || undefined,
        limit: 50,
      }),
    staleTime: 30_000,
  });

  // Szczegóły wybranego dokumentu
  const { data: skan, isFetching: loadingDetail } = useQuery<SkanRead>({
    queryKey: ["archiwum-detail", selectedId],
    queryFn: () => archiwumApi.get(selectedId!),
    enabled: !!selectedId,
    staleTime: 0,
  });

  // Upload
  const uploadMut = useMutation({
    mutationFn: (file: File) =>
      archiwumApi.upload(file, undefined, (p) => setUploadProgress(p)),
    onMutate: () => {
      setUploadError(null);
      setUploadProgress(0);
    },
    onSuccess: (data: SkanRead) => {
      qc.invalidateQueries({ queryKey: ["archiwum-lista"] });
      setSelectedId(data.id);
      setUploadProgress(0);
    },
    onError: (e: Error) => {
      setUploadError(e.message);
      setUploadProgress(0);
    },
  });

  function handleFile(file: File) {
    if (!ALLOWED.includes(file.type)) {
      setUploadError("Dozwolone formaty: PDF, JPG, PNG");
      return;
    }
    if (file.size > MAX_SIZE) {
      setUploadError("Plik zbyt duży – max 10 MB");
      return;
    }
    uploadMut.mutate(file);
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDraggingOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* ── Panel lewy: lista ── */}
      <aside className="w-80 flex-shrink-0 border-r bg-white flex flex-col">
        {/* Nagłówek + upload */}
        <div className="px-4 pt-4 pb-3 border-b space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Archive className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold text-foreground">Archiwum</span>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMut.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-white hover:bg-primary/90 transition-colors disabled:opacity-60"
            >
              {uploadMut.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Upload className="h-3.5 w-3.5" />
              )}
              Dodaj
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
                e.target.value = "";
              }}
            />
          </div>

          {/* Pasek postępu upload */}
          {uploadMut.isPending && (
            <div className="space-y-1">
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                {uploadProgress < 60 ? "Przesyłam plik…" : "Trwa OCR i klasyfikacja…"}
              </p>
            </div>
          )}

          {uploadError && (
            <div className="flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
              {uploadError}
            </div>
          )}

          {/* Wyszukiwarka */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Szukaj w tekście OCR…"
              className="w-full rounded-lg border bg-gray-50 pl-8 pr-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/60"
            />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-2.5 top-1/2 -translate-y-1/2">
                <X className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            )}
          </div>

          {/* Filtry */}
          <div className="flex gap-2">
            <select
              value={typFilter}
              onChange={(e) => setTypFilter(e.target.value)}
              className="flex-1 rounded-lg border bg-gray-50 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              <option value="">Wszystkie typy</option>
              {TYPY_LIST.map(([key, { label }]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
            <button
              onClick={() => setShowArchived((v) => !v)}
              className={cn(
                "rounded-lg border px-2.5 py-1.5 text-xs transition-colors",
                showArchived
                  ? "bg-primary/10 text-primary border-primary/30"
                  : "text-muted-foreground hover:bg-muted"
              )}
              title={showArchived ? "Ukryj archiwum" : "Pokaż archiwum"}
            >
              <Archive className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Aktywny tag filter */}
          {activeTag && (
            <div className="flex items-center gap-1.5">
              <span className="flex items-center gap-1 rounded-full border bg-primary/5 px-2.5 py-0.5 text-xs text-primary">
                <Tag className="h-3 w-3" /> {activeTag}
                <button onClick={() => setActiveTag("")}>
                  <X className="h-3 w-3 ml-0.5" />
                </button>
              </span>
            </div>
          )}
        </div>

        {/* Lista dokumentów */}
        <div className="flex-1 overflow-y-auto divide-y">
          {loadingLista && lista.length === 0 && (
            <div className="flex justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          )}
          {!loadingLista && lista.length === 0 && (
            <div className="p-6 text-center">
              <Archive className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">
                {search || typFilter ? "Brak wyników dla filtrów" : "Brak dokumentów. Dodaj pierwszy."}
              </p>
            </div>
          )}
          {lista.map((doc) => (
            <ListItem
              key={doc.id}
              doc={doc}
              active={selectedId === doc.id}
              onSelect={() => setSelectedId(doc.id)}
              onTagClick={(tag) => setActiveTag(tag)}
            />
          ))}
        </div>
      </aside>

      {/* ── Panel prawy: szczegóły ── */}
      <main
        className="flex-1 overflow-y-auto bg-gray-50"
        onDragOver={(e) => { e.preventDefault(); setDraggingOver(true); }}
        onDragLeave={() => setDraggingOver(false)}
        onDrop={handleDrop}
      >
        {draggingOver && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-primary/5 border-2 border-dashed border-primary rounded-xl m-4 pointer-events-none">
            <div className="text-center">
              <Upload className="h-10 w-10 text-primary mx-auto mb-2" />
              <p className="font-medium text-primary">Upuść plik tutaj</p>
            </div>
          </div>
        )}

        {!selectedId && !uploadMut.isPending ? (
          <EmptyState onUpload={() => fileInputRef.current?.click()} />
        ) : loadingDetail && !skan ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : uploadMut.isPending && !skan ? (
          <UploadingView progress={uploadProgress} />
        ) : skan ? (
          <DetailView
            skan={skan}
            onTagClick={(tag) => setActiveTag(tag)}
            onUpdated={() => {
              qc.invalidateQueries({ queryKey: ["archiwum-detail", selectedId] });
              qc.invalidateQueries({ queryKey: ["archiwum-lista"] });
            }}
            onDeleted={() => {
              qc.invalidateQueries({ queryKey: ["archiwum-lista"] });
              setSelectedId(null);
            }}
          />
        ) : null}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Element listy
// ---------------------------------------------------------------------------

function ListItem({
  doc,
  active,
  onSelect,
  onTagClick,
}: {
  doc: SkanListItem;
  active: boolean;
  onSelect: () => void;
  onTagClick: (t: string) => void;
}) {
  const cfg = TYP_CFG[doc.typ_dokumentu] ?? TYP_CFG.inne;
  const isPdf = doc.typ_pliku === "pdf";

  return (
    <div
      onClick={onSelect}
      className={cn(
        "px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors",
        active && "bg-primary/5 border-l-2 border-primary"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("mt-0.5 rounded-lg p-1.5 flex-shrink-0", active ? "bg-primary/10" : "bg-gray-100")}>
          {isPdf ? (
            <FileText className={cn("h-4 w-4", active ? "text-primary" : "text-muted-foreground")} />
          ) : (
            <FileImage className={cn("h-4 w-4", active ? "text-primary" : "text-muted-foreground")} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-foreground truncate">{doc.nazwa_pliku}</p>
          <span className={cn("inline-block mt-1 text-[10px] font-medium px-1.5 py-0.5 rounded border", cfg.kolor)}>
            {cfg.label}
          </span>
          {doc.tagi.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {doc.tagi.slice(0, 3).map((tag) => (
                <button
                  key={tag}
                  onClick={(e) => { e.stopPropagation(); onTagClick(tag); }}
                  className="text-[10px] rounded-full bg-muted px-1.5 py-0.5 text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors"
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
          <p className="text-[10px] text-muted-foreground mt-1">
            {new Date(doc.created_at).toLocaleDateString("pl-PL")}
            {doc.ocr_status === "blad" && (
              <span className="ml-2 text-destructive">⚠ OCR błąd</span>
            )}
            {doc.zarchiwizowany && (
              <span className="ml-2 text-amber-600">📦 archiwum</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Widok szczegółów
// ---------------------------------------------------------------------------

function DetailView({
  skan,
  onTagClick,
  onUpdated,
  onDeleted,
}: {
  skan: SkanRead;
  onTagClick: (t: string) => void;
  onUpdated: () => void;
  onDeleted: () => void;
}) {
  const [tagInput, setTagInput] = useState("");
  const [notes, setNotes] = useState(skan.notatki || "");
  const [ocrOpen, setOcrOpen] = useState(false);
  const cfg = TYP_CFG[skan.typ_dokumentu] ?? TYP_CFG.inne;

  const updateMut = useMutation({
    mutationFn: (data: unknown) => archiwumApi.update(skan.id, data),
    onSuccess: onUpdated,
  });

  const archiwizujMut = useMutation({
    mutationFn: () => archiwumApi.archiwizuj(skan.id),
    onSuccess: onUpdated,
  });

  const ocrMut = useMutation({
    mutationFn: () => archiwumApi.ponowOCR(skan.id),
    onSuccess: onUpdated,
  });

  const deleteMut = useMutation({
    mutationFn: () => archiwumApi.usun(skan.id),
    onSuccess: onDeleted,
  });

  async function handleDownload() {
    const { url } = await archiwumApi.pobierz(skan.id);
    window.open(url, "_blank");
  }

  function addTag() {
    const t = tagInput.trim().toLowerCase();
    if (!t || skan.tagi.includes(t)) { setTagInput(""); return; }
    updateMut.mutate({ tagi: [...skan.tagi, t] });
    setTagInput("");
  }

  function removeTag(tag: string) {
    updateMut.mutate({ tagi: skan.tagi.filter((x) => x !== tag) });
  }

  // Update notes on blur
  useEffect(() => {
    setNotes(skan.notatki || "");
  }, [skan.notatki]);

  return (
    <div className="p-6 space-y-5 max-w-4xl mx-auto">
      {/* Nagłówek */}
      <div className="bg-white rounded-xl border shadow-sm p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <div className="rounded-xl bg-primary/10 p-3 flex-shrink-0">
              {skan.typ_pliku === "pdf" ? (
                <FileText className="h-6 w-6 text-primary" />
              ) : (
                <FileImage className="h-6 w-6 text-primary" />
              )}
            </div>
            <div className="min-w-0">
              <h2 className="font-semibold text-foreground truncate">{skan.nazwa_pliku}</h2>
              <div className="flex flex-wrap gap-2 mt-1.5 items-center">
                <span className={cn("text-xs font-medium px-2 py-0.5 rounded border", cfg.kolor)}>
                  {cfg.label}
                </span>
                <span className="text-xs text-muted-foreground">
                  {(skan.rozmiar_bajtow / 1024).toFixed(0)} KB
                </span>
                <span className="text-xs text-muted-foreground">
                  {new Date(skan.created_at).toLocaleDateString("pl-PL", {
                    day: "numeric", month: "long", year: "numeric"
                  })}
                </span>
                {skan.ocr_status === "gotowy" && (
                  <span className="text-xs text-emerald-600 flex items-center gap-0.5">
                    <Check className="h-3 w-3" /> OCR gotowy
                  </span>
                )}
                {skan.ocr_status === "blad" && (
                  <span className="text-xs text-destructive flex items-center gap-0.5">
                    <AlertCircle className="h-3 w-3" /> OCR błąd
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Akcje */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleDownload}
              className="p-2 rounded-lg border hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
              title="Pobierz plik"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={() => archiwizujMut.mutate()}
              disabled={archiwizujMut.isPending}
              className="p-2 rounded-lg border hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
              title={skan.zarchiwizowany ? "Przywróć z archiwum" : "Archiwizuj"}
            >
              {skan.zarchiwizowany ? <ArchiveRestore className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
            </button>
            {skan.ocr_status === "blad" && (
              <button
                onClick={() => ocrMut.mutate()}
                disabled={ocrMut.isPending}
                className="p-2 rounded-lg border hover:bg-muted transition-colors text-muted-foreground hover:text-amber-600"
                title="Ponów OCR"
              >
                {ocrMut.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </button>
            )}
            <button
              onClick={() => { if (confirm("Usunąć dokument?")) deleteMut.mutate(); }}
              className="p-2 rounded-lg border hover:bg-destructive/10 transition-colors text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Błąd OCR */}
      {skan.ocr_status === "blad" && skan.ocr_blad && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 flex gap-2">
          <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-destructive">Błąd OCR</p>
            <p className="text-xs text-muted-foreground mt-0.5">{skan.ocr_blad}</p>
          </div>
        </div>
      )}

      {/* Siatka encji */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Osoby */}
        {skan.osoby.length > 0 && (
          <InfoCard icon={<User className="h-4 w-4" />} title="Osoby">
            {skan.osoby.map((osoba, i) => (
              <p key={i} className="text-sm text-foreground">{osoba}</p>
            ))}
          </InfoCard>
        )}

        {/* Data wystawienia + jednostka */}
        {(skan.data_wystawienia || skan.jednostka_wystawiajaca) && (
          <InfoCard icon={<Calendar className="h-4 w-4" />} title="Szczegóły">
            {skan.data_wystawienia && (
              <p className="text-sm text-foreground">
                {new Date(skan.data_wystawienia).toLocaleDateString("pl-PL", {
                  day: "numeric", month: "long", year: "numeric"
                })}
              </p>
            )}
            {skan.jednostka_wystawiajaca && (
              <p className="text-sm text-muted-foreground">{skan.jednostka_wystawiajaca}</p>
            )}
          </InfoCard>
        )}

        {/* Dane kontaktowe */}
        {Object.values(skan.dane_kontaktowe).some(Boolean) && (
          <InfoCard icon={<Phone className="h-4 w-4" />} title="Kontakt">
            {skan.dane_kontaktowe.telefon && (
              <div className="flex items-center gap-1.5 text-sm">
                <Phone className="h-3 w-3 text-muted-foreground" />
                {skan.dane_kontaktowe.telefon}
              </div>
            )}
            {skan.dane_kontaktowe.email && (
              <div className="flex items-center gap-1.5 text-sm">
                <Mail className="h-3 w-3 text-muted-foreground" />
                {skan.dane_kontaktowe.email}
              </div>
            )}
            {skan.dane_kontaktowe.adres && (
              <div className="flex items-center gap-1.5 text-sm">
                <MapPin className="h-3 w-3 text-muted-foreground" />
                {skan.dane_kontaktowe.adres}
              </div>
            )}
          </InfoCard>
        )}
      </div>

      {/* Tagi */}
      <div className="bg-white rounded-xl border shadow-sm p-5 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <Tag className="h-3.5 w-3.5" /> Tagi
        </h3>
        <div className="flex flex-wrap gap-2">
          {skan.tagi.map((tag) => (
            <button
              key={tag}
              onClick={() => onTagClick(tag)}
              className="group flex items-center gap-1 rounded-full border px-3 py-1 text-xs bg-muted hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-colors"
            >
              {tag}
              <X
                className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity ml-0.5"
                onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
              />
            </button>
          ))}
          <div className="flex items-center gap-1">
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addTag(); }}}
              placeholder="+ Dodaj tag"
              className="rounded-full border px-3 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40 w-28 placeholder:text-muted-foreground/50"
            />
            {tagInput && (
              <button
                onClick={addTag}
                className="rounded-full bg-primary/10 text-primary px-2 py-1 text-xs"
              >
                <Check className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Notatki */}
      <div className="bg-white rounded-xl border shadow-sm p-5 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Notatki
        </h3>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={() => {
            if (notes !== (skan.notatki || "")) {
              updateMut.mutate({ notatki: notes });
            }
          }}
          placeholder="Dodaj notatki do dokumentu… (zapisuje się automatycznie)"
          rows={3}
          className="w-full rounded-lg border bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground/50 resize-none"
        />
      </div>

      {/* Tekst OCR */}
      {skan.tresc_ocr && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <button
            onClick={() => setOcrOpen((v) => !v)}
            className="flex w-full items-center justify-between px-5 py-4 hover:bg-muted/20 transition-colors"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Tekst OCR ({skan.tresc_ocr.length} znaków)
            </span>
            <div className="flex items-center gap-2">
              <CopyButton text={skan.tresc_ocr} compact />
              {ocrOpen ? (
                <X className="h-3.5 w-3.5 text-muted-foreground" />
              ) : (
                <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              )}
            </div>
          </button>
          {ocrOpen && (
            <div className="px-5 pb-5">
              <pre className="whitespace-pre-wrap text-sm text-foreground font-mono leading-relaxed bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto border">
                {skan.tresc_ocr}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stany puste i ładowania
// ---------------------------------------------------------------------------

function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 p-8">
      <div className="rounded-2xl bg-primary/10 p-6">
        <Archive className="h-12 w-12 text-primary" />
      </div>
      <div className="text-center max-w-sm">
        <h2 className="text-lg font-semibold text-foreground">Archiwum Dokumentów</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Wgraj PDF, JPG lub PNG. AI automatycznie rozpozna tekst (OCR), sklasyfikuje dokument i wydobędzie kluczowe dane.
        </p>
      </div>
      <button
        onClick={onUpload}
        className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white hover:bg-primary/90 transition-colors"
      >
        <Upload className="h-4 w-4" />
        Wgraj pierwszy dokument
      </button>
      <p className="text-xs text-muted-foreground">PDF · JPG · PNG · max 10 MB</p>
      <p className="text-xs text-muted-foreground/60 max-w-xs text-center">
        Możesz też przeciągnąć i upuścić plik na ten obszar
      </p>
    </div>
  );
}

function UploadingView({ progress }: { progress: number }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 p-8">
      <div className="relative">
        <div className="rounded-2xl bg-primary/10 p-6">
          <Archive className="h-12 w-12 text-primary/30" />
        </div>
        <Loader2 className="h-7 w-7 animate-spin text-primary absolute -bottom-1 -right-1" />
      </div>
      <div className="text-center w-full max-w-xs">
        <p className="text-sm font-medium text-foreground">
          {progress < 60 ? "Przesyłam plik…" : "OCR i klasyfikacja AI…"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {progress < 60
            ? "Zapisuję dokument w bezpiecznym archiwum"
            : "Rozpoznaję tekst, classyfikuję typ, wydobywam encje"}
        </p>
        <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-500"
            style={{ width: `${Math.max(progress, 10)}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">To może zająć do 30 sekund</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pomocnicze komponenty
// ---------------------------------------------------------------------------

function InfoCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border shadow-sm p-4 space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
        <span className="text-muted-foreground">{icon}</span>
        {title}
      </h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function CopyButton({ text, compact }: { text: string; compact?: boolean }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  }
  return (
    <button
      onClick={(e) => { e.stopPropagation(); copy(); }}
      className={cn(
        "flex items-center gap-1 rounded border text-muted-foreground hover:text-foreground transition-colors",
        compact ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        copied && "text-emerald-600 border-emerald-200"
      )}
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {!compact && (copied ? "Skopiowano" : "Kopiuj")}
    </button>
  );
}
