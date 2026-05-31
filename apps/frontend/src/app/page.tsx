"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  BookOpen,
  Brain,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  FileText,
  Heart,
  MessageSquare,
  Shield,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getToken } from "@/lib/auth";

const FEATURES = [
  {
    icon: Heart,
    title: "Intencje mszalne",
    desc: "Rejestracja, weryfikacja, historia i wydruk intencji. Nigdy więcej zgubionych karteczek.",
    color: "text-rose-500",
    bg: "bg-rose-50",
  },
  {
    icon: FileText,
    title: "Dokumenty kancelaryjne",
    desc: "Tworzenie, archiwizacja i podpisywanie pism. Baza dokumentów dostępna z każdego urządzenia.",
    color: "text-blue-500",
    bg: "bg-blue-50",
  },
  {
    icon: CalendarDays,
    title: "Liturgia i kalendarz",
    desc: "Planowanie liturgii, zarządzanie harmonogramem mszy i wydarzeń parafialnych.",
    color: "text-purple-500",
    bg: "bg-purple-50",
  },
  {
    icon: Brain,
    title: "Asystent AI",
    desc: "Wsparcie w przygotowaniu homilii, dokumentów i komunikatów. AI pomaga – kapłan decyduje.",
    color: "text-amber-500",
    bg: "bg-amber-50",
  },
  {
    icon: Users,
    title: "Wspólnoty i grupy",
    desc: "Ewidencja wiernych, zarządzanie grupami, kołami różańcowymi i schola cantorum.",
    color: "text-green-500",
    bg: "bg-green-50",
  },
  {
    icon: Shield,
    title: "Bezpieczeństwo RODO",
    desc: "Dane parafian chronione zgodnie z RODO. Szyfrowanie, backupy, umowa powierzenia.",
    color: "text-slate-500",
    bg: "bg-slate-50",
  },
];

const KROKI = [
  {
    n: "1",
    title: "Rejestracja i onboarding",
    desc: "Zakładasz konto parafii w 5 minut. Kreator prowadzi Cię przez konfigurację – bez IT.",
  },
  {
    n: "2",
    title: "Import danych",
    desc: "Przenosisz istniejące intencje i dokumenty. Możesz zacząć od zera lub importować z Excela.",
  },
  {
    n: "3",
    title: "Codzienna praca",
    desc: "Kancelaria, zakrystian i wikariusze pracują razem w jednym systemie, na każdym urządzeniu.",
  },
];

