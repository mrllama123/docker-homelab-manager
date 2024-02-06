"""new error tables

Revision ID: 7c64154a5d29
Revises: 993ffcfdbaa0
Create Date: 2024-02-06 21:36:50.547203

"""
from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c64154a5d29'
down_revision: Union[str, None] = '993ffcfdbaa0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('errorbackups',
    sa.Column('backup_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('backup_id')
    )
    op.create_table('errorrestoredbackups',
    sa.Column('restore_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('restore_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('errorrestoredbackups')
    op.drop_table('errorbackups')
    # ### end Alembic commands ###
