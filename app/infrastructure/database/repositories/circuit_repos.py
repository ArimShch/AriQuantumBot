import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, delete

from ..models.models import QuantumCircuit, QuantumSimulation


logger = logging.getLogger(__name__)


class CircuitRepository:
    async def get_max_quantum_circuit_id(
            self, 
            session: AsyncSession, 
    ):
        result = await session.execute(
            select(func.max(QuantumCircuit.id))
        )
        return result.scalar_one_or_none() or 0 
    
    async def create_circuit(
            self, 
            tg_id: int, 
            circuit_name: str, 
            num_qubits: int, 
            session: AsyncSession, # УБРАНО: backend_id
    ):
        circuit = QuantumCircuit(
            user_id=tg_id, 
            circuit_name=circuit_name, 
            num_qubits=num_qubits, 
            # backend_id убрано
        )
        session.add(circuit)
        await session.flush()
        await session.refresh(circuit)

        logger.info('QuantumCircuit added. user_id=%d, circuit_name=%s, num_qubits=%d', 
                    tg_id, 
                    circuit_name, 
                    num_qubits)
        
        return circuit
    
    async def user_is_owner(
            self, 
            session: AsyncSession, 
            tg_id: int, 
            circuit_id: int, 
    ):
        query = (
            select(QuantumCircuit)
            .where(QuantumCircuit.id==circuit_id, 
                   QuantumCircuit.user_id==tg_id)
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        logger.info(
            'User tg_id=%d is owner circuit circuit_id=%d: %s', 
            tg_id, 
            circuit_id, 
            True if row else False, 
        )

        return True if row else False
    
    async def get_circuit(
            self, 
            session: AsyncSession,
            tg_id: int, 
            circuit_id: int,
    ):
        query = (
            select(QuantumCircuit)
            .where(QuantumCircuit.id==circuit_id, 
                   QuantumCircuit.user_id==tg_id)
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        logger.info(
            'Circuit tg_id=%d circuit_id=%d: %s', 
            tg_id, 
            circuit_id, 
            True if row else False, 
        )

        return row
    
    async def is_unique_circuit_name(
            self, 
            session: AsyncSession,
            tg_id: int, 
            name: str
    ): 
        query = (
            select(QuantumCircuit)
            .where(QuantumCircuit.user_id == tg_id, 
                   QuantumCircuit.circuit_name == name)
        )
        result = await session.execute(
            query
        )
        rows = result.scalars().all()
        # print(rows)
        logger.info('Circuit name is unique: %s', False if rows else True)

        return False if rows else True
    

    # Функция получающая последнюю запись симуляции схемы
    async def get_last_simulation_circuit(
            self, 
            session: AsyncSession, 
            circuit_id: int, 
    ):
        query = (
            select(QuantumSimulation)
            .where(QuantumSimulation.circuit_id == circuit_id)
            .order_by(desc(QuantumSimulation.created_at))  # Сортировка по убыванию
            .limit(1)  # Берем только первую (самую новую) запись
        )

        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        logger.info('Last simulation circuit is %s', row)

        return row 
    
    
    # Функция, удаляющая схему по ее id 
    async def delete_circuit(self, session: AsyncSession, circuit_id: int):
        stmt = delete(QuantumCircuit).where(QuantumCircuit.id == circuit_id)
        logger.info("Circuit id=%d was deleted", circuit_id)
        await session.execute(stmt)

    # Функци, выдающая список измеренных кубитов
    async def get_measured_qubits(
            self, 
            session: AsyncSession, 
            tg_id: int,
            circuit_id: int) -> list[int]:
        circuit = await self.get_circuit(
            session=session, 
            tg_id=tg_id, 
            circuit_id=circuit_id, 
        )
        measured_qubits = set()
        
        for op in circuit.circuit_history:
            gate_name, ctrls, targets = op
            if gate_name == 'M':
                measured_qubits.update(targets)
        
        return list(measured_qubits) 


    async def create_simulation_result(
        self,
        session: AsyncSession,
        tg_id: int, 
        circuit_id: int,
        backend_id: int, # ДОБАВЛЕНО: backend_id
        braket_state: str,
        counts,
        execution_time: float,
        shots: int
    ) -> None:
        """Создает запись результата симуляции"""
        simulation = QuantumSimulation(
            user_id=tg_id, 
            circuit_id=circuit_id,
            backend_id=backend_id, # ДОБАВЛЕНО
            braket_state=braket_state,
            counts=counts,
            execution_time=execution_time,
            shots=shots
        )
        session.add(simulation)
        await session.flush()
        await session.refresh(simulation)

    
        