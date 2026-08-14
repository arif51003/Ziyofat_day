"""add multi-tenant restaurant support

Revision ID: ee864af4201a
Revises: 3d0a954ea1a7
Create Date: 2026-08-14 16:20:02.295179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ee864af4201a'
down_revision: Union[str, Sequence[str], None] = '3d0a954ea1a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every existing row in these tables predates multi-tenancy and belongs to
# the single restaurant this app used to serve. They all get backfilled to
# the "default" restaurant created below.
TENANT_TABLES_NOT_NULL = [
    "dining_table",
    "menu_category",
    "menu_item",
    "menu_item_variant",
    "orders",
    "order_item",
    "payment",
    "ingredients",
    "menu_ingredient",
    "ingredient_stock",
    "stock_movements",
    "audit_log",
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'restaurants',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('subscription_status', sa.String(length=20), nullable=False),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    restaurants = sa.table(
        'restaurants',
        sa.column('id', sa.BigInteger),
        sa.column('name', sa.String),
        sa.column('code', sa.String),
        sa.column('subscription_status', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    conn = op.get_bind()
    default_restaurant_id = conn.execute(
        restaurants.insert()
        .values(
            name="Ziyofat Day",
            code="ziyofat",
            subscription_status="active",
            is_active=True,
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
        .returning(restaurants.c.id)
    ).scalar_one()

    # Nullable so existing rows don't error, backfilled below, then locked to NOT NULL.
    for table in TENANT_TABLES_NOT_NULL:
        op.add_column(table, sa.Column('restaurant_id', sa.BigInteger(), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table} SET restaurant_id = :rid WHERE restaurant_id IS NULL")
            .bindparams(rid=default_restaurant_id)
        )
        op.alter_column(table, 'restaurant_id', nullable=False)
        op.create_foreign_key(None, table, 'restaurants', ['restaurant_id'], ['id'])

    # users.restaurant_id stays nullable: NULL identifies a platform-owner account.
    op.add_column('users', sa.Column('restaurant_id', sa.BigInteger(), nullable=True))
    op.execute(
        sa.text("UPDATE users SET restaurant_id = :rid WHERE restaurant_id IS NULL")
        .bindparams(rid=default_restaurant_id)
    )
    op.create_foreign_key(None, 'users', 'restaurants', ['restaurant_id'], ['id'])

    op.add_column('users', sa.Column('is_platform_owner', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'is_platform_owner', server_default=None)

    op.drop_constraint(op.f('users_username_key'), 'users', type_='unique')
    op.create_unique_constraint('uq_user_restaurant_username', 'users', ['restaurant_id', 'username'])
    # Postgres treats NULLs as distinct, so the composite unique constraint above doesn't
    # stop two platform-owner accounts (restaurant_id IS NULL) from sharing a username.
    op.execute(
        "CREATE UNIQUE INDEX uq_platform_owner_username ON users (username) WHERE restaurant_id IS NULL"
    )

    op.drop_constraint(op.f('dining_table_table_no_key'), 'dining_table', type_='unique')
    op.create_unique_constraint('uq_table_restaurant_no', 'dining_table', ['restaurant_id', 'table_no'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_table_restaurant_no', 'dining_table', type_='unique')
    op.create_unique_constraint(op.f('dining_table_table_no_key'), 'dining_table', ['table_no'])

    op.execute("DROP INDEX IF EXISTS uq_platform_owner_username")
    op.drop_constraint('uq_user_restaurant_username', 'users', type_='unique')
    op.create_unique_constraint(op.f('users_username_key'), 'users', ['username'])

    op.drop_column('users', 'is_platform_owner')
    op.drop_constraint('users_restaurant_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'restaurant_id')

    for table in reversed(TENANT_TABLES_NOT_NULL):
        op.drop_constraint(f'{table}_restaurant_id_fkey', table, type_='foreignkey')
        op.drop_column(table, 'restaurant_id')

    op.drop_table('restaurants')
