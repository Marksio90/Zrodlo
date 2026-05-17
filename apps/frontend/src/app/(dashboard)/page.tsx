"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, FileText, Heart, Users } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { intencjeApi, dokumentyApi, wspolnotyApi, kalendarzeApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { ETYKIETY_INTENCJI } from "@/types";

export default function DashboardPage() {
  const today = new Date().toISOString().split("T")[0];
  const nextWeek = new Date(Date.now() + 7 * 86400_000).toISOString();

  const { data: intencje = [] } = useQuery({
    queryKey: ["intencje", { limit: 5 }],
    queryFn: () => intencjeApi.list({ limit: 5 }),
  });

  const { data: dokumenty = [] } = useQuery({
    queryKey: ["dokumenty", { limit: 5 }],
    queryFn: () => dokumentyApi.list({ limit: 5 }),
  });

  const { data: wspolnoty = [] } = useQuery({
    queryKey: ["wspolnoty"],
    queryFn: () => wspolnotyApi.list({ aktywna: true }),
  });

  const { data: wydarzenia = [] } = useQuery({
    queryKey: ["kalendarz", { od: today, do: nextWeek }],
    queryFn: () => kalendarzeApi.list({ od: today, do: nextWeek, limit: 5 }),
  });

  const stats = [
    {
      label: "Intencje",
      value: intencje.length,
      icon: Heart,
      desc: "Ostatnie wpisy",
      color: "text-rose-500",
    },
    {
      label: "Dokumenty",
      value: dokumenty.length,
      icon: FileText,
      desc: "Ostatnie dokumenty",
      color: "text-blue-500",
    },
    {
      label: "Wspólnoty",
      value: wspolnoty.length,
      icon: Users,
      desc: "Aktywne wspólnoty",
      color: "text-green-500",
    },
    {
      label: "Najbliższe wydarzenia",
      value: wydarzenia.length,
      icon: CalendarDays,
      desc: "Nadchodzące 7 dni",
      color: "text-purple-500",
    },
  ];

  return (
    <div>
      <Header title="Pulpit" description="Przegląd bieżącej działalności parafii" />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon, desc, color }) => (
            <Card key={label}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>{label}</CardDescription>
                  <Icon className={`h-4 w-4 ${color}`} />
                </div>
                <CardTitle className="text-3xl">{value}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ostatnie intencje</CardTitle>
            </CardHeader>
            <CardContent>
              {intencje.length === 0 ? (
                <p className="text-sm text-muted-foreground">Brak intencji</p>
              ) : (
                <ul className="space-y-3">
                  {intencje.slice(0, 5).map((i: { id: string; typ: keyof typeof ETYKIETY_INTENCJI; tresc: string; created_at: string }) => (
                    <li key={i.id} className="flex gap-3 text-sm">
                      <div className="mt-0.5 h-2 w-2 rounded-full bg-rose-400 shrink-0" />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{i.tresc}</p>
                        <p className="text-xs text-muted-foreground">
                          {ETYKIETY_INTENCJI[i.typ]} · {formatDateTime(i.created_at)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Najbliższe wydarzenia</CardTitle>
            </CardHeader>
            <CardContent>
              {wydarzenia.length === 0 ? (
                <p className="text-sm text-muted-foreground">Brak wydarzeń w nadchodzących 7 dniach</p>
              ) : (
                <ul className="space-y-3">
                  {wydarzenia.slice(0, 5).map((w: { id: string; kolor: string; tytul: string; data_od: string; miejsce: string | null }) => (
                    <li key={w.id} className="flex gap-3 text-sm">
                      <div
                        className="mt-0.5 h-2 w-2 rounded-full shrink-0"
                        style={{ backgroundColor: w.kolor }}
                      />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{w.tytul}</p>
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
        </div>
      </div>
    </div>
  );
}
