"""Transcript: ชั้นปีจากรหัสนักศึกษา, ปีการศึกษา, การกรองประเภทกิจกรรม/ชั้นปี และ PDF"""

from datetime import date, datetime
from io import BytesIO

import pytest
from pypdf import PdfReader

import transcript_config
import transcript_data
from models import (
    Activity,
    ActivityMember,
    ActivitySkill,
    ExternalActivity,
    ExternalActivitySkill,
    Student,
)
from transcript_data import (
    academic_year_of,
    collect_transcript,
    current_year_level,
    entry_year_from_student_id,
)

CHEM = "เคมี"
CS = "วิทยาการคอมพิวเตอร์"
STUDENT_ID = "670510999"
HEADERS = {"X-Student-Id": STUDENT_ID}
TODAY = date(2026, 9, 28)  # ปีการศึกษา 2569 -> รหัส 67 เป็นชั้นปีที่ 3


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(transcript_data, "today", lambda: TODAY)


# ------------------------------------------------------------
# ชั้นปี / ปีการศึกษา
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "student_id, expected",
    [
        ("670510659", 2567),
        ("650510001", 2565),
        ("TEST-CS-01", None),
        ("ZZTEST00001", None),
        ("67051065", None),
        ("6705106590", None),
        ("", None),
    ],
)
def test_entry_year_from_student_id(student_id, expected):
    assert entry_year_from_student_id(student_id) == expected


def test_academic_year_starts_in_configured_month(monkeypatch):
    monkeypatch.setattr(transcript_config, "ACADEMIC_YEAR_START_MONTH", 6)

    assert academic_year_of(date(2026, 5, 31)) == 2568
    assert academic_year_of(date(2026, 6, 1)) == 2569
    assert academic_year_of(datetime(2027, 1, 15, 9, 0)) == 2569

    monkeypatch.setattr(transcript_config, "ACADEMIC_YEAR_START_MONTH", 8)
    assert academic_year_of(date(2026, 7, 31)) == 2568
    assert academic_year_of(date(2026, 8, 1)) == 2569


def test_current_year_level():
    assert current_year_level("670510659", date(2026, 9, 28)) == 3
    assert current_year_level("670510659", date(2026, 5, 31)) == 2
    assert current_year_level("690510001", date(2026, 6, 1)) == 1
    # รหัสไม่ตรงรูปแบบ / ปีที่เข้ายังไม่มาถึง = ไม่รู้ชั้นปี
    assert current_year_level("TEST-CS-01", TODAY) is None
    assert current_year_level("700510001", TODAY) is None


# ------------------------------------------------------------
# ข้อมูลทดสอบ
# ------------------------------------------------------------


def add_student(db_session, student_id=STUDENT_ID, major=CHEM) -> Student:
    student = Student(
        student_id=student_id,
        first_name="สมหญิง",
        last_name="ทดสอบ",
        email=f"{student_id}@test.local",
        faculty="Faculty of Science",
        major=major,
    )
    db_session.add(student)
    db_session.commit()
    return student


def add_activity(
    db_session,
    name,
    start,
    major=None,
    status="active",
    role="participant",
    skills=None,
    student_id=STUDENT_ID,
) -> Activity:
    activity = Activity(
        activity_type="Workshop",
        name=name,
        start_at=start,
        end_at=start.replace(hour=16),
        department="",
        responsible_person="Staff",
        location="SCB1100",
        status=status,
        major=major,
    )
    db_session.add(activity)
    db_session.commit()

    db_session.add(
        ActivityMember(activity_id=activity.id, student_id=student_id, role=role)
    )
    for skill_key, level in (skills or {}).items():
        db_session.add(
            ActivitySkill(
                activity_id=activity.id,
                skill_key=skill_key,
                target_role="participant" if role == "participant" else "staff",
                level=level,
            )
        )
    db_session.commit()
    return activity


def add_external(
    db_session,
    title,
    start,
    status="approved",
    skills=None,
    student_id=STUDENT_ID,
) -> ExternalActivity:
    activity = ExternalActivity(
        student_id=student_id,
        title=title,
        organization="Some Org",
        activity_type="จิตอาสา / บริการสังคม",
        start_date=start,
        end_date=start,
        location="Chiang Mai",
        role="participant",
        description="",
        status=status,
    )
    db_session.add(activity)
    db_session.commit()

    for skill_key, level in (skills or {}).items():
        db_session.add(
            ExternalActivitySkill(
                external_activity_id=activity.id,
                skill_key=skill_key,
                target_role="participant",
                level=level,
            )
        )
    db_session.commit()
    return activity


