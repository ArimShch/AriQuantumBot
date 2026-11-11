from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from .draw_circuit import draw_history
from ...infrastructure.database.models.models import QuantumCircuit
from ...infrastructure.database.repositories import circuit_repository


async def render_circuit_details(
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit: QuantumCircuit,
) -> str:
    """Собирает HTML карточки схемы: диаграмма + состояние (из последней симуляции, если она есть)."""
    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session,
        circuit_id=circuit.id,
    )

    if last_simulation:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'
    else:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'

    return i18n.circuit_details(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        state_vector=state_vector,
        has_simulation=has_simulation,
    )
