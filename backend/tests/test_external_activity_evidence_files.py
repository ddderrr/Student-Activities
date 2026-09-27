import base64
import json
from datetime import date

from models import (
    ExternalActivity,
    ExternalActivityEvidence,
    ExternalActivitySkill,
    Student,
)

STUDENT_ID = "670510659"
HEADERS = {"X-Student-Id": STUDENT_ID}

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
PDF_BYTES = b"%PDF-1.4\n%test\n"
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"0" * 16

FORM = {
    "title": "Volunteer Camp",
    "organization": "Some NGO",
    "activity_type": "จิตอาสา / บริการสังคม",
    "start_date": "2026-02-01",
    "end_date": "2026-02-01",
    "location": "Chiang Mai",
    "role": "participant",
    "description": "",
    "skills": json.dumps({"volunteerism": 4}),
}


def png(name):
    return ("evidence", (name, PNG_BYTES, "image/png"))


def create_student(db_session, student_id=STUDENT_ID) -> Student:
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
    return student


def create_request(db_session, upload_dir, status="rejected", file_names=("a.png", "b.png"), student_id=STUDENT_ID):
    """คำขอในรูปแบบใหม่: ไฟล์อยู่ใน uploads/<id>/ และมีแถวใน external_activity_evidence"""
    activity = ExternalActivity(
        student_id=student_id,
        title="Old Title",
        organization="Old Org",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
        location="Chiang Mai",
        role="participant",
        status=status,
        reject_reason="ไม่ชัดเจน" if status == "rejected" else None,
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

    folder = upload_dir / str(activity.id)
    folder.mkdir()
    for index, name in enumerate(file_names):
        stored_name = f"stored{index}-{activity.id}.png"
        (folder / stored_name).write_bytes(PNG_BYTES)
        db_session.add(
            ExternalActivityEvidence(
                external_activity_id=activity.id,
                stored_name=stored_name,
                original_name=name,
                content_type="image/png",
                size=len(PNG_BYTES),
            )
        )
    db_session.commit()
    db_session.refresh(activity)
    return activity


def stored_files(upload_dir, activity_id):
    folder = upload_dir / str(activity_id)
    return sorted(path.name for path in folder.iterdir()) if folder.exists() else []


# ---------- Submit ----------

def test_submit_with_multiple_files(client, db_session, upload_dir):
    create_student(db_session)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
        files=[
            png("one.png"),
            ("evidence", ("two.pdf", PDF_BYTES, "application/pdf")),
            ("evidence", ("three.jpg", JPEG_BYTES, "image/jpeg")),
        ],
    )

    assert response.status_code == 201, response.text
    body = response.json()
    files = body["evidence_files"]
    assert [item["original_name"] for item in files] == ["one.png", "two.pdf", "three.jpg"]
    assert [item["content_type"] for item in files] == ["image/png", "application/pdf", "image/jpeg"]
    assert len(stored_files(upload_dir, body["id"])) == 3
    # ช่อง evidence เดิมยังอยู่ (ไฟล์แรก) ให้โค้ดเก่าใช้ต่อได้
    assert body["evidence"]["original_name"] == "one.png"

    downloaded = client.get(files[1]["url"])
    assert downloaded.status_code == 200
    assert downloaded.content == PDF_BYTES
    assert downloaded.headers["content-type"] == "application/pdf"


def test_submit_rejects_more_than_ten_files(client, db_session, upload_dir):
    create_student(db_session)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
        files=[png(f"{index}.png") for index in range(11)],
    )

    assert response.status_code == 400
    assert db_session.query(ExternalActivity).count() == 0
    assert list(upload_dir.iterdir()) == []


def test_submit_accepts_exactly_ten_files(client, db_session, upload_dir):
    create_student(db_session)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
        files=[png(f"{index}.png") for index in range(10)],
    )

    assert response.status_code == 201
    assert len(response.json()["evidence_files"]) == 10


def test_submit_requires_at_least_one_file(client, db_session, upload_dir):
    create_student(db_session)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
    )

    assert response.status_code == 400
    assert db_session.query(ExternalActivity).count() == 0


def test_one_bad_file_rejects_whole_submission(client, db_session, upload_dir):
    create_student(db_session)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
        files=[
            png("good.png"),
            # นามสกุล .png แต่เนื้อไฟล์เป็น PDF: magic bytes ไม่ตรง
            ("evidence", ("fake.png", PDF_BYTES, "image/png")),
        ],
    )

    assert response.status_code == 400
    assert db_session.query(ExternalActivity).count() == 0
    assert list(upload_dir.iterdir()) == []


def test_file_over_5mb_is_rejected(client, db_session, upload_dir):
    create_student(db_session)
    too_big = PNG_BYTES + b"0" * (5 * 1024 * 1024)

    response = client.post(
        "/api/student/me/external-activities",
        headers=HEADERS,
        data=FORM,
        files=[png("ok.png"), ("evidence", ("big.png", too_big, "image/png"))],
    )

    assert response.status_code == 400
    assert db_session.query(ExternalActivity).count() == 0


# ---------- Resubmit ----------

def test_resubmit_can_remove_and_add_files(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=("keep.png", "drop.png"))
    keep, drop = activity.evidence_files

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data={**FORM, "remove_evidence_ids": [str(drop.id)]},
        files=[png("new1.png"), ("evidence", ("new2.pdf", PDF_BYTES, "application/pdf"))],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert [item["original_name"] for item in body["evidence_files"]] == ["keep.png", "new1.png", "new2.pdf"]

    names = stored_files(upload_dir, activity.id)
    assert keep.stored_name in names
    assert drop.stored_name not in names
    assert len(names) == 3


