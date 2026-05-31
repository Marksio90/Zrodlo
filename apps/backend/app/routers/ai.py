from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from app.dependencies import AI, CurrentUser, DB
from app.models.ai_uzycie import TypAiUzycia
from app.services.ai_koszt import zapisz_uzycie

router = APIRouter(prefix="/ai", tags=["AI – Wsparcie duszpasterskie"])


class HomiliaRequest(BaseModel):
    niedziela: str = Field(..., description="Np. '15. Niedziela Zwykła, rok B'")
    czytania: list[str] = Field(..., min_length=1, description="Teksty czytań liturgicznych")
    wskazowki: str | None = Field(None, description="Dodatkowe wskazówki kapłana")


class HomiliaResponse(BaseModel):
    sugestia: str
    model: str
    zastrzezenie: str


class DokumentRequest(BaseModel):
    typ: str = Field(..., description="Typ dokumentu do zredagowania")
    dane: dict = Field(..., description="Dane do wypełnienia dokumentu")
    instrukcje: str | None = Field(None, description="Dodatkowe instrukcje")


class DokumentResponse(BaseModel):
    tresc: str
    model: str
    zastrzezenie: str


ZASTRZEZENIE = (
    "Treść wygenerowana przez AI. Wymaga weryfikacji i zatwierdzenia przez kapłana "
    "przed użyciem. AI nie zastępuje discernment'u duszpasterskiego."
)


@router.post("/homilia", response_model=HomiliaResponse)
async def wsparcie_homilii(req: HomiliaRequest, ai: AI, db: DB, current_user: CurrentUser):
    czytania_tekst = "\n\n".join(
        f"Czytanie {i + 1}:\n{c}" for i, c in enumerate(req.czytania)
    )
    prompt = f"""Przygotuj szkic myśli do homilii na {req.niedziela}.

Czytania liturgiczne:
{czytania_tekst}

{f"Wskazówki kapłana: {req.wskazowki}" if req.wskazowki else ""}

Zaproponuj:
1. Główną myśl homilii (1-2 zdania)
2. Trzy kluczowe punkty do rozwinięcia
3. Przykład lub ilustrację z życia codziennego
4. Wezwanie na zakończenie

Pamiętaj: to są propozycje do przemyślenia przez kapłana, nie gotowy tekst do odczytania."""

    try:
        sugestia, model_uzyty, usage = await ai.generate_tracked(prompt)
        await zapisz_uzycie(
            db,
            model=model_uzyty,
            typ=TypAiUzycia.HOMILIA,
            tokeny_wejscie=usage["prompt_tokens"],
            tokeny_wyjscie=usage["completion_tokens"],
            parafia_id=current_user.parafia_id,
            uzytkownik_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serwis AI niedostępny: {e}")

    return HomiliaResponse(sugestia=sugestia, model=model_uzyty, zastrzezenie=ZASTRZEZENIE)


@router.post("/dokument", response_model=DokumentResponse)
async def generuj_dokument(req: DokumentRequest, ai: AI, db: DB, current_user: CurrentUser):
    dane_str = "\n".join(f"- {k}: {v}" for k, v in req.dane.items())
    prompt = f"""Zredaguj treść dokumentu typu: {req.typ}

Dostarczone dane:
{dane_str}

{f"Dodatkowe instrukcje: {req.instrukcje}" if req.instrukcje else ""}

Użyj wyłącznie podanych danych. Nie uzupełniaj brakujących informacji domysłami.
Jeśli brakuje kluczowych danych, wskaż to wyraźnie w tekście."""

    try:
        tresc, model_uzyty, usage = await ai.generate_tracked(prompt)
        await zapisz_uzycie(
            db,
            model=model_uzyty,
            typ=TypAiUzycia.DOKUMENT,
            tokeny_wejscie=usage["prompt_tokens"],
            tokeny_wyjscie=usage["completion_tokens"],
            parafia_id=current_user.parafia_id,
            uzytkownik_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serwis AI niedostępny: {e}")

    return DokumentResponse(tresc=tresc, model=model_uzyty, zastrzezenie=ZASTRZEZENIE)


@router.get("/modele")
async def lista_modeli(ai: AI):
    modele = await ai.list_models()
    dostepna = await ai.is_available()
    return {"dostepna": dostepna, "modele": modele, "aktywny_model": ai._model}
