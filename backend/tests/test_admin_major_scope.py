"""แอดมินสาขาเห็น/จัดการได้เฉพาะนักศึกษาในสาขาตัวเอง ส่วนแอดมินกลางเห็นทุกสาขา

บัญชีแอดมินในเทสต์มาจาก fixture ใน conftest.py (ไม่ผูกกับ admin_accounts.py จริง)
"""

import base64
from datetime import date, datetime

import pytest

from models import (
    Activity,
    ActivityMember,
    ExternalActivity,
    ExternalActivityEvidence,
    ExternalActivitySkill,
    Student,
    StudentRequest,
)
from tests.conftest import (
    CENTRAL_ADMIN_EMAIL,
    CHEM_ADMIN_EMAIL,
    CS_ADMIN_EMAIL,
)

CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"

CENTRAL = {"X-Admin-Email": CENTRAL_ADMIN_EMAIL}
CHEM_ADMIN = {"X-Admin-Email": CHEM_ADMIN_EMAIL}
CS_ADMIN = {"X-Admin-Email": CS_ADMIN_EMAIL}

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def create_student(db_session, student_id, major) -> Student:
    student = Student(
        student_id=student_id,
        first_name="Test",
        last_name=student_id,
        email=f"{student_id}@test.local",
        faculty="Faculty of Science",
        major=major,
    )
    db_session.add(student)
    db_session.commit()
    return student


def create_external(db_session, student_id, status="pending", title=None) -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title=title or f"External {student_id}",
        organization="Some Org",
        activity_type="Workshop",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 2),
        location="Online",
        role="participant",
        description="",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add(
        ExternalActivitySkill(
            external_activity_id=activity.id,
            skill_key="volunteerism",
            target_role="participant",
            level=4,
        )
    )
    db_session.commit()
    return activity


