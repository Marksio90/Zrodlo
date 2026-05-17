"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { authApi } from "@/lib/api";
import { getToken, setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [haslo, setHaslo] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    }
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !haslo.trim()) return;
    setError("");
    setLoading(true);
    try {
      const data = await authApi.login(email.trim(), haslo);
      setToken(data.access_token);
      router.replace("/dashboard");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Nieprawidłowy email lub hasło"
      );
    } finally {
      setLoading(false);
    }
  }

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
            <CardTitle className="text-xl">Zaloguj się</CardTitle>
            <CardDescription>
              Wprowadź dane dostępowe do systemu parafialnego
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1.5 block">
                  Adres e-mail
                </label>
                <Input
                  type="email"
                  placeholder="jan@parafia.pl"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">
                  Hasło
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={haslo}
                  onChange={(e) => setHaslo(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              {error && (
                <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full gap-2" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Loguję..." : "Zaloguj się"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          AI wspiera człowieka – nie zastępuje kapłana
        </p>
      </div>
    </div>
  );
}
