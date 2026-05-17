export type TypIntencji =
  | "za_zmarlego"
  | "za_zyjacego"
  | "dziekczynna"
  | "dziekczynno_blogalna"
  | "rocznica_slubu"
  | "w_chorobie"
  | "wypominkowa"
  | "inna";

export type TypMszy =
  | "niedzielna"
  | "powszednia"
  | "pogrzebowa"
  | "slubna"
  | "zaduszna"
  | "okolicznosciowa";

export type TypDokumentu =
  | "metryka_chrztu"
  | "metryka_slubu"
  | "zaswiadczenie_bierzmowania"
  | "zaswiadczenie_komunii"
  | "zaswiadczenie_do_slubu"
  | "odpis_zgonu"
  | "pismo_ogolne"
  | "homilia"
  | "ogloszenia";

export type StatusDokumentu =
  | "szkic"
  | "do_zatwierdzenia"
  | "zatwierdzony"
  | "wydany"
  | "anulowany";

export interface Liturgia {
  id: string;
  data: string;
  godzina: string;
  typ: TypMszy;
  miejsce: string;
  uwagi: string | null;
  created_at: string;
  updated_at: string;
}

export interface Intencja {
  id: string;
  liturgia_id: string | null;
  typ: TypIntencji;
  tresc: string;
  ofiarodawca: string | null;
  kwota: string | null;
  potwierdzona: boolean;
  notatka_wewnetrzna: string | null;
  created_at: string;
  updated_at: string;
}

export interface Dokument {
  id: string;
  typ: TypDokumentu;
  status: StatusDokumentu;
  tytul: string;
  dane: Record<string, unknown>;
  tresc: string | null;
  plik_klucz: string | null;
  wygenerowane_przez_ai: boolean;
  zatwierdzone_przez: string | null;
  created_at: string;
  updated_at: string;
}

export interface Wspolnota {
  id: string;
  nazwa: string;
  opis: string | null;
  opiekun: string | null;
  kontakt_email: string | null;
  kontakt_telefon: string | null;
  aktywna: boolean;
  liczba_czlonkow: number;
  created_at: string;
  updated_at: string;
}

export interface CzlonekWspolnoty {
  id: string;
  wspolnota_id: string;
  imie: string;
  nazwisko: string;
  telefon: string | null;
  email: string | null;
  rola: string | null;
  aktywny: boolean;
  created_at: string;
  updated_at: string;
}

export interface Wydarzenie {
  id: string;
  tytul: string;
  opis: string | null;
  data_od: string;
  data_do: string | null;
  miejsce: string | null;
  wspolnota_id: string | null;
  cykliczne: boolean;
  cykl_opis: string | null;
  kolor: string;
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: "ok" | "degraded";
  timestamp: string;
  services: Record<string, string>;
}

export interface Powiadomienie {
  id: string;
  odbiorca_id: string;
  typ: string;
  tytul: string;
  tresc: string;
  przeczytane: boolean;
  data_przeczytania: string | null;
  referencja_tabela: string | null;
  referencja_id: string | null;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  imie: string;
  nazwisko: string;
  rola: string;
  parafia_id: string | null;
  aktywny: boolean;
}

export const ETYKIETY_INTENCJI: Record<TypIntencji, string> = {
  za_zmarlego: "Za +",
  za_zyjacego: "Za żyjącego",
  dziekczynna: "Dziękczynna",
  dziekczynno_blogalna: "Dziękczynno-błagalna",
  rocznica_slubu: "Rocznica ślubu",
  w_chorobie: "W chorobie",
  wypominkowa: "Wypominkowa",
  inna: "Inna",
};

export const ETYKIETY_DOKUMENTOW: Record<TypDokumentu, string> = {
  metryka_chrztu: "Metryka chrztu",
  metryka_slubu: "Metryka ślubu",
  zaswiadczenie_bierzmowania: "Zaświadczenie bierzmowania",
  zaswiadczenie_komunii: "Zaświadczenie komunii",
  zaswiadczenie_do_slubu: "Zaświadczenie do ślubu",
  odpis_zgonu: "Odpis zgonu",
  pismo_ogolne: "Pismo ogólne",
  homilia: "Homilia",
  ogloszenia: "Ogłoszenia",
};

export const ETYKIETY_TYPY_MSZY: Record<TypMszy, string> = {
  niedzielna: "Msza niedzielna",
  powszednia: "Msza powszednia",
  pogrzebowa: "Msza pogrzebowa",
  slubna: "Msza ślubna",
  zaduszna: "Msza zaduszna",
  okolicznosciowa: "Msza okolicznościowa",
};

