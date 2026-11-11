from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.models import (
    User, UserSetting, QuantumCircuit, QuantumSimulation, UserActivityLog
)


class UserStatRepository:
    async def search_users(self, session: AsyncSession, query: str) -> list[User]:
        """Поиск пользователей по ID → username → first/last name. Возвращает список."""
        # 1. Поиск по ID (если ввели число)
        if query.isdigit():
            res = await session.execute(
                select(User)
                .where(User.id == int(query))
                .options(
                    selectinload(User.setting).selectinload(UserSetting.language),
                    selectinload(User.setting).selectinload(UserSetting.complexity_level),
                    selectinload(User.setting).selectinload(UserSetting.backend),
                    selectinload(User.role),
                )
            )
            if u := res.scalar_one_or_none():
                return [u]

        # 2. Поиск по username
        res = await session.execute(
            select(User)
            .where(User.username.ilike(query.lstrip("@")))
            .options(
                selectinload(User.setting).selectinload(UserSetting.language),
                selectinload(User.setting).selectinload(UserSetting.complexity_level),
                selectinload(User.setting).selectinload(UserSetting.backend),
                selectinload(User.role),
            )
        )
        if u := res.scalar_one_or_none():
            return [u]

        # 3. Поиск по имени и фамилии (возвращает всех найденных)
        res = await session.execute(
            select(User)
            .where(
                (User.first_name.ilike(f"%{query}%"))
                | (User.last_name.ilike(f"%{query}%"))
            )
            .options(
                selectinload(User.setting).selectinload(UserSetting.language),
                selectinload(User.setting).selectinload(UserSetting.complexity_level),
                selectinload(User.setting).selectinload(UserSetting.backend),
                selectinload(User.role),
            )
        )
        return list(res.scalars().all())


    async def get_user_circuits_with_stats(self, session: AsyncSession, user_id: int):
        res = await session.execute(
            select(QuantumCircuit, func.count(QuantumSimulation.id).label('sim_count'))
            .outerjoin(QuantumSimulation, QuantumCircuit.id == QuantumSimulation.circuit_id)
            .where(QuantumCircuit.user_id == user_id)
            .group_by(QuantumCircuit.id)
            # УБРАНО: .options(selectinload(QuantumCircuit.backend)) - так как у схемы больше нет бэкенда
            .order_by(desc(QuantumCircuit.created_at))
        )
        return res.all()


    async def get_user_simulation_stats(self, session: AsyncSession, user_id: int):
        from ..models.models import Backend
        
        res = await session.execute(
            select(
                Backend.name,
                func.count(QuantumSimulation.id).label('total_sims'),
                func.avg(QuantumCircuit.num_qubits).label('avg_qubits'),
                func.avg(QuantumSimulation.execution_time).label('avg_time'),
                func.max(QuantumSimulation.execution_time).label('max_time'),
            )
            .select_from(QuantumSimulation)
            .join(QuantumCircuit, QuantumSimulation.circuit_id == QuantumCircuit.id)
            # ИЗМЕНЕНО: теперь джойним бэкенд через симуляцию
            .join(Backend, QuantumSimulation.backend_id == Backend.id)
            .where(QuantumSimulation.user_id == user_id)
            .group_by(Backend.name)
        )
        by_backend = {row.name: {
            'total': row.total_sims,
            'avg_qubits': float(row.avg_qubits) if row.avg_qubits else 0,
            'avg_time': float(row.avg_time) if row.avg_time else 0,
            'max_time': float(row.max_time) if row.max_time else 0,
        } for row in res.all()}

        res = await session.execute(
            select(
                func.avg(QuantumCircuit.num_qubits).label('avg_qubits'),
                func.avg(QuantumSimulation.execution_time).label('avg_time'),
            )
            .join(QuantumCircuit, QuantumSimulation.circuit_id == QuantumCircuit.id)
            .where(QuantumSimulation.user_id == user_id)
        )
        row = res.one()
        overall = {
            'avg_qubits': float(row.avg_qubits) if row.avg_qubits else 0,
            'avg_time': float(row.avg_time) if row.avg_time else 0,
        }
        return {'by_backend': by_backend, 'overall': overall}


    async def get_user_activity_logs(self, session: AsyncSession, user_id: int, limit: int = 50):
        res = await session.execute(
            select(UserActivityLog)
            .where(UserActivityLog.user_id == user_id)
            .order_by(desc(UserActivityLog.activity_date))
            .limit(limit)
        )
        return res.scalars().all()


    async def get_user_activity_count(self, session: AsyncSession, user_id: int):
        res = await session.execute(
            select(func.count(UserActivityLog.id)).where(UserActivityLog.user_id == user_id)
        )
        return res.scalar() or 0


    async def toggle_user_block(self, session: AsyncSession, user_id: int) -> bool:
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if user:
            user.is_blocked = not user.is_blocked
            await session.commit()
            return user.is_blocked
        return False


    async def get_user_full(self, session: AsyncSession, user_id: int):
        res = await session.execute(
            select(User).where(User.id == user_id).options(
                selectinload(User.setting).selectinload(UserSetting.language),
                selectinload(User.setting).selectinload(UserSetting.complexity_level),
                selectinload(User.setting).selectinload(UserSetting.backend),
                selectinload(User.role),
            )
        )
        return res.scalar_one_or_none()