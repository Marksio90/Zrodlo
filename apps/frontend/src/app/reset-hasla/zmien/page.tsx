"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";

function ZmienHasloForm() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token") ?? "";

  const [haslo, setHaslo] = useState("");
  const [haslo2, setHaslo2] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (haslo !== haslo2) {
      setError("Hasła nie są identyczne");
      return;
    }
    if (haslo.length < 8) {
      setError("Hasło musi mieć co najmniej 8 znaków");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await apiClient.post("/auth/reset-hasla/zmien", { token, nowe_haslo: haslo });
      setDone(true);
      setTimeout(() => router.replace("/login"), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Token wygasł lub jest nieprawidłowy");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-destructive text-center">
        Brak tokenu resetującego. <Link href="/reset-hasla" className="text-primary hover:underline">Wróć</Link>
      </p>
    );
  }

  return done ? (
    <div className="text-center space-y-4 py-2">
      <div className="flex justify-center">
        <CheckCircle className="h-12 w-12 text-green-500" />
      </div>
      <p className="text-sm text-muted-foreground">
        Hasło zostało zmienione. Zaraz nastąpi przekierowanie do logowania…
      </p>
    </div>
  ) : (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium mb-1.5 block">Nowe hasło</label>
        <Input
          type="password"
          placeholder="••••••••"
          value={haslo}
          onChange={(e) => setHaslo(e.target.value)}
          autoComplete="new-password"
          required
          minLength={8}
        />
      </div>
      <div>
        <label className="text-sm font-medium mb-1.5 block">Powtórz nowe hasło</label>
        <Input
          type="password"
          placeholder="••••••••"
          value={haslo2}
          onChange={(e) => setHaslo2(e.target.value)}
          autoComplete="new-password"
          required
        />
      </div>

      {error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
      )}

      <Button type="submit" className="w-full gap-2" disabled={loading}>
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {loading ? "Zapisuję..." : "Ustaw nowe hasło"}
      </Button>
    </form>
  );
}

export default function ZmienHasloPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-bold">
            Ź
          </div>
          <div>
            <p className="font-semibold leading-tight">Źródło</p>
            <p className="text-xs text-muted-foreground">System parafialny</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Nowe hasło</CardTitle>
            <CardDescription>Ustaw nowe hasło dla swojego konta</CardDescription>
          </CardHeader>
          <CardContent>
            <Suspense>
              <ZmienHasloForm />
            </Suspense>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
