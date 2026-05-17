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
- 4 GB RAM
- Klucz API OpenAI (`OPENAI_API_KEY`)

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone <repo-url> && cd Zrodlo

# 2. Skopiuj konfigurację i uzupełnij OPENAI_API_KEY
cp .env.example .env

# 3. Uruchom wszystkie serwisy
docker compose up -d

# 4. Sprawdź status
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
| **Archiwum OCR** | Upload PDF/JPG/PNG z automatyczną klasyfikacją AI |
| **Wspolnoty** | Grupy parafialne z lista czlonkow |
| **Kalendarz** | Planowanie wydarzen i uroczystosci |
| **Ogłoszenia** | Generowanie ogłoszeń w 3 stylach × 3 kanały (WWW/FB/SMS) |
| **Homilie** | Inspiracje homiletyczne w 3 wariantach z cytatami świętych i KKK |
| **Asystent** | Wieloturowy czat RAG z bazą wiedzy parafii |
| **Baza Wiedzy** | Notatki z embeddingami i wyszukiwaniem semantycznym |
| **Wsparcie AI** | Przygotowanie dokumentów i szkiców |

---

## Architektura

```
Nginx :80
 ├── Frontend (Next.js) :3000
 └── Backend (FastAPI) :8000 /api/*
      ├── PostgreSQL (dane)
      ├── Redis (cache)
      ├── Qdrant (wektory semantyczne)
      ├── MinIO (pliki)
      └── Worker (indeksowanie)
```

### Stack technologiczny

**Frontend:** Next.js 14 · TypeScript · Tailwind CSS · shadcn/ui · TanStack Query

**Backend:** FastAPI · SQLAlchemy async · Alembic · Pydantic v2

**AI:** OpenAI GPT-4o / GPT-4o-mini · text-embedding-3-small · Vision API

**Infrastruktura:** PostgreSQL 16 · Redis 7 · Qdrant · MinIO · Docker Compose

---

## Komendy

```bash
make up              # Uruchom wszystkie serwisy
make down            # Zatrzymaj serwisy
make logs            # Logi wszystkich serwisow
make health          # Sprawdz stan serwisow
make migrate         # Uruchom migracje bazy danych
make clean           # Usun kontenery i wolumeny
```

### Modele AI

System korzysta wyłącznie z OpenAI API. Kaskada modeli:

| Model | Zastosowanie |
|-------|-------------|
| `gpt-4o-mini` | Komunikacja, klasyfikacja, ogłoszenia, asystent |
| `gpt-4o` | Homilie, OCR obrazów, prawo kanoniczne |
| `text-embedding-3-small` | Embeddingi (1536 dim) – wyszukiwanie semantyczne |

Konfiguracja w `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_SIMPLE=gpt-4o-mini
OPENAI_MODEL_COMPLEX=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

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
- `GET/POST /intencje`
- `GET/POST /dokumenty`
- `GET/POST /wspolnoty`
- `GET/POST /kalendarz`
- `POST /archiwum/upload`
- `POST /wiedza/szukaj`
- `POST /homilia/inspiracje`
- `POST /komunikacja/generuj`
- `POST /asystent/rozmowy/{id}/wiadomosci`
- `GET /health`

---

## Bezpieczenstwo i prywatnosc

- Komunikacja z OpenAI API szyfrowana (TLS)
- Dane parafialne przechowywane lokalnie (PostgreSQL, MinIO)
- Klucz API przechowywany wyłącznie w zmiennych środowiskowych
- Dokumenty przechowywane w MinIO (obiektowa baza plikow)
- Audytowalnosc: kazdy rekord ma `created_at`, `updated_at` i log audytu

---

Zrodlo – odzyskaj czas dla tego, co wazne.
