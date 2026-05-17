"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, Plus, Trash2 } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { kalendarzeApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { type Wydarzenie } from "@/types";

export default function KalendarzPage() {
  const qc = useQueryClient();
  const [tytul, setTytul] = useState("");
  const [dataOd, setDataOd] = useState("");
  const [miejsce, setMiejsce] = useState("");
  const [kolor, setKolor] = useState("#3B82F6");

  const { data: wydarzenia = [], isLoading } = useQuery<Wydarzenie[]>({
    queryKey: ["kalendarz"],
    queryFn: () => kalendarzeApi.list({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      kalendarzeApi.create({
        tytul,
        data_od: new Date(dataOd).toISOString(),
        miejsce: miejsce || null,
        kolor,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kalendarz"] });
      setTytul("");
      setDataOd("");
      setMiejsce("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => kalendarzeApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kalendarz"] }),
  });

  const nadchodzace = wydarzenia.filter(
    (w) => new Date(w.data_od) >= new Date()
  );
  const minione = wydarzenia.filter((w) => new Date(w.data_od) < new Date());

  return (
    <div>
      <Header title="Kalendarz parafialny" description="Planowanie wydarzeń i uroczystości" />

      <div className="p-6 space-y-6">
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-medium mb-4">Nowe wydarzenie</h3>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <Input
                placeholder="Tytuł wydarzenia"
                value={tytul}
                onChange={(e) => setTytul(e.target.value)}
              />
              <Input
                type="datetime-local"
                value={dataOd}
                onChange={(e) => setDataOd(e.target.value)}
              />
              <Input
                placeholder="Miejsce (opcjonalnie)"
                value={miejsce}
                onChange={(e) => setMiejsce(e.target.value)}
              />
              <div className="flex items-center gap-3">
                <label className="text-sm text-muted-foreground whitespace-nowrap">Kolor:</label>
                <input
                  type="color"
                  value={kolor}
                  onChange={(e) => setKolor(e.target.value)}
                  className="h-10 w-20 rounded border cursor-pointer"
                />
              </div>
            </div>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={tytul.trim().length < 2 || !dataOd || createMutation.isPending}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              {createMutation.isPending ? "Zapisuję..." : "Dodaj wydarzenie"}
            </Button>
          </CardContent>
        </Card>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">Ładowanie...</p>
        ) : (
          <div className="space-y-6">
            <section>
              <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                Nadchodzące ({nadchodzace.length})
              </h2>
              {nadchodzace.length === 0 ? (
                <p className="text-sm text-muted-foreground">Brak nadchodzących wydarzeń.</p>
              ) : (
                <div className="space-y-2">
                  {nadchodzace.map((w) => (
                    <WydarzenieRow key={w.id} w={w} onDelete={() => deleteMutation.mutate(w.id)} />
                  ))}
                </div>
              )}
            </section>

            {minione.length > 0 && (
              <section>
                <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                  Minione ({minione.length})
                </h2>
                <div className="space-y-2 opacity-60">
                  {minione.slice(0, 10).map((w) => (
                    <WydarzenieRow key={w.id} w={w} onDelete={() => deleteMutation.mutate(w.id)} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function WydarzenieRow({ w, onDelete }: { w: Wydarzenie; onDelete: () => void }) {
  return (
    <Card>
      <CardContent className="py-3 flex items-center gap-4">
        <div
          className="h-10 w-1 rounded-full shrink-0"
          style={{ backgroundColor: w.kolor }}
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">{w.tytul}</p>
          <p className="text-xs text-muted-foreground">
            <CalendarDays className="h-3 w-3 inline mr-1" />
            {formatDateTime(w.data_od)}
            {w.miejsce && ` · ${w.miejsce}`}
          </p>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="text-destructive hover:text-destructive shrink-0"
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
