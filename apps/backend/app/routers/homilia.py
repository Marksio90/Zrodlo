"""Inspiracje Homilii – AI generuje 3 warianty z cytatami, KKK, kontekstem i pytaniami."""
import json
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import AI, CurrentUser

log = structlog.get_logger()

router = APIRouter(prefix="/homilia", tags=["Homilia – Inspiracje"])

# ---------------------------------------------------------------------------
# System prompt homiletyczny
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_HOMILETYCZNY = """Jesteś ekspertem od homiletyki katolickiej. Pomagasz kapłanom w przygotowaniu inspiracji do homilii.

Zasady:
- Odpowiadasz WYŁĄCZNIE po polsku
- Cytaty świętych muszą być autentyczne i przypisane konkretnemu autorowi
- Numery paragrafów Katechizmu Kościoła Katolickiego (KKK) muszą być dokładne
- Treść teologiczna w pełni zgodna z Magisterium Kościoła katolickiego
- Generujesz INSPIRACJE i SZKICE – nie gotowe teksty do głoszenia bez przemyślenia
- Kontekst historyczny oparty na faktach biblijnych lub historii Kościoła
- Styl: głęboki, pastoralny, dostosowany do wskazanej grupy odbiorców
- Pytania do refleksji muszą być konkretne i życiowe, nie abstrakcyjne
- Odpowiadasz TYLKO jako JSON – żadnych innych komentarzy"""

# ---------------------------------------------------------------------------
# Schematy wejściowe
# ---------------------------------------------------------------------------

class HomiliaInspiracjeRequest(BaseModel):
    ewangelia: str = Field(..., min_length=10, description="Tekst lub opis perykopy ewangelicznej")
    swieto: str | None = Field(None, description="Nazwa święta lub uroczystości")
    okres_liturgiczny: str = Field("Zwykły", description="Adwent / Boże Narodzenie / Wielki Post / Triduum Paschalne / Wielkanoc / Zwykły")
    patron_dnia: str | None = Field(None, description="Patron lub patronka dnia")
    grupa_odbiorcow: str = Field("parafianie", description="Np. dzieci, młodzież, małżeństwa, seniorzy, parafianie")
    dodatkowe_wskazowki: str | None = Field(None, max_length=500, description="Uwagi duszpasterza")


# ---------------------------------------------------------------------------
# Schematy odpowiedzi
# ---------------------------------------------------------------------------

class CytatSwietego(BaseModel):
    autor: str
    tresc: str


class OdniesieniKKK(BaseModel):
    numer: str
    tresc: str


class WariantHomilii(BaseModel):
    dlugosc_min: int
    tytul: str
    mysl_przewodnia: str
    struktura: list[str]
    cytaty_swietych: list[CytatSwietego]
    katechizm_kk: list[OdniesieniKKK]
    kontekst_historyczny: str
    praktyczne_zastosowanie: str
    pytania_do_refleksji: list[str]
    pelny_szkic: str


class HomiliaInspiracjeResponse(BaseModel):
    wariant_krotki: WariantHomilii
    wariant_sredni: WariantHomilii
    wariant_rozbudowany: WariantHomilii
    zastrzezenie: str


