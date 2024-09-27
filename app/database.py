from settings import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

async_engine = create_async_engine(settings.DB_URL, echo=True)
async_session = async_sessionmaker(async_engine)

# Для миграций
sync_engine = create_engine(settings.DB_URL)
