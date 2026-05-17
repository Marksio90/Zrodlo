from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.cache import RedisCache, get_cache
from app.services.storage import MinioStorage, get_storage
from app.services.ai import OllamaService, get_ai

DB = Annotated[AsyncSession, Depends(get_db)]
Cache = Annotated[RedisCache, Depends(get_cache)]
Storage = Annotated[MinioStorage, Depends(get_storage)]
AI = Annotated[OllamaService, Depends(get_ai)]
