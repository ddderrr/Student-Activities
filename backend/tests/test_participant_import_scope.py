"""import ผู้เข้าร่วม (confirm) ต้องไม่ให้แอดมินสาขาแก้ข้อมูลนักศึกษาสาขาอื่น

นักศึกษาต่างสาขาเข้าร่วมกิจกรรมได้ (เพิ่มเป็นผู้เข้าร่วม) แต่ชื่อ / อีเมล /
คณะ / สาขาในไฟล์ต้องไม่ไปทับข้อมูลเดิม (ดู docs/security-review.md ข้อ ก2)
"""

from datetime import datetime

from models import Activity, ActivityMember, Student
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL

CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"


def create_activity(db_session) -> Activity:
    activity = Activity(
        activity_type="Volunteer",
        name="Chem Activity",
        start_at=datetime(2026, 1, 10, 9, 0, 0),
        end_at=datetime(2026, 1, 10, 12, 0, 0),
        responsible_person="Staff Name",
        location="Room 101",
        major=CHEM,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def create_student(db_session, student_id, major) -> None:
    db_session.add(
        Student(
            student_id=student_id,
            first_name="ชื่อเดิม",
            last_name="นามสกุลเดิม",
            email=f"{student_id}@cmu.ac.th",
            faculty="Faculty of Science",
            major=major,
        )
    )
    db_session.commit()


def confirm(client, activity_id, row, admin_email=CHEM_ADMIN_EMAIL):
    return client.post(
        f"/api/activities/{activity_id}/participants/import/confirm",
        json={"students": [row]},
        headers={"X-Admin-Email": admin_email},
    )


def changed_row(student_id, major):
    return {
        "student_id": student_id,
        "first_name": "ชื่อใหม่",
        "last_name": "นามสกุลใหม่",
        "email": "attacker@evil.com",
        "faculty": "คณะวิศวกรรมศาสตร์",
        "major": major,
    }


def reload(db_session, student_id) -> Student:
    db_session.expire_all()
    return db_session.get(Student, student_id)


def test_branch_admin_cannot_overwrite_other_branch_student(client, db_session):
    activity = create_activity(db_session)
    create_student(db_session, "670510101", CS)

    response = confirm(client, activity.id, changed_row("670510101", CHEM))

    assert response.status_code == 200, response.text
    student = reload(db_session, "670510101")
    assert (student.first_name, student.last_name) == ("ชื่อเดิม", "นามสกุลเดิม")
    assert student.email == "670510101@cmu.ac.th"
    assert student.faculty == "Faculty of Science"
    assert student.major == CS
    # ยังเพิ่มเป็นผู้เข้าร่วมกิจกรรมข้ามสาขาได้
    assert db_session.get(ActivityMember, (activity.id, "670510101")) is not None


def test_branch_admin_still_updates_own_branch_student(client, db_session):
    activity = create_activity(db_session)
    create_student(db_session, "670510201", CHEM)

    response = confirm(client, activity.id, changed_row("670510201", CHEM))

    assert response.status_code == 200, response.text
    student = reload(db_session, "670510201")
    assert (student.first_name, student.last_name) == ("ชื่อใหม่", "นามสกุลใหม่")
    assert student.email == "attacker@evil.com"
    assert student.faculty == "คณะวิศวกรรมศาสตร์"
    assert student.major == CHEM


def test_branch_admin_cannot_move_own_student_to_other_branch(client, db_session):
    activity = create_activity(db_session)
    create_student(db_session, "670510201", CHEM)

    response = confirm(client, activity.id, changed_row("670510201", CS))

    assert response.status_code == 200, response.text
    student = reload(db_session, "670510201")
    assert student.major == CHEM
    assert student.first_name == "ชื่อใหม่"


def test_central_admin_can_update_any_student(client, db_session):
    activity = create_activity(db_session)
    create_student(db_session, "670510101", CS)

    response = confirm(
        client,
        activity.id,
        changed_row("670510101", CHEM),
        admin_email=CENTRAL_ADMIN_EMAIL,
    )

    assert response.status_code == 200, response.text
    student = reload(db_session, "670510101")
    assert student.first_name == "ชื่อใหม่"
    assert student.major == CHEM


def test_branch_admin_creates_new_student_with_major_from_file(client, db_session):
    # ทีมตัดสินใจ: นักศึกษาใหม่สร้างตามสาขาในไฟล์ (สร้างคนใหม่ไม่ได้แย่งข้อมูลใคร)
    activity = create_activity(db_session)

    response = confirm(client, activity.id, changed_row("670510301", CS))

    assert response.status_code == 200, response.text
    assert reload(db_session, "670510301").major == CS
