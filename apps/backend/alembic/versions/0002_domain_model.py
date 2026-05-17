"""Domain model – Parafia, Uzytkownik, Grupy, Ogloszenia, Powiadomienia, Wiedza, AuditLog

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Parafia ────────────────────────────────────────
    op.create_table(
        "parafie",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nazwa", sa.String(300), nullable=False),
        sa.Column("wezwanie", sa.String(200), nullable=True),
        sa.Column("adres", sa.String(400), nullable=False, server_default=""),
        sa.Column("miasto", sa.String(100), nullable=False, server_default=""),
        sa.Column("kod_pocztowy", sa.String(10), nullable=True),
        sa.Column("diecezja", sa.String(200), nullable=True),
        sa.Column("dekanat", sa.String(200), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("telefon", sa.String(30), nullable=True),
        sa.Column("strona_www", sa.String(300), nullable=True),
        sa.Column("nip", sa.String(20), nullable=True),
        sa.Column("regon", sa.String(20), nullable=True),
        sa.Column("data_erygowania", sa.Date(), nullable=True),
        sa.Column("aktywna", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parafie_email", "parafie", ["email"])

    # ── 2. Uzytkownicy ────────────────────────────────────
    op.create_table(
        "uzytkownicy",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("haslo_hash", sa.String(200), nullable=False),
        sa.Column("imie", sa.String(100), nullable=False),
        sa.Column("nazwisko", sa.String(100), nullable=False),
        sa.Column("rola", sa.String(30), nullable=False, server_default="parafianin"),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("aktywny", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ostatnie_logowanie", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_uzytkownicy_email", "uzytkownicy", ["email"])
    op.create_index("ix_uzytkownicy_rola", "uzytkownicy", ["rola"])
    op.create_index("ix_uzytkownicy_parafia_id", "uzytkownicy", ["parafia_id"])
    op.create_index("ix_uzytkownicy_deleted_at", "uzytkownicy", ["deleted_at"])

    # ── 3. Proboszczowie ──────────────────────────────────
    op.create_table(
        "proboszczowie",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("uzytkownik_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("numer_dekretu", sa.String(100), nullable=True),
        sa.Column("data_nominacji", sa.Date(), nullable=True),
        sa.Column("data_zakonczenia", sa.Date(), nullable=True),
        sa.Column("uwagi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["uzytkownik_id"], ["uzytkownicy.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uzytkownik_id"),
    )
    op.create_index("ix_proboszczowie_uzytkownik_id", "proboszczowie", ["uzytkownik_id"])
    op.create_index("ix_proboszczowie_parafia_id", "proboszczowie", ["parafia_id"])

    # ── 4. Wikariusze ─────────────────────────────────────
    op.create_table(
        "wikariusze",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("uzytkownik_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("specjalizacja", sa.String(200), nullable=True),
        sa.Column("data_nominacji", sa.Date(), nullable=True),
        sa.Column("data_zakonczenia", sa.Date(), nullable=True),
        sa.Column("uwagi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["uzytkownik_id"], ["uzytkownicy.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uzytkownik_id"),
    )
    op.create_index("ix_wikariusze_uzytkownik_id", "wikariusze", ["uzytkownik_id"])

    # ── 5. Parafianie ─────────────────────────────────────
    op.create_table(
        "parafianie",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("uzytkownik_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("imie", sa.String(100), nullable=False),
        sa.Column("nazwisko", sa.String(100), nullable=False),
        sa.Column("data_urodzenia", sa.Date(), nullable=True),
        sa.Column("data_chrztu", sa.Date(), nullable=True),
        sa.Column("numer_parafialny", sa.String(50), nullable=True),
        sa.Column("adres", sa.String(400), nullable=True),
        sa.Column("telefon", sa.String(30), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("uwagi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uzytkownik_id"], ["uzytkownicy.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uzytkownik_id"),
        sa.UniqueConstraint("numer_parafialny"),
    )
    op.create_index("ix_parafianie_uzytkownik_id", "parafianie", ["uzytkownik_id"])
    op.create_index("ix_parafianie_parafia_id", "parafianie", ["parafia_id"])
    op.create_index("ix_parafianie_imie", "parafianie", ["imie"])
    op.create_index("ix_parafianie_nazwisko", "parafianie", ["nazwisko"])
    op.create_index("ix_parafianie_deleted_at", "parafianie", ["deleted_at"])

    # ── 6. Grupy Parafialne ───────────────────────────────
    op.create_table(
        "grupy_parafialne",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nazwa", sa.String(200), nullable=False),
        sa.Column("opis", sa.Text(), nullable=True),
        sa.Column("typ", sa.String(50), nullable=False, server_default="wspolnota"),
        sa.Column("opiekun_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kontakt_email", sa.String(200), nullable=True),
        sa.Column("kontakt_telefon", sa.String(30), nullable=True),
        sa.Column("aktywna", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opiekun_id"], ["uzytkownicy.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_grupy_parafialne_parafia_id", "grupy_parafialne", ["parafia_id"])
    op.create_index("ix_grupy_parafialne_typ", "grupy_parafialne", ["typ"])
    op.create_index("ix_grupy_parafialne_nazwa", "grupy_parafialne", ["nazwa"])
    op.create_index("ix_grupy_parafialne_deleted_at", "grupy_parafialne", ["deleted_at"])

    # ── 7. Czlonkowie Grup ────────────────────────────────
    op.create_table(
        "czlonkowie_grup",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("grupa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parafianin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rola", sa.String(30), nullable=False, server_default="czlonek"),
        sa.Column("data_dolaczenia", sa.Date(), nullable=True),
        sa.Column("aktywny", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["grupa_id"], ["grupy_parafialne.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parafianin_id"], ["parafianie.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_czlonkowie_grup_grupa_id", "czlonkowie_grup", ["grupa_id"])
    op.create_index("ix_czlonkowie_grup_parafianin_id", "czlonkowie_grup", ["parafianin_id"])

    # ── 8. Ogloszenia ─────────────────────────────────────
    op.create_table(
        "ogloszenia",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tytul", sa.String(300), nullable=False),
        sa.Column("tresc", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="szkic"),
        sa.Column("priorytet", sa.String(20), nullable=False, server_default="normalny"),
        sa.Column("data_publikacji", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_wygasniecia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("zatwierdzone_przez_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("data_zatwierdzenia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tworca_id"], ["uzytkownicy.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["zatwierdzone_przez_id"], ["uzytkownicy.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ogloszenia_parafia_id", "ogloszenia", ["parafia_id"])
    op.create_index("ix_ogloszenia_status", "ogloszenia", ["status"])
    op.create_index("ix_ogloszenia_data_publikacji", "ogloszenia", ["data_publikacji"])
    op.create_index("ix_ogloszenia_deleted_at", "ogloszenia", ["deleted_at"])

    # ── 9. Powiadomienia ──────────────────────────────────
    op.create_table(
        "powiadomienia",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("odbiorca_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("typ", sa.String(30), nullable=False, server_default="info"),
        sa.Column("tytul", sa.String(300), nullable=False),
        sa.Column("tresc", sa.Text(), nullable=False),
        sa.Column("przeczytane", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_przeczytania", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referencja_tabela", sa.String(100), nullable=True),
        sa.Column("referencja_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["odbiorca_id"], ["uzytkownicy.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_powiadomienia_odbiorca_id", "powiadomienia", ["odbiorca_id"])
    op.create_index("ix_powiadomienia_przeczytane", "powiadomienia", ["przeczytane"])
    op.create_index("ix_powiadomienia_typ", "powiadomienia", ["typ"])
    op.create_index("ix_powiadomienia_created_at", "powiadomienia", ["created_at"])

    # ── 10. Notatki Wiedzy ────────────────────────────────
    op.create_table(
        "notatki_wiedzy",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tytul", sa.String(400), nullable=False),
        sa.Column("tresc", sa.Text(), nullable=False),
        sa.Column("kategoria", sa.String(60), nullable=False, server_default="inne"),
        sa.Column("tagi", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("publiczna", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qdrant_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parafia_id"], ["parafie.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tworca_id"], ["uzytkownicy.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qdrant_id"),
    )
    op.create_index("ix_notatki_wiedzy_parafia_id", "notatki_wiedzy", ["parafia_id"])
    op.create_index("ix_notatki_wiedzy_kategoria", "notatki_wiedzy", ["kategoria"])
    op.create_index("ix_notatki_wiedzy_publiczna", "notatki_wiedzy", ["publiczna"])
    op.create_index("ix_notatki_wiedzy_tytul", "notatki_wiedzy", ["tytul"])
    op.create_index("ix_notatki_wiedzy_deleted_at", "notatki_wiedzy", ["deleted_at"])

    # ── 11. Audit Logs ────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tabela", sa.String(100), nullable=False),
        sa.Column("rekord_id", sa.String(36), nullable=False),
        sa.Column("operacja", sa.String(30), nullable=False),
        sa.Column("uzytkownik_id", sa.String(36), nullable=True),
        sa.Column("parafia_id", sa.String(36), nullable=True),
        sa.Column("stare_wartosci", postgresql.JSONB(), nullable=True),
        sa.Column("nowe_wartosci", postgresql.JSONB(), nullable=True),
        sa.Column("ip_adres", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tabela", "audit_logs", ["tabela"])
    op.create_index("ix_audit_logs_rekord_id", "audit_logs", ["rekord_id"])
    op.create_index("ix_audit_logs_operacja", "audit_logs", ["operacja"])
    op.create_index("ix_audit_logs_uzytkownik_id", "audit_logs", ["uzytkownik_id"])
    op.create_index("ix_audit_logs_parafia_id", "audit_logs", ["parafia_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ── 12. ALTER istniejących tabel – soft delete + parafia_id ──

    # liturgie
    op.add_column("liturgie", sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("liturgie", sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("liturgie", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "liturgie", "parafie", ["parafia_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "liturgie", "uzytkownicy", ["tworca_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_liturgie_parafia_id", "liturgie", ["parafia_id"])
    op.create_index("ix_liturgie_deleted_at", "liturgie", ["deleted_at"])

    # intencje
    op.add_column("intencje", sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("intencje", sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("intencje", sa.Column("ofiarodawca_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("intencje", sa.Column("potwierdzone_przez_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("intencje", sa.Column("data_potwierdzenia", sa.DateTime(timezone=True), nullable=True))
    op.add_column("intencje", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "intencje", "parafie", ["parafia_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "intencje", "uzytkownicy", ["tworca_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "intencje", "parafianie", ["ofiarodawca_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "intencje", "uzytkownicy", ["potwierdzone_przez_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_intencje_parafia_id", "intencje", ["parafia_id"])
    op.create_index("ix_intencje_ofiarodawca_id", "intencje", ["ofiarodawca_id"])
    op.create_index("ix_intencje_deleted_at", "intencje", ["deleted_at"])
    op.create_index("ix_intencje_typ", "intencje", ["typ"])

    # dokumenty
    op.add_column("dokumenty", sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("dokumenty", sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("dokumenty", sa.Column("parafianin_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("dokumenty", sa.Column("zatwierdzone_przez_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("dokumenty", sa.Column("data_zatwierdzenia", sa.DateTime(timezone=True), nullable=True))
    op.add_column("dokumenty", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "dokumenty", "parafie", ["parafia_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "dokumenty", "uzytkownicy", ["tworca_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "dokumenty", "parafianie", ["parafianin_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "dokumenty", "uzytkownicy", ["zatwierdzone_przez_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_dokumenty_parafia_id", "dokumenty", ["parafia_id"])
    op.create_index("ix_dokumenty_parafianin_id", "dokumenty", ["parafianin_id"])
    op.create_index("ix_dokumenty_deleted_at", "dokumenty", ["deleted_at"])

    # wspolnoty
    op.add_column("wspolnoty", sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wspolnoty", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "wspolnoty", "parafie", ["parafia_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_wspolnoty_parafia_id", "wspolnoty", ["parafia_id"])
    op.create_index("ix_wspolnoty_deleted_at", "wspolnoty", ["deleted_at"])

    # czlonkowie_wspolnot
    op.add_column("czlonkowie_wspolnot", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # wydarzenia
    op.add_column("wydarzenia", sa.Column("parafia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wydarzenia", sa.Column("tworca_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wydarzenia", sa.Column("grupa_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wydarzenia", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "wydarzenia", "parafie", ["parafia_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "wydarzenia", "uzytkownicy", ["tworca_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "wydarzenia", "grupy_parafialne", ["grupa_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_wydarzenia_parafia_id", "wydarzenia", ["parafia_id"])
    op.create_index("ix_wydarzenia_grupa_id", "wydarzenia", ["grupa_id"])
    op.create_index("ix_wydarzenia_deleted_at", "wydarzenia", ["deleted_at"])


def downgrade() -> None:
    # Usuń kolumny z istniejących tabel
    for tabela, kolumny in [
        ("wydarzenia", ["parafia_id", "tworca_id", "grupa_id", "deleted_at"]),
        ("czlonkowie_wspolnot", ["deleted_at"]),
        ("wspolnoty", ["parafia_id", "deleted_at"]),
        ("dokumenty", ["parafia_id", "tworca_id", "parafianin_id", "zatwierdzone_przez_id", "data_zatwierdzenia", "deleted_at"]),
        ("intencje", ["parafia_id", "tworca_id", "ofiarodawca_id", "potwierdzone_przez_id", "data_potwierdzenia", "deleted_at"]),
        ("liturgie", ["parafia_id", "tworca_id", "deleted_at"]),
    ]:
        for kol in kolumny:
            op.drop_column(tabela, kol)

    op.drop_table("audit_logs")
    op.drop_table("notatki_wiedzy")
    op.drop_table("powiadomienia")
    op.drop_table("ogloszenia")
    op.drop_table("czlonkowie_grup")
    op.drop_table("grupy_parafialne")
    op.drop_table("parafianie")
    op.drop_table("wikariusze")
    op.drop_table("proboszczowie")
    op.drop_table("uzytkownicy")
    op.drop_table("parafie")
