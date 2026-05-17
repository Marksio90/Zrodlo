"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { pl } from "date-fns/locale";
import Link from "next/link";
import {
  Bell,
  CalendarDays,
  ChevronRight,
  Clock,
  FileText,
  Heart,
  MessageSquarePlus,
  Sparkles,
  Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  intencjeApi,
  liturgieApi,
  dokumentyApi,
  kalendarzeApi,
  powiadomieniaApi,
  wspolnotyApi,
} from "@/lib/api";
import { getUser } from "@/lib/auth";
import { formatTime, formatDateTime } from "@/lib/utils";
import type { Wspolnota } from "@/types";
import {
  ETYKIETY_INTENCJI,
  ETYKIETY_TYPY_MSZY,
} from "@/types";
import type { Liturgia, Intencja, Wydarzenie, Dokument, Powiadomienie } from "@/types";

function getPozdrowienie(h: number) {
  if (h >= 5 && h < 12) return "Dzień dobry";
  if (h >= 12 && h < 18) return "Dzień dobry";
  if (h >= 18 && h < 22) return "Dobry wieczór";
  return "Dobranoc";
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  proboszcz: "Proboszcz",
  wikariusz: "Wikariusz",
  parafianin: "Parafianin",
};

export default function CentrumZrodlaPage() {
  const user = getUser();
  const now = new Date();
  const today = format(now, "yyyy-MM-dd");
  const todayPlus7 = format(new Date(now.getTime() + 7 * 86_400_000), "yyyy-MM-dd");
  const dataPoPolsku = format(now, "EEEE, d MMMM yyyy", { locale: pl });

  const { data: liturgieDzisiaj = [], isLoading: loadingL } = useQuery<Liturgia[]>({
    queryKey: ["liturgie", { od: today, do: today }],
    queryFn: () => liturgieApi.list({ od: today, do: today, limit: 20 }),
    staleTime: 30_000,
  });

  const { data: intencje = [], isLoading: loadingI } = useQuery<Intencja[]>({
    queryKey: ["intencje", { limit: 5 }],
    queryFn: () => intencjeApi.list({ limit: 5 }),
    staleTime: 30_000,
  });

  const { data: wydarzenia = [], isLoading: loadingW } = useQuery<Wydarzenie[]>({
    queryKey: ["kalendarz", { od: today, do: todayPlus7 }],
    queryFn: () => kalendarzeApi.list({ od: today, do: todayPlus7, limit: 10 }),
    staleTime: 30_000,
  });

  const { data: dokumentyOczekujace = [], isLoading: loadingD } = useQuery<Dokument[]>({
    queryKey: ["dokumenty", { status: "do_zatwierdzenia" }],
    queryFn: () => dokumentyApi.list({ status: "do_zatwierdzenia", limit: 50 }),
    staleTime: 30_000,
  });

  const { data: powiadomienia = [], isLoading: loadingP } = useQuery<Powiadomienie[]>({
    queryKey: ["powiadomienia", { przeczytane: false }],
    queryFn: () => powiadomieniaApi.list({ przeczytane: false, limit: 5 }),
    staleTime: 30_000,
  });

  const { data: wspolnoty = [] } = useQuery<Wspolnota[]>({
    queryKey: ["wspolnoty"],
    queryFn: () => wspolnotyApi.list({ limit: 100 }),
    staleTime: 60_000,
  });

  const { data: wszystkieIntencje = [] } = useQuery<Intencja[]>({
    queryKey: ["intencje-stats"],
    queryFn: () => intencjeApi.list({ limit: 200 }),
    staleTime: 60_000,
  });

  const { data: wszystkieDokumenty = [] } = useQuery<Dokument[]>({
    queryKey: ["dokumenty-stats"],
    queryFn: () => dokumentyApi.list({ limit: 200 }),
    staleTime: 60_000,
  });

  const stats = [
    {
      label: "Intencje mszalne",
      value: wszystkieIntencje.length,
      icon: Heart,
      desc: "Łącznie w systemie",
      color: "text-rose-500",
      bg: "bg-rose-50",
      href: "/dashboard/intencje",
    },
    {
      label: "Dokumenty",
      value: wszystkieDokumenty.length,
      icon: FileText,
      desc: `${dokumentyOczekujace.length} oczekujących`,
      color: "text-blue-500",
      bg: "bg-blue-50",
      href: "/dashboard/dokumenty",
    },
    {
      label: "Wspólnoty",
      value: wspolnoty.length,
      icon: Users,
      desc: "Aktywne grupy",
      color: "text-green-500",
      bg: "bg-green-50",
      href: "/dashboard/wspolnoty",
    },
    {
      label: "Nadchodzące",
      value: wydarzenia.length,
      icon: CalendarDays,
      desc: "Najbliższe 7 dni",
      color: "text-purple-500",
      bg: "bg-purple-50",
      href: "/dashboard/kalendarz",
    },
  ];

  const szybkieAkcje = [
    {
      label: "Dodaj intencję",
      desc: "Nowa intencja mszalna",
      icon: Heart,
      href: "/dashboard/intencje",
      color: "text-rose-500",
      bg: "bg-rose-50",
    },
    {
      label: "Dodaj wydarzenie",
      desc: "Zaplanuj spotkanie lub uroczystość",
      icon: CalendarDays,
      href: "/dashboard/kalendarz",
      color: "text-purple-500",
      bg: "bg-purple-50",
    },
    {
      label: "Utwórz ogłoszenie",
      desc: "Nowy dokument lub pismo",
      icon: MessageSquarePlus,
      href: "/dashboard/dokumenty",
      color: "text-blue-500",
      bg: "bg-blue-50",
    },
    {
      label: "Otwórz asystenta",
      desc: "Wsparcie AI dla duszpasterza",
      icon: Sparkles,
      href: "/dashboard/ai",
      color: "text-amber-500",
      bg: "bg-amber-50",
    },
  ];

  return (
    <div className="min-h-full">
      {/* Greeting banner */}
      <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-background px-6 py-8 border-b">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground capitalize mb-0.5">{dataPoPolsku}</p>
            <h1 className="text-2xl font-semibold tracking-tight">
              {getPozdrowienie(now.getHours())}
              {user?.imie ? `, ${user.imie}` : ""}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Centrum Źródła — przegląd dnia w parafii
            </p>
          </div>
          {user?.rola && (
            <Badge variant="outline" className="shrink-0">
              {ROLE_LABELS[user.rola] ?? user.rola}
            </Badge>
          )}
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* ── DZISIAJ ── */}
        <section>
          <h2 className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">
            <Clock className="h-3.5 w-3.5" />
            Dzisiaj
          </h2>

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Msze */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-primary" />
                    Msze święte
                  </span>
                  <Badge variant="secondary">{liturgieDzisiaj.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingL ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-9 w-full" />
                    ))}
                  </div>
                ) : liturgieDzisiaj.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">
                    Brak zaplanowanych mszy na dziś
                  </p>
                ) : (
                  <ul className="divide-y">
                    {liturgieDzisiaj.map((l) => (
                      <li key={l.id} className="flex items-center gap-3 py-2 first:pt-0 last:pb-0">
                        <span className="text-sm font-mono font-semibold text-primary w-12 shrink-0">
                          {formatTime(l.godzina)}
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">
                            {ETYKIETY_TYPY_MSZY[l.typ] ?? l.typ}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">{l.miejsce}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Nadchodzące wydarzenia */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <CalendarDays className="h-4 w-4 text-purple-500" />
                    Nadchodzące wydarzenia
                  </span>
                  <Link href="/dashboard/kalendarz">
                    <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs px-2">
                      Wszystkie <ChevronRight className="h-3 w-3" />
                    </Button>
                  </Link>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingW ? (
                  <div className="space-y-2">
                    {[1, 2].map((i) => (
                      <Skeleton key={i} className="h-10 w-full" />
                    ))}
                  </div>
                ) : wydarzenia.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">
                    Brak wydarzeń w najbliższych 7 dniach
                  </p>
                ) : (
                  <ul className="divide-y">
                    {wydarzenia.slice(0, 5).map((w) => (
                      <li key={w.id} className="flex items-start gap-3 py-2 first:pt-0 last:pb-0">
                        <div
                          className="mt-1.5 h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: w.kolor }}
                        />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{w.tytul}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDateTime(w.data_od)}
                            {w.miejsce && ` · ${w.miejsce}`}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Intencje */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Heart className="h-4 w-4 text-rose-500" />
                    Intencje mszalne
                  </span>
                  <Link href="/dashboard/intencje">
                    <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs px-2">
                      Wszystkie <ChevronRight className="h-3 w-3" />
                    </Button>
                  </Link>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingI ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-10 w-full" />
                    ))}
                  </div>
                ) : intencje.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">Brak intencji</p>
                ) : (
                  <ul className="divide-y">
                    {intencje.map((i) => (
                      <li key={i.id} className="flex items-start gap-2 py-2 first:pt-0 last:pb-0">
                        <div
                          className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${
                            i.potwierdzona ? "bg-green-400" : "bg-rose-400"
                          }`}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm truncate">{i.tresc}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-muted-foreground">
                              {ETYKIETY_INTENCJI[i.typ]}
                            </span>
                            {!i.potwierdzona && (
                              <Badge variant="secondary" className="text-xs h-4 px-1">
                                Oczekuje
                              </Badge>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Dokumenty oczekujące + Powiadomienia */}
            <div className="space-y-4">
              <Card>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50">
                        <FileText className="h-5 w-5 text-amber-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Dokumenty oczekujące</p>
                        <p className="text-xs text-muted-foreground">Do zatwierdzenia</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold tabular-nums">
                        {loadingD ? (
                          <Skeleton className="h-7 w-8 inline-block" />
                        ) : (
                          dokumentyOczekujace.length
                        )}
                      </span>
                      <Link href="/dashboard/dokumenty">
                        <Button variant="outline" size="sm" className="h-8">
                          Przejdź
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                        <Bell className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Powiadomienia</p>
                        <p className="text-xs text-muted-foreground">Nieprzeczytane</p>
                      </div>
                    </div>
                    <span className="text-2xl font-bold tabular-nums">
                      {loadingP ? (
                        <Skeleton className="h-7 w-8 inline-block" />
                      ) : (
                        powiadomienia.length
                      )}
                    </span>
                  </div>
                  {powiadomienia.slice(0, 3).map((p) => (
                    <div key={p.id} className="mt-3 pt-3 border-t">
                      <p className="text-sm font-medium truncate">{p.tytul}</p>
                      <p className="text-xs text-muted-foreground truncate">{p.tresc}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* ── STATYSTYKI ── */}
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">
            Statystyki
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {stats.map(({ label, value, icon: Icon, desc, color, bg, href }) => (
              <Link key={label} href={href}>
                <Card className="hover:shadow-md transition-all hover:-translate-y-0.5 cursor-pointer">
                  <CardHeader className="pb-2">
                    <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${bg} mb-1`}>
                      <Icon className={`h-4 w-4 ${color}`} />
                    </div>
                    <p className="text-2xl font-bold tabular-nums">{value}</p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium leading-snug">{label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        {/* ── SZYBKIE AKCJE ── */}
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">
            Szybkie akcje
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {szybkieAkcje.map(({ label, desc, icon: Icon, href, color, bg }) => (
              <Link key={label} href={href}>
                <Card className="cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5">
                  <CardContent className="pt-5 pb-5">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl ${bg} mb-3`}
                    >
                      <Icon className={`h-5 w-5 ${color}`} />
                    </div>
                    <p className="text-sm font-semibold">{label}</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{desc}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        <div className="pt-4 border-t">
          <p className="text-center text-xs text-muted-foreground">
            AI wspiera człowieka – nie zastępuje kapłana
          </p>
        </div>
      </div>
    </div>
  );
}
