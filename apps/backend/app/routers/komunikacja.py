"""Komunikacja Parafialna – AI generuje ogłoszenia w 3 stylach i 3 kanałach."""
import json
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import AI, CurrentUser

log = structlog.get_logger()

router = APIRouter(prefix="/komunikacja", tags=["Komunikacja – Ogłoszenia AI"])

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_KOMUNIKACJA = """Jesteś specjalistą od komunikacji parafialnej. Tworzysz ogłoszenia dla wspólnoty parafialnej.

Zasady ogólne:
- Odpowiadasz WYŁĄCZNIE po polsku
- Treść konkretna, zwięzła i odpowiednia dla wspólnoty katolickiej
- Żadnych zmyślonych danych – opierasz się wyłącznie na dostarczonych informacjach
- Jeśli brakuje danych do danej sekcji – pomijasz ją, nie uzupełniasz domysłami

Styl FORMALNY:
- Język godny i liturgiczny, pełne zdania
- Bez emotikonów
- Nagłówki sekcji w wersji WWW (OGŁOSZENIA PARAFIALNE, INTENCJE, WYDARZENIA)
- Facebook: formalny post, hashtagi #parafia #ogłoszenia na końcu
- SMS: do 160 znaków, kluczowe info, bez skrótów

Styl PRZYJAZNY:
- Ciepły, zapraszający, wspólnotowy
- Umiarkowane emotikony (⛪ 🙏 ✝️ 📅)
- Facebook: wciągający pierwszy akapit, emotikony, hashtagi #parafia #razem #wiara
- SMS: do 160 znaków, ciepło i konkretnie

Styl RODZINNY:
- Serdeczny, prosty, dostępny dla całej rodziny
- Emotikony rodzinne (👨‍👩‍👧 ❤️ 🕊️ 🌟)
- Osobna wzmianka dla dzieci i rodziców w wersji WWW
- Facebook: super zapraszający, emojis, hashtagi #rodzina #wiara #parafia #dzieci
- SMS: do 160 znaków, dla całej rodziny

Format SMS: MAKSYMALNIE 160 ZNAKÓW – to wymóg techniczny, nie sugestia.
Odpowiadasz TYLKO jako JSON, bez żadnych komentarzy."""

# ---------------------------------------------------------------------------
# Schematy
# ---------------------------------------------------------------------------

class WydarzenieOgloszenia(BaseModel):
    tytul: str
    kiedy: str
    miejsce: str | None = None
    opis: str | None = None


class IntencjaOgloszenia(BaseModel):
    kiedy: str
    tresc: str


class OgloszeniaGenerujRequest(BaseModel):
    data_niedzieli: str | None = Field(None, description="Np. '18 maja 2025 (Zielone Świątki)'")
    swieto_liturgiczne: str | None = Field(None, description="Nazwa święta lub okresu")
    informacje_od_ksiedza: str | None = Field(None, max_length=1000)
    wydarzenia: list[WydarzenieOgloszenia] = Field(default_factory=list, max_length=10)
    intencje: list[IntencjaOgloszenia] = Field(default_factory=list, max_length=10)
    dodatkowe_info: str | None = Field(None, max_length=500)


class KanalOgloszenia(BaseModel):
    www: str
    facebook: str
    sms: str


class OgloszeniaResponse(BaseModel):
    formalne: KanalOgloszenia
    przyjazne: KanalOgloszenia
    rodzinne: KanalOgloszenia
    zastrzezenie: str


ZASTRZEZENIE = (
    "Treść wygenerowana przez AI na podstawie dostarczonych danych. "
    "Wymaga weryfikacji przez kapłana przed publikacją. "
    "AI nie uzupełnia brakujących informacji."
)

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/generuj", response_model=OgloszeniaResponse)
async def generuj_ogloszenia(
    req: OgloszeniaGenerujRequest,
    ai: AI,
    current_user: CurrentUser,
):
    if not any([
        req.informacje_od_ksiedza,
        req.wydarzenia,
        req.intencje,
        req.swieto_liturgiczne,
        req.dodatkowe_info,
    ]):
        raise HTTPException(
            status_code=422,
            detail="Podaj co najmniej jedną informację do ogłoszenia.",
        )

    prompt = _buduj_prompt(req)
    log.info("komunikacja_generate", user_id=str(current_user.id), events=len(req.wydarzenia))

    try:
        response = await ai._client.chat.completions.create(
            model=ai._model_prosty,  # gpt-4o-mini – komunikacja, nie teologia
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_KOMUNIKACJA},
                {"role": "user", "content": prompt},
            ],
            temperature=0.65,
            max_tokens=2800,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error("komunikacja_json_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd parsowania odpowiedzi AI")
    except Exception as e:
        log.error("komunikacja_ai_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"Serwis AI niedostępny: {e}")

    try:
        wynik = _parsuj_odpowiedz(data)
    except Exception as e:
        log.error("komunikacja_parse_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd struktury odpowiedzi AI")

    log.info("komunikacja_generated", user_id=str(current_user.id))
    return OgloszeniaResponse(**wynik, zastrzezenie=ZASTRZEZENIE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _buduj_prompt(req: OgloszeniaGenerujRequest) -> str:
    wiersze: list[str] = [
        "Przygotuj ogłoszenia parafialne na podstawie poniższych danych.",
        "",
    ]

    if req.data_niedzieli:
        wiersze.append(f"DATA NIEDZIELI: {req.data_niedzieli}")
    if req.swieto_liturgiczne:
        wiersze.append(f"ŚWIĘTO / OKRES: {req.swieto_liturgiczne}")

    if req.informacje_od_ksiedza:
        wiersze += ["", "INFORMACJE OD KSIĘDZA:", req.informacje_od_ksiedza]

    if req.wydarzenia:
        wiersze += ["", "WYDARZENIA TYGODNIA:"]
        for w in req.wydarzenia:
            linia = f"- {w.tytul}: {w.kiedy}"
            if w.miejsce:
                linia += f", {w.miejsce}"
            if w.opis:
                linia += f" – {w.opis}"
            wiersze.append(linia)

    if req.intencje:
        wiersze += ["", "INTENCJE MSZALNE:"]
        for i in req.intencje:
            wiersze.append(f"- {i.kiedy}: {i.tresc}")

    if req.dodatkowe_info:
        wiersze += ["", "DODATKOWE INFORMACJE:", req.dodatkowe_info]

    wiersze += [
        "",
        "Wygeneruj JSON z dokładnie trzema kluczami: formalne, przyjazne, rodzinne.",
        "Każdy klucz zawiera: www (pełny tekst), facebook (post z hashtagami), sms (MAX 160 ZNAKÓW).",
        "SMS musi mieć NAJWYŻEJ 160 znaków – jest to wymóg techniczny operatora SMS.",
        "Odpowiedz TYLKO jako JSON.",
    ]
    return "\n".join(wiersze)


def _parsuj_odpowiedz(data: dict) -> dict:
    def _kanal(raw: dict) -> KanalOgloszenia:
        sms = str(raw.get("sms", ""))
        if len(sms) > 160:
            sms = sms[:157] + "…"
        return KanalOgloszenia(
            www=str(raw.get("www", "")),
            facebook=str(raw.get("facebook", "")),
            sms=sms,
        )

    return {
        "formalne": _kanal(data.get("formalne") or {}),
        "przyjazne": _kanal(data.get("przyjazne") or {}),
        "rodzinne": _kanal(data.get("rodzinne") or {}),
    }
