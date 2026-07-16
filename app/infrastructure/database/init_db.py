import logging 

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from sqlalchemy import text, inspect, select

from .models.models import Base, Role, Language, Backend, ComplexityLevel


logger = logging.getLogger(__name__)


# Функция, логирующая версию СУБД, к которой происходит подключение
async def log_db_version(engine: AsyncEngine) -> bool:
    try:
        async with engine.connect() as connection:
            result = await connection.scalar(
                text("SELECT version();")
            )
            logger.info(f'Connected to PostgreSQL version: {result}')
            return True
    except Exception as e:
        logger.warning('Failed to fetch DB version: %s', e)
        return False
    

# Функция, проверяющая существуют таблицы в БД или нет
async def check_if_tables_exist(engine: AsyncEngine) -> bool:
    async with engine.connect() as connection:
        inspector = await connection.run_sync(lambda sync_conn: inspect(sync_conn))
        existings_tables = await connection.run_sync(
            lambda sync_conn: inspector.get_table_names()
        )
        logger.info(
            'Tables were create earliy: %s. All - %s', 
            existings_tables, 
            len(existings_tables)
        )
        return len(existings_tables) > 0


# Создает таблицы, если они не существуют
async def init_tables(engine: AsyncEngine) -> None:
    if await check_if_tables_exist(engine):
        logger.info('Tables were create earliy')
        return 
    
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )
    logger.info('All tables were create')


# Создает записи в таблице role
async def create_roles(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        try: 
            query = select(Role)
            result = await session.execute(
                query
            )
            rows = result.scalars().all()

            if len(rows) > 0:
                logger.info('Roles already exist: %s', 
                            rows)
                return
                
            session.add_all([
                Role(id=1, name='user'),
                Role(id=2, name='admin')
            ])
            await session.commit() 
            logger.info('Roles created successfully')
        except Exception as e:
            await session.rollback()  # Откатываем транзакцию
            logger.error('Error creating roles: %s', e)
            raise

# Содзание записей в таблице language
async def create_languages(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        try:
            result = await session.execute(
                select(Language)
            )
            rows = result.scalars().all()

            if len(rows) > 0:
                logger.info(
                    'Languages already exist: %s', rows
                )
                return 
            
            session.add_all([
                Language(code='en', name='English', emoji='🇬🇧'), 
                Language(code='ru', name='Русский', emoji='🇷🇺'),
            ])
            await session.commit()
            logger.info('Language created successfully!')
        except Exception as e:
            await session.rollback()
            logger.error('Error creating languages: %s', e)
            raise


# Содзание записей в таблице complexity_level
async def create_complexity_levels(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        try:
            result = await session.execute(
                select(ComplexityLevel)
            )
            rows = result.scalars().all()

            if len(rows) > 0:
                logger.info(
                    'Complexity level already exist: %s', rows
                )
                return 
            
            session.add_all([
                ComplexityLevel(id=1, name='Novice', emoji='🐣'),
                ComplexityLevel(id=2, name='Student', emoji='👨🏼‍🎓'),
                ComplexityLevel(id=3, name='Researcher', emoji='👨🏼‍💻'),
            ])
            await session.commit()
            logger.info('Complexity level created successfully!')
        except Exception as e:
            await session.rollback()
            logger.error('Error creating complexity level: %s', e)
            raise


# Содзание записей в таблице backend
async def create_backends(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        try:
            result = await session.execute(
                select(Backend)
            )
            rows = result.scalars().all()

            if len(rows) > 0:
                logger.info(
                    'Backend already exist: %s', rows
                )
                return 
            
            session.add_all([
                Backend(id=1, name='AriQuantum', max_qubits=6), 
                Backend(id=2, name='Qiskit', max_qubits=10)
            ])
            await session.commit()
            logger.info('Backends created successfully!')
        except Exception as e:
            await session.rollback()
            logger.error('Error creating backends: %s', e)
            raise


async def init_db(engine: AsyncEngine, 
                  session_factory: async_sessionmaker[AsyncSession]) -> bool:
    try:
        logger.info('Initialization of bd is started')

        if not await log_db_version(engine):
            return False 
        
        logger.info('Initialization tables start')
        await init_tables(engine)

        # Создаем все необходимые записи
        await create_roles(session_factory)
        await create_languages(session_factory)
        await create_complexity_levels(session_factory)
        await create_backends(session_factory)


        logger.info('Successfully initialization bd!')
        return True 
    except Exception as e:
        logger.error('Database initialization failed: %s', e)
        return False





