"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus, Trash2 } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { dokumentyApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  ETYKIETY_DOKUMENTOW,
  ETYKIETY_STATUSOW,
  type Dokument,
  type TypDokumentu,
  type StatusDokumentu,
} from "@/types";

const STATUS_COLORS: Record<
  StatusDokumentu,
  "default" | "secondary" | "success" | "warning" | "destructive" | "outline"
> = {
  szkic: "secondary",
  do_zatwierdzenia: "warning",
  zatwierdzony: "success",
  wydany: "default",
  anulowany: "destructive",
};

const TYPY_DOCS: TypDokumentu[] = [
  "metryka_chrztu",
  "metryka_slubu",
  "zaswiadczenie_bierzmowania",
  "zaswiadczenie_komunii",
  "zaswiadczenie_do_slubu",
  "odpis_zgonu",
  "pismo_ogolne",
  "ogloszenia",
];

export default function DokumentyPage() {
  const qc = useQueryClient();
  const [tytul, setTytul] = useState("");
  const [typ, setTyp] = useState<TypDokumentu>("pismo_ogolne");
  const [filterTyp, setFilterTyp] = useState<string>("");

  const { data: dokumenty = [], isLoading } = useQuery<Dokument[]>({
    queryKey: ["dokumenty", filterTyp],
    queryFn: () =>
      dokumentyApi.list(filterTyp ? { typ: filterTyp, limit: 100 } : { limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: () => dokumentyApi.create({ typ, tytul, dane: {} }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dokumenty"] });
      setTytul("");
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => dokumentyApi.zatwierdz(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dokumenty"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => dokumentyApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dokumenty"] }),
  });

  return (
    <div>
      <Header title="Dokumenty" description="Metryki, zaświadczenia i pisma parafialne" />

      <div className="p-6 space-y-6">
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-medium mb-4">Nowy dokument</h3>
            <div className="flex gap-3">
              <select
                value={typ}
                onChange={(e) => setTyp(e.target.value as TypDokumentu)}
                className="flex h-10 w-56 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {TYPY_DOCS.map((t) => (
                  <option key={t} value={t}>
                    {ETYKIETY_DOKUMENTOW[t]}
                  </option>
                ))}
              </select>
              <Input
                className="flex-1"
                placeholder="Tytuł dokumentu"
                value={tytul}
                onChange={(e) => setTytul(e.target.value)}
              />
              <Button
                onClick={() => createMutation.mutate()}
                disabled={tytul.trim().length < 3 || createMutation.isPending}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                {createMutation.isPending ? "Tworzę..." : "Utwórz"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-2 flex-wrap">
          <Button
            variant={filterTyp === "" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterTyp("")}
          >
            Wszystkie
          </Button>
          {TYPY_DOCS.map((t) => (
            <Button
              key={t}
              variant={filterTyp === t ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterTyp(t)}
            >
              {ETYKIETY_DOKUMENTOW[t]}
            </Button>
          ))}
        </div>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">Ładowanie...</p>
        ) : dokumenty.length === 0 ? (
          <p className="text-muted-foreground text-sm">Brak dokumentów.</p>
        ) : (
          <div className="space-y-2">
            {dokumenty.map((d) => (
              <Card key={d.id}>
                <CardContent className="py-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={STATUS_COLORS[d.status]}>
                          {ETYKIETY_STATUSOW[d.status]}
                        </Badge>
                        <Badge variant="outline">{ETYKIETY_DOKUMENTOW[d.typ]}</Badge>
                        {d.wygenerowane_przez_ai && (
                          <Badge variant="secondary">AI</Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium truncate">{d.tytul}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(d.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {d.status === "do_zatwierdzenia" && (
                      <Button
                        size="sm"
                        onClick={() => approveMutation.mutate(d.id)}
                        disabled={approveMutation.isPending}
                      >
                        Zatwierdź
                      </Button>
                    )}
                    <Button
                      size="icon"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => deleteMutation.mutate(d.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
