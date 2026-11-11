"""update user_settings

Revision ID: b1d1ea346e61
Revises: 8308308567d4
Create Date: 2026-08-12 20:24:36.465424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1d1ea346e61'
down_revision: Union[str, Sequence[str], None] = '8308308567d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Делаем поля nullable=True
    op.alter_column('quantum_simulation', 'backend_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('user_setting', 'simulation_shots',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('user_setting', 'backend_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Возвращаем nullable=False при откате
    op.alter_column('user_setting', 'backend_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('user_setting', 'simulation_shots',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('quantum_simulation', 'backend_id',
               existing_type=sa.INTEGER(),
               nullable=False)
