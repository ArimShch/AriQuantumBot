"""add output_mode to user_setting

Revision ID: c7a41f2d9e10
Revises: b1d1ea346e61
Create Date: 2026-11-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a41f2d9e10'
down_revision: Union[str, Sequence[str], None] = 'b1d1ea346e61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default заполнит существующих пользователей значением 'widget'
    op.add_column(
        'user_setting',
        sa.Column('output_mode', sa.String(length=10), server_default=sa.text("'widget'"), nullable=False),
    )
    op.create_check_constraint(
        'ck_user_setting_output_mode',
        'user_setting',
        "output_mode IN ('widget', 'ascii')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_user_setting_output_mode', 'user_setting', type_='check')
    op.drop_column('user_setting', 'output_mode')
