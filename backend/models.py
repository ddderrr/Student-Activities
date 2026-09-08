from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(30), unique=True, nullable=True, index=True)

    activity_type = Column(String(120), nullable=False)
    name = Column(String(255), nullable=False)

    start_at = Column(DateTime(timezone=False), nullable=False)
    end_at = Column(DateTime(timezone=False), nullable=False)

    department = Column(String(255), nullable=False, default="")
    responsible_person = Column(String(255), nullable=False)
    advisor = Column(String(255), nullable=False, default="")
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")

    status = Column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    members = relationship(
        "ActivityMember",
        back_populates="activity",
        cascade="all, delete-orphan",
    )

    skill_levels = relationship(
        "ActivitySkill",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class Student(Base):
    __tablename__ = "students"

    # รหัสนักศึกษาเป็น identifier จึงเก็บเป็น string
    student_id = Column(String(30), primary_key=True)

    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, index=True)

    faculty = Column(
        String(255),
        nullable=False,
        default="Faculty of Science",
    )

    major = Column(String(255), nullable=False, default="")

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    memberships = relationship(
        "ActivityMember",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class ActivityMember(Base):
    __tablename__ = "activity_members"

    activity_id = Column(
        Integer,
        ForeignKey(
            "activities.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    student_id = Column(
        String(30),
        ForeignKey(
            "students.student_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )

    role = Column(
        String(20),
        nullable=False,
        default="participant",
    )

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('participant', 'organizer')",
            name="ck_activity_member_role",
        ),
    )

    activity = relationship(
        "Activity",
        back_populates="members",
    )

    student = relationship(
        "Student",
        back_populates="memberships",
    )


class Skill(Base):
    __tablename__ = "skills"

    # ใช้ key จาก frontend เช่น innovation
    key = Column(String(80), primary_key=True)
    label = Column(String(150), nullable=False)


class StudentRequest(Base):
    __tablename__ = "student_requests"

    id = Column(Integer, primary_key=True, index=True)

    requester_name = Column(String(150), nullable=False)
    requester_student_id = Column(String(30), nullable=False)

    request_type = Column(String(40), nullable=False)
    detail = Column(String(255), nullable=False, default="")

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    submitted_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    decided_at = Column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_student_request_status",
        ),
    )


class ActivitySkill(Base):
    __tablename__ = "activity_skills"

    activity_id = Column(
        Integer,
        ForeignKey(
            "activities.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    skill_key = Column(
        String(80),
        ForeignKey(
            "skills.key",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    # หน้า Create Activity ใช้ Staff / Participant
    target_role = Column(
        String(20),
        primary_key=True,
    )

    level = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "target_role IN ('staff', 'participant')",
            name="ck_activity_skill_target_role",
        ),
        CheckConstraint(
            "level >= 1 AND level <= 5",
            name="ck_activity_skill_level",
        ),
    )

    activity = relationship(
        "Activity",
        back_populates="skill_levels",
    )

    skill = relationship("Skill")
