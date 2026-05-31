"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";

interface InviteInfo {
  email: string;
  rola: string;
}

const ETYKIETY_ROL: Record<string, string> = {
  proboszcz: "Proboszcz",
  wikariusz: "Wikariusz",
  parafianin: "Parafianin",
  admin: "Administrator",
};

function AktywujForm() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token") ?? "";

  const [info, setInfo] = useState<InviteInfo | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [invalidToken, setInvalidToken] = useState(false);

  const [imie, setImie] = useState("");
  const [nazwisko, setNazwisko] = useState("");
  const [haslo, setHaslo] = useState("");
  const [haslo2, setHaslo2] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) { setInvalidToken(true); setLoadingInfo(false); return; }
    apiClient.get(`/zaproszenia/info?token=${encodeURIComponent(token)}`)
      .then((r) => setInfo(r.data))
      .catch(() => setInvalidToken(true))
      .finally(() => setLoadingInfo(false));
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (haslo !== haslo2) { setError("Hasła nie są identyczne"); return; }
    if (haslo.length < 8) { setError("Hasło musi mieć co najmniej 8 znaków"); return; }
    setError("");
    setLoading(true);
    try {
      await apiClient.post("/zaproszenia/aktywuj", { token, imie, nazwisko, haslo });
      setDone(true);
      setTimeout(() => router.replace("/login"), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Błąd aktywacji konta");
    } finally {
      setLoading(false);
    }
  }

  if (loadingInfo) {
    return <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }

  if (invalidToken) {
    return (
      <div className="text-center space-y-3 py-2">
        <p className="text-sm text-destructive">Zaproszenie nie istnieje lub wygasło.</p>
        <Button variant="outline" asChild><Link href="/login">Przejdź do logowania</Link></Button>
      </div>
    );
  }

  if (done) {
    return (
      <div className="text-center space-y-4 py-2">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
        <p className="text-sm text-muted-foreground">
          Konto zostało aktywowane. Zaraz nastąpi przekierowanie do logowania…
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {info && (
        <div className="rounded-md bg-muted px-4 py-3 text-sm space-y-1">
          <p><span className="text-muted-foreground">Email:</span> <strong>{info.email}</strong></p>
          <p><span className="text-muted-foreground">Rola:</span> <strong>{ETYKIETY_ROL[info.rola] ?? info.rola}</strong></p>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium mb-1.5 block">Imię</label>
          <Input value={imie} onChange={(e) => setImie(e.target.value)} required minLength={2} />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Nazwisko</label>
          <Input value={nazwisko} onChange={(e) => setNazwisko(e.target.value)} required minLength={2} />
        </div>
      </div>
      <div>
        <label className="text-sm font-medium mb-1.5 block">Hasło</label>
        <Input type="password" value={haslo} onChange={(e) => setHaslo(e.target.value)} required minLength={8} autoComplete="new-password" />
      </div>
      <div>
        <label className="text-sm font-medium mb-1.5 block">Powtórz hasło</label>
        <Input type="password" value={haslo2} onChange={(e) => setHaslo2(e.target.value)} required autoComplete="new-password" />
      </div>
      {error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
      )}
      <Button type="submit" className="w-full gap-2" disabled={loading}>
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {loading ? "Aktywuję..." : "Aktywuj konto"}
      </Button>
    </form>
  );
}

export default function AktywujKontoPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-bold">Ź</div>
          <div>
            <p className="font-semibold leading-tight">Źródło</p>
            <p className="text-xs text-muted-foreground">System parafialny</p>
          </div>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Aktywacja konta</CardTitle>
            <CardDescription>Uzupełnij dane, aby aktywować swoje konto</CardDescription>
          </CardHeader>
          <CardContent>
            <Suspense><AktywujForm /></Suspense>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
