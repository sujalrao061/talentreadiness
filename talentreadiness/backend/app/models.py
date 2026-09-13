from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True); password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20)); job_title: Mapped[str] = mapped_column(String(120), default="")
    department: Mapped[str] = mapped_column(String(120), default=""); created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(100), unique=True); category: Mapped[str] = mapped_column(String(100), default="Technical")

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"; __table_args__=(UniqueConstraint("employee_id","skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); employee_id: Mapped[int] = mapped_column(ForeignKey("users.id")); skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    proficiency: Mapped[int] = mapped_column(Integer); years_experience: Mapped[float] = mapped_column(Float, default=0)
    employee = relationship("User", back_populates="skills"); skill = relationship("Skill")

class Project(Base):
    __tablename__="projects"
    id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(150)); description: Mapped[str] = mapped_column(Text, default="")
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id")); priority: Mapped[str] = mapped_column(String(30), default="Medium"); status: Mapped[str] = mapped_column(String(30), default="Active")
    skills = relationship("ProjectSkill", back_populates="project", cascade="all, delete-orphan"); members=relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectSkill(Base):
    __tablename__="project_skills"; __table_args__=(UniqueConstraint("project_id","skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); project_id: Mapped[int] = mapped_column(ForeignKey("projects.id")); skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    required_proficiency: Mapped[int] = mapped_column(Integer); importance: Mapped[int] = mapped_column(Integer, default=3); mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    project=relationship("Project", back_populates="skills"); skill=relationship("Skill")

class ProjectMember(Base):
    __tablename__="project_members"; __table_args__=(UniqueConstraint("project_id","employee_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); project_id: Mapped[int] = mapped_column(ForeignKey("projects.id")); employee_id: Mapped[int] = mapped_column(ForeignKey("users.id")); allocation_percentage: Mapped[int] = mapped_column(Integer, default=0)
    project=relationship("Project", back_populates="members"); employee=relationship("User")

class Availability(Base):
    __tablename__="availability"; __table_args__=(UniqueConstraint("employee_id","date"),)
    id: Mapped[int] = mapped_column(primary_key=True); employee_id: Mapped[int] = mapped_column(ForeignKey("users.id")); date: Mapped[date] = mapped_column(Date); status: Mapped[str] = mapped_column(String(30)); available_hours: Mapped[float] = mapped_column(Float, default=8)
    employee=relationship("User")

class Absence(Base):
    __tablename__="absences"; id: Mapped[int]=mapped_column(primary_key=True); employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); project_id: Mapped[int]=mapped_column(ForeignKey("projects.id")); date: Mapped[date]=mapped_column(Date); reason: Mapped[str]=mapped_column(String(250), default="")
    employee=relationship("User"); project=relationship("Project")

class ReplacementAssignment(Base):
    __tablename__="replacement_assignments"; id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey("projects.id")); absent_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); replacement_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); date: Mapped[date]=mapped_column(Date); assigned_by: Mapped[int]=mapped_column(ForeignKey("users.id"))

class CoveragePolicy(Base):
    __tablename__="coverage_policies"
    id: Mapped[int]=mapped_column(primary_key=True); coverage_assignment_mode: Mapped[str]=mapped_column(String(30),default="Consent Required")
    default_incentive_multiplier: Mapped[float]=mapped_column(Float,default=1.5); updated_by: Mapped[int|None]=mapped_column(ForeignKey("users.id"),nullable=True); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CoverageRequest(Base):
    __tablename__="coverage_requests"
    id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey("projects.id")); absent_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); requested_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); date: Mapped[date]=mapped_column(Date)
    required_hours: Mapped[float]=mapped_column(Float); incentive_multiplier: Mapped[float]=mapped_column(Float,default=1.5); status: Mapped[str]=mapped_column(String(20),default="Pending"); requested_by: Mapped[int]=mapped_column(ForeignKey("users.id")); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); responded_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    project=relationship("Project"); absent_employee=relationship("User",foreign_keys=[absent_employee_id]); requested_employee=relationship("User",foreign_keys=[requested_employee_id]); manager=relationship("User",foreign_keys=[requested_by])

class CoverageAuditLog(Base):
    __tablename__="coverage_audit_log"
    id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey("projects.id")); absent_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); replacement_employee_id: Mapped[int]=mapped_column(ForeignKey("users.id")); assignment_mode: Mapped[str]=mapped_column(String(30)); incentive_multiplier: Mapped[float]=mapped_column(Float,default=1.5); required_hours: Mapped[float]=mapped_column(Float,default=8); performed_by: Mapped[int]=mapped_column(ForeignKey("users.id")); reason: Mapped[str]=mapped_column(String(250),default=""); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    project=relationship("Project"); absent_employee=relationship("User",foreign_keys=[absent_employee_id]); replacement_employee=relationship("User",foreign_keys=[replacement_employee_id]); performer=relationship("User",foreign_keys=[performed_by])
