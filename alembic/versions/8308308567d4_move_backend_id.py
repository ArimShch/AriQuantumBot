"""move_backend_id

Revision ID: 8308308567d4
Revises: 1c2b59ebff46
Create Date: 2026-08-12 15:46:56.849722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8308308567d4'
down_revision: Union[str, Sequence[str], None] = '1c2b59ebff46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Сначала добавляем новую колонку в quantum_simulation (пока как nullable=True)
    op.add_column('quantum_simulation', sa.Column('backend_id', sa.Integer(), nullable=True))
    
    # 2. ПЕРЕНОСИМ ДАННЫЕ с помощью SQL-запроса
    op.execute("""
        UPDATE quantum_simulation qs
        SET backend_id = qc.backend_id
        FROM quantum_circuit qc
        WHERE qs.circuit_id = qc.id;
    """)
    
    # 3. Ставим бэкенд по умолчанию (AriQuantum id=1) для симуляций, у которых вдруг нет схемы (circuit_id IS NULL)
    op.execute("UPDATE quantum_simulation SET backend_id = 1 WHERE backend_id IS NULL;")
    
    # 4. Теперь делаем колонку обязательной (NOT NULL)
    op.alter_column('quantum_simulation', 'backend_id', nullable=False)
    
    # 5. Создаем внешний ключ для новой колонки с явным именем
    op.create_foreign_key('fk_quantum_simulation_backend_id', 'quantum_simulation', 'backend', ['backend_id'], ['id'], ondelete='RESTRICT')
    
    # 6. Только теперь безопасно удаляем старый внешний ключ и саму колонку из quantum_circuit
    op.drop_constraint(op.f('quantum_circuit_backend_id_fkey'), 'quantum_circuit', type_='foreignkey')
    op.drop_column('quantum_circuit', 'backend_id')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Возвращаем колонку в quantum_circuit (пока nullable=True)
    op.add_column('quantum_circuit', sa.Column('backend_id', sa.INTEGER(), autoincrement=False, nullable=True))
    
    # 2. Переносим данные ОБРАТНО (если понадобится откатить миграцию)
    op.execute("""
        UPDATE quantum_circuit qc
        SET backend_id = qs.backend_id
        FROM quantum_simulation qs
        WHERE qs.circuit_id = qc.id;
    """)
    
    # Дефолт и NOT NULL
    op.execute("UPDATE quantum_circuit SET backend_id = 1 WHERE backend_id IS NULL;")
    op.alter_column('quantum_circuit', 'backend_id', nullable=False)
    
    # 3. Восстанавливаем внешний ключ
    op.create_foreign_key(op.f('quantum_circuit_backend_id_fkey'), 'quantum_circuit', 'backend', ['backend_id'], ['id'], ondelete='RESTRICT')
    
    # 4. Удаляем колонку и ключ из quantum_simulation
    op.drop_constraint('fk_quantum_simulation_backend_id', 'quantum_simulation', type_='foreignkey')
    op.drop_column('quantum_simulation', 'backend_id')