@pytest.fixture()
def student(db_session):
    student = add_student(db_session)

    # ปี 1 (ปีการศึกษา 2567): กิจกรรมส่วนกลางของคณะ
    add_activity(
        db_session, "ปฐมนิเทศคณะ", datetime(2024, 8, 10, 9),
        skills={"academics": 4},
    )
    # ปี 2 (2568): กิจกรรมของสาขาเคมี
    add_activity(
        db_session, "ค่ายเคมีสัญจร", datetime(2025, 7, 1, 9),
        major=CHEM, skills={"academics": 2, "volunteerism": 5},
    )
    # ปี 3 (2569): กิจกรรมของสาขาอื่น เป็นทีมงาน
    add_activity(
        db_session, "งานวันคอมพิวเตอร์", datetime(2026, 7, 1, 9),
        major=CS, role="organizer", skills={"innovation": 5},
    )
    # ยกเลิกแล้ว: ไม่นับ
    add_activity(
        db_session, "กิจกรรมที่ถูกยกเลิก", datetime(2025, 9, 1, 9),
        status="cancelled", skills={"academics": 1},
    )
    # ภายนอก ปี 2 (ก.พ. 2569 = ปีการศึกษา 2568): อนุมัติแล้ว
    add_external(
        db_session, "อาสาปลูกป่า", date(2026, 2, 1),
        skills={"volunteerism": 3},
    )
    # ภายนอกที่ยังไม่อนุมัติ / ถูกปฏิเสธ: ไม่นับ
    add_external(db_session, "รออนุมัติ", date(2026, 3, 1), status="pending")
    add_external(db_session, "ไม่อนุมัติ", date(2026, 3, 2), status="rejected")

    return student


def titles(result):
    return sorted(
        item["title"]
        for group in result["groups"]
        for item in group["activities"]
    )


# ------------------------------------------------------------
# กรองประเภทกิจกรรม
# ------------------------------------------------------------


def test_scope_all_excludes_cancelled_and_unapproved(db_session, student):
    result = collect_transcript(db_session, student, scope="all")

    assert titles(result) == sorted(
        ["ปฐมนิเทศคณะ", "ค่ายเคมีสัญจร", "งานวันคอมพิวเตอร์", "อาสาปลูกป่า"]
    )
    assert result["summary"]["total"] == 4


@pytest.mark.parametrize(
    "scope, expected",
    [
        ("major", ["ค่ายเคมีสัญจร"]),
        ("faculty", ["ปฐมนิเทศคณะ"]),
        ("external", ["อาสาปลูกป่า"]),
    ],
)
def test_scope_filters(db_session, student, scope, expected):
    assert titles(collect_transcript(db_session, student, scope=scope)) == expected


def test_major_scope_is_empty_for_student_without_major(db_session):
    student = add_student(db_session, student_id="670510998", major="")
    add_activity(
        db_session, "กิจกรรมของสาขาเคมี", datetime(2025, 7, 1, 9),
        major=CHEM, student_id="670510998",
    )

    assert titles(collect_transcript(db_session, student, scope="major")) == []
    assert titles(collect_transcript(db_session, student, scope="all")) == [
        "กิจกรรมของสาขาเคมี"
    ]


def test_invalid_scope_is_rejected(db_session, student):
    with pytest.raises(ValueError):
        collect_transcript(db_session, student, scope="everything")


# ------------------------------------------------------------
# กรองชั้นปี
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "year_levels, expected",
    [
        ([1], ["ปฐมนิเทศคณะ"]),
        ([2], ["ค่ายเคมีสัญจร", "อาสาปลูกป่า"]),
        ([3], ["งานวันคอมพิวเตอร์"]),
        ([1, 3], ["ปฐมนิเทศคณะ", "งานวันคอมพิวเตอร์"]),
    ],
)
def test_year_level_filter(db_session, student, year_levels, expected):
    result = collect_transcript(db_session, student, scope="all", year_levels=year_levels)
    assert titles(result) == sorted(expected)


def test_scope_and_year_filters_combine(db_session, student):
    result = collect_transcript(db_session, student, scope="external", year_levels=[1])
    assert titles(result) == []


def test_year_level_above_current_is_rejected(db_session, student):
    with pytest.raises(ValueError):
        collect_transcript(db_session, student, scope="all", year_levels=[4])

    with pytest.raises(ValueError):
        collect_transcript(db_session, student, scope="all", year_levels=[0])


