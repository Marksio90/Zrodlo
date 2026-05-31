"""
RBAC – macierz uprawnień oparta na rolach.
Zasób + akcja → zestaw ról które mogą ją wykonać.
"""

from app.models.uzytkownicy import RolaUzytkownika

# Macierz: rola → zasób → dozwolone akcje
_MACIERZ: dict[str, dict[str, set[str]]] = {
    RolaUzytkownika.ADMIN: {
        "*": {"czytaj", "tworz", "edytuj", "usun", "zatwierdz"},
    },
    RolaUzytkownika.PROBOSZCZ: {
        "parafia":     {"czytaj", "edytuj"},
        "uzytkownik":  {"czytaj", "tworz", "edytuj"},
        "parafianin":  {"czytaj", "tworz", "edytuj", "usun"},
        "intencja":    {"czytaj", "tworz", "edytuj", "usun", "zatwierdz"},
        "liturgia":    {"czytaj", "tworz", "edytuj", "usun"},
        "dokument":    {"czytaj", "tworz", "edytuj", "usun", "zatwierdz"},
        "ogloszenie":  {"czytaj", "tworz", "edytuj", "usun", "zatwierdz"},
        "wydarzenie":  {"czytaj", "tworz", "edytuj", "usun"},
        "wspolnota":   {"czytaj", "tworz", "edytuj", "usun"},
        "grupa":       {"czytaj", "tworz", "edytuj", "usun"},
        "wiedza":      {"czytaj", "tworz", "edytuj", "usun"},
        "powiadomienie": {"czytaj"},
    },
    RolaUzytkownika.WIKARIUSZ: {
        "parafia":     {"czytaj"},
        "uzytkownik":  {"czytaj"},
        "parafianin":  {"czytaj", "tworz", "edytuj"},
        "intencja":    {"czytaj", "tworz", "edytuj", "zatwierdz"},
        "liturgia":    {"czytaj", "tworz", "edytuj"},
        "dokument":    {"czytaj", "tworz", "edytuj"},
        "ogloszenie":  {"czytaj", "tworz", "edytuj"},
        "wydarzenie":  {"czytaj", "tworz", "edytuj"},
        "wspolnota":   {"czytaj", "tworz", "edytuj"},
        "grupa":       {"czytaj", "tworz", "edytuj"},
        "wiedza":      {"czytaj", "tworz", "edytuj"},
        "powiadomienie": {"czytaj"},
    },
    RolaUzytkownika.PARAFIANIN: {
        "parafia":       {"czytaj"},
        "intencja":      {"tworz"},
        "ogloszenie":    {"czytaj"},
        "wydarzenie":    {"czytaj"},
        "wspolnota":     {"czytaj"},
        "grupa":         {"czytaj"},
        "wiedza":        {"czytaj"},
        "powiadomienie": {"czytaj"},
    },
}


def moze(rola: str, zasob: str, akcja: str) -> bool:
    """Sprawdza czy dana rola ma uprawnienie do akcji na zasobie."""
    zasoby = _MACIERZ.get(rola, {})
    # wildcard dla admina
    if "*" in zasoby and akcja in zasoby["*"]:
        return True
    return akcja in zasoby.get(zasob, set())


def wymagaj_uprawnienia(zasob: str, akcja: str):
    """
    FastAPI dependency factory.
    Użycie: Depends(wymagaj_uprawnienia("intencja", "zatwierdz"))
    """
    from fastapi import Depends, HTTPException, status
    from app.dependencies import get_current_user
    from app.models.uzytkownicy import Uzytkownik

    async def _check(current_user: Uzytkownik = Depends(get_current_user)) -> Uzytkownik:
        if not moze(current_user.rola, zasob, akcja):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Brak uprawnień: {zasob}/{akcja}",
            )
        return current_user

    return _check
