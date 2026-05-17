"""OCR – ekstrakcja tekstu i klasyfikacja dokumentów przez OpenAI Vision."""
import base64
import json
import structlog

log = structlog.get_logger()

SYSTEM_OCR = (
    "Jesteś ekspertem od analizy dokumentów kościelnych i urzędowych w języku polskim. "
    "Rozpoznajesz: metryki sakramentalne, zaświadczenia, formularze, korespondencję, akty. "
    "Odpowiadasz WYŁĄCZNIE jako JSON. Nieczytelne fragmenty oznaczasz [NIECZYTELNE]."
)

_PROMPT_JSON = (
    'Przeanalizuj dokument i zwróć dokładnie ten JSON:\n'
    '{\n'
    '  "tresc_ocr": "kompletna transkrypcja całego tekstu dokumentu",\n'
    '  "typ_dokumentu": "metryka_chrztu|metryka_slubu|metryka_bierzmowania|'
    'metryka_komunii|zaswiadczenie|formularz|akt_zgonu|pismo_urzedowe|korespondencja|inne",\n'
    '  "jednostka_wystawiajaca": "pełna nazwa parafii/urzędu/instytucji lub null",\n'
    '  "data_wystawienia": "YYYY-MM-DD lub null",\n'
    '  "osoby": ["pełne imiona i nazwiska z dokumentu"],\n'
    '  "dane_kontaktowe": {"email": null, "telefon": null, "adres": null},\n'
    '  "tagi_sugerowane": ["max 5 tagów po polsku małymi literami"],\n'
    '  "encje": {\n'
    '    "numery_dokumentow": [],\n'
    '    "parafia": null,\n'
    '    "diecezja": null,\n'
    '    "numer_ksiegi": null,\n'
    '    "dodatkowe": {}\n'
    '  }\n'
    '}'
)


async def _ocr_obraz(client, image_bytes: bytes, mime_type: str, model: str) -> dict:
    b64 = base64.b64encode(image_bytes).decode()
    response = await client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": f"{SYSTEM_OCR}\n\n{_PROMPT_JSON}",
                },
            ],
        }],
        max_tokens=2500,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")


async def _klasyfikuj_tekst(client, tekst: str, model: str) -> dict:
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_OCR},
            {
                "role": "user",
                "content": f"Poniżej tekst wyekstrahowany z dokumentu PDF:\n\n{tekst[:5000]}\n\n{_PROMPT_JSON}",
            },
        ],
        max_tokens=1500,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content or "{}")
    data["tresc_ocr"] = tekst  # używamy oryginalnego tekstu
    return data


async def przetworz(content: bytes, typ_pliku: str, ai) -> dict:
    """
    Przetwarza plik (PDF/JPG/PNG) – zwraca znormalizowany słownik wyników OCR.
    `ai` to instancja OpenAIService (z app.services.ai).
    """
    log.debug("ocr_start", typ=typ_pliku, size=len(content))

    if typ_pliku == "pdf":
        tekst = _ekstrahuj_tekst_pdf(content)
        if len(tekst.strip()) >= 80:
            log.debug("ocr_pdf_native_text", chars=len(tekst))
            data = await _klasyfikuj_tekst(ai._client, tekst, ai._model_prosty)
        else:
            log.debug("ocr_pdf_scanned")
            img_bytes = _pdf_strona_na_png(content)
            if img_bytes:
                data = await _ocr_obraz(ai._client, img_bytes, "image/png", ai._model_zlozony)
            else:
                return _pusty("Zeskanowany PDF – wymagana ręczna konwersja")
    elif typ_pliku in ("jpg", "jpeg"):
        data = await _ocr_obraz(ai._client, content, "image/jpeg", ai._model_zlozony)
    else:  # png
        data = await _ocr_obraz(ai._client, content, "image/png", ai._model_zlozony)

    log.debug("ocr_done", typ_dokumentu=data.get("typ_dokumentu"))
    return _normalizuj(data)


def _ekstrahuj_tekst_pdf(content: bytes) -> str:
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=content, filetype="pdf")
        tekst = "".join(page.get_text() for page in doc)
        doc.close()
        return tekst
    except Exception as e:
        log.warning("pdf_text_extract_failed", error=str(e))
        return ""


def _pdf_strona_na_png(content: bytes) -> bytes | None:
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        if not doc.page_count:
            return None
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
    except Exception as e:
        log.warning("pdf_to_png_failed", error=str(e))
        return None


def _normalizuj(data: dict) -> dict:
    return {
        "tresc_ocr": str(data.get("tresc_ocr") or ""),
        "typ_dokumentu": str(data.get("typ_dokumentu") or "inne"),
        "jednostka_wystawiajaca": data.get("jednostka_wystawiajaca") or None,
        "data_wystawienia": data.get("data_wystawienia") or None,
        "osoby": [str(o) for o in (data.get("osoby") or [])],
        "dane_kontaktowe": dict(data.get("dane_kontaktowe") or {}),
        "tagi": [str(t) for t in (data.get("tagi_sugerowane") or [])],
        "encje": dict(data.get("encje") or {}),
    }


def _pusty(notatka: str) -> dict:
    return {
        "tresc_ocr": notatka,
        "typ_dokumentu": "inne",
        "jednostka_wystawiajaca": None,
        "data_wystawienia": None,
        "osoby": [],
        "dane_kontaktowe": {},
        "tagi": [],
        "encje": {},
    }
