from fastapi import APIRouter, HTTPException

from app.demo.seeder import seed_demo
from app.dependencies import CurrentUser, DB
from app.models.uzytkownicy import RolaUzytkownika

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/seed", status_code=200)
async def seed(db: DB, current_user: CurrentUser):
    if current_user.rola not in (RolaUzytkownika.ADMIN, RolaUzytkownika.PROBOSZCZ):
        raise HTTPException(status_code=403, detail="Tylko administrator może uruchomić tryb demo")
    result = await seed_demo(db)
    return result
