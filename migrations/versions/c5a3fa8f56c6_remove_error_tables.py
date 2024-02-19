"""remove error tables

Revision ID: c5a3fa8f56c6
Revises: 677098e97ac3
Create Date: 2024-02-19 18:17:18.494206

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5a3fa8f56c6"
down_revision: Union[str, None] = "677098e97ac3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("backups", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "successful",
                sa.Boolean(),
                nullable=False,
                default=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "error_message",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=True,
            )
        )
        batch_op.alter_column(
            "backup_created", new_column_name="created_at", nullable=True
        )

    with op.batch_alter_table("restoredbackups", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("successful", sa.Boolean(), nullable=False, default=True)
        )
        batch_op.add_column(
            sa.Column(
                "error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True
            )
        )
        batch_op.alter_column(
            "restored_date", new_column_name="created_at", nullable=True
        )

    op.execute(
        "INSERT INTO backups (backup_id, backup_name, error_message, successful) SELECT backup_id, backup_name, error_message, false FROM errorbackups"
    )

    op.execute(
        "INSERT INTO restoredbackups (restore_id, restore_name, error_message, successful) SELECT restore_id, restore_name, error_message, false FROM errorrestoredbackups"
    )

    op.drop_table("errorrestoredbackups")
    op.drop_table("errorbackups")


def downgrade() -> None:
    op.create_table(
        "errorbackups",
        sa.Column("backup_id", sa.VARCHAR(), nullable=False),
        sa.Column("backup_name", sa.VARCHAR(), nullable=True),
        sa.Column("error_message", sa.VARCHAR(), nullable=True),
        sa.PrimaryKeyConstraint("backup_id", name="pk_errorbackups"),
    )
    op.create_table(
        "errorrestoredbackups",
        sa.Column("restore_id", sa.VARCHAR(), nullable=False),
        sa.Column("restore_name", sa.VARCHAR(), nullable=True),
        sa.Column("error_message", sa.VARCHAR(), nullable=True),
        sa.PrimaryKeyConstraint("restore_id", name="pk_errorrestoredbackups"),
    )

    op.execute(
        "INSERT INTO errorbackups (backup_id, backup_name, error_message) SELECT backup_id, backup_name, error_message FROM backups WHERE successful = false"
    )

    op.execute(
        "INSERT INTO errorrestoredbackups (restore_id, restore_name, error_message) SELECT restore_id, restore_name, error_message FROM restoredbackups WHERE successful = false"
    )

    with op.batch_alter_table("restoredbackups", schema=None) as batch_op:
        batch_op.execute("DELETE FROM restoredbackups WHERE successful = false")
        batch_op.alter_column(
            "created_at", new_column_name="restored_date", nullable=True
        )
        batch_op.drop_column("error_message")
        batch_op.drop_column("successful")

    with op.batch_alter_table("backups", schema=None) as batch_op:
        batch_op.execute("DELETE FROM backups WHERE successful = false")
        batch_op.alter_column(
            "created_at", new_column_name="backup_created", nullable=False
        )
        batch_op.drop_column("error_message")
        batch_op.drop_column("successful")
