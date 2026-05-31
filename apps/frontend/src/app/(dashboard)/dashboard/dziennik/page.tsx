"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { pl } from "date-fns/locale";
import {
  ArrowDownToLine,
  BookMarked,
  ChevronDown,
  ChevronRight,
  Download,
  Inbox,
  Loader2,
  Plus,
  Search,
  Send,
  Shuffle,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { dziennikApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

// ── Types ──────────────────────────────────────────────────────────────────────

interface WpisDziennika {
  id: string;
  numer_pelny: string;
  typ: "przychodzace" | "wychodzace" | "wewnetrzne";
  status: string;
  data_wpisu: string;
  data_pisma: string | null;
  nadawca: string | null;
  odbiorca: string | null;
  przedmiot: string;
  uwagi: string | null;
  kolejny_numer: number;
  rok: number;
}

interface StatystykiDziennika {
  rok: number;
  lacznie: number;
  przychodzace: number;
  wychodzace: number;
  wewnetrzne: number;
  ostatni_numer: number;
}

interface FormData {
  typ: string;
  data_wpisu: string;
  data_pisma: string;
  nadawca: string;
  odbiorca: string;
  przedmiot: string;
  uwagi: string;
  status: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const TYP_CFG = {
  przychodzace: {
    label: "Przychodzące",
    icon: Inbox,
    color: "text-blue-600",
    bg: "bg-blue-50",
    badge: "bg-blue-100 text-blue-700",
  },
  wychodzace: {
    label: "Wychodzące",
    icon: Send,
    color: "text-green-600",
    bg: "bg-green-50",
    badge: "bg-green-100 text-green-700",
  },
  wewnetrzne: {
    label: "Wewnętrzne",
    icon: Shuffle,
    color: "text-purple-600",
    bg: "bg-purple-50",
    badge: "bg-purple-100 text-purple-700",
  },
};

const STATUS_LABELS: Record<string, string> = {
  robocze: "Robocze",
  zarejestrowane: "Zarejestrowane",
  wyslane: "Wysłane",
  zarchiwizowane: "Zarchiwizowane",
};

const STATUS_COLORS: Record<string, string> = {
  robocze: "bg-gray-100 text-gray-600",
  zarejestrowane: "bg-blue-100 text-blue-700",
  wyslane: "bg-green-100 text-green-700",
  zarchiwizowane: "bg-amber-100 text-amber-700",
};

function formatDate(d: string) {
  try {
    return format(new Date(d), "d MMM yyyy", { locale: pl });
  } catch {
    return d;
  }
}

const TODAY = new Date().toISOString().split("T")[0];
const ROK = new Date().getFullYear();

const EMPTY_FORM: FormData = {
  typ: "przychodzace",
  data_wpisu: TODAY,
  data_pisma: "",
  nadawca: "",
  odbiorca: "",
  przedmiot: "",
  uwagi: "",
  status: "robocze",
};

// ── Komponent główny ───────────────────────────────────────────────────────────

export default function DziennikPage() {
  const user = getUser();
  const queryClient = useQueryClient();

  const [szukaj, setSzukaj] = useState("");
  const [filtrTyp, setFiltrTyp] = useState<string>("all");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [error, setError] = useState("");

  const canWrite = user?.rola && ["proboszcz", "wikariusz", "admin"].includes(user.rola);
  const canAdmin = user?.rola && ["proboszcz", "admin"].includes(user.rola);

  // ── Queries ──────────────────────────────────────────────────────────────────

  const { data: statystyki } = useQuery<StatystykiDziennika>({
    queryKey: ["dziennik-statystyki"],
    queryFn: () => dziennikApi.statystyki(),
    staleTime: 30_000,
  });

  const params: Record<string, unknown> = { rok: ROK };
  if (filtrTyp !== "all") params.typ = filtrTyp;
  if (szukaj.trim()) params.szukaj = szukaj.trim();

  const { data: listPage, isLoading } = useQuery<{
    items: WpisDziennika[];
    total: number;
    page: number;
    pages: number;
  }>({
    queryKey: ["dziennik", params],
    queryFn: () => dziennikApi.list(params),
    staleTime: 15_000,
  });
  const wpisy = listPage?.items ?? [];

  // ── Mutations ─────────────────────────────────────────────────────────────────

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["dziennik"] });
    queryClient.invalidateQueries({ queryKey: ["dziennik-statystyki"] });
  };

  const createMut = useMutation({
    mutationFn: (data: unknown) => dziennikApi.create(data),
    onSuccess: () => { invalidate(); resetForm(); },
    onError: (e: Error) => setError(e.message),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: unknown }) =>
      dziennikApi.update(id, data),
    onSuccess: () => { invalidate(); resetForm(); },
    onError: (e: Error) => setError(e.message),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => dziennikApi.delete(id),
    onSuccess: invalidate,
  });

  // ── Helpers ───────────────────────────────────────────────────────────────────

  function resetForm() {
    setForm(EMPTY_FORM);
    setShowForm(false);
    setEditId(null);
    setError("");
  }

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditId(null);
    setShowForm(true);
    setError("");
  }

  function openEdit(w: WpisDziennika) {
    setForm({
      typ: w.typ,
      data_wpisu: w.data_wpisu,
      data_pisma: w.data_pisma ?? "",
      nadawca: w.nadawca ?? "",
      odbiorca: w.odbiorca ?? "",
      przedmiot: w.przedmiot,
      uwagi: w.uwagi ?? "",
      status: w.status,
    });
    setEditId(w.id);
    setShowForm(true);
    setError("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.przedmiot.trim()) { setError("Podaj przedmiot wpisu"); return; }
    const payload = {
      typ: form.typ,
      data_wpisu: form.data_wpisu,
      data_pisma: form.data_pisma || null,
      nadawca: form.nadawca || null,
      odbiorca: form.odbiorca || null,
      przedmiot: form.przedmiot.trim(),
      uwagi: form.uwagi || null,
      status: form.status,
    };
    if (editId) {
      updateMut.mutate({ id: editId, data: payload });
    } else {
      createMut.mutate(payload);
    }
  }

  function handleExport() {
    dziennikApi.exportCsv(ROK).then((blob: Blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dziennik_${ROK}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  const isSaving = createMut.isPending || updateMut.isPending;

  return (
    <div className="min-h-full">
      {/* ── Nagłówek ── */}
      <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-background px-6 py-6 border-b">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <BookMarked className="h-5 w-5 text-primary" />
              <h1 className="text-xl font-semibold tracking-tight">Dziennik kancleryjny</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Rejestr korespondencji · rok {ROK}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {canAdmin && (
              <Button variant="outline" size="sm" onClick={handleExport} className="gap-1.5">
                <Download className="h-3.5 w-3.5" />
                CSV
              </Button>
            )}
            {canWrite && (
              <Button size="sm" onClick={openCreate} className="gap-1.5">
                <Plus className="h-4 w-4" />
                Nowy wpis
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">

        {/* ── Statystyki ── */}
        {statystyki && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Łącznie", value: statystyki.lacznie, color: "text-foreground" },
              { label: "Przychodzące", value: statystyki.przychodzace, color: "text-blue-600" },
              { label: "Wychodzące", value: statystyki.wychodzace, color: "text-green-600" },
              { label: "Wewnętrzne", value: statystyki.wewnetrzne, color: "text-purple-600" },
            ].map(({ label, value, color }) => (
              <Card key={label} className="text-center">
                <CardContent className="py-4">
                  <p className={`text-2xl font-bold tabular-nums ${color}`}>{value}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* ── Formularz nowego wpisu ── */}
        {showForm && (
          <Card className="border-primary/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span>{editId ? "Edytuj wpis" : "Nowy wpis dziennika"}</span>
                <Button variant="ghost" size="sm" onClick={resetForm} className="h-7 w-7 p-0">
                  <X className="h-4 w-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
                {/* Typ */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Typ *</label>
                  <div className="flex gap-2">
                    {(["przychodzace", "wychodzace", "wewnetrzne"] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, typ: t }))}
                        className={`flex-1 text-xs py-2 px-2 rounded-md border transition-colors ${
                          form.typ === t
                            ? "bg-primary text-primary-foreground border-primary"
                            : "border-border hover:bg-muted"
                        }`}
                      >
                        {TYP_CFG[t].label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Status */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Status</label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="robocze">Robocze</option>
                    <option value="zarejestrowane">Zarejestrowane</option>
                    <option value="wyslane">Wysłane</option>
                    <option value="zarchiwizowane">Zarchiwizowane</option>
                  </select>
                </div>

                {/* Data wpisu */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Data wpisu *</label>
                  <Input
                    type="date"
                    value={form.data_wpisu}
                    onChange={(e) => setForm((f) => ({ ...f, data_wpisu: e.target.value }))}
                    required
                  />
                </div>

                {/* Data pisma */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Data pisma</label>
                  <Input
                    type="date"
                    value={form.data_pisma}
                    onChange={(e) => setForm((f) => ({ ...f, data_pisma: e.target.value }))}
                  />
                </div>

                {/* Nadawca */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    {form.typ === "wychodzace" ? "Nadawca (parafia)" : "Nadawca"}
                  </label>
                  <Input
                    value={form.nadawca}
                    onChange={(e) => setForm((f) => ({ ...f, nadawca: e.target.value }))}
                    placeholder="np. Kuria Metropolitalna"
                    maxLength={200}
                  />
                </div>

                {/* Odbiorca */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Odbiorca</label>
                  <Input
                    value={form.odbiorca}
                    onChange={(e) => setForm((f) => ({ ...f, odbiorca: e.target.value }))}
                    placeholder="np. Urząd Gminy"
                    maxLength={200}
                  />
                </div>

                {/* Przedmiot */}
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Przedmiot / temat *</label>
                  <Input
                    value={form.przedmiot}
                    onChange={(e) => setForm((f) => ({ ...f, przedmiot: e.target.value }))}
                    placeholder="Krótki opis sprawy"
                    maxLength={500}
                    required
                  />
                </div>

                {/* Uwagi */}
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Uwagi / notatki</label>
                  <textarea
                    value={form.uwagi}
                    onChange={(e) => setForm((f) => ({ ...f, uwagi: e.target.value }))}
                    rows={3}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="Dodatkowe informacje, numer pisma itp."
                  />
                </div>

                {error && (
                  <div className="sm:col-span-2 text-xs text-destructive">{error}</div>
                )}

                <div className="sm:col-span-2 flex gap-2 justify-end">
                  <Button type="button" variant="outline" size="sm" onClick={resetForm}>
                    Anuluj
                  </Button>
                  <Button type="submit" size="sm" disabled={isSaving} className="gap-1.5">
                    {isSaving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    {editId ? "Zapisz zmiany" : "Zarejestruj wpis"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* ── Filtrowanie i wyszukiwanie ── */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={szukaj}
              onChange={(e) => setSzukaj(e.target.value)}
              placeholder="Szukaj wpisów..."
              className="pl-9"
            />
          </div>
          <div className="flex gap-1.5">
            {(["all", "przychodzace", "wychodzace", "wewnetrzne"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFiltrTyp(t)}
                className={`px-3 py-1.5 text-xs rounded-md border transition-colors ${
                  filtrTyp === t
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border hover:bg-muted text-muted-foreground"
                }`}
              >
                {t === "all" ? "Wszystkie" : TYP_CFG[t].label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Lista wpisów ── */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : wpisy.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <BookMarked className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                {szukaj || filtrTyp !== "all"
                  ? "Brak wpisów spełniających kryteria wyszukiwania"
                  : "Brak wpisów w dzienniku kancleryjnym"}
              </p>
              {canWrite && !showForm && (
                <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={openCreate}>
                  <Plus className="h-3.5 w-3.5" />
                  Dodaj pierwszy wpis
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="rounded-xl border overflow-hidden">
            {wpisy.map((wpis, idx) => {
              const cfg = TYP_CFG[wpis.typ] ?? TYP_CFG.przychodzace;
              const Icon = cfg.icon;
              const isExpanded = expandedId === wpis.id;

              return (
                <div
                  key={wpis.id}
                  className={`border-b last:border-b-0 ${idx % 2 === 0 ? "bg-background" : "bg-muted/20"}`}
                >
                  {/* Wiersz główny */}
                  <div
                    className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/40 transition-colors"
                    onClick={() => setExpandedId(isExpanded ? null : wpis.id)}
                  >
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${cfg.bg}`}>
                      <Icon className={`h-4 w-4 ${cfg.color}`} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-semibold text-muted-foreground">
                          {wpis.numer_pelny}
                        </span>
                        <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${cfg.badge}`}>
                          {cfg.label}
                        </span>
                        <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${STATUS_COLORS[wpis.status] ?? ""}`}>
                          {STATUS_LABELS[wpis.status] ?? wpis.status}
                        </span>
                      </div>
                      <p className="text-sm font-medium mt-0.5 truncate">{wpis.przedmiot}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {wpis.nadawca && <span>{wpis.nadawca}</span>}
                        {wpis.nadawca && wpis.odbiorca && <span> → </span>}
                        {wpis.odbiorca && <span>{wpis.odbiorca}</span>}
                      </p>
                    </div>

                    <div className="text-xs text-muted-foreground shrink-0 text-right">
                      <p>{formatDate(wpis.data_wpisu)}</p>
                    </div>

                    <ChevronRight
                      className={`h-4 w-4 text-muted-foreground shrink-0 transition-transform ${isExpanded ? "rotate-90" : ""}`}
                    />
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t bg-muted/10">
                      <div className="grid gap-3 sm:grid-cols-2 text-sm mb-4">
                        {wpis.data_pisma && (
                          <div>
                            <span className="text-xs text-muted-foreground block mb-0.5">Data pisma</span>
                            {formatDate(wpis.data_pisma)}
                          </div>
                        )}
                        {wpis.nadawca && (
                          <div>
                            <span className="text-xs text-muted-foreground block mb-0.5">Nadawca</span>
                            {wpis.nadawca}
                          </div>
                        )}
                        {wpis.odbiorca && (
                          <div>
                            <span className="text-xs text-muted-foreground block mb-0.5">Odbiorca</span>
                            {wpis.odbiorca}
                          </div>
                        )}
                        {wpis.uwagi && (
                          <div className="sm:col-span-2">
                            <span className="text-xs text-muted-foreground block mb-0.5">Uwagi</span>
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{wpis.uwagi}</p>
                          </div>
                        )}
                      </div>
                      {canAdmin && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => openEdit(wpis)}
                          >
                            Edytuj
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs text-destructive hover:bg-destructive/10"
                            onClick={() => {
                              if (confirm("Usunąć ten wpis?")) deleteMut.mutate(wpis.id);
                            }}
                          >
                            <Trash2 className="h-3 w-3 mr-1" />
                            Usuń
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Info o numeracji ── */}
        {statystyki && statystyki.lacznie > 0 && (
          <p className="text-xs text-muted-foreground text-center">
            Ostatni numer: <strong>L.dz. {statystyki.ostatni_numer}/{ROK}</strong>
            {" · "}
            Łącznie wpisów w {ROK} roku: <strong>{statystyki.lacznie}</strong>
            {listPage && listPage.pages > 1 && (
              <span> · Strona <strong>{listPage.page}</strong> z <strong>{listPage.pages}</strong></span>
            )}
          </p>
        )}
      </div>
    </div>
  );
}
