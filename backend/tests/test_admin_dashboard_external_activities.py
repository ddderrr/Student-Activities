from datetime import date, datetime

from models import ExternalActivity, ExternalActivitySkill, Student


def create_student(db_session, student_id="670510659") -> Student:
    student = Student(
        student_id=student_id,
        first_name="Test",
        last_name="Student",
        email="",
        faculty="Faculty of Science",
        major="",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def create_external_activity(db_session, student_id="670510659", **overrides) -> ExternalActivity:
    defaults = dict(
        student_id=student_id,
        title="Volunteer Camp",
        organization="Some NGO",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 1),
        location="Chiang Mai",
        role="participant",
        description="",
        evidence_filename="evidence.png",
        evidence_original_name="evidence.png",
        evidence_content_type="image/png",
        evidence_size=100,
        status="pending",
    )
    defaults.update(overrides)

    activity = ExternalActivity(**defaults)
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_dashboard_never_counts_external_activities_even_when_approved(client, db_session):
    """
    "กิจกรรม" ในหน้า Dashboard หมายถึงกิจกรรมของคณะ (Activity) เท่านั้น เพื่อให้
    ตรงกับหน้า Activities list เสมอ -- อนุมัติกิจกรรมภายนอกแล้วก็ไม่ควรทำให้
    totalActivities/totalParticipants/activityGrowth ของ Dashboard เปลี่ยน
    (ก่อนหน้านี้เคยรวมกันเงียบ ๆ ทำให้ตัวเลขไม่ตรงกับ Activities list)
    """
    create_student(db_session)

    baseline = client.get("/api/admin/dashboard").json()

    activity = create_external_activity(db_session, status="pending")

    pending_stats = client.get("/api/admin/dashboard").json()
    assert pending_stats["totalActivities"] == baseline["totalActivities"]
    assert pending_stats["totalParticipants"] == baseline["totalParticipants"]

    activity.status = "approved"
    activity.decided_at = datetime(2026, 3, 2)
    db_session.commit()

    approved_stats = client.get("/api/admin/dashboard").json()
    assert approved_stats["totalActivities"] == baseline["totalActivities"]
    assert approved_stats["totalParticipants"] == baseline["totalParticipants"]

    if approved_stats["year"] == 2026:
        march_count = next(
            item["count"] for item in approved_stats["activityGrowth"] if item["month"] == "MAR"
        )
        baseline_march_count = next(
            item["count"] for item in baseline["activityGrowth"] if item["month"] == "MAR"
        )
        assert march_count == baseline_march_count


def test_dashboard_external_activities_endpoint_only_lists_approved(client, db_session):
    create_student(db_session)

    pending = create_external_activity(db_session, status="pending")
    approved = create_external_activity(
        db_session,
        student_id="670510659",
        status="approved",
        start_date=date(2026, 5, 20),
        end_date=date(2026, 5, 20),
    )

    response = client.get("/api/admin/dashboard/external-activities")
    assert response.status_code == 200

    items = response.json()["external_activities"]
    ids = [item["id"] for item in items]

    assert f"external-{approved.id}" in ids
    assert f"external-{pending.id}" not in ids

    approved_item = next(item for item in items if item["id"] == f"external-{approved.id}")
    assert approved_item["start_at"] == "2026-05-20"


def test_dashboard_external_activities_endpoint_includes_skills(client, db_session):
    create_student(db_session)

    activity = create_external_activity(
        db_session,
        status="approved",
        role="participant",
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 5),
    )
    db_session.add(
        ExternalActivitySkill(
            external_activity_id=activity.id,
            skill_key="volunteerism",
            target_role="participant",
            level=4,
        )
    )
    db_session.commit()

    response = client.get("/api/admin/dashboard/external-activities")
    item = next(
        i for i in response.json()["external_activities"] if i["id"] == f"external-{activity.id}"
    )

    assert item["participant_skills"] == {"volunteerism": 4}
    assert item["staff_skills"] == {}
