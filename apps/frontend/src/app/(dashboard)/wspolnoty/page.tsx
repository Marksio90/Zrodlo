"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Users } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { wspolnotyApi } from "@/lib/api";
import { type Wspolnota } from "@/types";

export default function WspolnotyPage() {
  const qc = useQueryClient();
  const [nazwa, setNazwa] = useState("");
  const [opiekun, setOpiekun] = useState("");

  const { data: wspolnoty = [], isLoading } = useQuery<Wspolnota[]>({
    queryKey: ["wspolnoty"],
    queryFn: () => wspolnotyApi.list({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      wspolnotyApi.create({ nazwa, opiekun: opiekun || null }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wspolnoty"] });
      setNazwa("");
      setOpiekun("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => wspolnotyApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wspolnoty"] }),
  });

  return (
    <div>
      <Header title="Wspólnoty parafialne" description="Grupy i wspólnoty działające w parafii" />

      <div className="p-6 space-y-6">
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-medium mb-4">Nowa wspólnota</h3>
            <div className="flex gap-3">
              <Input
                placeholder="Nazwa wspólnoty"
                value={nazwa}
                className="flex-1"
                onChange={(e) => setNazwa(e.target.value)}
              />
              <Input
                placeholder="Opiekun (opcjonalnie)"
                value={opiekun}
                className="w-56"
                onChange={(e) => setOpiekun(e.target.value)}
              />
              <Button
                onClick={() => createMutation.mutate()}
                disabled={nazwa.trim().length < 2 || createMutation.isPending}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                {createMutation.isPending ? "Tworzę..." : "Utwórz"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">Ładowanie...</p>
        ) : wspolnoty.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Brak wspólnot. Utwórz pierwszą powyżej.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {wspolnoty.map((w) => (
              <Card key={w.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{w.nazwa}</CardTitle>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => deleteMutation.mutate(w.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span>{w.liczba_czlonkow} członków</span>
                  </div>
                  {w.opiekun && (
                    <p className="text-sm mt-1">
                      <span className="text-muted-foreground">Opiekun: </span>
                      {w.opiekun}
                    </p>
                  )}
                  {!w.aktywna && (
                    <Badge variant="secondary" className="mt-2">Nieaktywna</Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
