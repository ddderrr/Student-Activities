from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship, validates

from database import Base
from timeutil import now_bangkok, now_bangkok_aware
from major_utils import normalize_major


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
    activity_hours = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")

    # เจ้าของกิจกรรม (สาขา) สำหรับ major-scoping เหมือน students.major
    # None = สร้างโดยแอดมินกลาง หรือกิจกรรมเก่าก่อนมีคอลัมน์นี้ -> เห็นได้ทุกแอดมิน
    major = Column(String(255), nullable=True, default=None)

    status = Column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=now_bangkok,
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

    __table_args__ = (CheckConstraint("activity_hours >= 0", name="ck_activity_hours_nonnegative"),)

    @validates("major")
    def _normalize_major(self, _key, value):
        # normalize ตอนบันทึก: ตัดช่องว่าง ค่าว่าง = NULL (กิจกรรมส่วนกลางของคณะ)
        # query ที่เทียบ Activity.major ตรงตัว (เช่น admin_scope) พึ่งกติกานี้
        return normalize_major(value)


class Admin(Base):
    """บัญชีแอดมินที่ login ด้วยอีเมล + รหัสผ่าน (หน้า /login)

    major = None คือแอดมินกลางของคณะ (เห็นทุกสาขา) นอกนั้นเป็นแอดมินสาขา
    """

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    # เก็บเป็นตัวพิมพ์เล็กเสมอ (ดู validates ด้านล่าง) จึง unique ได้ตรง ๆ
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False, default="")
    password_hash = Column(String(255), nullable=False)
    major = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=now_bangkok,
        server_default=func.now(),
    )

    @validates("email")
    def _normalize_email(self, _key, value):
        return (value or "").strip().lower()

    @validates("major")
    def _normalize_major(self, _key, value):
        return normalize_major(value)

    @property
    def is_central(self) -> bool:
        return self.major is None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


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
        default=now_bangkok,
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

    major_history = relationship(
        "StudentMajorHistory",
        cascade="all, delete-orphan",
    )

    @validates("major")
    def _normalize_major(self, _key, value):
        # normalize ตอนบันทึก: ตัดช่องว่าง ค่าว่าง = "" (คอลัมน์ NOT NULL ใช้ "" แทนไม่มีสาขา)
        return normalize_major(value) or ""


class StudentMajorHistory(Base):
    """สาขาเดิมของนักศึกษาที่ย้ายสาขา: อยู่สาขา major มาจนถึง ended_at (ไม่รวม ended_at)

    ใช้ตัดสินว่ากิจกรรมเป็น "กิจกรรมสาขา" ตามสาขา ณ วันที่ทำกิจกรรม (ดู major_history.py)
    สาขาปัจจุบันอยู่ที่ students.major เหมือนเดิม
    """

    __tablename__ = "student_major_history"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        String(30),
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    major = Column(String(255), nullable=False)

    ended_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=now_bangkok,
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
        default=now_bangkok,
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
        default=now_bangkok,
        server_default=func.now(),
        onupdate=now_bangkok,
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
        default=now_bangkok,
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
        default=now_bangkok,
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
    activity_hours = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")

    # เลิกใช้แล้ว: หลักฐานย้ายไปอยู่ที่ external_activity_evidence (หลายไฟล์ต่อคำขอ)
    # เก็บคอลัมน์ไว้เป็นข้อมูลเดิมเผื่อย้อนกลับ ห้ามอ่าน/เขียนในโค้ดใหม่
    # ดู migration_multiple_evidence_files.sql
    evidence_filename = Column(String(100), nullable=True)
    evidence_original_name = Column(String(255), nullable=True)
    evidence_content_type = Column(String(100), nullable=True)
    evidence_size = Column(Integer, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    reject_reason = Column(Text, nullable=True)

    # เวลาทั้งหมดเป็นเวลาไทย (timeutil.now_bangkok) ทั้ง submitted_at และ decided_at
    submitted_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=now_bangkok,
        server_default=func.now(),
    )
    decided_at = Column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "role IN ('participant', 'organizer')",
            name="ck_external_activity_role",
        ),
        CheckConstraint("activity_hours >= 0", name="ck_external_hours_nonnegative"),
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

    evidence_files = relationship(
        "ExternalActivityEvidence",
        back_populates="external_activity",
        cascade="all, delete-orphan",
        order_by="ExternalActivityEvidence.id",
    )


