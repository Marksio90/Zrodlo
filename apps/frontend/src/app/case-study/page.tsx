import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  Heart,
  Quote,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export const metadata: Metadata = {
  title: "Case study – Parafia pw. Wniebowzięcia NMP | Źródło",
  description:
    "Jak parafia w Nowej Hucie wdrożyła Źródło i skróciła czas obsługi intencji o 70%. Pełna historia wdrożenia cyfrowej kancelarii parafialnej.",
};

const METRYKI = [
  {
    icon: TrendingDown,
    value: "70%",
    label: "mniej czasu na rejestrację intencji",
    color: "text-green-500",
    bg: "bg-green-50",
    opis: "Z 8 minut na kładkę do 2,5 minuty",
  },
  {
    icon: FileText,
    value: "3×",
    label: "szybsze tworzenie dokumentów",
    color: "text-blue-500",
    bg: "bg-blue-50",
    opis: "AI przygotowuje szkic w 30 sekund",
  },
  {
    icon: Heart,
    value: "0",
    label: "zagubionych intencji",
    color: "text-rose-500",
    bg: "bg-rose-50",
    opis: "Wcześniej średnio 2–3 miesięcznie",
  },
  {
    icon: Users,
    value: "6",
    label: "użytkowników systemu",
    color: "text-purple-500",
    bg: "bg-purple-50",
    opis: "Proboszcz, 2 wikariuszy, 3 pracowników kancelarii",
  },
  {
    icon: Clock,
    value: "1 dzień",
    label: "czas wdrożenia",
    color: "text-amber-500",
    bg: "bg-amber-50",
    opis: "Od rejestracji do pełnej pracy kancelarii",
  },
  {
    icon: Zap,
    value: "120+",
    label: "zapytań AI miesięcznie",
    color: "text-indigo-500",
    bg: "bg-indigo-50",
    opis: "Homilie, dokumenty, odpowiedzi na pytania",
  },
];

const HARMONOGRAM = [
  {
    data: "Tydzień 1",
    tytul: "Rejestracja i konfiguracja",
    opis:
      "Ks. proboszcz Marek wypełnił formularz rejestracyjny i skonfigurował dane parafii. Kreator onboarding przeprowadził go przez akceptację umowy RODO i zaproszenie pierwszych użytkowników. Całość zajęła niecałe 2 godziny.",
    tag: "Start",
    color: "bg-green-500",
  },
  {
    data: "Tydzień 1–2",
    tytul: "Import historycznych danych",
    opis:
      "Sekretarka Irena przeniosła intencje z papierowego zeszytu za ostatnie 3 miesiące. 287 wpisów zaimportowano ręcznie, korzystając z formularzy systemu. Jednocześnie zeskanowano i dodano 40 najważniejszych dokumentów kancelarii.",
    tag: "Migracja danych",
    color: "bg-blue-500",
  },
  {
    data: "Tydzień 3",
    tytul: "Szkolenie i pierwsze użycie",
    opis:
      "Wszyscy 6 użytkowników przeszło przez wewnętrzne szkolenie z systemu (90 minut). Pierwsze intencje zaczęły trafiać bezpośrednio do Źródła. Wikariusz Tomasz przetestował asystenta AI do przygotowania szkicu kazania.",
    tag: "Szkolenie",
    color: "bg-purple-500",
  },
  {
    data: "Miesiąc 2",
    tytul: "Pełna praca kancelarii",
    opis:
      "100% nowych intencji i dokumentów w systemie. Papierowy zeszyt odłożony na bok – tylko jako archiwum. Pierwsze ogłoszenia parafialne przygotowane z pomocą AI i zatwierdzone przez ks. proboszcza.",
    tag: "Pełne wdrożenie",
    color: "bg-amber-500",
  },
  {
    data: "Miesiąc 3+",
    tytul: "Optimizacja i rozwój",
    opis:
      "Parafia wgrała do bazy wiedzy statut parafii, regulamin grup i historię kościoła. Asystent AI zaczął odpowiadać na pytania parafian (przez zakrystię) korzystając z lokalnej bazy wiedzy. Wdrożono komunikację masową – SMS i e-mail do grup.",
    tag: "Dojrzałość",
    color: "bg-primary",
  },
];

