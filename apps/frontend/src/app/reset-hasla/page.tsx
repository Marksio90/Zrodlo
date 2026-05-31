"use client";

import { useState } from "react";
import Link from "next/link";
import { Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";

export default function ResetHaslaPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setError("");
    setLoading(true);
    try {
      await apiClient.post("/auth/reset-hasla/wyslij", { email: email.trim() });
      setSent(true);
    } catch {
      setError("Wystąpił błąd. Spróbuj ponownie.");
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
            <CardTitle className="text-xl">Reset hasła</CardTitle>
            <CardDescription>
              Podaj adres e-mail powiązany z kontem – wyślemy link do resetu
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="text-center space-y-4 py-2">
                <div className="flex justify-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                    <Mail className="h-7 w-7 text-primary" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Jeśli podany adres istnieje w systemie, wysłaliśmy link do resetu hasła.
                  Sprawdź skrzynkę (i folder spam).
                </p>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/login">Wróć do logowania</Link>
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Adres e-mail</label>
                  <Input
                    type="email"
                    placeholder="jan@parafia.pl"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
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
                  {loading ? "Wysyłam..." : "Wyślij link resetujący"}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  <Link href="/login" className="text-primary hover:underline">
                    Wróć do logowania
                  </Link>
                </p>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
