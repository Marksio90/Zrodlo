# UMOWA POWIERZENIA PRZETWARZANIA DANYCH OSOBOWYCH

**na podstawie art. 28 Rozporządzenia Parlamentu Europejskiego i Rady (UE) 2016/679
z dnia 27 kwietnia 2016 r. (RODO)**

**Wersja: 1.0 | Data wejścia w życie: 2025-06-01**

---

## § 1. STRONY UMOWY

**Administrator danych osobowych** (dalej: **Administrator**):

Parafia korzystająca z systemu Źródło, reprezentowana przez jej proboszcza, zwana dalej
„Administratorem" — jako podmiot samodzielnie ustalający cele i sposoby przetwarzania danych
swoich wiernych, pracowników i wolontariuszy.

**Podmiot przetwarzający** (dalej: **Podmiot przetwarzający**):

[NAZWA SPÓŁKI / IMIĘ NAZWISKO PROWADZĄCEGO DZIAŁALNOŚĆ]
ul. [ADRES], [KOD POCZTOWY] [MIASTO]
NIP: [NIP], REGON: [REGON]
adres e-mail: rodo@zrodlo.app

---

## § 2. PRZEDMIOT I CEL UMOWY

1. Podmiot przetwarzający zobowiązuje się do przetwarzania danych osobowych wyłącznie
   w imieniu Administratora i zgodnie z jego udokumentowanymi poleceniami, w celu
   świadczenia usługi systemu informatycznego „Źródło" (dalej: **System**).

2. Przetwarzanie odbywa się wyłącznie na potrzeby:
   a) prowadzenia ewidencji parafialnej (dane wiernych, sakramenty);
   b) zarządzania intencjami mszalnymi;
   c) obsługi dokumentów kancelaryjnych (metryki, zaświadczenia);
   d) komunikacji z wiernymi (ogłoszenia, powiadomienia);
   e) administracji kadrowej (pracownicy, wolontariusze);
   f) wsparcia przez sztuczną inteligencję (asystent, generowanie dokumentów).

3. Podmiot przetwarzający nie przetwarza danych w celach własnych ani nie udostępnia
   ich innym podmiotom bez zgody Administratora, za wyjątkiem sytuacji wymaganych
   przez bezwzględnie obowiązujące przepisy prawa.

---

## § 3. KATEGORIE DANYCH I OSÓB, KTÓRYCH DANE DOTYCZĄ

**Kategorie osób:**
- wierni (parafianie, ochrzczeni, bierzmowani, osoby zawierające sakrament małżeństwa);
- pracownicy i wolontariusze parafii;
- użytkownicy systemu (kapłani, administratorzy).

**Kategorie danych zwykłych:**
- imię i nazwisko, data i miejsce urodzenia;
- adres zamieszkania, numer telefonu, adres e-mail;
- numer PESEL (w dokumentach urzędowych);
- daty przyjętych sakramentów;
- przynależność do wspólnot i grup parafialnych.

**Kategorie danych szczególnych (art. 9 RODO):**
- dane dotyczące przynależności religijnej (jako naturalna konsekwencja prowadzenia
  ewidencji parafialnej — przetwarzanie na podstawie art. 9 ust. 2 lit. d RODO
  w zakresie działalności organizacji o charakterze religijnym).

---

## § 4. CZAS TRWANIA PRZETWARZANIA

1. Niniejsza umowa obowiązuje przez czas trwania Umowy Głównej o świadczenie usług
   systemu Źródło.

2. Po wygaśnięciu lub rozwiązaniu Umowy Głównej Podmiot przetwarzający, na wybór
   Administratora:
   a) zwraca wszelkie dane osobowe w formacie CSV/JSON/SQL (eksport dostępny przez
      API systemu przez 30 dni od zakończenia umowy); lub
   b) usuwa dane ze swoich systemów w ciągu 30 dni od zakończenia umowy,
      potwierdzając ten fakt pisemnie.

3. Usunięcie nie dotyczy danych, do których przechowywania Podmiot przetwarzający
   jest zobowiązany przepisami prawa (np. dokumentacja finansowa — max. 5 lat).

---

## § 5. OBOWIĄZKI PODMIOTU PRZETWARZAJĄCEGO

Podmiot przetwarzający zobowiązuje się do:

1. **Przetwarzania danych wyłącznie na udokumentowane polecenie Administratora** —
   wszelkie konfiguracje dokonane przez Administratora w Systemie stanowią takie polecenia.

2. **Zapewnienia poufności** — osoby upoważnione do przetwarzania danych zobowiązane są
   do zachowania tajemnicy (umowy o poufności lub wynikającej z przepisów prawa).

3. **Stosowania odpowiednich środków technicznych i organizacyjnych** (§ 6).

4. **Niepowierzania danych dalszym podmiotom przetwarzającym** bez uprzedniej zgody
   Administratora, z zastrzeżeniem § 7.

5. **Pomocy Administratorowi** w wykonywaniu obowiązków wobec osób, których dane dotyczą
   (dostęp, sprostowanie, usunięcie, przenoszenie, sprzeciw, ograniczenie przetwarzania).

6. **Pomocy Administratorowi** w realizacji obowiązków wynikających z art. 32–36 RODO
   (bezpieczeństwo, naruszenia, DPIA).

7. **Niezwłocznego powiadamiania Administratora** (nie później niż 24 godziny po wykryciu)
   o wszelkich naruszeniach ochrony danych mogących skutkować naruszeniem praw lub wolności
   osób fizycznych.

8. **Udostępniania Administratorowi wszelkich informacji** niezbędnych do wykazania
   spełnienia obowiązków oraz umożliwienia i uczestnictwa w audytach.

