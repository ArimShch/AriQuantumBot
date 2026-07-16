import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, delete, insert, text 

from ..models.models import UserActivityLog, User, QuantumCircuit, QuantumSimulation, Backend, UserSetting, Language, ComplexityLevel


logger = logging.getLogger(__name__)


class ActivityRepository:
    # Получение активности определенного пользователя
    async def get_activity_today(
            self, session: AsyncSession, tg_id: int, 
    ):
        query = (
            select(UserActivityLog)
            .where(UserActivityLog.user_id == tg_id, 
                   UserActivityLog.activity_date == datetime.now().date())
        )
        row = await session.execute(query)
        row = row.scalar_one_or_none()

        logger.info('Get user activity tg_id=%d', tg_id)

        return row 

    # Создание активности для определенного пользователя
    async def create_activity_today(
            self, session: AsyncSession, tg_id: int, 
    ):
        activity_today = UserActivityLog(
            user_id=tg_id, 
        )
        session.add(activity_today)
        await session.flush()
        await session.refresh(activity_today)

    # Получени количества всех пользователей в системе
    async def get_count_users(
            self, 
            session: AsyncSession, 
    ):
        query = select(func.count(User.id))

        result = await session.execute(
            query
        )

        row = result.scalar_one_or_none()

        return row 
    
    # Получение статистики использования за последние 20 дней
    async def get_user_activity_last_20_days(self, session: AsyncSession):
        ten_days_ago = datetime.now().date() - timedelta(days=20)

        query = (
            select(UserActivityLog.activity_date, func.count(UserActivityLog.user_id))
            .where(UserActivityLog.activity_date >= ten_days_ago)
            .group_by(UserActivityLog.activity_date)
            .order_by(UserActivityLog.activity_date.desc())
        )
        result = await session.execute(query)
        rows = result.fetchall()

        return rows 
    
    # Получение ТОП 5 Пользователей по использованию Бота (дни)
    async def get_top_10_user_activity_days(
            self, session: AsyncSession, 
    ):
        query = (
            select(User.username, func.count(UserActivityLog.user_id))
            .join(User)
            .group_by(User.username)
            .order_by(func.count(UserActivityLog.user_id).desc())
            .limit(5)
        )
        result = await session.execute(query)
        rows = result.fetchall()
        
        return rows 
    
    # Получение ТОП 5 Пользователей по использованию Бота (созданные схемы)
    async def get_top_10_user_activity_circuits(
            self, session: AsyncSession, 
    ):
        query = (
            select(User.username, func.sum(UserActivityLog.circuits_created))
            .join(User)
            .group_by(User.username)
            .order_by(func.sum(UserActivityLog.circuits_created).desc())
            .limit(5)
        )
        result = await session.execute(query)
        rows = result.fetchall()
        
        return rows 

    # Получение ТОП 5 Пользователей по использованию Бота (запущенные симуляции)
    async def get_top_10_user_activity_simulations(
            self, session: AsyncSession, 
    ):
        query = (
            select(User.username, func.sum(UserActivityLog.simulations_run))
            .join(User)
            .group_by(User.username)
            .order_by(func.sum(UserActivityLog.simulations_run).desc())
            .limit(5)
        )
        result = await session.execute(query)
        rows = result.fetchall()
        
        return rows 

    
    # Получение кол-ва схем в БД (на данный момент сколько всего схем)
    async def get_count_circuits_now(
            self, 
            session: AsyncSession, 
    ):
        query = (
            select(func.count(QuantumCircuit.id))
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        return row 
    
    # Получение кол-ва схем созданных за ВСЕ время
    async def get_count_circuits_all(
            self, 
            session: AsyncSession, 
    ):
        query = select(func.sum(UserActivityLog.circuits_created))
        result = await session.execute(query)
        row = result.scalar_one_or_none()

        return row

    # Получени статистики создания схем и запусков за последние 20 дней
    async def get_circuits_activity_last_20_days(
            self, 
            session: AsyncSession, 
    ):
        twenty_days_ago = datetime.now().date() - timedelta(days=20)

        query = (
            select(UserActivityLog.activity_date, func.sum(UserActivityLog.circuits_created), func.sum(UserActivityLog.simulations_run))
            .where(UserActivityLog.activity_date >= twenty_days_ago)
            .group_by(UserActivityLog.activity_date)
            .order_by(UserActivityLog.activity_date.desc())
        )
        result = await session.execute(query)
        rows = result.fetchall()

        return rows 
    
    # Получение кол-ва запусков в БД (на данный момент - к списку существующих схем)
    async def get_count_simulations_now(
            self, 
            session: AsyncSession, 
    ):
        query = (
            select(func.count(QuantumSimulation.id))
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        return row 
    
    # Получение кол-ва запусков за ВСЕ время
    async def get_count_simulations_all(
            self, 
            session: AsyncSession, 
    ):
        query = select(func.sum(UserActivityLog.simulations_run))
        result = await session.execute(query)
        row = result.scalar_one_or_none()

        return row
    
    # Получение среднего кол-ва кубитов на всех схемах
    async def get_avg_count_qubits(
            self, 
            session: AsyncSession, 
    ):
        query = select(func.avg(QuantumCircuit.num_qubits))
        result = await session.execute(query)
        avg_qubits = result.scalar()

        return float(avg_qubits) if avg_qubits is not None else None
    
    # Получение среднего кол-ва времени выполнения на всех схемах
    async def get_avg_time(
            self, 
            session: AsyncSession, 
    ):
        query = select(func.avg(QuantumSimulation.execution_time))
        result = await session.execute(query)
        avg_time = result.scalar()

        return float(avg_time) if avg_time is not None else None
        
    # Получение кол-ва схем по бэкендам
    async def get_circuits_by_backends(self, session: AsyncSession):
        query = (
            select(Backend.name, func.count(QuantumCircuit.id))
            .select_from(QuantumCircuit)
            .join(Backend)
            .group_by(Backend.name, Backend.id)
            .order_by(Backend.name)
        )
        result = await session.execute(query)
        return result.fetchall()


    # Получение кол-ва симуляций по бэкендам
    async def get_simulations_by_backends(self, session: AsyncSession):
        query = (
            select(Backend.name, func.count(QuantumSimulation.id))
            .select_from(QuantumSimulation)
            .join(QuantumCircuit)
            .join(Backend)
            .group_by(Backend.name, Backend.id)
            .order_by(Backend.name)
        )
        result = await session.execute(query)
        return result.fetchall()


    # Среднее кол-во кубитов по бэкендам
    async def get_avg_qubits_by_backends(self, session: AsyncSession):
        query = (
            select(Backend.name, func.avg(QuantumCircuit.num_qubits))
            .select_from(QuantumCircuit)
            .join(Backend)
            .group_by(Backend.name, Backend.id)
            .order_by(Backend.name)
        )
        result = await session.execute(query)
        return result.fetchall()


    # Среднее время исполнения симуляции по бэкендам
    async def get_avg_time_simulations_by_backends(self, session: AsyncSession):
        query = (
            select(Backend.name, func.avg(QuantumSimulation.execution_time))
            .select_from(QuantumSimulation)
            .join(QuantumCircuit)
            .join(Backend)
            .group_by(Backend.name, Backend.id)
            .order_by(Backend.name)
        )
        result = await session.execute(query)
        return result.fetchall()
    
    async def get_users_by_language(self, session: AsyncSession):
        """Статистика по языкам"""
        result = await session.execute(
            select(Language.emoji, Language.name, func.count(UserSetting.id))
            .select_from(UserSetting)
            .join(Language)
            .group_by(Language.emoji, Language.name)
            .order_by(func.count(UserSetting.id).desc())
        )
        return result.fetchall()


    async def get_users_by_complexity_level(self, session: AsyncSession):
        """Статистика по уровням сложности"""
        result = await session.execute(
            select(ComplexityLevel.emoji, ComplexityLevel.name, func.count(UserSetting.id))
            .select_from(UserSetting)
            .join(ComplexityLevel)
            .group_by(ComplexityLevel.emoji, ComplexityLevel.name)
            .order_by(func.count(UserSetting.id).desc())
        )
        return result.fetchall()


    async def get_users_by_backend(self, session: AsyncSession):
        """Статистика по бэкендам"""
        result = await session.execute(
            select(Backend.name, func.count(UserSetting.id))
            .select_from(UserSetting)
            .join(Backend)
            .group_by(Backend.id, Backend.name)
            .order_by(func.count(UserSetting.id).desc())
        )
        return result.fetchall()


    async def get_automatic_name_stats(self, session: AsyncSession):
        """Статистика по автоматическому именованию"""
        result = await session.execute(
            select(UserSetting.automatic_name, func.count(UserSetting.id))
            .group_by(UserSetting.automatic_name)
        )
        return result.fetchall()


    async def get_qubit_input_text_stats(self, session: AsyncSession):
        """Статистика по вводу кубитов текстом"""
        result = await session.execute(
            select(UserSetting.qubit_input_text, func.count(UserSetting.id))
            .group_by(UserSetting.qubit_input_text)
        )
        return result.fetchall()


    async def get_simulation_shots_distribution(self, session: AsyncSession):
        """Распределение количества запусков симуляции"""
        result = await session.execute(
            select(UserSetting.simulation_shots, func.count(UserSetting.id))
            .group_by(UserSetting.simulation_shots)
            .order_by(UserSetting.simulation_shots)
        )
        return result.fetchall()
    

    async def get_avg_simulation_shots_distribution(self, session: AsyncSession):
        """Среднее значение кол-ва запусков"""
        result = await session.execute(
            select(func.avg(UserSetting.simulation_shots))
        )
        return result.scalar_one_or_none()

    async def get_users_by_ref_source(self, session: AsyncSession):
        """Статистика по источникам перехода (ref_source)"""
        # Создаём выражение ОДИН РАЗ и используем его везде
        source_expr = func.coalesce(User.ref_source, 'direct')
        
        result = await session.execute(
            select(source_expr.label('source'), func.count(User.id))
            .group_by(source_expr)  # ← Группируем по тому же выражению
            .order_by(func.count(User.id).desc())
        )
        return result.fetchall()


    async def get_users_by_tg_locale(self, session: AsyncSession):
        """Статистика по языкам Telegram пользователей (tg_locate)"""
        locale_expr = func.coalesce(User.tg_locate, 'unknown')
        
        result = await session.execute(
            select(locale_expr.label('locale'), func.count(User.id))
            .group_by(locale_expr)  # ← Группируем по тому же выражению
            .order_by(func.count(User.id).desc())
        )
        return result.fetchall()
    

        

