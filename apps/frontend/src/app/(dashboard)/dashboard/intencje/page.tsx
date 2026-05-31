"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Printer, Trash2 } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { intencjeApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { ETYKIETY_INTENCJI, type Intencja, type TypIntencji } from "@/types";

const TYPY: TypIntencji[] = [
  "za_zmarlego",
  "za_zyjacego",
  "dziekczynna",
  "rocznica_slubu",
  "w_chorobie",
  "wypominkowa",
  "inna",
];

export default function IntencjePage() {
  const qc = useQueryClient();
  const [tresc, setTresc] = useState("");
  const [typ, setTyp] = useState<TypIntencji>("inna");
  const [ofiarodawca, setOfiarodawca] = useState("");

  const { data: intencje = [], isLoading } = useQuery<Intencja[]>({
    queryKey: ["intencje"],
    queryFn: () => intencjeApi.list({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: () => intencjeApi.create({ tresc, typ, ofiarodawca: ofiarodawca || null }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["intencje"] });
      setTresc("");
      setOfiarodawca("");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (id: string) => intencjeApi.potwierdz(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["intencje"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => intencjeApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["intencje"] }),
  });

  return (
    <div>
      <Header title="Intencje mszalne" description="Zarządzanie intencjami liturgicznymi">
        <Button variant="outline" size="sm" className="gap-2 print:hidden" onClick={() => window.print()}>
          <Printer className="h-4 w-4" />
          Drukuj
        </Button>
      </Header>

      <div className="p-6 space-y-6">
        <Card className="print:hidden">
          <CardContent className="pt-6">
            <h3 className="font-medium mb-4">Nowa intencja</h3>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Typ intencji</label>
                  <select
                    value={typ}
                    onChange={(e) => setTyp(e.target.value as TypIntencji)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {TYPY.map((t) => (
                      <option key={t} value={t}>
                        {ETYKIETY_INTENCJI[t]}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1 block">Ofiarodawca</label>
                  <Input
                    placeholder="Imię i nazwisko (opcjonalnie)"
                    value={ofiarodawca}
                    onChange={(e) => setOfiarodawca(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Treść intencji</label>
                <Input
                  placeholder="Wpisz treść intencji..."
                  value={tresc}
                  onChange={(e) => setTresc(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && tresc.trim().length >= 3) {
                      createMutation.mutate();
                    }
                  }}
                />
              </div>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={tresc.trim().length < 3 || createMutation.isPending}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                {createMutation.isPending ? "Zapisuję..." : "Dodaj intencję"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">Ładowanie...</p>
        ) : intencje.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Brak intencji. Dodaj pierwszą intencję powyżej.
          </p>
        ) : (
          <div className="print-area">
            <div className="print-header hidden print:block">
              <h1>Intencje mszalne</h1>
              <p>Wydrukowano: {new Date().toLocaleDateString("pl-PL")}</p>
            </div>

            <div className="space-y-2 print:hidden">
              {intencje.map((i) => (
                <Card key={i.id}>
                  <CardContent className="py-4 flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={i.potwierdzona ? "success" : "secondary"}>
                          {i.potwierdzona ? "Potwierdzona" : "Oczekuje"}
                        </Badge>
                        <Badge variant="outline">{ETYKIETY_INTENCJI[i.typ]}</Badge>
                      </div>
                      <p className="text-sm font-medium truncate">{i.tresc}</p>
                      {i.ofiarodawca && (
                        <p className="text-xs text-muted-foreground">{i.ofiarodawca}</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatDate(i.created_at)}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      {!i.potwierdzona && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => confirmMutation.mutate(i.id)}
                          disabled={confirmMutation.isPending}
                        >
                          Potwierdź
                        </Button>
                      )}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        onClick={() => deleteMutation.mutate(i.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <table className="hidden print:table w-full">
              <thead>
                <tr>
                  <th>Typ</th>
                  <th>Treść</th>
                  <th>Ofiarodawca</th>
                  <th>Status</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {intencje.map((i) => (
                  <tr key={i.id}>
                    <td>{ETYKIETY_INTENCJI[i.typ]}</td>
                    <td>{i.tresc}</td>
                    <td>{i.ofiarodawca ?? "—"}</td>
                    <td>{i.potwierdzona ? "Potwierdzona" : "Oczekuje"}</td>
                    <td>{formatDate(i.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