9. **Przechowywania danych na serwerach w Europejskim Obszarze Gospodarczym** (EOG).
   Transfer poza EOG możliwy wyłącznie na podstawie odpowiedniej gwarancji (art. 46 RODO)
   i po poinformowaniu Administratora.

---

## § 6. ŚRODKI BEZPIECZEŃSTWA TECHNICZNE I ORGANIZACYJNE

Podmiot przetwarzający stosuje co najmniej następujące środki:

**Techniczne:**
- szyfrowanie danych w tranzycie (TLS 1.2+) i w spoczynku (szyfrowanie dysku);
- pseudonimizacja tokenów sesji i haseł (bcrypt);
- izolacja danych parafii w architekturze multi-tenant (identyfikator `parafia_id`
  weryfikowany przy każdym zapytaniu);
- automatyczne kopie zapasowe (PostgreSQL, MinIO, Qdrant) przechowywane przez 30 dni;
- monitorowanie dostępu i logowanie zdarzeń (audit log);
- automatyczna aktualizacja zależności z oceną podatności.

**Organizacyjne:**
- dostęp do danych produkcyjnych wyłącznie dla upoważnionych pracowników
  na zasadzie minimalnych uprawnień;
- szkolenia z ochrony danych dla personelu technicznego;
- procedura zgłaszania naruszeń;
- regularne testy bezpieczeństwa i przeglądy kodu.

---

## § 7. DALSZE PODMIOTY PRZETWARZAJĄCE (PODPRZETWARZAJĄCY)

1. Administrator niniejszym wyraża ogólną zgodę na korzystanie z podprzetwarzających
   wymienionych poniżej. Podmiot przetwarzający powiadomi Administratora z 14-dniowym
   wyprzedzeniem o zamiarze dodania lub zmiany podprzetwarzającego.

2. **Aktualna lista podprzetwarzających:**

   | Podmiot | Siedziba | Zakres | Podstawa transferu |
   |---------|----------|--------|-------------------|
   | Hetzner Online GmbH | Niemcy (EOG) | Infrastruktura serwerowa (VPS) | EOG |
   | OpenAI, L.L.C. | USA | Modele językowe AI | SCC (art. 46 ust. 2 lit. c) |

3. Podmiot przetwarzający zobowiązuje się nałożyć na podprzetwarzających obowiązki
   ochrony danych równoważne niniejszej umowie.

4. Podmiot przetwarzający ponosi pełną odpowiedzialność za działania podprzetwarzających.

---

## § 8. PRAWA I OBOWIĄZKI ADMINISTRATORA

Administrator zobowiązuje się do:

1. Przetwarzania danych wyłącznie na podstawie ważnej podstawy prawnej (art. 6 RODO)
   i we własnym zakresie spełnienia obowiązku informacyjnego wobec wiernych.

2. Zapewnienia, że dane wprowadzane do Systemu są poprawne i aktualne.

3. Zarządzania uprawnieniami użytkowników Systemu (nadawanie, odbieranie dostępu).

4. Stosowania silnych haseł i nieudostępniania danych dostępowych osobom nieupoważnionym.

5. Niezwłocznego informowania Podmiotu przetwarzającego o wszelkich zmianach mogących
   wpłynąć na bezpieczeństwo przetwarzania.

---

## § 9. AUDYT

1. Administrator ma prawo do przeprowadzenia audytu (samodzielnie lub przez upoważnionego
   audytora) nie częściej niż raz w roku, po 14-dniowym powiadomieniu.

2. Podmiot przetwarzający udostępni niezbędną dokumentację techniczną i organizacyjną.

3. Koszty audytu ponosi Administrator, chyba że audyt ujawni naruszenia — wówczas koszty
   pokrywa Podmiot przetwarzający.

---

## § 10. ODPOWIEDZIALNOŚĆ

1. Podmiot przetwarzający odpowiada za szkody wyrządzone przetwarzaniem niezgodnym
   z niniejszą umową lub RODO, chyba że udowodni, że nie ponosi winy za zdarzenie.

2. Administrator odpowiada za to, że cele i sposoby przetwarzania są zgodne z RODO
   oraz że dane wprowadzane do Systemu są przetwarzane na właściwej podstawie prawnej.

3. Odpowiedzialność Podmiotu przetwarzającego z tytułu tej umowy ograniczona jest do
   wysokości wynagrodzenia netto zapłaconego za 12 miesięcy poprzedzających zdarzenie,
   z wyjątkiem szkód wyrządzonych umyślnie.

---

## § 11. POSTANOWIENIA KOŃCOWE

1. Wszelkie zmiany umowy wymagają formy pisemnej (w tym elektronicznej z kwalifikowanym
   podpisem elektronicznym) pod rygorem nieważności.

2. W sprawach nieuregulowanych stosuje się przepisy RODO oraz prawa polskiego.

3. Spory rozstrzygane są przez sąd właściwy dla siedziby Podmiotu przetwarzającego.

4. Umowa wchodzi w życie z chwilą zaakceptowania przez Administratora (proboszcza)
   w Systemie Źródło, co jest równoznaczne z zawarciem umowy w formie elektronicznej.

---

**Akceptacja elektroniczna w systemie Źródło jest równoznaczna z zawarciem umowy
w formie dokumentowej (art. 772 Kodeksu cywilnego).**

---

*Wersja dokumentu: 1.0 | Ostatnia aktualizacja: 2025-06-01*
*Aktualna wersja zawsze dostępna pod adresem: [DOMENA]/rodo/umowa*
