from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
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

    external_activities = relationship(
        "ExternalActivity",
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


class StudentSkillBenchmark(Base):
    """Benchmark ที่ Admin ปรับได้สำหรับ participant skills (1.0-5.0)."""
    __tablename__ = "student_skill_benchmarks"

    skill_key = Column(
        String(80),
        ForeignKey("skills.key", ondelete="CASCADE"),
        primary_key=True,
    )
    # เก็บเป็นจำนวนเต็ม x100 เพื่อเลี่ยง floating-point ใน DB เช่น 4.25 => 425
    score_x100 = Column(Integer, nullable=False, default=400, server_default="400")
    updated_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "score_x100 >= 100 AND score_x100 <= 500",
            name="ck_student_skill_benchmark_score",
        ),
    )

    skill = relationship("Skill")


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
    reject_reason = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_student_request_status",
        ),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # requester_student_id ของ student_requests ไม่ผูก FK กับ students
    # (อาจไม่ใช่ student ที่มีอยู่ในระบบ) จึงเก็บ student_id เป็น string เฉย ๆ เหมือนกัน
    student_id = Column(String(30), nullable=False, index=True)

    source = Column(String(30), nullable=False)

    external_activity_id = Column(
        Integer,
        ForeignKey("external_activities.id", ondelete="CASCADE"),
        nullable=True,
    )

    request_id = Column(
        Integer,
        ForeignKey("student_requests.id", ondelete="CASCADE"),
        nullable=True,
    )

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # 'Pending' | 'Approved' | 'Rejected'
    status = Column(String(20), nullable=False)

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "source IN ('external_activity', 'student_request')",
            name="ck_notification_source",
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


class ExternalActivity(Base):
    # กิจกรรมภายนอกที่นักศึกษาส่งเอง ต้องผ่านการอนุมัติจาก admin
    __tablename__ = "external_activities"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        String(30),
        ForeignKey(
            "students.student_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    activity_type = Column(String(120), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    location = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    description = Column(Text, nullable=False, default="")

    # ไฟล์จริงอยู่ใน backend/uploads/external_activities/ เก็บแค่ชื่อไฟล์ (uuid)
    evidence_filename = Column(String(100), nullable=False)
    evidence_original_name = Column(String(255), nullable=False)
    evidence_content_type = Column(String(100), nullable=False)
    evidence_size = Column(Integer, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    reject_reason = Column(Text, nullable=True)

    # ใช้ convention เดียวกับ student_requests: submitted_at จาก DB now(),
    # decided_at จาก datetime.now() ฝั่ง Python
    submitted_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    decided_at = Column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "role IN ('participant', 'organizer')",
            name="ck_external_activity_role",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_external_activity_status",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_external_activity_dates",
        ),
    )

    student = relationship(
        "Student",
        back_populates="external_activities",
    )

    skill_levels = relationship(
        "ExternalActivitySkill",
        back_populates="external_activity",
        cascade="all, delete-orphan",
    )


class ExternalActivitySkill(Base):
    # นักศึกษาตั้งเอง (Skill Mapping) ตอนส่งฟอร์ม
    # role participant -> participant skills, organizer -> staff skills
    __tablename__ = "external_activity_skills"

    external_activity_id = Column(
        Integer,
        ForeignKey(
            "external_activities.id",
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

    target_role = Column(String(20), nullable=False)
    level = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "target_role IN ('staff', 'participant')",
            name="ck_external_activity_skill_target_role",
        ),
        CheckConstraint(
            "level >= 1 AND level <= 5",
            name="ck_external_activity_skill_level",
        ),
    )

    external_activity = relationship(
        "ExternalActivity",
        back_populates="skill_levels",
    )

    skill = relationship("Skill")