class ExternalActivityEvidence(Base):
    # ไฟล์หลักฐานของคำขอกิจกรรมภายนอก (สูงสุด 10 ไฟล์ต่อคำขอ)
    # ไฟล์จริงอยู่ที่ uploads/external_activities/<external_activity_id>/<stored_name>
    __tablename__ = "external_activity_evidence"

    id = Column(Integer, primary_key=True, index=True)

    external_activity_id = Column(
        Integer,
        ForeignKey(
            "external_activities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ชื่อไฟล์ที่ระบบสร้างเอง (uuid + นามสกุล)
    stored_name = Column(String(100), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        default=now_bangkok,
        server_default=func.now(),
    )

    external_activity = relationship(
        "ExternalActivity",
        back_populates="evidence_files",
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


class AdminNotification(Base):
    """แจ้งเตือนฝั่งแอดมิน (กระดิ่งมุมขวาบน) หนึ่งแถวต่อเหตุการณ์

    major = สาขาของนักศึกษาตอนเกิดเหตุการณ์: แอดมินสาขาเห็นเฉพาะ major ของตัวเอง
    แอดมินกลางเห็นทุกแถว (รวม major ว่าง) สถานะอ่านแล้วเก็บแยกต่อแอดมินใน
    admin_notification_reads (แอดมินคนหนึ่งอ่านไม่ทำให้คนอื่นเห็นว่าอ่านแล้ว)
    """

    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, index=True)

    # 'external_submitted' | 'external_resubmitted'
    type = Column(String(40), nullable=False)
    major = Column(String(255), nullable=True, index=True)

    student_id = Column(String(30), nullable=False)
    student_name = Column(String(300), nullable=False, default="")
    activity_title = Column(String(255), nullable=False, default="")

    external_activity_id = Column(
        Integer,
        ForeignKey("external_activities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ข้อความภาษาไทยไว้สำรอง หน้าเว็บสร้างข้อความตามภาษาเองจาก type + ชื่อ
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=False)

    # เวลาแบบมี timezone (เวลาไทย): หน้าเว็บคำนวณ "x นาทีที่แล้ว" ได้ถูกไม่ว่าเครื่องอยู่ timezone ไหน
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=now_bangkok_aware,
        index=True,
    )

    @validates("major")
    def _normalize_major(self, _key, value):
        return normalize_major(value)

    __table_args__ = (
        CheckConstraint(
            "type IN ('external_submitted', 'external_resubmitted')",
            name="ck_admin_notification_type",
        ),
    )


class AdminNotificationRead(Base):
    __tablename__ = "admin_notification_reads"

    notification_id = Column(
        Integer,
        ForeignKey("admin_notifications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # อีเมลแอดมิน (ใช้ได้ทั้งบัญชีในตาราง admins และบัญชีทดสอบใน admin_accounts.py)
    admin_email = Column(String(255), primary_key=True)

    read_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=now_bangkok_aware,
    )


class AdminNotificationClear(Base):
    """"ลบทั้งหมด" ในกระดิ่งของแอดมิน: ซ่อนรายการที่ id <= cleared_through_id เฉพาะแอดมินคนนี้

    การแจ้งเตือนหนึ่งรายการแอดมินหลายคนเห็นร่วมกัน (แอดมินสาขา + แอดมินกลาง) จึงลบแถวจริงไม่ได้
    เก็บแค่ id ล่าสุดที่ล้างไว้ (แถวเดียวต่อแอดมิน) รายการใหม่ id มากกว่าเสมอจึงแสดงตามปกติ
    """

    __tablename__ = "admin_notification_clears"

    admin_email = Column(String(255), primary_key=True)
    cleared_through_id = Column(Integer, nullable=False)
    cleared_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=now_bangkok_aware,
        onupdate=now_bangkok_aware,
    )


class AppSetting(Base):
    """ค่าตั้งของระบบที่แอดมินกลางแก้ได้จากหน้า Settings (key / value)

    ตอนนี้ใช้กับหัวเอกสาร Transcript (ดู transcript_settings.py) ไม่มีแถว = ใช้ค่าเริ่มต้น
    """

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=False), nullable=False, default=now_bangkok, onupdate=now_bangkok)
