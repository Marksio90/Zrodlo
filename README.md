# Źródło

Inteligentny system wspierający pracę parafii, proboszczów, wikariuszy i wspólnot parafialnych.

> **AI wspiera człowieka – nie zastępuje kapłana.**

## Zasady systemu

1. AI wspiera człowieka
2. AI nie podejmuje decyzji
3. AI nie wymyśla danych
4. Wszystkie dane są audytowalne
5. Każda treść AI wymaga zatwierdzenia przez kapłana

---

## Uruchomienie lokalne

### Wymagania

- Docker Engine >= 24
- Docker Compose >= 2.20
- 8 GB RAM (Ollama wymaga min. 4 GB)

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone <repo-url> && cd Zrodlo

# 2. Skopiuj konfigurację
cp .env.example .env

# 3. Uruchom wszystkie serwisy
docker compose up -d

# 4. (Jednorazowo) Pobierz model językowy
docker compose exec ollama ollama pull gemma2:2b

# 5. Sprawdź status
make health
```

Po uruchomieniu:
- **Aplikacja:** http://localhost
- **API (docs):** http://localhost/api/docs
- **MinIO Console:** http://localhost:9001
- **Health check:** http://localhost/health

---

## Funkcje MVP

| Modul | Opis |
|---|---|
| **Intencje mszalne** | Rejestracja, potwierdzanie i zarządzanie intencjami |
| **Dokumenty** | Metryki, zaswiadczenia, pisma i ogloszenia |
| **Wspolnoty** | Grupy parafialne z lista czlonkow |
| **Kalendarz** | Planowanie wydarzen i uroczystosci |
| **Wsparcie AI** | Przygotowanie homilii, drafty dokumentow |

---

## Architektura

```
Nginx :80
 ├── Frontend (Next.js) :3000
 └── Backend (FastAPI) :8000 /api/*
      ├── PostgreSQL (dane)
      ├── Redis (cache)
      ├── Qdrant (wektory)
      ├── MinIO (pliki)
      ├── Ollama (model lokalny)
      └── Worker (indeksowanie)
```

### Stack technologiczny

**Frontend:** Next.js 14 · TypeScript · Tailwind CSS · shadcn/ui · TanStack Query

**Backend:** FastAPI · SQLAlchemy async · Alembic · Pydantic v2

**Infrastruktura:** PostgreSQL 16 · Redis 7 · Qdrant · MinIO · Ollama · Docker Compose

---

## Komendy

```bash
make up              # Uruchom wszystkie serwisy
make down            # Zatrzymaj serwisy
make logs            # Logi wszystkich serwisow
make health          # Sprawdz stan serwisow
make migrate         # Uruchom migracje bazy danych
make pull-model      # Pobierz model Ollama (domyslnie: gemma2:2b)
make clean           # Usun kontenery i wolumeny
```

### Zmiana modelu AI

```bash
# W .env ustaw:
OLLAMA_MODEL=llama3.2:3b

# Pobierz model:
make pull-model MODEL=llama3.2:3b

# Restartuj backend:
docker compose restart backend
```

Sprawdzone modele z jezykiem polskim:
- gemma2:2b  -- szybki, 2B parametrow (domyslny)
- llama3.2:3b -- lepsza jakosc
- mistral:7b  -- najlepsza jakosc (wymaga 8 GB RAM)

---

## Struktura projektu

```
Zrodlo/
├── apps/
│   ├── frontend/          # Next.js
│   ├── backend/           # FastAPI
│   └── worker/            # ARQ worker (indeksowanie)
├── infra/
│   ├── nginx/             # Reverse proxy
│   └── postgres/          # Inicjalizacja bazy
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## API

Dokumentacja API dostepna po uruchomieniu pod: http://localhost/api/docs

Glowne endpointy:
- GET/POST /intencje
- GET/POST /dokumenty
- GET/POST /wspolnoty
- GET/POST /kalendarz
- POST /ai/homilia
- POST /ai/dokument
- GET /health

---

## Bezpieczenstwo i prywatnosc

- Dane parafialne nie opuszczaja serwera (Ollama dziala lokalnie)
- Brak zewnetrznych API AI – pelna kontrola nad danymi
- Dokumenty przechowywane w MinIO (obiektowa baza plikow)
- Audytowalnosc: kazdy rekord ma created_at i updated_at

---

Zrodlo – odzyskaj czas dla tego, co wazne.