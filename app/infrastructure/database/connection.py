import logging
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool

from config.config import load_config, Config


logger = logging.getLogger(__name__)

# Функция, возвращающая безопасную строку для подключеия к PostgreSQL
def build_pg_conninfo(
        db_name: str,
        host: str,
        port: int,
        user: str,
        password: str
) -> str:
    conninfo = f"postgresql+asyncpg://{quote(user, safe='')}:{quote(password, safe='')}" \
               f"@{host}:{port}/{db_name}"
    
    logger.debug(f"Building PostgreSQL connection string (password omitted): " \
                 f"postgresql+asyncpg://{quote(user, safe='')}@{host}:{port}/{db_name}")
    
    return conninfo


config: Config = load_config()

engine = create_async_engine(
    url=build_pg_conninfo(
        db_name=config.db.name, 
        host=config.db.host, 
        port=config.db.port, 
        user=config.db.user, 
        password=config.db.password
    ), 
    poolclass=AsyncAdaptedQueuePool,
    pool_size=15, 
    max_overflow=25, 
    pool_recycle=1800,
    pool_timeout=30, 
    echo=config.db.logging, 
    pool_pre_ping=True, 
)

# AsyncSessionLocal = async_sessionmaker(
#     bind=engine, 
#     expire_on_commit=False, 
# )

def get_session_factory():
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )




