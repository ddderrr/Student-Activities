import base64
import json
from datetime import date

from models import ExternalActivity, ExternalActivitySkill, Student

# 1x1 transparent PNG, valid enough to pass the evidence content-sniff check.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


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


def create_rejected_activity(db_session, student_id="670510659") -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title="Old Title",
        organization="Old Org",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
        location="Chiang Mai",
        role="participant",
        description="old description",
        evidence_filename="old-evidence.png",
        evidence_original_name="old-evidence.png",
        evidence_content_type="image/png",
        evidence_size=100,
        status="rejected",
        reject_reason="ไฟล์หลักฐานไม่ชัดเจน",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    db_session.add(
        ExternalActivitySkill(
            external_activity_id=activity.id,
            skill_key="volunteerism",
            target_role="participant",
            level=3,
        )
    )
    db_session.commit()

    return activity


def test_resubmit_rejected_activity_without_new_evidence(client, db_session):
    create_student(db_session)
    activity = create_rejected_activity(db_session)

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers={"X-Student-Id": "670510659"},
        data={
            "title": "Updated Title",
            "organization": "Updated Org",
            "activity_type": "จิตอาสา / บริการสังคม",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "location": "Bangkok",
            "role": "participant",
            "description": "updated description",
            "skills": json.dumps({"volunteerism": 5}),
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["title"] == "Updated Title"
    assert body["status"] == "pending"
    assert body["reject_reason"] is None
    assert body["skills"] == {"volunteerism": 5}
    # ไม่ได้แนบไฟล์ใหม่ ต้องยังใช้ไฟล์เดิม
    assert body["evidence"]["original_name"] == "old-evidence.png"


def test_resubmit_rejected_activity_with_new_evidence(client, db_session):
    create_student(db_session)
    activity = create_rejected_activity(db_session)

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers={"X-Student-Id": "670510659"},
        data={
            "title": "Updated Title",
            "organization": "Updated Org",
            "activity_type": "จิตอาสา / บริการสังคม",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "location": "Bangkok",
            "role": "participant",
            "description": "updated description",
            "skills": json.dumps({"volunteerism": 5}),
        },
        files={"evidence": ("new-evidence.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"]["original_name"] == "new-evidence.png"


def test_cannot_edit_non_rejected_activity(client, db_session):
    create_student(db_session)
    activity = create_rejected_activity(db_session)
    activity.status = "pending"
    db_session.commit()

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers={"X-Student-Id": "670510659"},
        data={
            "title": "Updated Title",
            "organization": "Updated Org",
            "activity_type": "จิตอาสา / บริการสังคม",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "location": "Bangkok",
            "role": "participant",
            "description": "",
            "skills": json.dumps({"volunteerism": 5}),
        },
    )

    assert response.status_code == 400


def test_cannot_edit_another_students_activity(client, db_session):
    create_student(db_session, student_id="670510659")
    create_student(db_session, student_id="111111111")
    activity = create_rejected_activity(db_session, student_id="670510659")

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers={"X-Student-Id": "111111111"},
        data={
            "title": "Hijacked",
            "organization": "Updated Org",
            "activity_type": "จิตอาสา / บริการสังคม",
            "start_date": "2026-02-01",
            "end_date": "2026-02-01",
            "location": "Bangkok",
            "role": "participant",
            "description": "",
            "skills": json.dumps({"volunteerism": 5}),
        },
    )

    assert response.status_code == 404
