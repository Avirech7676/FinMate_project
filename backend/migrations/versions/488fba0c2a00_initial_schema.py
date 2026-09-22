"""initial_schema

Revision ID: 488fba0c2a00
Revises: 
Create Date: 2026-09-22 19:15:49.256563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '488fba0c2a00'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(), unique=True, index=True),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('preferences', sa.String(), nullable=True, server_default="{}"),
        sa.Column('currency', sa.String(), nullable=True, server_default="USD"),
        sa.Column('currency_symbol', sa.String(), nullable=True, server_default="$")
    )

    # 2. financial_profiles
    op.create_table(
        'financial_profiles',
        sa.Column('profile_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), unique=True),
        sa.Column('monthly_income', sa.Float(), nullable=True, server_default="0.0"),
        sa.Column('employment_type', sa.String(), nullable=True),
        sa.Column('risk_tolerance', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

    # 3. transactions
    op.create_table(
        'transactions',
        sa.Column('transaction_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), index=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True, index=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True)
    )

    # 4. budget_goals
    op.create_table(
        'budget_goals',
        sa.Column('goal_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('goal_type', sa.String(), nullable=True),
        sa.Column('target_amount', sa.Float(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('current_progress', sa.Float(), nullable=True, server_default="0.0"),
        sa.Column('status', sa.String(), nullable=True, server_default="active"),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 5. user_stats
    op.create_table(
        'user_stats',
        sa.Column('stat_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), unique=True),
        sa.Column('total_xp', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('current_streak', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('longest_streak', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('total_transactions', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('total_spending', sa.Float(), nullable=True, server_default="0.0"),
        sa.Column('last_streak_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

    # 6. achievements
    op.create_table(
        'achievements',
        sa.Column('achievement_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('achievement_type', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('xp_reward', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True)
    )

    # 7. notifications
    op.create_table(
        'notifications',
        sa.Column('notification_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('notification_type', sa.String(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default="0"),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 8. receipts_pending
    op.create_table(
        'receipts_pending',
        sa.Column('receipt_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('extracted_data', sa.String(), nullable=True),
        sa.Column('receipt_image_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default="pending"),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 9. subscription_decisions
    op.create_table(
        'subscription_decisions',
        sa.Column('decision_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), index=True),
        sa.Column('candidate_id', sa.String(), nullable=True, index=True),
        sa.Column('merchant', sa.String(), nullable=True),
        sa.Column('avg_amount', sa.Float(), nullable=True, server_default="0.0"),
        sa.Column('interval_days', sa.Integer(), nullable=True, server_default="30"),
        sa.Column('occurrences', sa.Integer(), nullable=True, server_default="0"),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 10. Performance & Composite Indexes
    op.create_index('ix_transactions_user_date', 'transactions', ['user_id', 'date'])
    op.create_index('ix_budget_goals_user', 'budget_goals', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_budget_goals_user', table_name='budget_goals')
    op.drop_index('ix_transactions_user_date', table_name='transactions')
    op.drop_table('subscription_decisions')
    op.drop_table('receipts_pending')
    op.drop_table('notifications')
    op.drop_table('achievements')
    op.drop_table('user_stats')
    op.drop_table('budget_goals')
    op.drop_table('transactions')
    op.drop_table('financial_profiles')
    op.drop_table('users')
