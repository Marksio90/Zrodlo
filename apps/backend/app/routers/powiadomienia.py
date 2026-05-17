import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.powiadomienia import Powiadomienie
from app.schemas.powiadomienia import PowiadomienieCreate, PowiadomienieRead

router = APIRouter(prefix="/powiadomienia", tags=["Powiadomienia"])


@router.get("", response_model=list[PowiadomienieRead])
async def lista_powiadomien(
    db: DB,
    current_user: CurrentUser,
    przeczytane: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """Zwraca powiadomienia zalogowanego użytkownika."""
    q = select(Powiadomienie).where(Powiadomienie.odbiorca_id == current_user.id)
    if przeczytane is not None:
        q = q.where(Powiadomienie.przeczytane == przeczytane)
    q = q.order_by(Powiadomienie.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.post("/{pow_id}/przeczytaj", response_model=PowiadomienieRead)
async def oznacz_przeczytane(pow_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Powiadomienie, pow_id)
    if not obj or obj.odbiorca_id != current_user.id:
        raise HTTPException(status_code=404, detail="Powiadomienie nie znalezione")
    if not obj.przeczytane:
        obj.przeczytane = True
        obj.data_przeczytania = datetime.now(timezone.utc)
        await db.flush()
    return obj


@router.post("/przeczytaj-wszystkie", status_code=status.HTTP_204_NO_CONTENT)
async def oznacz_wszystkie_przeczytane(db: DB, current_user: CurrentUser):
    q = select(Powiadomienie).where(
        Powiadomienie.odbiorca_id == current_user.id,
        Powiadomienie.przeczytane.is_(False),
    )
    wyniki = (await db.execute(q)).scalars().all()
    teraz = datetime.now(timezone.utc)
    for p in wyniki:
        p.przeczytane = True
        p.data_przeczytania = teraz
    await db.flush()


@router.get("/liczba-nieprzeczytanych")
async def liczba_nieprzeczytanych(db: DB, current_user: CurrentUser):
    from sqlalchemy import func
    q = select(func.count()).where(
        Powiadomienie.odbiorca_id == current_user.id,
        Powiadomienie.przeczytane.is_(False),
    )
    count = (await db.execute(q)).scalar_one()
    return {"nieprzeczytane": count}


async def wyslij_powiadomienie(
    db,
    *,
    odbiorca_id: uuid.UUID,
    tytul: str,
    tresc: str,
    typ: str = "info",
    referencja_tabela: str | None = None,
    referencja_id: str | None = None,
) -> Powiadomienie:
    """Pomocnicza funkcja wywoływana z innych routerów."""
    p = Powiadomienie(
        odbiorca_id=odbiorca_id,
        typ=typ,
        tytul=tytul,
        tresc=tresc,
        referencja_tabela=referencja_tabela,
        referencja_id=referencja_id,
    )
    db.add(p)
    return p
