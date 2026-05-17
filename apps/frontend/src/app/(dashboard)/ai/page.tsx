"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Plus, Sparkles, X } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { aiApi } from "@/lib/api";

export default function AIPage() {
  const [niedziela, setNiedziela] = useState("");
  const [czytania, setCzytania] = useState<string[]>([""]);
  const [wskazowki, setWskazowki] = useState("");
  const [wynik, setWynik] = useState<{ sugestia: string; zastrzezenie: string } | null>(null);

  const { data: modele } = useQuery({
    queryKey: ["ai-modele"],
    queryFn: aiApi.modele,
    retry: false,
  });

  const homiliaMutation = useMutation({
    mutationFn: () =>
      aiApi.homilia({
        niedziela,
        czytania: czytania.filter((c) => c.trim().length > 0),
        wskazowki: wskazowki || null,
      }),
    onSuccess: (data) => setWynik(data),
  });

  const addCzytanie = () => setCzytania((prev) => [...prev, ""]);
  const removeCzytanie = (i: number) =>
    setCzytania((prev) => prev.filter((_, idx) => idx !== i));
  const updateCzytanie = (i: number, val: string) =>
    setCzytania((prev) => prev.map((c, idx) => (idx === i ? val : c)));

  const canSubmit =
    niedziela.trim().length > 0 && czytania.some((c) => c.trim().length > 0);

  return (
    <div>
      <Header
        title="Wsparcie AI"
        description="Narzędzia duszpasterskie wspomagane przez sztuczną inteligencję"
      />

      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <AlertTriangle className="h-5 w-5 text-yellow-600 shrink-0" />
          <div>
            <p className="text-sm font-medium text-yellow-800">Ważne zastrzeżenie</p>
            <p className="text-sm text-yellow-700">
              AI proponuje, kapłan decyduje. Wszystkie treści wymagają weryfikacji przed użyciem.
              AI nie zastępuje discernmentu duszpasterskiego.
            </p>
          </div>
        </div>

        {modele && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            <span>Model: </span>
            <Badge variant="secondary">{modele.aktywny_model}</Badge>
            <span className={modele.dostepna ? "text-green-600" : "text-red-500"}>
              {modele.dostepna ? "● Dostępny" : "● Niedostępny"}
            </span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Przygotowanie homilii</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Niedziela / Uroczystość
              </label>
              <Input
                placeholder="np. 15. Niedziela Zwykła, rok B"
                value={niedziela}
                onChange={(e) => setNiedziela(e.target.value)}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-muted-foreground">Czytania liturgiczne</label>
                <Button size="sm" variant="outline" onClick={addCzytanie} className="gap-1 h-7">
                  <Plus className="h-3 w-3" /> Dodaj czytanie
                </Button>
              </div>
              <div className="space-y-2">
                {czytania.map((c, i) => (
                  <div key={i} className="flex gap-2">
                    <textarea
                      className="flex-1 min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      placeholder={`Czytanie ${i + 1}...`}
                      value={c}
                      onChange={(e) => updateCzytanie(i, e.target.value)}
                    />
                    {czytania.length > 1 && (
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 mt-1"
                        onClick={() => removeCzytanie(i)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Wskazówki kapłana (opcjonalnie)
              </label>
              <textarea
                className="w-full min-h-[60px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Dodatkowe myśli, akcenty, grupy odbiorców..."
                value={wskazowki}
                onChange={(e) => setWskazowki(e.target.value)}
              />
            </div>

            <Button
              onClick={() => homiliaMutation.mutate()}
              disabled={!canSubmit || homiliaMutation.isPending || modele?.dostepna === false}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" />
              {homiliaMutation.isPending ? "Generuję propozycję..." : "Generuj propozycję"}
            </Button>

            {homiliaMutation.isError && (
              <p className="text-sm text-destructive">
                {homiliaMutation.error?.message ?? "Błąd połączenia z Ollama"}
              </p>
            )}
          </CardContent>
        </Card>

        {wynik && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Propozycja AI</CardTitle>
                <Button size="sm" variant="ghost" onClick={() => setWynik(null)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md bg-muted p-4">
                <pre className="text-sm whitespace-pre-wrap font-sans leading-relaxed">
                  {wynik.sugestia}
                </pre>
              </div>
              <div className="flex items-start gap-2 rounded border border-yellow-200 bg-yellow-50 p-3">
                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 shrink-0" />
                <p className="text-xs text-yellow-700">{wynik.zastrzezenie}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