const PLANY = [
  {
    id: "trial",
    name: "Próbny",
    price: "0 zł",
    period: "30 dni",
    desc: "Pełna funkcjonalność Standardu na miesiąc próbny.",
    features: ["5 użytkowników", "30 zapytań AI", "Asystent AI", "Baza wiedzy"],
    cta: "Wypróbuj bezpłatnie",
    highlight: false,
  },
  {
    id: "podstawowy",
    name: "Podstawowy",
    price: "49 zł",
    period: "/ miesiąc",
    desc: "Zarządzanie bez AI – idealne dla małych parafii.",
    features: ["10 użytkowników", "Intencje i liturgia", "Dokumenty i archiwum", "Eksport danych"],
    cta: "Wybierz plan",
    highlight: false,
  },
  {
    id: "standard",
    name: "Standard",
    price: "99 zł",
    period: "/ miesiąc",
    desc: "Pełny system z asystentem AI i bazą wiedzy.",
    features: ["30 użytkowników", "300 zapytań AI/mies.", "Asystent AI + baza wiedzy", "Komunikacja masowa"],
    cta: "Wybierz Standard",
    highlight: true,
  },
  {
    id: "premium",
    name: "Premium",
    price: "199 zł",
    period: "/ miesiąc",
    desc: "Bez limitów, API i priorytetowe wsparcie.",
    features: ["Nielimitowani użytkownicy", "Nieograniczone AI", "Integracje API", "Wsparcie priorytetowe"],
    cta: "Skontaktuj się",
    highlight: false,
  },
];

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      {/* ── NAWIGACJA ── */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
              Ź
            </div>
            <span className="font-semibold text-base">Źródło</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <a href="#funkcje" className="hover:text-foreground transition-colors">Funkcje</a>
            <a href="#jak-dziala" className="hover:text-foreground transition-colors">Jak działa</a>
            <a href="#cennik" className="hover:text-foreground transition-colors">Cennik</a>
            <Link href="/case-study" className="hover:text-foreground transition-colors">Case study</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/login">Zaloguj się</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/login">Wypróbuj bezpłatnie</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* ── HERO ── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary/5 via-primary/3 to-background py-24 px-6">
        <div className="mx-auto max-w-4xl text-center relative z-10">
          <Badge variant="secondary" className="mb-6 gap-1.5">
            <Sparkles className="h-3 w-3" />
            Asystent AI wspiera – kapłan decyduje
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl leading-tight mb-6">
            Cyfrowa kancelaria<br />
            <span className="text-primary">dla parafii</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Źródło łączy zarządzanie intencjami, dokumentami i liturgią
            z asystentem AI przygotowanym specjalnie dla duszpasterzy.
            Spokojne, godne narzędzie codziennej pracy kancelarii.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button size="lg" className="gap-2" asChild>
              <Link href="/login">
                Wypróbuj 30 dni bezpłatnie
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/case-study">
                <BookOpen className="h-4 w-4 mr-2" />
                Zobacz case study
              </Link>
            </Button>
          </div>
          <p className="mt-5 text-xs text-muted-foreground">
            Bez karty kredytowej · Bez zobowiązań · Pełna funkcjonalność Standardu
          </p>
        </div>
        <div className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl" />
      </section>

      {/* ── FUNKCJE ── */}
      <section id="funkcje" className="py-20 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold tracking-tight mb-3">Wszystko czego potrzebuje parafia</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Jeden system zamiast zeszytów, teczek i arkuszy kalkulacyjnych.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, desc, color, bg }) => (
              <Card key={title} className="group hover:shadow-md transition-all hover:-translate-y-0.5">
                <CardContent className="pt-6">
                  <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${bg} mb-4`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                  <h3 className="font-semibold mb-2">{title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── JAK DZIAŁA ── */}
      <section id="jak-dziala" className="py-20 px-6 bg-muted/30">
        <div className="mx-auto max-w-4xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold tracking-tight mb-3">Jak to działa?</h2>
            <p className="text-muted-foreground">
              Od rejestracji do pełnej pracy kancelarii w ciągu jednego dnia.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {KROKI.map(({ n, title, desc }) => (
              <div key={n} className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-lg mb-4">
                  {n}
                </div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CASE STUDY PREVIEW ── */}
      <section className="py-20 px-6">
        <div className="mx-auto max-w-4xl">
          <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-primary/5 to-background">
            <CardContent className="p-8 md:p-12">
              <div className="flex flex-col md:flex-row gap-8 items-start">
                <div className="flex-1">
                  <Badge className="mb-4">Case study</Badge>
                  <h2 className="text-2xl font-bold tracking-tight mb-3">
                    Parafia pw. Wniebowzięcia NMP,<br />Kraków – Nowa Huta
                  </h2>
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    Jak 1200-osobowa parafia przeszła z papierowych zeszytów
                    na cyfrową kancelarię i skróciła czas obsługi intencji o 70%.
                  </p>
                  <Button variant="outline" className="gap-2" asChild>
                    <Link href="/case-study">
                      Czytaj całą historię
                      <ChevronRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4 shrink-0">
                  {[
                    { value: "70%", label: "mniej czasu na intencje" },
                    { value: "3×", label: "szybsze dokumenty" },
                    { value: "0", label: "zagubionych intencji" },
                    { value: "100%", label: "zgodność z RODO" },
                  ].map(({ value, label }) => (
                    <div key={label} className="text-center bg-background rounded-xl p-4 shadow-sm">
                      <p className="text-2xl font-bold text-primary">{value}</p>
                      <p className="text-xs text-muted-foreground mt-1 leading-tight">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ── CENNIK ── */}
      <section id="cennik" className="py-20 px-6 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold tracking-tight mb-3">Przejrzyste ceny</h2>
            <p className="text-muted-foreground">
              Bez ukrytych kosztów. Parafie i stowarzyszenia charytatywne – 50% rabatu.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {PLANY.map((plan) => (
              <Card
                key={plan.id}
                className={`relative flex flex-col ${
                  plan.highlight
                    ? "border-primary shadow-md shadow-primary/10 ring-1 ring-primary"
                    : ""
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="shadow-sm">Najpopularniejszy</Badge>
                  </div>
                )}
                <CardHeader className="pb-4">
                  <p className="text-sm font-medium text-muted-foreground">{plan.name}</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-sm text-muted-foreground">{plan.period}</span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">{plan.desc}</p>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col gap-4">
                  <ul className="space-y-2 flex-1">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={plan.highlight ? "default" : "outline"}
                    className="w-full"
                    asChild
                  >
                    <Link href="/login">{plan.cta}</Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="text-center text-xs text-muted-foreground mt-6">
            Ceny netto. Parafia jako podmiot kościelny jest zwolniona z VAT.
            Rabat 20% przy płatności rocznej · Rabat 50% dla organizacji charytatywnych.
          </p>
        </div>
      </section>

      {/* ── AI DISCLAIMER ── */}
      <section className="py-16 px-6">
        <div className="mx-auto max-w-3xl text-center">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50">
              <Sparkles className="h-6 w-6 text-amber-500" />
            </div>
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-4">
            AI wspiera duszpasterza – nie zastępuje kapłana
          </h2>
          <p className="text-muted-foreground leading-relaxed mb-3">
            Asystent AI w Źródle to narzędzie pomocnicze. Generowane materiały –
            szkice homilii, treści dokumentów, odpowiedzi chatbota – wymagają
            weryfikacji i zatwierdzenia przez kapłana przed użyciem.
          </p>
          <p className="text-sm text-muted-foreground">
            AI nie podejmuje decyzji teologicznych ani duszpasterskich.
            Działa wyłącznie na dostarczonych danych parafii.
          </p>
        </div>
      </section>

      {/* ── CTA KOŃCOWE ── */}
      <section className="py-20 px-6 bg-primary text-primary-foreground">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight mb-4">
            Zacznij korzystać już dziś
          </h2>
          <p className="text-primary-foreground/80 mb-8 leading-relaxed">
            30 dni bezpłatnie, bez karty kredytowej.
            Jeśli Źródło nie usprawni pracy Twojej kancelarii – po prostu nie płać.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button size="lg" variant="secondary" className="gap-2" asChild>
              <Link href="/login">
                Wypróbuj bezpłatnie
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10"
              asChild
            >
              <a href="mailto:kontakt@zrodlo.pl">
                <MessageSquare className="h-4 w-4 mr-2" />
                Porozmawiaj z nami
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t py-10 px-6 bg-background">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs">
                Ź
              </div>
              <span className="font-semibold text-sm">Źródło</span>
              <Separator orientation="vertical" className="h-4 mx-1" />
              <span className="text-xs text-muted-foreground">Cyfrowa kancelaria parafialna</span>
            </div>
            <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
              <Link href="/case-study" className="hover:text-foreground transition-colors">Case study</Link>
              <a href="#cennik" className="hover:text-foreground transition-colors">Cennik</a>
              <Link href="/login" className="hover:text-foreground transition-colors">Logowanie</Link>
              <a href="mailto:kontakt@zrodlo.pl" className="hover:text-foreground transition-colors">Kontakt</a>
            </nav>
            <p className="text-xs text-muted-foreground">
              © {new Date().getFullYear()} Źródło. Wszelkie prawa zastrzeżone.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