const PRZED_PO = [
  {
    aspekt: "Rejestracja intencji",
    przed: "Papierowy zeszyt, ryzyko pomyłki przy odczycie, brak historii",
    po: "Cyfrowy formularz, podgląd historii, powiadomienie e-mail dla rodziny",
  },
  {
    aspekt: "Dokumenty kancelaryjne",
    przed: "Word + drukarka, segregatory, trudne wyszukiwanie",
    po: "Cyfrowe archiwum, wyszukiwanie pełnotekstowe, AI-assisted szkice",
  },
  {
    aspekt: "Komunikacja z wiernymi",
    przed: "Ogłoszenia z ambony i tablicy, brak potwierdzenia odbioru",
    po: "Masowy SMS i e-mail do grup, powiadomienia push w systemie",
  },
  {
    aspekt: "Praca zespołowa",
    przed: "Każdy ma własne notatki, informacje giną między zmianami",
    po: "Wspólny system, historia zmian, przydzielanie zadań",
  },
  {
    aspekt: "Bezpieczeństwo danych",
    przed: "Dane w szafkach i na dysku lokalnym, brak backupu",
    po: "Szyfrowane kopie zapasowe, RODO, dostęp z każdego miejsca",
  },
];

export default function CaseStudyPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* ── NAWIGACJA ── */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-4xl px-6 py-3 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
              Ź
            </div>
            <span className="font-semibold text-base">Źródło</span>
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/" className="gap-1.5">
                <ArrowLeft className="h-3.5 w-3.5" />
                Strona główna
              </Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/login">Wypróbuj bezpłatnie</Link>
            </Button>
          </div>
        </div>
      </header>

      <article className="mx-auto max-w-4xl px-6 pb-20">

        {/* ── NAGŁÓWEK ── */}
        <div className="py-16 text-center">
          <Badge className="mb-5 gap-1.5">
            <BookOpen className="h-3 w-3" />
            Case study
          </Badge>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl mb-5 leading-tight">
            Parafia pw. Wniebowzięcia NMP<br />
            <span className="text-muted-foreground font-normal">Kraków – Nowa Huta</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Jak 1200-osobowa parafia przeszła z papierowych zeszytów
            na cyfrową kancelarię i odzyskała czas, spokój i pewność,
            że żadna intencja się nie zgubi.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-6 text-sm text-muted-foreground">
            <span>Plan: <strong>Standard</strong></span>
            <Separator orientation="vertical" className="h-4" />
            <span>Wdrożenie: <strong>1 dzień</strong></span>
            <Separator orientation="vertical" className="h-4" />
            <span>Użytkownicy: <strong>6 osób</strong></span>
            <Separator orientation="vertical" className="h-4" />
            <span>W systemie od: <strong>marzec 2025</strong></span>
          </div>
        </div>

        {/* ── METRYKI ── */}
        <section className="mb-16">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            {METRYKI.map(({ icon: Icon, value, label, color, bg, opis }) => (
              <Card key={label} className="text-center">
                <CardContent className="pt-6 pb-5">
                  <div className={`mx-auto flex h-10 w-10 items-center justify-center rounded-xl ${bg} mb-3`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                  <p className={`text-2xl font-bold ${color} mb-1`}>{value}</p>
                  <p className="text-sm font-medium leading-snug mb-1">{label}</p>
                  <p className="text-xs text-muted-foreground">{opis}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* ── KONTEKST ── */}
        <section className="mb-16 prose prose-gray max-w-none">
          <h2 className="text-2xl font-bold tracking-tight mb-4">Kontekst i wyzwanie</h2>
          <p className="text-muted-foreground leading-relaxed mb-4">
            Parafia pw. Wniebowzięcia NMP w krakowskiej Nowej Hucie liczy około 1200 aktywnych
            parafian. Kancelaria obsługuje średnio 45 intencji miesięcznie, wystawia kilkadziesiąt
            dokumentów rocznie i organizuje dziesiątki wydarzeń – od rekolekcji po kółka różańcowe.
          </p>
          <p className="text-muted-foreground leading-relaxed mb-4">
            Do marca 2025 roku cała administracja opierała się na papierowym zeszycie intencji,
            folderach na lokalnym dysku twardym i wydrukach przechowywanych w segregatorach.
            Informacje przepływały ustnie między zmianami. Dwa lub trzy razy w roku zdarzało się,
            że intencja zapisana w zeszycie nie trafiała do celebransa – lub trafiała z błędem
            w nazwisku lub dacie.
          </p>
          <p className="text-muted-foreground leading-relaxed">
            Proboszcz, ks. Marek W., podjął decyzję o cyfryzacji kancelarii po tym, jak wikariusz
            pomylił daty dwóch intencji podczas Triduum Paschalnego. "Wtedy zrozumiałem, że nie
            chodzi o zaniedbanie, tylko o system. Papier nie daje pewności."
          </p>
        </section>

        {/* ── CYTAT ── */}
        <section className="mb-16">
          <Card className="bg-gradient-to-br from-primary/5 to-background border-primary/20">
            <CardContent className="pt-8 pb-8 px-8 md:px-12">
              <Quote className="h-8 w-8 text-primary/30 mb-4" />
              <blockquote className="text-lg font-medium leading-relaxed mb-4">
                "Bałem się, że system będzie skomplikowany i nie przyjmie się w parafii.
                Tymczasem Irena, nasza sekretarka, po jednym dniu mówi, że nie wyobraża sobie
                powrotu do zeszytu. To chyba najlepsza recenzja."
              </blockquote>
              <footer className="text-sm text-muted-foreground">
                <strong className="text-foreground">Ks. Marek W.</strong>
                <span className="mx-2">·</span>
                Proboszcz parafii pw. Wniebowzięcia NMP, Kraków
              </footer>
            </CardContent>
          </Card>
        </section>

        {/* ── PRZED / PO ── */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight mb-6">Przed i po</h2>
          <div className="rounded-xl border overflow-hidden">
            <div className="grid grid-cols-[1fr,1fr,1fr] bg-muted/50 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <div className="px-4 py-3">Obszar</div>
              <div className="px-4 py-3 border-l">Przed Źródłem</div>
              <div className="px-4 py-3 border-l text-primary">Po wdrożeniu</div>
            </div>
            {PRZED_PO.map(({ aspekt, przed, po }, i) => (
              <div
                key={aspekt}
                className={`grid grid-cols-[1fr,1fr,1fr] text-sm ${
                  i % 2 === 0 ? "bg-background" : "bg-muted/20"
                }`}
              >
                <div className="px-4 py-4 font-medium">{aspekt}</div>
                <div className="px-4 py-4 border-l text-muted-foreground leading-relaxed">
                  {przed}
                </div>
                <div className="px-4 py-4 border-l text-foreground leading-relaxed flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                  {po}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── HARMONOGRAM ── */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight mb-6">Harmonogram wdrożenia</h2>
          <div className="relative pl-8">
            <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-border" />
            <div className="space-y-8">
              {HARMONOGRAM.map(({ data, tytul, opis, tag, color }) => (
                <div key={data} className="relative">
                  <div className={`absolute -left-5 top-1 h-4 w-4 rounded-full border-2 border-background ${color}`} />
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {data}
                    </span>
                    <Badge variant="secondary" className="text-xs">{tag}</Badge>
                  </div>
                  <h3 className="font-semibold mb-2">{tytul}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{opis}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── AI W PARAFII ── */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight mb-4">Asystent AI w praktyce</h2>
          <p className="text-muted-foreground leading-relaxed mb-6">
            Parafia korzysta z asystenta AI głównie w trzech obszarach:
          </p>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                icon: Sparkles,
                title: "Szkice homilii",
                desc: "Wikariusz Tomasz używa asystenta do przygotowania pierwszego szkicu myśli na niedzielne kazanie. Zawsze weryfikuje i uzupełnia własnymi przemyśleniami. \"Asystent daje punkt wyjścia – kapłan daje duszę.\"",
                color: "text-amber-500",
                bg: "bg-amber-50",
              },
              {
                icon: FileText,
                title: "Dokumenty kancelaryjne",
                desc: "Sekretarka Irena zleca asystentowi przygotowanie szkiców pism urzędowych na podstawie podanych danych. Proboszcz zatwierdza i podpisuje. Czas tworzenia pisma skrócił się z 25 do 8 minut.",
                color: "text-blue-500",
                bg: "bg-blue-50",
              },
              {
                icon: Users,
                title: "Odpowiedzi na pytania",
                desc: "Baza wiedzy parafii zawiera statut, regulaminy i historię kościoła. Pracownicy kancelarii pytają asystenta o szczegóły, gdy nie pamiętają regulacji – system odpowiada na podstawie wgranych dokumentów.",
                color: "text-green-500",
                bg: "bg-green-50",
              },
            ].map(({ icon: Icon, title, desc, color, bg }) => (
              <Card key={title}>
                <CardContent className="pt-6">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${bg} mb-3`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                  <h3 className="font-semibold mb-2">{title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="mt-6 bg-amber-50/50 border-amber-200">
            <CardContent className="pt-5 pb-5 flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-900 leading-relaxed">
                <strong>Ważna zasada:</strong> Wszystkie materiały generowane przez AI
                są traktowane jako szkice wymagające weryfikacji i zatwierdzenia przez kapłana.
                System wyświetla stosowne zastrzeżenie przy każdym wyniku AI.
                AI nie zastępuje discernmentu duszpasterskiego.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* ── CYTAT 2 ── */}
        <section className="mb-16">
          <Card className="bg-muted/30">
            <CardContent className="pt-8 pb-8 px-8">
              <Quote className="h-6 w-6 text-muted-foreground/50 mb-3" />
              <blockquote className="text-base leading-relaxed mb-4">
                "Pierwszy raz od 12 lat pracy w kancelarii nie musiałam szukać
                dokumentu przez pół godziny. Wpisuję słowo i jest. Mogę też pracować
                zdalnie, gdy jestem chora – system działa na telefonie."
              </blockquote>
              <footer className="text-sm text-muted-foreground">
                <strong className="text-foreground">Irena K.</strong>
                <span className="mx-2">·</span>
                Sekretarka kancelarii parafialnej
              </footer>
            </CardContent>
          </Card>
        </section>

        {/* ── PODSUMOWANIE ── */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight mb-4">Podsumowanie</h2>
          <p className="text-muted-foreground leading-relaxed mb-4">
            Wdrożenie Źródła w parafii pw. Wniebowzięcia NMP zajęło jeden dzień roboczy.
            Po 3 miesiącach użytkowania parafia nie wróciła do papierowego zeszytu – ani jednym
            wpisem. Liczba błędów w intencjach spadła do zera.
          </p>
          <p className="text-muted-foreground leading-relaxed">
            Kluczem do sukcesu okazało się nie samo oprogramowanie, ale to, że system był
            wystarczająco prosty, by sekretarka i wikariusze nauczyli się go sami – w ciągu
            jednego popołudnia. Proboszcz ocenił, że oszczędza tygodniowo około 3 godzin
            czasu administracyjnego, które może przeznaczyć na pracę duszpasterską.
          </p>
        </section>

        <Separator className="mb-12" />

        {/* ── CTA ── */}
        <section className="text-center">
          <h2 className="text-2xl font-bold tracking-tight mb-3">
            Chcesz podobnych rezultatów?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            Zacznij od 30-dniowego okresu próbnego – bez karty kredytowej,
            bez zobowiązań, z pełną funkcjonalnością planu Standard.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button size="lg" className="gap-2" asChild>
              <Link href="/login">
                Wypróbuj bezpłatnie
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <a href="mailto:kontakt@zrodlo.pl">
                Skontaktuj się z nami
              </a>
            </Button>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Masz pytania? Napisz na kontakt@zrodlo.pl – odpowiadamy w ciągu 24 godzin.
          </p>
        </section>
      </article>

      {/* ── FOOTER ── */}
      <footer className="border-t py-8 px-6 bg-muted/20">
        <div className="mx-auto max-w-4xl flex flex-col md:flex-row items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs">
              Ź
            </div>
            <span className="text-sm font-semibold">Źródło</span>
          </Link>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Źródło · Cyfrowa kancelaria parafialna
          </p>
        </div>
      </footer>
    </div>
  );
}
