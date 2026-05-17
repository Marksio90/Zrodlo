import httpx

from app.config import settings

SYSTEM_PROMPT_DUSZPASTERSKI = """Jesteś asystentem duszpasterskim wspierającym pracę kapłana.
Twoim zadaniem jest pomoc w przygotowaniu materiałów duszpasterskich.

Zasady:
- Odpowiadasz wyłącznie po polsku
- Nie podejmujesz decyzji teologicznych ani duszpasterskich
- Wszystkie sugestie wymagają weryfikacji przez kapłana
- Nie tworzysz danych – opierasz się wyłącznie na dostarczonych informacjach
- Styl: spokojny, godny, pastoralny
"""


class OllamaService:
    def __init__(self) -> None:
        self._base_url = settings.ollama_url
        self._model = settings.ollama_model
        self._timeout = settings.ollama_timeout

    async def generate(self, prompt: str, system: str = SYSTEM_PROMPT_DUSZPASTERSKI) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []


_ai_instance: OllamaService | None = None


def get_ai() -> OllamaService:
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = OllamaService()
    return _ai_instance
