"""Testy jednostkowe macierzy RBAC."""
import pytest

from app.models.uzytkownicy import RolaUzytkownika
from app.services.permissions import moze


class TestAdminAccess:
    def test_admin_can_do_anything_on_any_resource(self):
        for akcja in ("czytaj", "tworz", "edytuj", "usun", "zatwierdz"):
            for zasob in ("intencja", "dokument", "wiedza", "wydarzenie", "wspolnota"):
                assert moze(RolaUzytkownika.ADMIN, zasob, akcja), \
                    f"Admin powinien móc '{akcja}' na '{zasob}'"

    def test_admin_nonexistent_resource_still_allowed(self):
        assert moze(RolaUzytkownika.ADMIN, "nieistniejacy_zasob", "czytaj") is True


class TestProboszczAccess:
    def test_proboszcz_full_intencja_access(self):
        for akcja in ("czytaj", "tworz", "edytuj", "usun", "zatwierdz"):
            assert moze(RolaUzytkownika.PROBOSZCZ, "intencja", akcja)

    def test_proboszcz_full_dokument_access(self):
        for akcja in ("czytaj", "tworz", "edytuj", "usun", "zatwierdz"):
            assert moze(RolaUzytkownika.PROBOSZCZ, "dokument", akcja)

    def test_proboszcz_manages_wspolnoty(self):
        for akcja in ("czytaj", "tworz", "edytuj", "usun"):
            assert moze(RolaUzytkownika.PROBOSZCZ, "wspolnota", akcja)

    def test_proboszcz_manages_wydarzenia(self):
        for akcja in ("czytaj", "tworz", "edytuj", "usun"):
            assert moze(RolaUzytkownika.PROBOSZCZ, "wydarzenie", akcja)


class TestWikariuszAccess:
    def test_wikariusz_can_confirm_intencja(self):
        assert moze(RolaUzytkownika.WIKARIUSZ, "intencja", "zatwierdz") is True

    def test_wikariusz_cannot_delete_intencja(self):
        assert moze(RolaUzytkownika.WIKARIUSZ, "intencja", "usun") is False

    def test_wikariusz_cannot_delete_dokument(self):
        assert moze(RolaUzytkownika.WIKARIUSZ, "dokument", "usun") is False

    def test_wikariusz_cannot_approve_document(self):
        assert moze(RolaUzytkownika.WIKARIUSZ, "dokument", "zatwierdz") is False

    def test_wikariusz_can_read_write_events(self):
        for akcja in ("czytaj", "tworz", "edytuj"):
            assert moze(RolaUzytkownika.WIKARIUSZ, "wydarzenie", akcja)

    def test_wikariusz_cannot_delete_events(self):
        assert moze(RolaUzytkownika.WIKARIUSZ, "wydarzenie", "usun") is False


class TestParafianinAccess:
    def test_parafianin_can_create_intencja(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "intencja", "tworz") is True

    def test_parafianin_cannot_read_intencja(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "intencja", "czytaj") is False

    def test_parafianin_cannot_delete_intencja(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "intencja", "usun") is False

    def test_parafianin_can_read_ogloszenia(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "ogloszenie", "czytaj") is True

    def test_parafianin_cannot_create_ogloszenie(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "ogloszenie", "tworz") is False

    def test_parafianin_can_read_wspolnoty(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "wspolnota", "czytaj") is True

    def test_parafianin_cannot_create_wspolnota(self):
        assert moze(RolaUzytkownika.PARAFIANIN, "wspolnota", "tworz") is False


class TestEdgeCases:
    def test_unknown_role_always_denied(self):
        assert moze("kapuцын", "intencja", "czytaj") is False

    def test_empty_role_denied(self):
        assert moze("", "intencja", "czytaj") is False