def test_unknown_year_level_only_allows_all_years(db_session):
    student = add_student(db_session, student_id="TEST-CHEM-99")
    add_activity(
        db_session, "กิจกรรม", datetime(2025, 7, 1, 9), student_id="TEST-CHEM-99",
    )

    result = collect_transcript(db_session, student, scope="all")
    assert titles(result) == ["กิจกรรม"]
    assert result["student"]["year_level"] is None
    # ยังแยกตามปีการศึกษาได้ แต่ไม่รู้ว่าเป็นชั้นปีไหน
    assert result["groups"][0]["academic_year"] == 2568
    assert result["groups"][0]["year_level"] is None

    with pytest.raises(ValueError):
        collect_transcript(db_session, student, scope="all", year_levels=[1])


def test_groups_are_ordered_by_academic_year(db_session, student):
    result = collect_transcript(db_session, student, scope="all")

    assert [
        (group["academic_year"], group["year_level"])
        for group in result["groups"]
    ] == [(2567, 1), (2568, 2), (2569, 3)]
    assert [len(group["activities"]) for group in result["groups"]] == [1, 2, 1]


# ------------------------------------------------------------
# คะแนนทักษะ: คิดจากกิจกรรมที่เลือกเท่านั้น
# ------------------------------------------------------------


def test_skill_scores_use_selected_activities_only(db_session, student):
    all_scores = collect_transcript(db_session, student, scope="all")["skills"]
    assert all_scores["academics"] == 3.0  # (4 + 2) / 2, ไม่นับกิจกรรมที่ยกเลิก
    assert all_scores["volunteerism"] == 4.0  # (5 + 3) / 2
    # งานวันคอมพิวเตอร์เป็น organizer: ไม่นับในทักษะผู้เข้าร่วม
    assert all_scores["arts_culture_traditions"] is None

    external = collect_transcript(db_session, student, scope="external")["skills"]
    assert external["volunteerism"] == 3.0
    assert external["academics"] is None

    year_one = collect_transcript(db_session, student, scope="all", year_levels=[1])["skills"]
    assert year_one["academics"] == 4.0
    assert year_one["volunteerism"] is None


def test_summary_counts(db_session, student):
    summary = collect_transcript(db_session, student, scope="all")["summary"]

    assert summary["total"] == 4
    assert summary["by_source"] == {"faculty": 1, "major": 1, "other_major": 1, "external": 1}
    assert summary["participant"] == 3
    assert summary["organizer"] == 1


# ------------------------------------------------------------
# API
# ------------------------------------------------------------


def test_options_endpoint(client, student):
    response = client.get("/api/student/me/transcript/options", headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["current_year_level"] == 3
    assert body["allowed_year_levels"] == [1, 2, 3]
    assert {item["key"]: item["count"] for item in body["scopes"]} == {
        "all": 4,
        "major": 1,
        "faculty": 1,
        "external": 1,
    }
    assert [item["key"] for item in body["styles"]] == ["A", "B"]


def test_options_for_unknown_year_level(client, db_session):
    add_student(db_session, student_id="TEST-CHEM-99")

    body = client.get(
        "/api/student/me/transcript/options",
        headers={"X-Student-Id": "TEST-CHEM-99"},
    ).json()

    assert body["current_year_level"] is None
    assert body["allowed_year_levels"] == []


@pytest.mark.parametrize(
    "query",
    [
        "style=C",
        "style=A&scope=everything",
        "style=A&years=4",
        "style=A&years=0",
        "style=A&years=abc",
    ],
)
def test_export_rejects_invalid_options(client, student, query):
    response = client.get(f"/api/student/me/transcript/export?{query}", headers=HEADERS)
    assert response.status_code == 400


def test_export_rejects_years_when_year_level_unknown(client, db_session):
    add_student(db_session, student_id="TEST-CHEM-99")
    headers = {"X-Student-Id": "TEST-CHEM-99"}

    assert client.get(
        "/api/student/me/transcript/export?style=A&years=1", headers=headers
    ).status_code == 400
    assert client.get(
        "/api/student/me/transcript/export?style=A", headers=headers
    ).status_code == 200


def pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@pytest.mark.parametrize("style", ["A", "B"])
def test_export_pdf(client, student, style):
    response = client.get(
        f"/api/student/me/transcript/export?style={style}&scope=all&years=1,2",
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")

    text = pdf_text(response.content)
    assert STUDENT_ID in text
    assert "ค่ายเคมีสัญจร" in text
    assert "อาสาปลูกป่า" in text
    # ปี 3 ไม่ได้เลือก
    assert "งานวันคอมพิวเตอร์" not in text
    assert "2567" in text and "2568" in text
    assert transcript_config.SIGNER_NAME in text