export const ETYKIETY_STATUSOW: Record<StatusDokumentu, string> = {
  szkic: "Szkic",
  do_zatwierdzenia: "Do zatwierdzenia",
  zatwierdzony: "Zatwierdzony",
  wydany: "Wydany",
  anulowany: "Anulowany",
};

export interface ZrodloInfo {
  typ: string;
  id: string | null;
  tytul: string;
  fragment: string | null;
  score: number | null;
}

export interface WiadomoscRozmowy {
  id: string;
  rozmowa_id: string;
  rola: "user" | "assistant";
  tresc: string;
  model_uzyty: string | null;
  zrodla: ZrodloInfo[] | null;
  tokens_uzyte: number | null;
  created_at: string;
}

export interface Rozmowa {
  id: string;
  tytul: string;
  created_at: string;
  updated_at: string;
}

// --- Homilia ---

export type OkresLiturgiczny =
  | "Zwykły"
  | "Adwent"
  | "Boże Narodzenie"
  | "Wielki Post"
  | "Triduum Paschalne"
  | "Wielkanoc";

export interface CytatSwietego {
  autor: string;
  tresc: string;
}

export interface OdniesieniKKK {
  numer: string;
  tresc: string;
}

export interface WariantHomilii {
  dlugosc_min: number;
  tytul: string;
  temat_przewodni: string;
  mysl_przewodnia: string;
  struktura: string[];
  cytaty_swietych: CytatSwietego[];
  katechizm_kk: OdniesieniKKK[];
  kontekst_historyczny: string;
  praktyczne_zastosowanie: string;
  pytania_do_refleksji: string[];
  propozycja_zakonczenia: string;
  pelny_szkic: string;
}

export interface HomiliaInspiracjeResponse {
  wariant_krotki: WariantHomilii;
  wariant_sredni: WariantHomilii;
  wariant_rozbudowany: WariantHomilii;
  zastrzezenie: string;
}

// --- Komunikacja / Ogłoszenia ---

export interface WydarzenieOgloszenia {
  tytul: string;
  kiedy: string;
  miejsce?: string;
  opis?: string;
}

export interface IntencjaOgloszenia {
  kiedy: string;
  tresc: string;
}

export interface KanalOgloszenia {
  www: string;
  facebook: string;
  sms: string;
}

export interface OgloszeniaResponse {
  formalne: KanalOgloszenia;
  przyjazne: KanalOgloszenia;
  rodzinne: KanalOgloszenia;
  zastrzezenie: string;
}

// --- Wiedza ---

export type KategoriaWiedzy =
  | "liturgia"
  | "duszpasterstwo"
  | "administracja"
  | "prawo_kanoniczne"
  | "historia_parafii"
  | "katecheza"
  | "inne";

export interface NotatkaWiedzy {
  id: string;
  parafia_id: string | null;
  tytul: string;
  tresc: string;
  kategoria: KategoriaWiedzy;
  tagi: string[];
  publiczna: boolean;
  tworca_id: string | null;
  qdrant_id: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface WynikSzukania {
  id: string;
  tytul: string;
  fragment: string;
  kategoria: string;
  score: number | null;
}

export interface SzukajWiedzyResponse {
  odpowiedz: string;
  wyniki: WynikSzukania[];
  model_uzyty: string;
}

export const ETYKIETY_KATEGORII: Record<KategoriaWiedzy, string> = {
  liturgia: "Liturgia",
  duszpasterstwo: "Duszpasterstwo",
  administracja: "Administracja",
  prawo_kanoniczne: "Prawo kanoniczne",
  historia_parafii: "Historia parafii",
  katecheza: "Katecheza",
  inne: "Inne",
};

// --- Archiwum / OCR ---

export type OcrStatus = "oczekujacy" | "przetwarzanie" | "gotowy" | "blad";

export type TypDokumentuSkan =
  | "metryka_chrztu"
  | "metryka_slubu"
  | "metryka_bierzmowania"
  | "metryka_komunii"
  | "zaswiadczenie"
  | "formularz"
  | "akt_zgonu"
  | "pismo_urzedowe"
  | "korespondencja"
  | "inne";

export interface SkanListItem {
  id: string;
  nazwa_pliku: string;
  typ_pliku: string;
  mime_type: string;
  rozmiar_bajtow: number;
  typ_dokumentu: TypDokumentuSkan;
  jednostka_wystawiajaca: string | null;
  data_wystawienia: string | null;
  osoby: string[];
  tagi: string[];
  zarchiwizowany: boolean;
  ocr_status: OcrStatus;
  created_at: string;
}

export interface SkanRead extends SkanListItem {
  tresc_ocr: string | null;
  dane_kontaktowe: Record<string, string | null>;
  encje: Record<string, unknown>;
  notatki: string | null;
  ocr_blad: string | null;
  updated_at: string;
}
