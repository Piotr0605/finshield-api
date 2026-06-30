"""add_budget_org_category_unique

Revision ID: b3f8a2c91d04
Revises: affe1ccf6a41
Create Date: 2026-06-25 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b3f8a2c91d04"
down_revision: Union[str, Sequence[str], None] = "affe1ccf6a41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_budgets_org_category",
        "budgets",
        ["organization_id", "category"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_budgets_org_category", "budgets", type_="unique")