ZASTRZEZENIE = (
    "Inspiracje wygenerowane przez AI. Wymagają przemyślenia, weryfikacji teologicznej "
    "i osobistego przepracowania przez kapłana. AI nie zastępuje przygotowania duchowego "
    "ani discernmentu duszpasterskiego. Cytaty i numery KKK należy zweryfikować."
)

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/inspiracje", response_model=HomiliaInspiracjeResponse)
async def generuj_inspiracje(
    req: HomiliaInspiracjeRequest,
    ai: AI,
    current_user: CurrentUser,
):
    prompt = _buduj_prompt(req)
    log.info(
        "homilia_generate",
        user_id=str(current_user.id),
        season=req.okres_liturgiczny,
        audience=req.grupa_odbiorcow,
    )

    try:
        response = await ai._client.chat.completions.create(
            model=ai._model_zlozony,  # gpt-4o – złożona treść teologiczna w JSON
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_HOMILETYCZNY},
                {"role": "user", "content": prompt},
            ],
            temperature=0.72,
            max_tokens=4500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error("homilia_json_parse_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd parsowania odpowiedzi AI")
    except Exception as e:
        log.error("homilia_ai_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"Serwis AI niedostępny: {e}")

    try:
        warianty = _parsuj_warianty(data)
    except Exception as e:
        log.error("homilia_schema_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd struktury odpowiedzi AI")

    log.info("homilia_generated", user_id=str(current_user.id))
    return HomiliaInspiracjeResponse(**warianty, zastrzezenie=ZASTRZEZENIE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _buduj_prompt(req: HomiliaInspiracjeRequest) -> str:
    wiersze = [
        "Przygotuj inspiracje homiletyczne na podstawie poniższych danych liturgicznych.",
        "",
        f"EWANGELIA / PERYKOPA: {req.ewangelia}",
    ]
    if req.swieto:
        wiersze.append(f"ŚWIĘTO / UROCZYSTOŚĆ: {req.swieto}")
    wiersze.append(f"OKRES LITURGICZNY: {req.okres_liturgiczny}")
    if req.patron_dnia:
        wiersze.append(f"PATRON DNIA: {req.patron_dnia}")
    wiersze.append(f"GRUPA ODBIORCÓW: {req.grupa_odbiorcow}")
    if req.dodatkowe_wskazowki:
        wiersze.append(f"WSKAZÓWKI KAPŁANA: {req.dodatkowe_wskazowki}")

    wiersze += [
        "",
        "Wygeneruj JSON z dokładnie trzema wariantami inspiracji:",
        "",
        "wariant_krotki (~5 min): prosta struktura, 1 główny punkt, 1 cytat świętego, 1 KKK",
        "  pelny_szkic: 150-200 słów",
        "",
        "wariant_sredni (~10 min): 3 punkty, 2 cytaty świętych, 2 KKK",
        "  pelny_szkic: 350-450 słów",
        "",
        "wariant_rozbudowany (~20 min): 4-5 punktów, 3+ cytaty świętych, 3+ KKK, głębszy kontekst",
        "  pelny_szkic: 750-900 słów",
        "",
        "Każdy wariant ma pola:",
        "  dlugosc_min (int), tytul, mysl_przewodnia,",
        "  struktura (lista punktów z czasem np. 'Wstęp (1 min): ...'),",
        "  cytaty_swietych (lista {autor, tresc}),",
        "  katechizm_kk (lista {numer: 'KKK XXXX', tresc}),",
        "  kontekst_historyczny,",
        "  praktyczne_zastosowanie (konkretne dla podanej grupy odbiorców),",
        "  pytania_do_refleksji (lista 3-5 pytań),",
        "  pelny_szkic",
        "",
        "Odpowiedz TYLKO jako JSON. Klucze: wariant_krotki, wariant_sredni, wariant_rozbudowany.",
    ]
    return "\n".join(wiersze)


def _parsuj_warianty(data: dict) -> dict:
    def _wariant(raw: dict) -> WariantHomilii:
        cytaty = [
            CytatSwietego(autor=c.get("autor", ""), tresc=c.get("tresc", ""))
            for c in (raw.get("cytaty_swietych") or [])
        ]
        kkk = [
            OdniesieniKKK(numer=k.get("numer", ""), tresc=k.get("tresc", ""))
            for k in (raw.get("katechizm_kk") or [])
        ]
        return WariantHomilii(
            dlugosc_min=int(raw.get("dlugosc_min", 0)),
            tytul=str(raw.get("tytul", "")),
            mysl_przewodnia=str(raw.get("mysl_przewodnia", "")),
            struktura=[str(p) for p in (raw.get("struktura") or [])],
            cytaty_swietych=cytaty,
            katechizm_kk=kkk,
            kontekst_historyczny=str(raw.get("kontekst_historyczny", "")),
            praktyczne_zastosowanie=str(raw.get("praktyczne_zastosowanie", "")),
            pytania_do_refleksji=[str(q) for q in (raw.get("pytania_do_refleksji") or [])],
            pelny_szkic=str(raw.get("pelny_szkic", "")),
        )

    return {
        "wariant_krotki": _wariant(data.get("wariant_krotki") or {}),
        "wariant_sredni": _wariant(data.get("wariant_sredni") or {}),
        "wariant_rozbudowany": _wariant(data.get("wariant_rozbudowany") or {}),
    }
