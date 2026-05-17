const TOKEN_KEY = "zrodlo_token";

export interface CurrentUser {
  id: string;
  email: string;
  imie: string;
  nazwisko: string;
  rola: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getUser(): CurrentUser | null {
  const token = getToken();
  if (!token) return null;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return {
      id: payload.sub ?? "",
      email: payload.email ?? "",
      imie: payload.imie ?? "",
      nazwisko: payload.nazwisko ?? "",
      rola: payload.rola ?? "",
    };
  } catch {
    return null;
  }
}
