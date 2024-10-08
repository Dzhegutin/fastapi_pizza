"""Initial migration2

Revision ID: d377950785e1
Revises: ffe4a0b4afdf
Create Date: 2024-08-27 17:01:45.354417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd377950785e1'
down_revision: Union[str, None] = 'ffe4a0b4afdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('pizza_prices', 'pizza_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('pizza_prices', 'dough_type_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('pizza_prices', 'dough_thickness_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_index('ix_pizza_prices_id', table_name='pizza_prices')
    op.drop_column('pizza_prices', 'id')
    op.drop_index('ix_user_pizza_cart_id', table_name='user_pizza_cart')
    op.drop_column('user_pizza_cart', 'id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_pizza_cart', sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_index('ix_user_pizza_cart_id', 'user_pizza_cart', ['id'], unique=False)
    op.add_column('pizza_prices', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.create_index('ix_pizza_prices_id', 'pizza_prices', ['id'], unique=False)
    op.alter_column('pizza_prices', 'dough_thickness_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('pizza_prices', 'dough_type_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('pizza_prices', 'pizza_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
