/**
 * Centralne schematy Zod dla formularzy frontendowych.
 */
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Podaj prawidłowy adres e-mail"),
  haslo: z.string().min(1, "Hasło jest wymagane"),
});

export const resetWyslijSchema = z.object({
  email: z.string().email("Podaj prawidłowy adres e-mail"),
});

export const resetZmienSchema = z
  .object({
    nowe_haslo: z.string().min(8, "Hasło musi mieć co najmniej 8 znaków").max(200),
    powtorz_haslo: z.string().min(1, "Powtórz hasło"),
  })
  .refine((d) => d.nowe_haslo === d.powtorz_haslo, {
    path: ["powtorz_haslo"],
    message: "Hasła nie są identyczne",
  });

export const aktywujKontoSchema = z
  .object({
    imie: z.string().min(2, "Minimum 2 znaki").max(100),
    nazwisko: z.string().min(2, "Minimum 2 znaki").max(100),
    haslo: z.string().min(8, "Hasło musi mieć co najmniej 8 znaków").max(200),
    powtorz_haslo: z.string().min(1, "Powtórz hasło"),
  })
  .refine((d) => d.haslo === d.powtorz_haslo, {
    path: ["powtorz_haslo"],
    message: "Hasła nie są identyczne",
  });

export const zaproszenieSchema = z.object({
  email: z.string().email("Podaj prawidłowy adres e-mail"),
  rola: z.enum(["proboszcz", "wikariusz", "parafianin", "admin"]),
});

export type LoginForm = z.infer<typeof loginSchema>;
export type ResetWyslijForm = z.infer<typeof resetWyslijSchema>;
export type ResetZmienForm = z.infer<typeof resetZmienSchema>;
export type AktywujKontoForm = z.infer<typeof aktywujKontoSchema>;
export type ZaproszenieForm = z.infer<typeof zaproszenieSchema>;
