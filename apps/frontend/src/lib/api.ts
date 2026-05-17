import axios from "axios";
import { getToken, clearToken } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    const message =
      error.response?.data?.detail ?? error.message ?? "Nieznany błąd";
    return Promise.reject(new Error(String(message)));
  }
);

// --- Auth ---
export const authApi = {
  login: (email: string, haslo: string) =>
    apiClient.post("/auth/token", { email, haslo }).then((r) => r.data),
  mnie: () => apiClient.get("/auth/mnie").then((r) => r.data),
};

// --- Intencje ---
export const intencjeApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/intencje", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/intencje/${id}`).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/intencje", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/intencje/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/intencje/${id}`),
  potwierdz: (id: string) =>
    apiClient.post(`/intencje/${id}/potwierdz`).then((r) => r.data),
};

export const liturgieApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/intencje/liturgie", { params }).then((r) => r.data),
  create: (data: unknown) =>
    apiClient.post("/intencje/liturgie", data).then((r) => r.data),
};

// --- Dokumenty ---
export const dokumentyApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/dokumenty", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/dokumenty/${id}`).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/dokumenty", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/dokumenty/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/dokumenty/${id}`),
  downloadUrl: (id: string) =>
    apiClient.get(`/dokumenty/${id}/pobierz`).then((r) => r.data),
  zatwierdz: (id: string) =>
    apiClient.post(`/dokumenty/${id}/zatwierdz`).then((r) => r.data),
};

// --- Wspólnoty ---
export const wspolnotyApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/wspolnoty", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/wspolnoty/${id}`).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/wspolnoty", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/wspolnoty/${id}`),
  listCzlonkow: (id: string) =>
    apiClient.get(`/wspolnoty/${id}/czlonkowie`).then((r) => r.data),
  addCzlonek: (id: string, data: unknown) =>
    apiClient.post(`/wspolnoty/${id}/czlonkowie`, data).then((r) => r.data),
};

// --- Kalendarz ---
export const kalendarzeApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/kalendarz", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/kalendarz/${id}`).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/kalendarz", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/kalendarz/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/kalendarz/${id}`),
};

// --- Powiadomienia ---
export const powiadomieniaApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/powiadomienia", { params }).then((r) => r.data),
  countUnread: () =>
    apiClient.get("/powiadomienia/liczba-nieprzeczytanych").then((r) => r.data),
  markRead: (id: string) =>
    apiClient.post(`/powiadomienia/${id}/przeczytaj`).then((r) => r.data),
  markAllRead: () => apiClient.post("/powiadomienia/przeczytaj-wszystkie"),
};

// --- AI ---
export const aiApi = {
  homilia: (data: unknown) => apiClient.post("/ai/homilia", data).then((r) => r.data),
  dokument: (data: unknown) => apiClient.post("/ai/dokument", data).then((r) => r.data),
  modele: () => apiClient.get("/ai/modele").then((r) => r.data),
};

// --- Asystent ---
export const asystentApi = {
  listRozmow: () => apiClient.get("/asystent/rozmowy").then((r) => r.data),
  createRozmowa: (tytul?: string) =>
    apiClient.post("/asystent/rozmowy", { tytul: tytul ?? "Nowa rozmowa" }).then((r) => r.data),
  deleteRozmowa: (id: string) => apiClient.delete(`/asystent/rozmowy/${id}`),
  listWiadomosci: (rozmowaId: string) =>
    apiClient.get(`/asystent/rozmowy/${rozmowaId}/wiadomosci`).then((r) => r.data),
  wyslij: (rozmowaId: string, tresc: string) =>
    apiClient
      .post(`/asystent/rozmowy/${rozmowaId}/wiadomosci`, { tresc })
      .then((r) => r.data),
};

// --- Komunikacja / Ogłoszenia ---
export const komunikacjaApi = {
  generuj: (data: unknown) =>
    apiClient.post("/komunikacja/generuj", data).then((r) => r.data),
};

// --- Homilia ---
export const homiliaApi = {
  generujInspiracje: (data: unknown) =>
    apiClient.post("/homilia/inspiracje", data).then((r) => r.data),
};

// --- Health ---
export const healthApi = {
  check: () => apiClient.get("/health").then((r) => r.data),
};
