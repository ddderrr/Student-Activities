from datetime import date, datetime

import main as main_module
from models import (
    Activity,
    ActivityMember,
    ExternalActivity,
    ExternalActivityEvidence,
    ExternalActivitySkill,
    Notification,
    Student,
    StudentRequest,
)
from tests.conftest import CHEM_ADMIN_EMAIL


def make_student(db_session, student_id, first_name="ทดสอบ", major="เคมี", email=None):
    student = Student(
        student_id=student_id,
        first_name=first_name,
        last_name="นักศึกษา",
        email=email if email is not None else f"{student_id}@test.com",
        faculty="Faculty of Science",
        major=major,
    )
    db_session.add(student)
    db_session.commit()
    return student


def add_related_data(db_session, student_id):
    """กิจกรรมคณะ + external activity (มีไฟล์หลักฐาน) + คำขอ + notification ของนักศึกษา"""
    activity = Activity(
        activity_type="Volunteer",
        name=f"Activity of {student_id}",
        start_at=datetime(2026, 1, 10, 9),
        end_at=datetime(2026, 1, 10, 12),
        responsible_person="Staff",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.add(ActivityMember(activity_id=activity.id, student_id=student_id, role="participant"))

    external = ExternalActivity(
        student_id=student_id,
        title="Camp",
        organization="NGO",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
        location="Chiang Mai",
        role="participant",
        status="pending",
    )
    db_session.add(external)
    db_session.commit()
    db_session.add(ExternalActivitySkill(external_activity_id=external.id, skill_key="volunteerism", target_role="participant", level=3))
    db_session.add(ExternalActivityEvidence(external_activity_id=external.id, stored_name="proof.png", original_name="proof.png", content_type="image/png", size=4))
    folder = main_module.evidence_folder(external.id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "proof.png").write_bytes(b"test")

    request = StudentRequest(requester_name="ทดสอบ", requester_student_id=student_id, request_type="skill_validation", detail="x", status="pending")
    db_session.add(request)
    db_session.commit()
    db_session.add(Notification(student_id=student_id, source="external_activity", external_activity_id=external.id, title="t", message="m", status="Rejected"))
    db_session.add(Notification(student_id=student_id, source="student_request", request_id=request.id, title="t", message="m", status="Rejected"))
    db_session.commit()

    return activity.id, external.id, folder


def test_list_students_with_counts_and_search(client, db_session):
    make_student(db_session, "680510001", first_name="สมชาย")
    make_student(db_session, "680510002", first_name="สมหญิง", major="")
    add_related_data(db_session, "680510001")

    body = client.get("/api/admin/students").json()
    assert (body["total"], body["all_total"]) == (2, 2)
    by_id = {s["student_id"]: s for s in body["students"]}
    assert by_id["680510001"]["activity_count"] == 1
    assert by_id["680510001"]["external_activity_count"] == 1
    assert by_id["680510002"]["activity_count"] == 0
    assert by_id["680510002"]["major"] == ""

    found = client.get("/api/admin/students", params={"search": "สมหญิง"}).json()
    assert [s["student_id"] for s in found["students"]] == ["680510002"]
    assert (found["total"], found["all_total"]) == (1, 2)


def test_list_students_paginates(client, db_session):
    for index in range(25):
        make_student(db_session, f"6805100{index:02d}")

    page1 = client.get("/api/admin/students", params={"page_size": 10}).json()
    page3 = client.get("/api/admin/students", params={"page_size": 10, "page": 3}).json()

    assert page1["total"] == 25
    assert len(page1["students"]) == 10
    assert len(page3["students"]) == 5


def test_delete_one_student_removes_related_data_and_files(client, db_session):
    make_student(db_session, "680510001")
    make_student(db_session, "680510002")
    activity_id, external_id, folder = add_related_data(db_session, "680510001")
    add_related_data(db_session, "680510002")

    response = client.delete("/api/admin/students/680510001")

    assert response.status_code == 200
    assert response.json() == {
        "students": 1,
        "activity_memberships": 1,
        "external_activities": 1,
        "requests": 1,
        "notifications": 2,
    }
    db_session.expire_all()
    assert db_session.get(Student, "680510001") is None
    assert db_session.query(ActivityMember).filter_by(student_id="680510001").count() == 0
    assert db_session.get(ExternalActivity, external_id) is None
    assert db_session.query(ExternalActivitySkill).filter_by(external_activity_id=external_id).count() == 0
    assert db_session.query(ExternalActivityEvidence).filter_by(external_activity_id=external_id).count() == 0
    assert db_session.query(StudentRequest).filter_by(requester_student_id="680510001").count() == 0
    assert db_session.query(Notification).filter_by(student_id="680510001").count() == 0
    assert not folder.exists()
    # กิจกรรมคณะยังอยู่ ลบแค่การเป็นสมาชิก และข้อมูลคนอื่นไม่ถูกแตะ
    assert db_session.get(Activity, activity_id) is not None
    assert db_session.get(Student, "680510002") is not None
    assert db_session.query(Notification).filter_by(student_id="680510002").count() == 2


def test_delete_unknown_student_returns_404(client):
    assert client.delete("/api/admin/students/000000000").status_code == 404


def test_delete_all_requires_confirmation(client, db_session):
    make_student(db_session, "680510001")

    assert client.delete("/api/admin/students").status_code == 400
    assert client.delete("/api/admin/students", params={"confirm": "yes"}).status_code == 400
    db_session.expire_all()
    assert db_session.query(Student).count() == 1


def test_delete_all_students(client, db_session):
    for student_id in ["680510001", "680510002", "680510003"]:
        make_student(db_session, student_id)
    _, _, folder = add_related_data(db_session, "680510002")

    response = client.delete("/api/admin/students", params={"confirm": "all"})

    assert response.status_code == 200
    assert response.json()["students"] == 3
    db_session.expire_all()
    assert db_session.query(Student).count() == 0
    assert db_session.query(ExternalActivity).count() == 0
    assert db_session.query(Notification).count() == 0
    assert not folder.exists()
    assert db_session.query(Activity).count() == 1


def test_branch_admin_cannot_list_or_delete(client, db_session):
    make_student(db_session, "680510001")
    branch = {"X-Admin-Email": CHEM_ADMIN_EMAIL}

    assert client.get("/api/admin/students", headers=branch).status_code == 403
    assert client.delete("/api/admin/students/680510001", headers=branch).status_code == 403
    assert client.delete("/api/admin/students", params={"confirm": "all"}, headers=branch).status_code == 403
    db_session.expire_all()
    assert db_session.get(Student, "680510001") is not None
