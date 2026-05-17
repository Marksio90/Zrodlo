"""Serwis AI – OpenAI z kaskadowym doborem modeli."""
import structlog
from openai import AsyncOpenAI

from app.config import settings

log = structlog.get_logger()

# Tematy wymagające mocniejszego modelu (prawo kanoniczne, kwestie specjalne)
_TEMATY_ZLOZONE = frozenset([
    "prawo kanoniczne", "kan.", "kodeks prawa kanonicznego", "unieważnienie",
    "ekskomunika", "dyspensa", "trybunał kościelny", "anulowanie ślubu",
    "separacja kościelna", "apostazja", "interdykt", "suspensa",
    "proces kanoniczny", "nullitatis matrimonii",
])

SYSTEM_PROMPT_DUSZPASTERSKI = """Jesteś asystentem wspierającym pracę parafii.
Twoim zadaniem jest pomoc w przygotowaniu materiałów duszpasterskich.

Zasady:
- Odpowiadasz wyłącznie po polsku
- Nie podejmujesz decyzji teologicznych ani duszpasterskich
- Wszystkie sugestie wymagają weryfikacji przez kapłana
- Nie tworzysz danych – opierasz się wyłącznie na dostarczonych informacjach
- Styl: spokojny, godny, pastoralny
"""


def _czy_trudne(tekst: str) -> bool:
    """Czy pytanie dotyczy prawa kanonicznego – wymaga mocniejszego modelu."""
    t = tekst.lower()
    return any(temat in t for temat in _TEMATY_ZLOZONE)


class OpenAIService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
        self._model_prosty = settings.openai_model_simple      # gpt-4o-mini
        self._model_zlozony = settings.openai_model_complex    # gpt-4o
        self._model_embedding = settings.openai_embedding_model

    @property
    def _model(self) -> str:
        return self._model_prosty

    async def generate(self, prompt: str, system: str = SYSTEM_PROMPT_DUSZPASTERSKI) -> str:
        """Jednokrotne generowanie – dla homilii, dokumentów itp."""
        model = self._model_zlozony if _czy_trudne(prompt) else self._model_prosty
        log.debug("openai_generate", model=model, chars=len(prompt))
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return response.choices[0].message.content or ""

    async def chat(self, messages: list[dict], complex: bool = False) -> tuple[str, str]:
        """Wieloturowy czat. Zwraca (tekst_odpowiedzi, użyty_model)."""
        model = self._model_zlozony if complex else self._model_prosty
        log.debug("openai_chat", model=model, n_msgs=len(messages))
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1000,
        )
        return response.choices[0].message.content or "Niestety nie mam tej informacji.", model

    async def embed(self, text: str) -> list[float]:
        """Generuje embedding (text-embedding-3-small, 1536 wymiarów)."""
        response = await self._client.embeddings.create(
            model=self._model_embedding,
            input=text[:8000],
        )
        return response.data[0].embedding

    async def is_available(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self._client.models.list()
            return [m.id for m in resp.data if "gpt" in m.id][:10]
        except Exception:
            return []


_ai_instance: OpenAIService | None = None


def get_ai() -> OpenAIService:
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = OpenAIService()
    return _ai_instance
