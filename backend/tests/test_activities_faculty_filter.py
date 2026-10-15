"""หน้า Activities: ตัวเลือก "กิจกรรมส่วนกลางของคณะ" (?faculty_only=true)

แสดงเฉพาะกิจกรรมส่วนกลาง ตามกติกา skill_scoring.faculty_activity_filter
(major เป็น None หรือค่าว่าง) ทั้งแอดมินกลางและแอดมินสาขา
ตัวเลือกเดิม (ทุกสาขา / เลือกสาขา) ต้องทำงานเหมือนเดิม
"""

from datetime import datetime

from models import Activity

CS = "วิทยาการคอมพิวเตอร์"
CHEM = "เคมี"

CENTRAL = {"X-Admin-Email": "central@test.local"}
CHEM_ADMIN = {"X-Admin-Email": "chem@test.local"}


def create_activity(db_session, major, name):
    start_at = datetime(2026, 3, 10, 9, 0, 0)
    db_session.add(
        Activity(
            activity_type="Workshop",
            name=name,
            start_at=start_at,
            end_at=start_at,
            responsible_person="Staff",
            location="Room 1",
            major=major,
        )
    )
    db_session.commit()


def setup_activities(db_session):
    create_activity(db_session, None, "Faculty None")
    create_activity(db_session, "  ", "Faculty Blank")
    create_activity(db_session, CHEM, "Chem Only")
    create_activity(db_session, CS, "CS Only")


def names(response):
    assert response.status_code == 200, response.text
    return sorted(activity["name"] for activity in response.json()["activities"])


def test_central_admin_faculty_only_lists_only_faculty_activities(client, db_session):
    setup_activities(db_session)

    response = client.get("/api/activities?faculty_only=true", headers=CENTRAL)

    assert names(response) == ["Faculty Blank", "Faculty None"]


def test_branch_admin_faculty_only_lists_only_faculty_activities(client, db_session):
    setup_activities(db_session)

    response = client.get("/api/activities?faculty_only=true", headers=CHEM_ADMIN)

    assert names(response) == ["Faculty Blank", "Faculty None"]


def test_existing_filters_are_unchanged(client, db_session):
    setup_activities(db_session)

    assert names(client.get("/api/activities", headers=CENTRAL)) == [
        "CS Only", "Chem Only", "Faculty Blank", "Faculty None",
    ]
    assert names(client.get("/api/activities?major=" + CHEM, headers=CENTRAL)) == [
        "Chem Only", "Faculty Blank", "Faculty None",
    ]
    assert names(client.get("/api/activities", headers=CHEM_ADMIN)) == [
        "Chem Only", "Faculty Blank", "Faculty None",
    ]


# ------------------------------------------------------------
# "เฉพาะกิจกรรมสาขา" (?branch_only=true) ตามกติกา skill_scoring.major_activity_filter
# ------------------------------------------------------------

CS_ADMIN = {"X-Admin-Email": "cs@test.local"}


def test_central_admin_branch_only_excludes_faculty_activities(client, db_session):
    setup_activities(db_session)

    response = client.get(f"/api/activities?major={CHEM}&branch_only=true", headers=CENTRAL)

    assert names(response) == ["Chem Only"]


def test_branch_admin_branch_only_lists_only_own_branch(client, db_session):
    setup_activities(db_session)

    assert names(client.get("/api/activities?branch_only=true", headers=CHEM_ADMIN)) == ["Chem Only"]
    assert names(client.get("/api/activities?branch_only=true", headers=CS_ADMIN)) == ["CS Only"]


def test_branch_admin_cannot_switch_branch_with_branch_only(client, db_session):
    setup_activities(db_session)

    response = client.get(f"/api/activities?major={CS}&branch_only=true", headers=CHEM_ADMIN)

    assert names(response) == ["Chem Only"]


def test_central_admin_branch_only_without_branch_lists_everything(client, db_session):
    # ยังไม่ได้เลือกสาขา = ไม่มีสาขาให้จำกัด แสดงทุกกิจกรรมเหมือน "ทุกสาขา"
    setup_activities(db_session)

    assert names(client.get("/api/activities?branch_only=true", headers=CENTRAL)) == [
        "CS Only", "Chem Only", "Faculty Blank", "Faculty None",
    ]
