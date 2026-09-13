"""Coverage policy, requests, and audit log."""
from alembic import op
import sqlalchemy as sa

revision = "0002_coverage_policy"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("coverage_policies",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("coverage_assignment_mode",sa.String(30),nullable=False),sa.Column("default_incentive_multiplier",sa.Float(),nullable=False),sa.Column("updated_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=True),sa.Column("updated_at",sa.DateTime(),nullable=False))
    op.create_table("coverage_requests",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("absent_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("requested_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("date",sa.Date(),nullable=False),sa.Column("required_hours",sa.Float(),nullable=False),sa.Column("incentive_multiplier",sa.Float(),nullable=False),sa.Column("status",sa.String(20),nullable=False),sa.Column("requested_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("responded_at",sa.DateTime(),nullable=True))
    op.create_table("coverage_audit_log",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("absent_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("replacement_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("assignment_mode",sa.String(30),nullable=False),sa.Column("incentive_multiplier",sa.Float(),nullable=False),sa.Column("required_hours",sa.Float(),nullable=False),sa.Column("performed_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("reason",sa.String(250),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False))

def downgrade():
    op.drop_table("coverage_audit_log"); op.drop_table("coverage_requests"); op.drop_table("coverage_policies")
