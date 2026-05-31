"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Circle, ArrowRight, ArrowLeft, Loader2, PartyPopper } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

// ── Typy ──────────────────────────────────────────────────────────────────────

interface KrokStatus {
  id: string;
  tytul: string;
  opis: string;
  ukonczone: boolean;
}

interface OnboardingStatus {
  parafia_id: string;
  gotowy: boolean;
  ukonczone_kroki: number;
  wszystkich_krokow: number;
  kroki: KrokStatus[];
}

// ── Stałe ─────────────────────────────────────────────────────────────────────

const SKIP_KEY = "zrodlo_onboarding_konto_skip";
const DONE_KEY = "zrodlo_onboarding_done";

// ── Krok 1: Dane parafii ──────────────────────────────────────────────────────

function KrokDaneParafii({
  onUkoncz,
  ukonczone,
}: {
  onUkoncz: () => void;
  ukonczone: boolean;
}) {
  const [email, setEmail] = useState("");
  const [telefon, setTelefon] = useState("");
  const [diecezja, setDiecezja] = useState("");
  const [dekanat, setDekanat] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [parafiaId, setParafiaId] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get("/auth/mnie").then((r) => {
      const pid = r.data?.parafia_id;
      if (pid) {
        setParafiaId(pid);
        apiClient.get(`/parafia/${pid}`).then((rp) => {
          setEmail(rp.data.email ?? "");
          setTelefon(rp.data.telefon ?? "");
          setDiecezja(rp.data.diecezja ?? "");
          setDekanat(rp.data.dekanat ?? "");
        }).catch(() => {});
      }
    }).catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!parafiaId) return;
    setLoading(true);
    setError("");
    try {
      await apiClient.patch(`/parafia/${parafiaId}`, { email, telefon, diecezja, dekanat });
      onUkoncz();
    } catch {
      setError("Nie udało się zapisać danych. Sprawdź połączenie i spróbuj ponownie.");
    } finally {
      setLoading(false);
    }
  }

  if (ukonczone) {
    return (
      <div className="text-center py-4">
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-3" />
        <p className="font-medium">Dane parafii są uzupełnione</p>
        <p className="text-sm text-muted-foreground mt-1">Możesz przejść dalej.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="text-sm font-medium mb-1.5 block">E-mail parafii *</label>
          <Input
            type="email"
            placeholder="biuro@parafia.pl"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="col-span-2">
          <label className="text-sm font-medium mb-1.5 block">Telefon *</label>
          <Input
            type="tel"
            placeholder="12 345 67 89"
            value={telefon}
            onChange={(e) => setTelefon(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Diecezja</label>
          <Input
            placeholder="np. Archidiecezja Krakowska"
            value={diecezja}
            onChange={(e) => setDiecezja(e.target.value)}
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Dekanat</label>
          <Input
            placeholder="np. Dekanat Nowa Huta"
            value={dekanat}
            onChange={(e) => setDekanat(e.target.value)}
          />
        </div>
      </div>
      {error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
      )}
      <Button type="submit" className="w-full gap-2" disabled={loading}>
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        Zapisz i kontynuuj
      </Button>
    </form>
  );
}

// ── Krok 2: RODO ─────────────────────────────────────────────────────────────

function KrokRODO({ onUkoncz, ukonczone }: { onUkoncz: () => void; ukonczone: boolean }) {
  const [zaznaczone, setZaznaczone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAkceptuj() {
    setLoading(true);
    setError("");
    try {
      await apiClient.post("/rodo/akceptuj", { wersja: "1.0" });
      onUkoncz();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Błąd akceptacji";
      if (msg.includes("409") || msg.includes("już")) {
        onUkoncz();
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  if (ukonczone) {
    return (
      <div className="text-center py-4">
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-3" />
        <p className="font-medium">Umowa RODO zaakceptowana</p>
        <p className="text-sm text-muted-foreground mt-1">Dziękujemy. Możesz przejść dalej.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-muted/30 p-4 text-sm space-y-3 max-h-52 overflow-y-auto">
        <p className="font-semibold">Umowa Powierzenia Przetwarzania Danych Osobowych (art. 28 RODO)</p>
        <p className="text-muted-foreground">
          Jako dostawca systemu Źródło przetwarzamy dane osobowe wiernych Twojej parafii
          wyłącznie w Twoim imieniu i zgodnie z Twoimi instrukcjami. Stosujemy szyfrowanie
          (TLS 1.2+, bcrypt), izolację danych parafii (multi-tenant) oraz automatyczne
          kopie zapasowe przechowywane przez 30 dni.
        </p>
        <p className="text-muted-foreground">
          Dane przechowujemy na serwerach w EOG (Hetzner, Niemcy). Modele AI (OpenAI)
          objęte są Standardowymi Klauzulami Umownymi. Każda parafia może w dowolnym
          momencie wyeksportować lub usunąć swoje dane.
        </p>
        <p className="text-muted-foreground">
          Pełna treść umowy dostępna pod adresem: <strong>/rodo/umowa/tresc</strong>
        </p>
      </div>

      <label className="flex items-start gap-3 cursor-pointer group">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-gray-300 accent-primary"
          checked={zaznaczone}
          onChange={(e) => setZaznaczone(e.target.checked)}
        />
        <span className="text-sm leading-relaxed">
          Potwierdzam, że zapoznałem(-am) się z treścią Umowy Powierzenia Przetwarzania
          Danych Osobowych i akceptuję jej warunki w imieniu parafii.
        </span>
      </label>

      {error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
      )}

      <Button
        className="w-full gap-2"
        disabled={!zaznaczone || loading}
        onClick={handleAkceptuj}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        Akceptuję umowę RODO
      </Button>
    </div>
  );
}

// ── Krok 3: Subskrypcja ────────────────────────────────────────────────────────

function KrokSubskrypcja({ onUkoncz, ukonczone }: { onUkoncz: () => void; ukonczone: boolean }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleTrial() {
    setLoading(true);
    setError("");
    try {
      await apiClient.post("/subskrypcja/trial", {});
      onUkoncz();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Błąd aktywacji";
      if (msg.includes("409") || msg.includes("już")) {
        onUkoncz();
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  if (ukonczone) {
    return (
      <div className="text-center py-4">
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-3" />
        <p className="font-medium">Subskrypcja aktywna</p>
        <p className="text-sm text-muted-foreground mt-1">Korzystasz z bezpłatnego okresu próbnego.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-4 text-center">
        <p className="text-2xl font-bold text-primary">30 dni</p>
        <p className="font-semibold">Bezpłatny okres próbny</p>
        <p className="text-sm text-muted-foreground mt-1">Pełna funkcjonalność planu Standard</p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        {[
          ["Asystent AI", "30 zapytań"],
          ["Baza wiedzy", "✓"],
          ["Generowanie dokumentów", "✓"],
          ["Użytkownicy", "do 5"],
        ].map(([label, val]) => (
          <div key={label} className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium">{val}</span>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Po 30 dniach możesz wybrać plan od 49 zł/mies. Nie wymagamy karty kredytowej.
      </p>

      {error && (
        <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
      )}

      <Button className="w-full gap-2" onClick={handleTrial} disabled={loading}>
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        Aktywuj bezpłatny okres próbny
      </Button>
    </div>
  );
}

// ── Krok 4: Pierwsze konto ─────────────────────────────────────────────────────

function KrokPierwszeKonto({
  onUkoncz,
  onPrzeskocz,
  ukonczone,
}: {
  onUkoncz: () => void;
  onPrzeskocz: () => void;
  ukonczone: boolean;
}) {
  const [imie, setImie] = useState("");
  const [nazwisko, setNazwisko] = useState("");
  const [email, setEmail] = useState("");
  const [haslo, setHaslo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await apiClient.post("/uzytkownicy/wikariusze", { imie, nazwisko, email, haslo });
      onUkoncz();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Nie udało się utworzyć konta");
    } finally {
      setLoading(false);
    }
  }

  if (ukonczone) {
    return (
      <div className="text-center py-4">
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-3" />
        <p className="font-medium">Współpracownik dodany</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Dodaj wikariusza lub sekretarkę, aby mogli korzystać z systemu.
        Ten krok możesz wykonać później w zakładce Użytkownicy.
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium mb-1.5 block">Imię</label>
            <Input placeholder="Jan" value={imie} onChange={(e) => setImie(e.target.value)} required />
          </div>
          <div>
            <label className="text-sm font-medium mb-1.5 block">Nazwisko</label>
            <Input placeholder="Kowalski" value={nazwisko} onChange={(e) => setNazwisko(e.target.value)} required />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">E-mail</label>
          <Input type="email" placeholder="wik@parafia.pl" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Hasło tymczasowe</label>
          <Input type="password" placeholder="min. 8 znaków" value={haslo} onChange={(e) => setHaslo(e.target.value)} minLength={8} required />
        </div>
        {error && (
          <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">{error}</p>
        )}
        <div className="flex gap-2">
          <Button type="button" variant="outline" className="flex-1" onClick={onPrzeskocz}>
            Pomiń na razie
          </Button>
          <Button type="submit" className="flex-1 gap-2" disabled={loading}>
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Dodaj konto
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── Krok 5: Gotowe! ────────────────────────────────────────────────────────────

function KrokGotowy({ onZakoncz }: { onZakoncz: () => void }) {
  const user = getUser();

  return (
    <div className="text-center space-y-6">
      <div className="flex justify-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
          <PartyPopper className="h-10 w-10 text-green-600" />
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold">Parafia gotowa!</h2>
        <p className="text-muted-foreground mt-2">
          {user ? `Witaj, ${user.imie}!` : "Witaj!"} System Źródło jest skonfigurowany
          i gotowy do pracy.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-left">
        {[
          { emoji: "🙏", label: "Intencje mszalne", opis: "Zarządzaj intencjami parafian" },
          { emoji: "📅", label: "Kalendarz", opis: "Planuj wydarzenia parafii" },
          { emoji: "📄", label: "Dokumenty", opis: "Twórz metryki i zaświadczenia" },
          { emoji: "🤖", label: "Asystent AI", opis: "Wsparcie w pracy kapłańskiej" },
        ].map(({ emoji, label, opis }) => (
          <div key={label} className="rounded-lg border bg-white p-3">
            <p className="text-lg">{emoji}</p>
            <p className="font-medium text-sm">{label}</p>
            <p className="text-xs text-muted-foreground">{opis}</p>
          </div>
        ))}
      </div>

      <Button className="w-full gap-2" onClick={onZakoncz}>
        Przejdź do pulpitu
        <ArrowRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

// ── Główny komponent wizard ────────────────────────────────────────────────────

const KROKI_DEF = [
  { id: "dane_parafii",   tytul: "Dane parafii",             opis: "Kontakt i informacje administracyjne" },
  { id: "rodo",           tytul: "Umowa RODO",                opis: "Wymagana przez RODO art. 28" },
  { id: "subskrypcja",    tytul: "Plan i subskrypcja",        opis: "30 dni bezpłatnie" },
  { id: "pierwsze_konto", tytul: "Zaproś współpracownika",    opis: "Opcjonalnie – możesz pominąć" },
  { id: "gotowy",         tytul: "Gotowe!",                   opis: "Zaczynamy" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [activeStep, setActiveStep] = useState(0);
  const [statusKrokow, setStatusKrokow] = useState<Record<string, boolean>>({});
  const [loadingStatus, setLoadingStatus] = useState(true);

  const stepsCount = KROKI_DEF.length - 1; // bez "gotowy"

  async function refreshStatus() {
    try {
      const r = await apiClient.get("/onboarding/status");
      const nowy: Record<string, boolean> = {};
      for (const k of r.data.kroki as KrokStatus[]) {
        nowy[k.id] = k.ukonczone;
      }
      // krok "pierwsze_konto" można pominąć
      const przeskoczone = typeof window !== "undefined" && localStorage.getItem(SKIP_KEY) === "1";
      if (przeskoczone) nowy["pierwsze_konto"] = true;
      setStatusKrokow(nowy);
      return nowy;
    } catch {
      return {};
    } finally {
      setLoadingStatus(false);
    }
  }

  useEffect(() => {
    // Jeśli onboarding już zakończony, idź od razu do dashboardu
    if (typeof window !== "undefined" && localStorage.getItem(DONE_KEY) === "1") {
      router.replace("/dashboard");
      return;
    }
    refreshStatus().then((status) => {
      // Ustaw activeStep na pierwszy nieukończony krok
      const kroki = ["dane_parafii", "rodo", "subskrypcja", "pierwsze_konto"];
      const first = kroki.findIndex((id) => !status[id]);
      setActiveStep(first === -1 ? stepsCount : first);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onKrokUkoncz(krokId: string) {
    setStatusKrokow((prev) => ({ ...prev, [krokId]: true }));
    // Automatycznie przejdź do następnego kroku po chwili
    setTimeout(() => {
      setActiveStep((s) => Math.min(s + 1, stepsCount));
    }, 600);
  }

  function handlePrzeskoczKonto() {
    if (typeof window !== "undefined") localStorage.setItem(SKIP_KEY, "1");
    setStatusKrokow((prev) => ({ ...prev, pierwsze_konto: true }));
    setActiveStep(stepsCount);
  }

  function handleZakoncz() {
    if (typeof window !== "undefined") localStorage.setItem(DONE_KEY, "1");
    router.replace("/dashboard");
  }

  if (loadingStatus) {
    return (
      <div className="flex items-center gap-3 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Ładowanie...
      </div>
    );
  }

  const wizardKroki = KROKI_DEF.slice(0, stepsCount);
  const ukonczonychWizard = wizardKroki.filter((k) => statusKrokow[k.id]).length;
  const progress = Math.round((ukonczonychWizard / stepsCount) * 100);
  const isGotowy = activeStep === stepsCount;

  return (
    <div className="w-full max-w-lg">
      {/* Pasek postępu */}
      {!isGotowy && (
        <div className="mb-6">
          <div className="flex justify-between text-xs text-muted-foreground mb-2">
            <span>Konfiguracja parafii</span>
            <span>{ukonczonychWizard}/{stepsCount} kroków</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Kroki */}
          <div className="flex items-center justify-between mt-4">
            {wizardKroki.map((krok, idx) => {
              const done = statusKrokow[krok.id];
              const active = idx === activeStep;
              return (
                <button
                  key={krok.id}
                  onClick={() => setActiveStep(idx)}
                  className="flex flex-col items-center gap-1 group"
                >
                  <div className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors text-xs font-medium",
                    done
                      ? "border-green-500 bg-green-500 text-white"
                      : active
                      ? "border-primary bg-primary text-white"
                      : "border-muted-foreground/30 text-muted-foreground"
                  )}>
                    {done ? <CheckCircle2 className="h-4 w-4" /> : <span>{idx + 1}</span>}
                  </div>
                  <span className={cn(
                    "text-[10px] max-w-[64px] text-center leading-tight",
                    active ? "text-primary font-medium" : "text-muted-foreground"
                  )}>
                    {krok.tytul}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Karta kroku */}
      <Card>
        {!isGotowy && (
          <CardHeader>
            <CardTitle>{KROKI_DEF[activeStep]?.tytul}</CardTitle>
            <CardDescription>{KROKI_DEF[activeStep]?.opis}</CardDescription>
          </CardHeader>
        )}
        <CardContent className={isGotowy ? "pt-6" : ""}>
          {activeStep === 0 && (
            <KrokDaneParafii
              ukonczone={!!statusKrokow["dane_parafii"]}
              onUkoncz={() => onKrokUkoncz("dane_parafii")}
            />
          )}
          {activeStep === 1 && (
            <KrokRODO
              ukonczone={!!statusKrokow["rodo"]}
              onUkoncz={() => onKrokUkoncz("rodo")}
            />
          )}
          {activeStep === 2 && (
            <KrokSubskrypcja
              ukonczone={!!statusKrokow["subskrypcja"]}
              onUkoncz={() => onKrokUkoncz("subskrypcja")}
            />
          )}
          {activeStep === 3 && (
            <KrokPierwszeKonto
              ukonczone={!!statusKrokow["pierwsze_konto"]}
              onUkoncz={() => onKrokUkoncz("pierwsze_konto")}
              onPrzeskocz={handlePrzeskoczKonto}
            />
          )}
          {isGotowy && <KrokGotowy onZakoncz={handleZakoncz} />}

          {/* Nawigacja – strzałki */}
          {!isGotowy && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <Button
                variant="ghost"
                size="sm"
                disabled={activeStep === 0}
                onClick={() => setActiveStep((s) => s - 1)}
                className="gap-1"
              >
                <ArrowLeft className="h-4 w-4" />
                Wstecz
              </Button>

              <Button
                variant="ghost"
                size="sm"
                disabled={activeStep >= stepsCount - 1}
                onClick={() => setActiveStep((s) => s + 1)}
                className="gap-1"
              >
                Dalej
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
