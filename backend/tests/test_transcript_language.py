"""Transcript PDF สองภาษา: lang=th ข้อความไทยทั้งฉบับ (พ.ศ.) / lang=en อังกฤษทั้งฉบับ (ค.ศ.)

ข้อมูลที่ผู้ใช้กรอก (ชื่อ, ชื่อกิจกรรม, ผู้จัด) แสดงตามที่บันทึก เทสต์จึงใช้ข้อมูลภาษาอังกฤษ
แล้วตรวจว่าเอกสารภาษาอังกฤษไม่มีอักษรไทยเหลือเลย
"""

import re
from datetime import date, datetime
from io import BytesIO

import pytest
from pypdf import PdfReader

import transcript_data
from models import Activity, ActivityMember, ActivitySkill, ExternalActivity, Student
from transcript_pdf import render_transcript_html

THAI = re.compile(r"[฀-๿]")
STUDENT_ID = "670510123"
HEADERS = {"X-Student-Id": STUDENT_ID}
ISSUED_ON = date(2026, 10, 2)


@pytest.fixture()
def student(db_session):
    db_session.add(Student(student_id=STUDENT_ID, first_name="John", last_name="Smith",
                           email="john@cmu.ac.th", faculty="Faculty of Science", major="เคมี"))
    activity = Activity(activity_type="Workshop", name="Lab Safety Day", start_at=datetime(2025, 8, 15, 9),
                        end_at=datetime(2025, 8, 15, 12), department="Chemistry Dept", responsible_person="Staff",
                        location="Room 101", major="เคมี")
    faculty_wide = Activity(activity_type="Sports", name="Science Sports Day", start_at=datetime(2026, 1, 20, 9),
                            end_at=datetime(2026, 1, 20, 12), responsible_person="Staff", location="Stadium", major=None)
    db_session.add_all([activity, faculty_wide])
    db_session.commit()
    db_session.add_all([
        ActivityMember(activity_id=activity.id, student_id=STUDENT_ID, role="participant"),
        ActivityMember(activity_id=faculty_wide.id, student_id=STUDENT_ID, role="organizer"),
        ActivitySkill(activity_id=activity.id, skill_key="academics", target_role="participant", level=4),
        ExternalActivity(student_id=STUDENT_ID, title="Beach Cleanup", organization="Green NGO",
                         activity_type="จิตอาสา / บริการสังคม", start_date=date(2026, 2, 3), end_date=date(2026, 2, 3),
                         location="Phuket", role="participant", status="approved"),
    ])
    db_session.commit()
    return db_session.get(Student, STUDENT_ID)


def render(db_session, student, style, lang):
    data = transcript_data.collect_transcript(db_session, student)
    return render_transcript_html(data, style, issued_on=ISSUED_ON, lang=lang)


def visible(html):
    # คอมเมนต์ใน template (ภาษาไทยสำหรับนักพัฒนา) ไม่ได้อยู่ใน PDF
    return re.sub(r"<!--.*?-->|/\*.*?\*/", "", html, flags=re.S)


@pytest.mark.parametrize("style", ["A", "B"])
def test_english_document_has_no_thai_text(db_session, student, style):
    html = visible(render(db_session, student, style, "en"))

    assert THAI.findall(html) == [], set(THAI.findall(html))
    for expected in [
        'lang="en"', "Student Activity Transcript", "Chiang Mai University", "John Smith",
        "Chemistry", "Department of Chemistry", "Faculty of Science",
        "Academic Year 2025/2026", "2 October 2026", "15 Aug 2025",
        "Participant", "Organizer / Staff", "External", "Academics", "SAMPLE",
    ]:
        assert expected in html, expected


@pytest.mark.parametrize("style", ["A", "B"])
def test_thai_document_has_thai_labels_and_buddhist_dates(db_session, student, style):
    html = render(db_session, student, style, "th")

    for expected in ['lang="th"', "ใบรับรองการเข้าร่วมกิจกรรมนักศึกษา", "ปีการศึกษา 2568",
                     "2 ตุลาคม 2569", "15 ส.ค. 2568", "สาขาเคมี", "ผู้เข้าร่วม", "กิจกรรมภายนอก",
                     "การเรียนรู้และพัฒนาทางวิชาการ", "ตัวอย่าง"]:
        assert expected in html, expected

    # ป้ายภาษาอังกฤษต้องไม่หลุดมา (ชื่อกิจกรรม/ชื่อคนเป็นข้อมูล ไม่นับ)
    for english_label in ["Student Activity Transcript", "Academic Year", "Skill Scores", "Participant",
                          "Organizer / Staff", "Date of Issue", "Department of", "October", "SAMPLE"]:
        assert english_label not in html, english_label


def test_unknown_major_falls_back_to_original_text(db_session, student):
    student.major = "สาขาใหม่ที่ยังไม่มีชื่ออังกฤษ"
    db_session.commit()

    assert "สาขาใหม่ที่ยังไม่มีชื่ออังกฤษ" in render(db_session, student, "A", "en")


@pytest.mark.parametrize("lang, expected_text", [("en", "Student Activity Transcript"), ("th", "ใบรับรอง")])
def test_export_endpoint_language(client, student, lang, expected_text):
    response = client.get("/api/student/me/transcript/export", params={"style": "B", "lang": lang}, headers=HEADERS)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert f"-B-{lang}.pdf" in response.headers["content-disposition"]
    text = "".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
    assert expected_text in text.replace("\n", " ")
    if lang == "en":
        # ข้อความใน PDF จริงไม่มีอักษรไทยเลย (ข้อมูลในเทสต์เป็นภาษาอังกฤษทั้งหมด)
        assert THAI.findall(text) == []


def test_export_defaults_to_thai_and_rejects_unknown_language(client, student):
    default = client.get("/api/student/me/transcript/export", headers=HEADERS)
    assert default.status_code == 200
    assert "-A-th.pdf" in default.headers["content-disposition"]

    assert client.get("/api/student/me/transcript/export", params={"lang": "jp"}, headers=HEADERS).status_code == 400
