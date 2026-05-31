"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, XCircle, Zap } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { aiKosztyApi } from "@/lib/api";

interface AlertAi {
  poziom: "ok" | "ostrzezenie" | "krytyczny";
  procent_limitu: number | null;
  zapytania_w_miesiacu: number;
  limit_zapytan: number | null;
  wiadomosc: string;
}

const POZIOM_CFG = {
  ok:          { icon: CheckCircle2, color: "text-green-500",  bg: "bg-green-50",  bar: "bg-green-400",  label: "W normie" },
  ostrzezenie: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-50",  bar: "bg-amber-400",  label: "Ostrzeżenie" },
  krytyczny:   { icon: XCircle,       color: "text-red-500",   bg: "bg-red-50",    bar: "bg-red-500",    label: "Krytyczny" },
};

export function AiKosztWidget() {
  const { data, isLoading, isError } = useQuery<AlertAi>({
    queryKey: ["ai-alerty"],
    queryFn: () => aiKosztyApi.alerty(),
    staleTime: 60_000,
    retry: false,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-500" />
            Limit AI
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2.5 w-full rounded-full" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !data) return null;

  const cfg = POZIOM_CFG[data.poziom] ?? POZIOM_CFG.ok;
  const Icon = cfg.icon;
  const procent = data.procent_limitu ?? 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-500" />
            Limit AI – bieżący miesiąc
          </span>
          <span className={`flex items-center gap-1 text-xs font-medium ${cfg.color}`}>
            <Icon className="h-3.5 w-3.5" />
            {cfg.label}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.limit_zapytan ? (
          <>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {data.zapytania_w_miesiacu} / {data.limit_zapytan} zapytań
              </span>
              <span className={`font-semibold tabular-nums ${cfg.color}`}>
                {procent.toFixed(1)}%
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${cfg.bar}`}
                style={{ width: `${Math.min(procent, 100)}%` }}
              />
            </div>
          </>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
            <span>
              {data.zapytania_w_miesiacu} zapytań · plan bez limitu
            </span>
          </div>
        )}

        <p className="text-xs text-muted-foreground leading-relaxed">
          {data.wiadomosc}
        </p>

        <Link
          href="/dashboard/ai"
          className="text-xs text-primary hover:underline inline-flex items-center gap-1"
        >
          Przejdź do asystenta →
        </Link>
      </CardContent>
    </Card>
  );
}
