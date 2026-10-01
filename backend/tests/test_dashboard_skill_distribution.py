"""กราฟ Skill Distribution ของหน้า Dashboard (คำนวณที่ backend)

- นับกิจกรรมของคณะตามขอบเขตแอดมิน (เหมือน KPI: ไม่รวมกิจกรรมที่ยังไม่มีเจ้าของสำหรับแอดมินสาขา)
- ไม่นับกิจกรรม cancelled
- เฉลี่ยตามกิจกรรม (แต่ละกิจกรรมน้ำหนักเท่ากัน) ปัดเศษแบบครึ่งขึ้นเหมือน frontend เดิม
"""

from datetime import datetime

import pytest

from models import Activity, ActivitySkill
from tests.conftest import CENTRAL_ADMIN_EMAIL, CHEM_ADMIN_EMAIL

CHEM = "เคมี"
CENTRAL = {"X-Admin-Email": CENTRAL_ADMIN_EMAIL}
CHEM_ADMIN = {"X-Admin-Email": CHEM_ADMIN_EMAIL}
URL = "/api/admin/dashboard/skill-distribution"


def add_activity(db_session, name, start, status="active", major=None, participant=None, staff=None):
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

    for target, skills in (("participant", participant or {}), ("staff", staff or {})):
        for skill_key, level in skills.items():
            db_session.add(
                ActivitySkill(activity_id=activity.id, skill_key=skill_key, target_role=target, level=level)
            )
    db_session.commit()
    return activity


@pytest.fixture()
def activities(db_session):
    add_activity(db_session, "Faculty March", datetime(2026, 3, 10, 9),
                 participant={"academics": 4, "volunteerism": 2}, staff={"innovation": 3})
    add_activity(db_session, "Completed March", datetime(2026, 3, 20, 9), status="completed",
                 participant={"academics": 5})
    add_activity(db_session, "Chem March", datetime(2026, 3, 15, 9), major=CHEM,
                 participant={"academics": 3}, staff={"innovation": 5})
    # ถูกยกเลิก: ห้ามนับ (level ต่ำ ถ้าหลุดเข้ามาค่าเฉลี่ยจะเพี้ยนชัด)
    add_activity(db_session, "Cancelled March", datetime(2026, 3, 25, 9), status="cancelled",
                 participant={"academics": 1, "health_promotion": 1}, staff={"innovation": 1})
    add_activity(db_session, "Cancelled Chem March", datetime(2026, 3, 26, 9), status="cancelled", major=CHEM,
                 participant={"academics": 1})
    # นอกช่วง
    add_activity(db_session, "Faculty August", datetime(2026, 8, 10, 9), participant={"academics": 2})
    add_activity(db_session, "Last year", datetime(2025, 3, 10, 9), participant={"academics": 1})


def skills(response):
    assert response.status_code == 200, response.text
    return {item["key"]: item for item in response.json()["skills"]}


def test_cancelled_activities_are_not_counted(client, activities):
    body = skills(client.get(f"{URL}?year=2026&months=3", headers=CENTRAL))

    # Faculty March 4, Completed March 5, Chem March 3 (ไม่รวม Cancelled 1)
    assert body["academics"]["evidenceCount"] == 3
    assert body["academics"]["averageLevel"] == 4.0
    assert body["academics"]["percentage"] == 80
    # ทักษะที่มีแต่ในกิจกรรมที่ยกเลิก = ไม่มีข้อมูล
    assert body["health_promotion"] == {
        "key": "health_promotion",
        "averageLevel": None,
        "percentage": 0,
        "evidenceCount": 0,
    }


def test_cancelled_not_counted_for_branch_admin(client, activities):
    body = skills(client.get(f"{URL}?year=2026&months=3", headers=CHEM_ADMIN))

    # แอดมินสาขาเห็นเฉพาะกิจกรรมของสาขาตัวเอง (ไม่รวมส่วนกลาง) และไม่นับที่ยกเลิก
    assert body["academics"]["evidenceCount"] == 1
    assert body["academics"]["averageLevel"] == 3.0


