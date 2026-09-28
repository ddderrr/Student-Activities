"""
แอดมินกลางเลือก filter สาขา (?major=) ได้จากหน้า Dashboard / Activities /
Student Skills / Approvals -- ดู admin_scope.resolve_branch_filter

แอดมินสาขาเรียกเองส่ง ?major= มาก็ไม่มีผล (ถูก scope ตามสาขาตัวเองอยู่แล้ว)
"""

from datetime import date, datetime

from models import Activity, ActivityMember, ExternalActivity, Student

CS = "วิทยาการคอมพิวเตอร์"
CHEM = "เคมี"

CENTRAL = {"X-Admin-Email": "central@test.local"}
CHEM_ADMIN = {"X-Admin-Email": "chem@test.local"}
CS_ADMIN = {"X-Admin-Email": "cs@test.local"}


def create_student(db_session, student_id, major) -> Student:
    student = Student(
        student_id=student_id,
        first_name="Test",
        last_name=student_id,
        email=f"{student_id}@test.local",
        faculty="คณะวิทยาศาสตร์",
        major=major,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def create_activity(db_session, major, name, start_at=datetime(2026, 3, 10, 9, 0, 0)) -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=start_at,
        end_at=start_at,
        responsible_person="Staff",
        location="Room 1",
        major=major,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def add_member(db_session, activity, student_id, role="participant"):
    db_session.add(
        ActivityMember(activity_id=activity.id, student_id=student_id, role=role)
    )
    db_session.commit()


def setup_two_branches(db_session):
    cs_student = create_student(db_session, "S001", CS)
    chem_student = create_student(db_session, "C001", CHEM)

    cs_activity = create_activity(db_session, CS, "CS Only")
    chem_activity = create_activity(db_session, CHEM, "Chem Only")

    add_member(db_session, cs_activity, cs_student.student_id)
    add_member(db_session, chem_activity, chem_student.student_id)

    return cs_activity, chem_activity


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------


def test_dashboard_major_filter_matches_the_real_branch_admin(client, db_session):
    setup_two_branches(db_session)

    central_as_cs = client.get(
        "/api/admin/dashboard?year=2026&major=" + CS, headers=CENTRAL
    ).json()
    real_cs = client.get("/api/admin/dashboard?year=2026", headers=CS_ADMIN).json()

    assert central_as_cs["totalActivities"] == real_cs["totalActivities"] == 1
    assert central_as_cs["totalParticipants"] == real_cs["totalParticipants"] == 1
    assert central_as_cs["totalStudents"] == real_cs["totalStudents"]

    central_as_chem = client.get(
        "/api/admin/dashboard?year=2026&major=" + CHEM, headers=CENTRAL
    ).json()
    assert central_as_chem["totalActivities"] == 1
    assert central_as_chem["totalParticipants"] == 1


def test_dashboard_no_major_param_still_sees_everything(client, db_session):
    setup_two_branches(db_session)

    everything = client.get("/api/admin/dashboard?year=2026", headers=CENTRAL).json()
    assert everything["totalActivities"] == 2
    assert everything["totalParticipants"] == 2


def test_dashboard_major_filter_ignored_for_branch_admin(client, db_session):
    setup_two_branches(db_session)

    # แอดมิน CS ส่ง major=เคมี มาเอง ก็ไม่ควรได้เห็นข้อมูลเคมี
    response = client.get(
        "/api/admin/dashboard?year=2026&major=" + CHEM, headers=CS_ADMIN
    ).json()
    assert response["totalActivities"] == 1  # ยังเห็นแค่ของ CS ตัวเอง


# ------------------------------------------------------------
# Activities list
# ------------------------------------------------------------


def test_activities_major_filter_for_central_admin(client, db_session):
    cs_activity, chem_activity = setup_two_branches(db_session)

    response = client.get(
        "/api/activities?major=" + CS, headers=CENTRAL
    ).json()
    ids = {item["id"] for item in response["activities"]}

    assert cs_activity.id in ids
    assert chem_activity.id not in ids


# ------------------------------------------------------------
# Student Skills
# ------------------------------------------------------------


def test_student_skills_major_filter_for_central_admin(client, db_session):
    setup_two_branches(db_session)

    response = client.get(
        "/api/admin/student-skills?major=" + CS, headers=CENTRAL
    ).json()

    # totalFaculty = จำนวนนักศึกษาสาขา CS เท่านั้น (S001)
    assert response["totalFaculty"] == 1


# ------------------------------------------------------------
# Approvals (/api/requests, /api/requests/stats)
# ------------------------------------------------------------


def create_external(db_session, student_id, status="pending") -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title="External",
        organization="Org",
        activity_type="Workshop",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 1),
        location="Online",
        role="participant",
        description="",
        evidence_filename="e.png",
        evidence_original_name="e.png",
        evidence_content_type="image/png",
        evidence_size=10,
        status=status,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_requests_major_filter_for_central_admin(client, db_session):
    create_student(db_session, "S001", CS)
    create_student(db_session, "C001", CHEM)
    create_external(db_session, "S001")
    create_external(db_session, "C001")

    response = client.get(
        "/api/requests?status=pending&major=" + CS, headers=CENTRAL
    ).json()

    assert response["total"] == 1
    assert response["requests"][0]["requester_student_id"] == "S001"


def test_requests_stats_major_filter_for_central_admin(client, db_session):
    create_student(db_session, "S001", CS)
    create_student(db_session, "C001", CHEM)
    create_external(db_session, "S001")
    create_external(db_session, "C001")

    response = client.get(
        "/api/requests/stats?major=" + CS, headers=CENTRAL
    ).json()

    assert response["total_pending"] == 1
