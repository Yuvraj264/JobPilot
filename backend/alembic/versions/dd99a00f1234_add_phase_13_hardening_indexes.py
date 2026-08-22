"""add_phase_13_hardening_indexes

Revision ID: dd99a00f1234
Revises: be68281f1ea3
Create Date: 2026-08-22 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd99a00f1234'
down_revision: Union[str, None] = 'be68281f1ea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraints to prevent duplicate database matches and duplicate applications
    op.create_unique_constraint('uq_job_matches_job_profile', 'job_matches', ['job_id', 'profile_id'])
    op.create_unique_constraint('uq_applications_job_profile', 'applications', ['job_id', 'profile_id'])


def downgrade() -> None:
    # Drop unique constraints
    op.drop_constraint('uq_job_matches_job_profile', 'job_matches', type_='unique')
    op.drop_constraint('uq_applications_job_profile', 'applications', type_='unique')
