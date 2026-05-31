import axios from "axios";
import { getToken, setToken, clearToken } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
  withCredentials: true, // send httpOnly refresh_token cookie
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Silent token refresh on 401
let isRefreshing = false;
let pendingQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function drainQueue(token: string | null, error: unknown) {
  pendingQueue.forEach((p) => (token ? p.resolve(token) : p.reject(error)));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (r) => r,
  async (error) => {
    const originalRequest = error.config;

    // Only attempt refresh once per request; skip refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !originalRequest._retried &&
      !originalRequest.url?.includes("/auth/refresh") &&
      !originalRequest.url?.includes("/auth/token")
    ) {
      originalRequest._retried = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      isRefreshing = true;
      try {
        const { data } = await apiClient.post<{ access_token: string }>("/auth/refresh");
        setToken(data.access_token);
        drainQueue(data.access_token, null);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        drainQueue(null, refreshError);
        clearToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
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
  refresh: () => apiClient.post("/auth/refresh").then((r) => r.data),
  logout: () => apiClient.post("/auth/logout"),
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

// --- Archiwum / OCR ---
export const archiwumApi = {
  upload: (plik: File, notatki?: string, onProgress?: (p: number) => void) => {
    const fd = new FormData();
    fd.append("plik", plik);
    if (notatki) fd.append("notatki", notatki);
    return apiClient
      .post("/archiwum/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 60));
        },
        timeout: 120_000,
      })
      .then((r) => r.data);
  },
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/archiwum/", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/archiwum/${id}`).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/archiwum/${id}`, data).then((r) => r.data),
  archiwizuj: (id: string) =>
    apiClient.post(`/archiwum/${id}/archiwizuj`).then((r) => r.data),
  ponowOCR: (id: string) =>
    apiClient.post(`/archiwum/${id}/ponow-ocr`).then((r) => r.data),
  pobierz: (id: string) => apiClient.get(`/archiwum/${id}/pobierz`).then((r) => r.data),
  usun: (id: string) => apiClient.delete(`/archiwum/${id}`),
};

// --- Wiedza ---
export const wiedzaApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/wiedza", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get(`/wiedza/${id}`).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/wiedza", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/wiedza/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/wiedza/${id}`),
  szukaj: (data: { pytanie: string; limit?: number }) =>
    apiClient.post("/wiedza/szukaj", data).then((r) => r.data),
  embed: (id: string) => apiClient.post(`/wiedza/${id}/embed`).then((r) => r.data),
  embedWszystkie: () => apiClient.post("/wiedza/embed-wszystkie").then((r) => r.data),
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

// --- Demo ---
export const demoApi = {
  seed: () => apiClient.post("/demo/seed").then((r) => r.data),
};

// --- Health ---
export const healthApi = {
  check: () => apiClient.get("/health").then((r) => r.data),
};

// --- RODO ---
export const rodoApi = {
  umowa: () => apiClient.get("/rodo/umowa").then((r) => r.data),
  status: () => apiClient.get("/rodo/status").then((r) => r.data),
  akceptuj: (wersja = "1.0") =>
    apiClient.post("/rodo/akceptuj", { wersja }).then((r) => r.data),
  historia: () => apiClient.get("/rodo/historia").then((r) => r.data),
};

// --- Subskrypcja ---
export const subskrypcjaApi = {
  plany: () => apiClient.get("/subskrypcja/plany").then((r) => r.data),
  status: () => apiClient.get("/subskrypcja/status").then((r) => r.data),
  trial: () => apiClient.post("/subskrypcja/trial", {}).then((r) => r.data),
};

// --- Onboarding ---
export const onboardingApi = {
  status: () => apiClient.get("/onboarding/status").then((r) => r.data),
};

// --- Dziennik kancleryjny ---
export const dziennikApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get("/dziennik", { params }).then((r) => r.data),
  create: (data: unknown) => apiClient.post("/dziennik", data).then((r) => r.data),
  get: (id: string) => apiClient.get(`/dziennik/${id}`).then((r) => r.data),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/dziennik/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/dziennik/${id}`),
  statystyki: () => apiClient.get("/dziennik/statystyki").then((r) => r.data),
  exportCsv: (rok?: number) =>
    apiClient.get("/dziennik/export/csv", {
      params: rok ? { rok } : {},
      responseType: "blob",
    }).then((r) => r.data),
};

// --- AI Koszty ---
export const aiKosztyApi = {
  podsumowanie: () => apiClient.get("/ai/koszty/podsumowanie").then((r) => r.data),
  alerty: () => apiClient.get("/ai/koszty/alerty").then((r) => r.data),
  szczegoly: (params?: Record<string, unknown>) =>
    apiClient.get("/ai/koszty/szczegoly", { params }).then((r) => r.data),
};
