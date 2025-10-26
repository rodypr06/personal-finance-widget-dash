"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-10-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema with all tables and indexes.
    """
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('txn_date', sa.Date(), nullable=False),
        sa.Column('posted_at', postgresql.TIMESTAMPTZ(), server_default=sa.text('now()'), nullable=False),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False, server_default='USD'),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('raw_descriptor', sa.Text(), nullable=False),
        sa.Column('canonical_vendor', sa.Text(), nullable=True),
        sa.Column('mcc', sa.Text(), nullable=True),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('source_account', sa.Text(), nullable=False),
        sa.Column('hash_id', sa.Text(), nullable=False),
        sa.Column('receipt_url', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('subcategory', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='ingested'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.CheckConstraint("direction IN ('debit', 'credit')", name='transactions_direction_check'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hash_id')
    )

    # Create indexes for transactions
    op.create_index('ix_transactions_txn_date', 'transactions', ['txn_date'])
    op.create_index('ix_transactions_canonical_vendor', 'transactions', ['canonical_vendor'])
    op.create_index('ix_transactions_category', 'transactions', ['category'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])

    # Create vendors table
    op.create_table(
        'vendors',
        sa.Column('canonical_vendor', sa.Text(), nullable=False),
        sa.Column('default_category', sa.Text(), nullable=True),
        sa.Column('default_subcat', sa.Text(), nullable=True),
        sa.Column('aliases', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('canonical_vendor')
    )

    # Create rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('action', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', postgresql.TIMESTAMPTZ(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for rules
    op.create_index('ix_rules_active_priority', 'rules', ['active', 'priority'])

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('period', sa.Text(), nullable=False),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMPTZ(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for reports
    op.create_index('ix_reports_period_kind', 'reports', ['period', 'kind'])


def downgrade() -> None:
    """
    Drop all tables and indexes.
    """
    op.drop_index('ix_reports_period_kind', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_rules_active_priority', table_name='rules')
    op.drop_table('rules')

    op.drop_table('vendors')

    op.drop_index('ix_transactions_status', table_name='transactions')
    op.drop_index('ix_transactions_category', table_name='transactions')
    op.drop_index('ix_transactions_canonical_vendor', table_name='transactions')
    op.drop_index('ix_transactions_txn_date', table_name='transactions')
    op.drop_table('transactions')
