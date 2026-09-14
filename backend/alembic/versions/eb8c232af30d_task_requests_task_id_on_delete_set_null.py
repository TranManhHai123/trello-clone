"""task_requests task_id on delete set null

Revision ID: eb8c232af30d
Revises: aa595449eec7
Create Date: 2026-09-14 15:08:04.078266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb8c232af30d'
down_revision: Union[str, Sequence[str], None] = 'aa595449eec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "task_requests_task_id_fkey", "task_requests", type_="foreignkey"
    )
    op.create_foreign_key(
        "task_requests_task_id_fkey",
        "task_requests", "tasks",
        ["task_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "task_requests_task_id_fkey", "task_requests", type_="foreignkey"
    )
    op.create_foreign_key(
        "task_requests_task_id_fkey",
        "task_requests", "tasks",
        ["task_id"], ["id"],
    )
