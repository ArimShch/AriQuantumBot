# utils/reset_db.py (запускается вручную!)
from .connection import engine
from .models.models import Base

async def reset_database():
    print("⚠️ ВНИМАНИЕ: Полная очистка базы данных!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("🧹 БД сброшена")

# Как запустить вручную:
# python -c "from app.infrastructure.database.reset import reset_database; import asyncio; asyncio.run(reset_database())"


