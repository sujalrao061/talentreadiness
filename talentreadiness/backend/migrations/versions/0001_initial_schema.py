"""Initial TalentReadiness schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(120),nullable=False),sa.Column("email",sa.String(200),nullable=False,unique=True),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("role",sa.String(20),nullable=False),sa.Column("job_title",sa.String(120),nullable=False),sa.Column("department",sa.String(120),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False))
    op.create_index("ix_users_email","users",["email"])
    op.create_table("skills",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(100),nullable=False,unique=True),sa.Column("category",sa.String(100),nullable=False))
    op.create_table("employee_skills",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("skill_id",sa.Integer(),sa.ForeignKey("skills.id"),nullable=False),sa.Column("proficiency",sa.Integer(),nullable=False),sa.Column("years_experience",sa.Float(),nullable=False),sa.UniqueConstraint("employee_id","skill_id"))
    op.create_table("projects",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(150),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("manager_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("priority",sa.String(30),nullable=False),sa.Column("status",sa.String(30),nullable=False))
    op.create_table("project_skills",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("skill_id",sa.Integer(),sa.ForeignKey("skills.id"),nullable=False),sa.Column("required_proficiency",sa.Integer(),nullable=False),sa.Column("importance",sa.Integer(),nullable=False),sa.Column("mandatory",sa.Boolean(),nullable=False),sa.UniqueConstraint("project_id","skill_id"))
    op.create_table("project_members",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("allocation_percentage",sa.Integer(),nullable=False),sa.UniqueConstraint("project_id","employee_id"))
    op.create_table("availability",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("date",sa.Date(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("available_hours",sa.Float(),nullable=False),sa.UniqueConstraint("employee_id","date"))
    op.create_table("absences",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("date",sa.Date(),nullable=False),sa.Column("reason",sa.String(250),nullable=False))
    op.create_table("replacement_assignments",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("project_id",sa.Integer(),sa.ForeignKey("projects.id"),nullable=False),sa.Column("absent_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("replacement_employee_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("date",sa.Date(),nullable=False),sa.Column("assigned_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False))

def downgrade():
    for table in ["replacement_assignments","absences","availability","project_members","project_skills","projects","employee_skills","skills","users"]: op.drop_table(table)