def add_evidence(db_session, upload_dir, activity) -> ExternalActivityEvidence:
    folder = upload_dir / str(activity.id)
    folder.mkdir()
    stored_name = f"evidence-{activity.id}.png"
    (folder / stored_name).write_bytes(PNG_BYTES)

    evidence = ExternalActivityEvidence(
        external_activity_id=activity.id,
        stored_name=stored_name,
        original_name="evidence.png",
        content_type="image/png",
        size=len(PNG_BYTES),
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return evidence


def create_student_request(db_session, student_id) -> StudentRequest:
    request = StudentRequest(
        requester_name=f"Test {student_id}",
        requester_student_id=student_id,
        request_type="special_request",
        detail=f"Request {student_id}",
        status="pending",
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


@pytest.fixture()
def data(db_session):
    """นักศึกษาเคมี 1, CS 1, ไม่มีสาขา 1 พร้อมคำขอ pending คนละ 1 รายการ"""
    create_student(db_session, "C001", CHEM)
    create_student(db_session, "S001", CS)
    create_student(db_session, "N001", "")

    return {
        "chem_external": create_external(db_session, "C001"),
        "cs_external": create_external(db_session, "S001"),
        "none_external": create_external(db_session, "N001"),
        "chem_request": create_student_request(db_session, "C001"),
        "cs_request": create_student_request(db_session, "S001"),
        "none_request": create_student_request(db_session, "N001"),
        # คำขอที่ requester_student_id ไม่มีในตาราง students
        "orphan_request": create_student_request(db_session, "X999"),
    }


def request_keys(response):
    assert response.status_code == 200, response.text
    return {
        (item["source"], item["requester_student_id"])
        for item in response.json()["requests"]
    }


def status_of(db_session, model, item_id):
    db_session.expire_all()
    return db_session.get(model, item_id).status


# ------------------------------------------------------------
# Bypass on/off และการระบุตัวแอดมิน
# ------------------------------------------------------------


def test_bypass_disabled_blocks_admin_api(client, monkeypatch, data):
    monkeypatch.setenv("ADMIN_BYPASS_ENABLED", "false")

    response = client.get("/api/requests", headers=CENTRAL)

    assert response.status_code == 401
    assert "ADMIN_BYPASS_ENABLED=true" in response.json()["detail"]


def test_bypass_disabled_when_env_missing(client, monkeypatch):
    monkeypatch.delenv("ADMIN_BYPASS_ENABLED", raising=False)

    assert client.get("/api/admin/dashboard", headers=CENTRAL).status_code == 401


def test_old_admin_bypass_account_list_is_removed(client):
    # หน้า /admin/login (เลือกบัญชีจากรายการ) ถูกแทนด้วยหน้า /login เดียว
    assert client.get("/api/admin/auth/bypass").status_code in (404, 405)


def test_missing_or_unknown_admin_email_is_rejected(client):
    client.headers.pop("X-Admin-Email", None)

    assert client.get("/api/requests").status_code == 401
    assert client.get(
        "/api/requests",
        headers={"X-Admin-Email": "someone@test.local"},
    ).status_code == 401


def test_admin_email_is_case_insensitive(client):
    response = client.get(
        "/api/admin/me",
        headers={"X-Admin-Email": f"  {CHEM_ADMIN_EMAIL.upper()} "},
    )

    assert response.status_code == 200
    assert response.json()["email"] == CHEM_ADMIN_EMAIL


def test_me_returns_admin_scope(client):
    chem = client.get("/api/admin/me", headers=CHEM_ADMIN).json()
    central = client.get("/api/admin/me", headers=CENTRAL).json()

    assert chem["major"] == CHEM
    assert chem["is_central"] is False
    assert central["major"] is None
    assert central["is_central"] is True


# ------------------------------------------------------------
# รายการคำขอ (/api/requests)
# ------------------------------------------------------------


def test_branch_admin_lists_only_own_major(client, data):
    assert request_keys(client.get("/api/requests", headers=CHEM_ADMIN)) == {
        ("external_activity", "C001"),
        ("student_request", "C001"),
    }
    assert request_keys(client.get("/api/requests", headers=CS_ADMIN)) == {
        ("external_activity", "S001"),
        ("student_request", "S001"),
    }


def test_only_central_admin_sees_requests_without_major(client, data):
    keys = request_keys(client.get("/api/requests", headers=CENTRAL))

    assert ("external_activity", "N001") in keys
    assert ("student_request", "N001") in keys
    assert ("student_request", "X999") in keys
    assert len(keys) == 7


def test_request_type_filter_keeps_major_scope(client, data):
    keys = request_keys(
        client.get(
            "/api/requests?request_type=external_activity",
            headers=CS_ADMIN,
        )
    )

    assert keys == {("external_activity", "S001")}


def test_request_stats_are_scoped(client, data):
    chem = client.get("/api/requests/stats", headers=CHEM_ADMIN).json()
    central = client.get("/api/requests/stats", headers=CENTRAL).json()

    assert chem["total_pending"] == 2
    assert central["total_pending"] == 7


# ------------------------------------------------------------
# ดูรายละเอียด / ไฟล์หลักฐาน
# ------------------------------------------------------------


def test_branch_admin_cannot_view_other_major_external_activity(client, data):
    cs_id = data["cs_external"].id

    assert client.get(
        f"/api/external-activities/{cs_id}",
        headers=CHEM_ADMIN,
    ).status_code == 403
    assert client.get(
        f"/api/external-activities/{cs_id}",
        headers=CS_ADMIN,
    ).status_code == 200


def test_branch_admin_cannot_view_request_without_major(client, data):
    none_id = data["none_external"].id

    assert client.get(
        f"/api/external-activities/{none_id}",
        headers=CHEM_ADMIN,
    ).status_code == 403
    assert client.get(
        f"/api/external-activities/{none_id}",
        headers=CENTRAL,
    ).status_code == 200


def test_evidence_is_scoped_to_major_or_owner(client, db_session, upload_dir, data):
    activity = data["cs_external"]
    evidence = add_evidence(db_session, upload_dir, activity)
    urls = [
        f"/api/external-activities/{activity.id}/evidence",
        f"/api/external-activities/{activity.id}/evidence/{evidence.id}",
    ]

    client.headers.pop("X-Admin-Email", None)

    for url in urls:
        assert client.get(url, headers=CHEM_ADMIN).status_code == 403
        assert client.get(url, headers=CS_ADMIN).status_code == 200
        assert client.get(url, headers=CENTRAL).status_code == 200
        # นักศึกษาเจ้าของคำขอเปิดไฟล์ของตัวเองได้ แต่คนอื่นเปิดไม่ได้
        assert client.get(url, headers={"X-Student-Id": "S001"}).status_code == 200
        assert client.get(url, headers={"X-Student-Id": "C001"}).status_code == 403
        assert client.get(url).status_code == 401


# ------------------------------------------------------------
# อนุมัติ / ปฏิเสธ
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "approved"},
        {"status": "rejected", "reject_reason": "ไม่ผ่าน"},
    ],
)
def test_branch_admin_cannot_decide_other_major_external_activity(
    client, db_session, data, payload
):
    cs_id = data["cs_external"].id

    response = client.patch(
        f"/api/external-activities/{cs_id}/decision",
        json=payload,
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 403
    assert status_of(db_session, ExternalActivity, cs_id) == "pending"


def test_branch_admin_can_decide_own_major_external_activity(client, db_session, data):
    chem_id = data["chem_external"].id

    response = client.patch(
        f"/api/external-activities/{chem_id}/decision",
        json={"status": "approved"},
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 200
    assert status_of(db_session, ExternalActivity, chem_id) == "approved"


def test_branch_admin_cannot_decide_external_activity_without_major(
    client, db_session, data
):
    none_id = data["none_external"].id

    response = client.patch(
        f"/api/external-activities/{none_id}/decision",
        json={"status": "approved"},
        headers=CS_ADMIN,
    )

    assert response.status_code == 403
    assert status_of(db_session, ExternalActivity, none_id) == "pending"


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "approved"},
        {"status": "rejected", "reject_reason": "ไม่ผ่าน"},
    ],
)
def test_branch_admin_cannot_decide_other_major_student_request(
    client, db_session, data, payload
):
    cs_id = data["cs_request"].id

    response = client.patch(
        f"/api/requests/{cs_id}",
        json=payload,
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 403
    assert status_of(db_session, StudentRequest, cs_id) == "pending"


def test_orphan_student_request_is_central_only(client, db_session, data):
    orphan_id = data["orphan_request"].id

    denied = client.patch(
        f"/api/requests/{orphan_id}",
        json={"status": "approved"},
        headers=CHEM_ADMIN,
    )
    assert denied.status_code == 403
    assert status_of(db_session, StudentRequest, orphan_id) == "pending"

    allowed = client.patch(
        f"/api/requests/{orphan_id}",
        json={"status": "approved"},
        headers=CENTRAL,
    )
    assert allowed.status_code == 200
    assert status_of(db_session, StudentRequest, orphan_id) == "approved"


def test_branch_admin_can_decide_own_major_student_request(client, db_session, data):
    cs_id = data["cs_request"].id

    response = client.patch(
        f"/api/requests/{cs_id}",
        json={"status": "approved"},
        headers=CS_ADMIN,
    )

    assert response.status_code == 200
    assert status_of(db_session, StudentRequest, cs_id) == "approved"


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------


def approve_all_external(db_session):
    for activity in db_session.query(ExternalActivity).all():
        activity.status = "approved"
    db_session.commit()


def test_dashboard_counts_only_own_major(client, db_session, data):
    approve_all_external(db_session)

    # กิจกรรมของคณะ 1 รายการ (เป็นของสาขาเคมี) มีผู้เข้าร่วมทั้งเคมีและ CS
    activity = Activity(
        activity_type="Volunteer",
        name="Faculty Activity",
        start_at=datetime(2026, 3, 10, 9, 0, 0),
        end_at=datetime(2026, 3, 10, 12, 0, 0),
        responsible_person="Staff",
        location="Room 101",
        major=CHEM,
    )
    db_session.add(activity)
    db_session.commit()
    for student_id in ("C001", "S001"):
        db_session.add(
            ActivityMember(
                activity_id=activity.id,
                student_id=student_id,
                role="participant",
            )
        )
    create_student(db_session, "C002", CHEM)
    db_session.add(
        ActivityMember(
            activity_id=activity.id,
            student_id="C002",
            role="participant",
        )
    )
    db_session.commit()

    chem = client.get("/api/admin/dashboard?year=2026", headers=CHEM_ADMIN).json()
    central = client.get("/api/admin/dashboard?year=2026", headers=CENTRAL).json()

    assert chem["totalStudents"] == 2
    assert central["totalStudents"] == 4

    # C001, C002 (เคมี) เท่านั้น / C001, S001, C002 ทุกคน (ไม่รวมกิจกรรมภายนอก)
    assert chem["totalParticipants"] == 2
    assert central["totalParticipants"] == 3

    # "กิจกรรม" หมายถึงกิจกรรมของคณะเท่านั้น ไม่รวมกิจกรรมภายนอกที่อนุมัติแล้ว
    assert chem["totalActivities"] == 1
    assert central["totalActivities"] == 1


def test_dashboard_excludes_unowned_activity_from_branch_stats(client, db_session, data):
    """
    กิจกรรมที่ยังไม่มีเจ้าของ (major=None) ไม่ควรถูกนับเป็นสถิติ Dashboard ของ
    แอดมินสาขาไหนสาขาหนึ่ง (ต่างจาก GET /api/activities ที่ยังให้แอดมินสาขา
    เห็น/จัดการกิจกรรมที่ยังไม่มีเจ้าของได้ตามเดิม)
    """
    legacy_activity = Activity(
        activity_type="Workshop",
        name="Legacy Unowned",
        start_at=datetime(2026, 3, 15, 9, 0, 0),
        end_at=datetime(2026, 3, 15, 12, 0, 0),
        responsible_person="Staff",
        location="Room 1",
        major=None,
    )
    db_session.add(legacy_activity)
    db_session.commit()
    db_session.add(
        ActivityMember(
            activity_id=legacy_activity.id,
            student_id="C001",
            role="participant",
        )
    )
    db_session.commit()

    chem = client.get("/api/admin/dashboard?year=2026", headers=CHEM_ADMIN).json()
    central = client.get("/api/admin/dashboard?year=2026", headers=CENTRAL).json()

    # ไม่มีสถิติของเคมี เพราะกิจกรรมนี้ยังไม่มีเจ้าของ
    assert chem["totalActivities"] == 0
    assert chem["totalParticipants"] == 0

    # แอดมินกลางยังเห็น/นับกิจกรรมนี้ตามปกติ
    assert central["totalActivities"] == 1
    assert central["totalParticipants"] == 1

    # หน้ารายการกิจกรรม (list, ค่าเริ่มต้น) แอดมินสาขายังเห็นกิจกรรมที่ยังไม่มี
    # เจ้าของอยู่เหมือนเดิม -- เปลี่ยนแค่สถิติ Dashboard เท่านั้น
    activities_default = client.get("/api/activities", headers=CHEM_ADMIN).json()
    assert legacy_activity.id in {item["id"] for item in activities_default["activities"]}

    # แต่ตอนขอแบบ owned_only=true (ที่หน้า Dashboard ใช้คำนวณ Activity
    # Growth/Skill Distribution เอง) ต้องไม่เห็นกิจกรรมที่ยังไม่มีเจ้าของ
    activities_owned_only = client.get(
        "/api/activities?owned_only=true", headers=CHEM_ADMIN
    ).json()
    assert legacy_activity.id not in {
        item["id"] for item in activities_owned_only["activities"]
    }

    # แอดมินกลางเห็นเหมือนกันทั้งสองแบบ (ไม่มี major ให้กรอง)
    central_owned_only = client.get(
        "/api/activities?owned_only=true", headers=CENTRAL
    ).json()
    assert legacy_activity.id in {item["id"] for item in central_owned_only["activities"]}


def test_dashboard_external_activities_are_scoped(client, db_session, data):
    approve_all_external(db_session)

    chem = client.get(
        "/api/admin/dashboard/external-activities",
        headers=CHEM_ADMIN,
    ).json()["external_activities"]
    central = client.get(
        "/api/admin/dashboard/external-activities",
        headers=CENTRAL,
    ).json()["external_activities"]

    assert [item["id"] for item in chem] == [f"external-{data['chem_external'].id}"]
    assert len(central) == 3


# ------------------------------------------------------------
# Student Skills
# ------------------------------------------------------------


def test_student_skills_are_scoped(client, db_session, data):
    approve_all_external(db_session)

    chem = client.get(
        "/api/admin/student-skills?year=2026",
        headers=CHEM_ADMIN,
    ).json()
    central = client.get(
        "/api/admin/student-skills?year=2026",
        headers=CENTRAL,
    ).json()

    assert [item["id"] for item in chem["students"]] == ["C001"]
    assert chem["totalFaculty"] == 1
    assert {item["id"] for item in central["students"]} == {"C001", "N001", "S001"}
    assert central["totalFaculty"] == 3


def test_branch_admin_cannot_view_other_major_student_history(client, data):
    assert client.get(
        "/api/admin/students/S001/activities",
        headers=CHEM_ADMIN,
    ).status_code == 403
    assert client.get(
        "/api/admin/students/C001/activities",
        headers=CHEM_ADMIN,
    ).status_code == 200
    assert client.get(
        "/api/admin/students/N001/activities",
        headers=CHEM_ADMIN,
    ).status_code == 403


def test_only_central_admin_updates_benchmark(client):
    payload = {"scores": {"volunteerism": 3.5}}

    assert client.put(
        "/api/admin/student-skills/benchmark",
        json=payload,
        headers=CHEM_ADMIN,
    ).status_code == 403
    assert client.put(
        "/api/admin/student-skills/benchmark",
        json=payload,
        headers=CENTRAL,
    ).status_code == 200


def test_only_central_admin_imports_students(client):
    files = {"file": ("students.csv", b"student_id,first_name\n", "text/csv")}

    response = client.post(
        "/api/students/import",
        files=files,
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 403


# ------------------------------------------------------------
# ผู้เข้าร่วมกิจกรรมของคณะ (กิจกรรมใช้ร่วมกัน แต่รายชื่อกรองตามสาขา)
# ------------------------------------------------------------


@pytest.fixture()
def faculty_activity(db_session, data):
    activity = Activity(
        activity_type="Volunteer",
        name="Faculty Activity",
        start_at=datetime(2026, 3, 10, 9, 0, 0),
        end_at=datetime(2026, 3, 10, 12, 0, 0),
        responsible_person="Staff",
        location="Room 101",
    )
    db_session.add(activity)
    db_session.commit()
    for student_id in ("C001", "S001", "N001"):
        db_session.add(
            ActivityMember(
                activity_id=activity.id,
                student_id=student_id,
                role="participant",
            )
        )
    db_session.commit()
    return activity


def participant_ids(response):
    assert response.status_code == 200, response.text
    return {item["student_id"] for item in response.json()["students"]}


def test_all_admins_see_faculty_activities(client, faculty_activity):
    for headers in (CENTRAL, CHEM_ADMIN, CS_ADMIN):
        response = client.get("/api/activities", headers=headers)
        assert response.status_code == 200
        assert client.get(
            f"/api/activities/{faculty_activity.id}",
            headers=headers,
        ).status_code == 200


def test_participants_are_filtered_by_major(client, faculty_activity):
    url = f"/api/activities/{faculty_activity.id}/participants"

    assert participant_ids(client.get(url, headers=CHEM_ADMIN)) == {"C001"}
    assert participant_ids(client.get(url, headers=CS_ADMIN)) == {"S001"}
    assert participant_ids(client.get(url, headers=CENTRAL)) == {
        "C001",
        "S001",
        "N001",
    }


def test_activity_list_participant_count_matches_detail_view(
    client, faculty_activity
):
    # บั๊กเดิม: /api/activities นับสมาชิกทุกคนแบบไม่กรอง major เลย ในขณะที่
    # /api/activities/{id}/participants กรองตาม major ของแอดมิน ทำให้หน้า
    # list บอกว่ามี 3 คน แต่พอกดดูหน้า detail กลับเห็นแค่บางส่วน (หรือ 0 คน)
    # ต้องนับให้ตรงกันเสมอ ไม่ว่าแอดมินที่เรียกจะเป็นแอดมินสาขาไหนก็ตาม
    def list_participant_count(headers):
        activities = client.get(
            "/api/activities", headers=headers
        ).json()["activities"]
        activity = next(
            item
            for item in activities
            if item["id"] == faculty_activity.id
        )
        return activity["participants"]

    detail_url = f"/api/activities/{faculty_activity.id}/participants"

    for headers, expected_ids in (
        (CHEM_ADMIN, {"C001"}),
        (CS_ADMIN, {"S001"}),
        (CENTRAL, {"C001", "S001", "N001"}),
    ):
        detail_ids = participant_ids(
            client.get(detail_url, headers=headers)
        )
        assert detail_ids == expected_ids
        assert list_participant_count(headers) == len(expected_ids)


def participant_payload(major):
    return {
        "first_name": "Edited",
        "last_name": "Name",
        "email": "edited@test.local",
        "faculty": "Faculty of Science",
        "major": major,
        "role": "participant",
    }


def test_branch_admin_cannot_edit_or_remove_other_major_participant(
    client, db_session, faculty_activity
):
    url = f"/api/activities/{faculty_activity.id}/participants/S001"

    assert client.patch(
        url,
        json=participant_payload(CS),
        headers=CHEM_ADMIN,
    ).status_code == 403
    assert client.delete(url, headers=CHEM_ADMIN).status_code == 403

    db_session.expire_all()
    assert db_session.get(Student, "S001").first_name == "Test"
    assert db_session.get(ActivityMember, (faculty_activity.id, "S001")) is not None


def test_branch_admin_cannot_move_student_to_other_major(
    client, db_session, faculty_activity
):
    response = client.patch(
        f"/api/activities/{faculty_activity.id}/participants/C001",
        json=participant_payload(CS),
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 403
    db_session.expire_all()
    assert db_session.get(Student, "C001").major == CHEM


def test_branch_admin_can_edit_own_major_participant(
    client, db_session, faculty_activity
):
    response = client.patch(
        f"/api/activities/{faculty_activity.id}/participants/C001",
        json=participant_payload(CHEM),
        headers=CHEM_ADMIN,
    )

    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(Student, "C001").first_name == "Edited"


def test_student_endpoints_do_not_need_admin(client, data):
    client.headers.pop("X-Admin-Email", None)

    response = client.get(
        "/api/student/me/external-activities",
        headers={"X-Student-Id": "C001"},
    )

    assert response.status_code == 200


# ------------------------------------------------------------
# Activity major-scoping: แอดมินสาขาเห็นเฉพาะกิจกรรมของสาขาตัวเอง
# (รวมกิจกรรมที่ยังไม่มีเจ้าของ major=None) ส่วนแอดมินกลางเห็นทุกกิจกรรม
# ------------------------------------------------------------


def create_activity(db_session, major=None, name="Branch Activity") -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=datetime(2026, 4, 1, 9, 0, 0),
        end_at=datetime(2026, 4, 1, 12, 0, 0),
        responsible_person="Staff",
        location="Room 1",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def activity_ids(response):
    assert response.status_code == 200, response.text
    return {item["id"] for item in response.json()["activities"]}


def test_branch_admin_cannot_see_other_branch_activity(client, db_session):
    chem_activity = create_activity(db_session, major=CHEM, name="Chem Only")
    cs_activity = create_activity(db_session, major=CS, name="CS Only")

    assert activity_ids(
        client.get("/api/activities", headers=CHEM_ADMIN)
    ) == {chem_activity.id}
    assert activity_ids(
        client.get("/api/activities", headers=CS_ADMIN)
    ) == {cs_activity.id}

    assert (
        client.get(
            f"/api/activities/{cs_activity.id}", headers=CHEM_ADMIN
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/activities/{chem_activity.id}", headers=CS_ADMIN
        ).status_code
        == 403
    )

    assert (
        client.get(
            f"/api/activities/{chem_activity.id}", headers=CHEM_ADMIN
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/activities/{cs_activity.id}", headers=CS_ADMIN
        ).status_code
        == 200
    )

    # participants endpoint ใช้ require_activity เหมือนกัน ต้อง 403 ด้วย
    assert (
        client.get(
            f"/api/activities/{cs_activity.id}/participants",
            headers=CHEM_ADMIN,
        ).status_code
        == 403
    )


def test_central_admin_sees_all_branch_activities(client, db_session):
    chem_activity = create_activity(db_session, major=CHEM, name="Chem Only")
    cs_activity = create_activity(db_session, major=CS, name="CS Only")

    seen = activity_ids(client.get("/api/activities", headers=CENTRAL))
    assert {chem_activity.id, cs_activity.id} <= seen

    assert (
        client.get(
            f"/api/activities/{chem_activity.id}", headers=CENTRAL
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/activities/{cs_activity.id}", headers=CENTRAL
        ).status_code
        == 200
    )


def test_legacy_activity_without_major_is_visible_to_every_admin(
    client, db_session
):
    legacy_activity = create_activity(db_session, major=None, name="No Owner Yet")

    for headers in (CHEM_ADMIN, CS_ADMIN, CENTRAL):
        assert legacy_activity.id in activity_ids(
            client.get("/api/activities", headers=headers)
        )
        assert (
            client.get(
                f"/api/activities/{legacy_activity.id}", headers=headers
            ).status_code
            == 200
        )


ACTIVITY_CREATE_PAYLOAD = {
    "activity_type": "Workshop",
    "name": "New Activity",
    "start_at": "2026-05-01T09:00:00",
    "end_at": "2026-05-01T12:00:00",
    "department": "",
    "responsible_person": "Staff",
    "advisor": "",
    "location": "Room 1",
    "description": "",
    "staff_skills": {},
    "participant_skills": {},
}


def test_new_activity_is_auto_owned_by_creating_branch_admin(client, db_session):
    response = client.post(
        "/api/activities",
        json=ACTIVITY_CREATE_PAYLOAD,
        headers=CHEM_ADMIN,
    )
    assert response.status_code == 201
    activity_id = response.json()["id"]

    db_session.expire_all()
    assert db_session.get(Activity, activity_id).major == CHEM

    assert (
        client.get(
            f"/api/activities/{activity_id}", headers=CS_ADMIN
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/activities/{activity_id}", headers=CENTRAL
        ).status_code
        == 200
    )


def test_new_activity_created_by_central_admin_has_no_owner(client, db_session):
    response = client.post(
        "/api/activities",
        json=ACTIVITY_CREATE_PAYLOAD,
        headers=CENTRAL,
    )
    assert response.status_code == 201
    activity_id = response.json()["id"]

    db_session.expire_all()
    assert db_session.get(Activity, activity_id).major is None

    assert (
        client.get(
            f"/api/activities/{activity_id}", headers=CHEM_ADMIN
        ).status_code
        == 200
    )
