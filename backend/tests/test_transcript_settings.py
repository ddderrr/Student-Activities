"""หัวเอกสาร Transcript ที่แอดมินกลางแก้จากหน้า Settings (GET / PUT /api/admin/settings/transcript)"""

from io import BytesIO

from pypdf import PdfReader

import transcript_config
from models import Student
from tests.conftest import CHEM_ADMIN_EMAIL

URL = "/api/admin/settings/transcript"
STUDENT = {"X-Student-Id": "670510123"}


def make_student(db_session):
    db_session.add(Student(student_id="670510123", first_name="John", last_name="Smith",
                           email="john@cmu.ac.th", faculty="Faculty of Science", major="เคมี"))
    db_session.commit()


def pdf_text(client, lang):
    response = client.get("/api/student/me/transcript/export", params={"style": "A", "lang": lang}, headers=STUDENT)
    assert response.status_code == 200
    return " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages).replace("\n", " ")


def test_defaults_come_from_config(client):
    body = client.get(URL).json()

    assert body["values"]["university_name"] == transcript_config.UNIVERSITY_NAME
    assert body["values"]["document_title_en"] == transcript_config.DOCUMENT_TITLE_EN
    assert body["values"] == body["defaults"]
    assert len(body["values"]) == 10


def test_saved_header_is_used_by_next_pdf_in_both_languages(client, db_session):
    make_student(db_session)
    response = client.put(URL, json={
        "signer_name": "ศ.ดร.สมศักดิ์ ใจดี",
        "signer_name_en": "Prof. Somsak Jaidee",
        "signer_position": "คณบดีคณะวิทยาศาสตร์",
        "signer_position_en": "Dean, Faculty of Science",
        "document_title_en": "Official Activity Transcript",
    })
    assert response.status_code == 200
    assert response.json()["values"]["signer_name"] == "ศ.ดร.สมศักดิ์ ใจดี"

    assert "Prof. Somsak Jaidee" in pdf_text(client, "en")
    assert "Dean, Faculty of Science" in pdf_text(client, "en")
    assert "Official Activity Transcript" in pdf_text(client, "en")
    thai = pdf_text(client, "th")
    assert "สมศักดิ์" in thai
    # ไม่ได้แก้ช่องภาษาไทยของหัวข้อ = ยังเป็นค่าเริ่มต้น
    assert "ใบรับรอง" in thai


def test_empty_value_resets_to_default_and_whitespace_is_tidied(client):
    client.put(URL, json={"university_name": "  มหาวิทยาลัย   ทดสอบ  "})
    assert client.get(URL).json()["values"]["university_name"] == "มหาวิทยาลัย ทดสอบ"

    client.put(URL, json={"university_name": ""})
    assert client.get(URL).json()["values"]["university_name"] == transcript_config.UNIVERSITY_NAME


def test_validation(client):
    assert client.put(URL, json={"signer_name": "ก" * 201}).status_code == 400
    assert client.put(URL, json={"watermark": "x"}).status_code == 400


def test_branch_admin_can_edit_shared_header(client):
    branch = {"X-Admin-Email": CHEM_ADMIN_EMAIL}

    assert client.get(URL, headers=branch).status_code == 200
    assert client.put(URL, json={"signer_name": "ศ.ดร.สาขา"}, headers=branch).status_code == 200
    # หัวเอกสารใช้ร่วมกันทั้งคณะ แอดมินกลางเห็นค่าเดียวกัน
    assert client.get(URL).json()["values"]["signer_name"] == "ศ.ดร.สาขา"


def preview_text(response):
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    return " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages).replace("\n", " ")


def test_preview_uses_unsaved_values_and_sample_student(client):
    client.put(URL, json={"signer_name_en": "Prof. Saved Value"})

    for style in ("A", "B"):
        text = preview_text(client.post(f"{URL}/preview", params={"style": style, "lang": "en"},
                                        json={"document_title_en": "Draft Title"}))
        assert "Draft Title" in text
        assert "Prof. Saved Value" in text  # ช่องที่ไม่ได้ส่งมา = ค่าที่บันทึกไว้
        assert "670510123" in text
        assert "47" in text  # ชั่วโมงกิจกรรมสะสมของนักศึกษาตัวอย่าง

    # ตัวอย่างไม่บันทึกอะไร
    assert client.get(URL).json()["values"]["document_title_en"] == transcript_config.DOCUMENT_TITLE_EN


def test_preview_empty_value_shows_default(client):
    client.put(URL, json={"signer_name_en": "Prof. Saved Value"})
    text = preview_text(client.post(f"{URL}/preview", params={"lang": "en"}, json={"signer_name_en": "  "}))
    assert "Prof. Saved Value" not in text


def test_preview_validation_and_access(client):
    assert client.post(f"{URL}/preview", params={"style": "C"}, json={}).status_code == 400
    assert client.post(f"{URL}/preview", params={"lang": "jp"}, json={}).status_code == 400
    assert client.post(f"{URL}/preview", json={"unknown": "x"}).status_code == 400
    assert client.post(f"{URL}/preview", json={"signer_name": "x" * 201}).status_code == 400
    assert client.post(f"{URL}/preview", json={}, headers={"X-Admin-Email": CHEM_ADMIN_EMAIL}).status_code == 200
