"""Testy jednostkowe serwisu kalkulacji kosztów AI."""
from decimal import Decimal

import pytest

from app.services.ai_koszt import oblicz_koszt


class TestObliczKoszt:
    def test_gpt4o_mini_zwraca_koszt(self):
        koszt = oblicz_koszt("gpt-4o-mini", 1000, 500)
        assert isinstance(koszt, Decimal)
        assert koszt > Decimal("0")

    def test_gpt4o_droższy_niż_mini(self):
        mini = oblicz_koszt("gpt-4o-mini", 1000, 1000)
        full = oblicz_koszt("gpt-4o", 1000, 1000)
        assert full > mini

    def test_embedding_zero_output(self):
        koszt = oblicz_koszt("text-embedding-3-small", 1000, 0)
        assert koszt > Decimal("0")

    def test_zero_tokenow_daje_zero(self):
        assert oblicz_koszt("gpt-4o-mini", 0, 0) == Decimal("0.00000000")

    def test_nieznany_model_uzywa_fallbacku(self):
        koszt = oblicz_koszt("nieznany-model-xyz", 1000, 1000)
        assert koszt > Decimal("0")

    def test_wynik_ma_osiem_miejsc_po_przecinku(self):
        koszt = oblicz_koszt("gpt-4o-mini", 100, 100)
        # quantize do 8 miejsc dziesiętnych
        assert koszt == koszt.quantize(Decimal("0.00000001"))

    def test_wersjonowane_modele_maja_te_same_ceny(self):
        a = oblicz_koszt("gpt-4o-mini", 500, 200)
        b = oblicz_koszt("gpt-4o-mini-2024-07-18", 500, 200)
        assert a == b
