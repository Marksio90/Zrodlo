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

export const ETYKIETY_STATUSOW: Record<StatusDokumentu, string> = {
  szkic: "Szkic",
  do_zatwierdzenia: "Do zatwierdzenia",
  zatwierdzony: "Zatwierdzony",
  wydany: "Wydany",
  anulowany: "Anulowany",
};