def test_resubmit_without_file_changes_keeps_files(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir)

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data=FORM,
    )

    assert response.status_code == 200
    assert [item["original_name"] for item in response.json()["evidence_files"]] == ["a.png", "b.png"]
    assert len(stored_files(upload_dir, activity.id)) == 2


def test_resubmit_cannot_exceed_ten_files(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=[f"{i}.png" for i in range(8)])

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data=FORM,
        files=[png(f"new{i}.png") for i in range(3)],
    )

    assert response.status_code == 400
    db_session.expire_all()
    assert db_session.get(ExternalActivity, activity.id).status == "rejected"
    assert len(stored_files(upload_dir, activity.id)) == 8


def test_resubmit_can_swap_files_at_the_limit(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=[f"{i}.png" for i in range(10)])
    remove_ids = [str(item.id) for item in activity.evidence_files[:2]]

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data={**FORM, "remove_evidence_ids": remove_ids},
        files=[png("x.png"), png("y.png")],
    )

    assert response.status_code == 200, response.text
    assert len(response.json()["evidence_files"]) == 10


def test_resubmit_cannot_remove_every_file(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir)
    remove_ids = [str(item.id) for item in activity.evidence_files]

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data={**FORM, "remove_evidence_ids": remove_ids},
    )

    assert response.status_code == 400
    assert len(stored_files(upload_dir, activity.id)) == 2


def test_resubmit_cannot_remove_file_of_another_request(client, db_session, upload_dir):
    create_student(db_session)
    mine = create_request(db_session, upload_dir)
    other = create_request(db_session, upload_dir)

    response = client.put(
        f"/api/student/me/external-activities/{mine.id}",
        headers=HEADERS,
        data={**FORM, "remove_evidence_ids": [str(other.evidence_files[0].id)]},
    )

    assert response.status_code == 400
    assert len(stored_files(upload_dir, other.id)) == 2


def test_resubmit_bad_new_file_changes_nothing(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir)
    drop = activity.evidence_files[0]

    response = client.put(
        f"/api/student/me/external-activities/{activity.id}",
        headers=HEADERS,
        data={**FORM, "remove_evidence_ids": [str(drop.id)]},
        files=[("evidence", ("fake.pdf", PNG_BYTES, "application/pdf"))],
    )

    assert response.status_code == 400
    assert drop.stored_name in stored_files(upload_dir, activity.id)
    assert len(stored_files(upload_dir, activity.id)) == 2


# ---------- Admin / serving ----------

def test_admin_detail_lists_every_file(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, status="pending", file_names=("1.png", "2.png", "3.png"))

    response = client.get(f"/api/external-activities/{activity.id}")

    assert response.status_code == 200
    files = response.json()["evidence_files"]
    assert [item["original_name"] for item in files] == ["1.png", "2.png", "3.png"]
    for item in files:
        assert client.get(item["url"]).status_code == 200


def test_file_url_of_another_request_is_404(client, db_session, upload_dir):
    create_student(db_session)
    first = create_request(db_session, upload_dir)
    second = create_request(db_session, upload_dir)

    response = client.get(
        f"/api/external-activities/{first.id}/evidence/{second.evidence_files[0].id}"
    )

    assert response.status_code == 404


def test_legacy_evidence_url_serves_first_file(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=("first.png", "second.png"))

    response = client.get(f"/api/external-activities/{activity.id}/evidence")

    assert response.status_code == 200
    assert "first.png" in response.headers["content-disposition"]


def test_file_not_yet_moved_is_still_served(client, db_session, upload_dir):
    # คำขอเก่าหลังรัน SQL migration แต่ยังไม่ได้รันสคริปต์ย้ายไฟล์: ไฟล์ยังอยู่ที่ uploads/ ชั้นบน
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=("old.png",))
    evidence = activity.evidence_files[0]
    (upload_dir / str(activity.id) / evidence.stored_name).rename(upload_dir / evidence.stored_name)

    response = client.get(f"/api/external-activities/{activity.id}/evidence/{evidence.id}")

    assert response.status_code == 200
    assert response.content == PNG_BYTES


def test_my_activities_lists_every_file_of_approved_request(client, db_session, upload_dir):
    create_student(db_session)
    create_request(db_session, upload_dir, status="approved", file_names=("1.png", "2.png"))

    response = client.get("/api/student/me/activities", headers=HEADERS)

    assert response.status_code == 200
    external = [item for item in response.json()["activities"] if item["source"] == "external_activity"]
    assert [item["original_name"] for item in external[0]["evidence_files"]] == ["1.png", "2.png"]


# ---------- Delete (งานข้อ 2) ----------

def test_delete_request_removes_every_file(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=("1.png", "2.png", "3.png"))
    activity_id = activity.id

    response = client.delete(f"/api/student/me/external-activities/{activity_id}", headers=HEADERS)

    assert response.status_code == 204
    assert not (upload_dir / str(activity_id)).exists()
    db_session.expire_all()
    assert db_session.query(ExternalActivityEvidence).filter_by(external_activity_id=activity_id).count() == 0


def test_delete_request_removes_files_not_yet_moved(client, db_session, upload_dir):
    create_student(db_session)
    activity = create_request(db_session, upload_dir, file_names=("old.png",))
    evidence = activity.evidence_files[0]
    (upload_dir / str(activity.id) / evidence.stored_name).rename(upload_dir / evidence.stored_name)

    response = client.delete(f"/api/student/me/external-activities/{activity.id}", headers=HEADERS)

    assert response.status_code == 204
    assert not (upload_dir / evidence.stored_name).exists()