def test_central_admin_branch_filter_matches_branch_admin(client, activities):
    central = client.get(f"{URL}?year=2026&months=3&major={CHEM}", headers=CENTRAL).json()
    branch = client.get(f"{URL}?year=2026&months=3", headers=CHEM_ADMIN).json()

    assert central == branch


def test_branch_admin_cannot_use_major_param_to_see_other_scope(client, activities):
    plain = client.get(f"{URL}?year=2026&months=3", headers=CHEM_ADMIN).json()
    spoofed = client.get(f"{URL}?year=2026&months=3&major=วิทยาการคอมพิวเตอร์", headers=CHEM_ADMIN).json()

    assert spoofed == plain


def test_semester_is_used_when_months_not_given(client, activities):
    semester_1 = skills(client.get(f"{URL}?year=2026&semester=SEMESTER_1", headers=CENTRAL))
    semester_2 = skills(client.get(f"{URL}?year=2026&semester=SEMESTER_2", headers=CENTRAL))
    whole_year = skills(client.get(f"{URL}?year=2026", headers=CENTRAL))

    assert semester_1["academics"]["evidenceCount"] == 3
    assert semester_2["academics"]["evidenceCount"] == 1
    assert semester_2["academics"]["averageLevel"] == 2.0
    assert whole_year["academics"]["evidenceCount"] == 4


def test_year_filter(client, activities):
    body = skills(client.get(f"{URL}?year=2025&months=3", headers=CENTRAL))

    assert body["academics"]["evidenceCount"] == 1
    assert body["academics"]["averageLevel"] == 1.0


def test_staff_track_uses_staff_skills(client, activities):
    body = skills(client.get(f"{URL}?year=2026&months=3&track=staff", headers=CENTRAL))

    assert list(body) == [
        "creative_leadership",
        "innovation",
        "entrepreneurship",
        "promote_equality",
        "academic",
        "nature_environmental",
    ]
    # Faculty March 3, Chem March 5 (ไม่รวม Cancelled 1)
    assert body["innovation"]["evidenceCount"] == 2
    assert body["innovation"]["averageLevel"] == 4.0


def test_participant_skill_order(client, activities):
    body = skills(client.get(f"{URL}?year=2026&months=3", headers=CENTRAL))

    assert list(body) == [
        "arts_culture_traditions",
        "volunteerism",
        "academics",
        "internationalization",
        "health_promotion",
        "nature_environmental_conservation",
    ]


def test_average_percentage_uses_skills_with_evidence(client, activities):
    body = client.get(f"{URL}?year=2026&months=3", headers=CENTRAL).json()

    # academics 80%, volunteerism 40% -> (80 + 40) / 2
    assert body["averagePercentage"] == 60


def test_no_activities_gives_zero_average(client, activities):
    body = client.get(f"{URL}?year=2026&months=12", headers=CENTRAL).json()

    assert body["averagePercentage"] == 0
    assert all(item["evidenceCount"] == 0 for item in body["skills"])


def test_rounds_half_up_like_the_old_frontend(client, db_session):
    # 8 กิจกรรม ผลรวม 25 -> 3.125 -> 3.13 และ 62.5% -> 63%
    for index, level in enumerate([3, 3, 3, 3, 3, 3, 3, 4]):
        add_activity(db_session, f"A{index}", datetime(2026, 4, 1 + index, 9), participant={"academics": level})

    body = client.get(f"{URL}?year=2026&months=4", headers=CENTRAL).json()
    academics = next(item for item in body["skills"] if item["key"] == "academics")

    assert academics["averageLevel"] == 3.13
    assert academics["percentage"] == 63
    assert body["averagePercentage"] == 63


@pytest.mark.parametrize("query", ["months=13", "months=abc", "track=boss"])
def test_invalid_params(client, activities, query):
    assert client.get(f"{URL}?year=2026&{query}", headers=CENTRAL).status_code == 400


def test_requires_admin(client, activities):
    client.headers.pop("X-Admin-Email", None)
    assert client.get(f"{URL}?year=2026").status_code == 401
