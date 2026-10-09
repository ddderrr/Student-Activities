"""แท็บ "กิจกรรมของสาขา" ในหน้า My Activities: GET /api/student/me/major-activities"""

from datetime import datetime

from models import Activity, ActivityMember, ActivitySkill, Student

URL = "/api/student/me/major-activities"
CS = "วิทยาการคอมพิวเตอร์"


def make_student(db_session, student_id, major=CS):
    db_session.add(Student(student_id=student_id, first_name="ทดสอบ", last_name="ระบบ",
                           email=f"{student_id}@cmu.ac.th", faculty="Faculty of Science", major=major))
    db_session.commit()


def make_activity(db_session, name, major, start, status="active"):
    activity = Activity(activity_type="กิจกรรมวิชาการ", name=name, start_at=start,
                        end_at=start.replace(hour=23, minute=59), department="สาขา",
                        responsible_person="อาจารย์", location="CMU", major=major, status=status)
    db_session.add(activity)
    db_session.commit()
    return activity


def test_lists_all_activities_of_my_major_with_joined_flag(client, db_session):
    make_student(db_session, "670510001")
    make_student(db_session, "670510002")
    joined = make_activity(db_session, "Coding Day", CS, datetime(2026, 9, 1, 9))
    upcoming = make_activity(db_session, "Hackathon", f"  {CS} ", datetime(2026, 12, 1, 9))
    make_activity(db_session, "Chem Fair", "เคมี", datetime(2026, 9, 5, 9))
    make_activity(db_session, "Faculty Day", None, datetime(2026, 9, 6, 9))
    db_session.add_all([
        ActivityMember(activity_id=joined.id, student_id="670510001", role="organizer"),
        ActivityMember(activity_id=joined.id, student_id="670510002", role="participant"),
        ActivitySkill(activity_id=joined.id, skill_key="innovation", target_role="staff", level=4),
        ActivitySkill(activity_id=joined.id, skill_key="academics", target_role="participant", level=3),
        ActivitySkill(activity_id=upcoming.id, skill_key="academics", target_role="participant", level=5),
    ])
    db_session.commit()

    body = client.get(URL, headers={"X-Student-Id": "670510001"}).json()

    assert body["major"] == CS
    # เฉพาะกิจกรรมของสาขาตัวเอง ใหม่ไปเก่า (ไม่รวมสาขาอื่นและกิจกรรมส่วนกลาง)
    assert [item["title"] for item in body["activities"]] == ["Hackathon", "Coding Day"]
    hackathon, coding = body["activities"]
    assert (coding["joined"], coding["role"], coding["participants"]) == (True, "organizer", 1)
    assert coding["skills"] == {"innovation": 4}  # ผู้จัด = ทักษะฝั่ง staff
    assert (hackathon["joined"], hackathon["role"]) == (False, None)
    assert hackathon["skills"] == {"academics": 5}


def test_student_without_major_gets_empty_list(client, db_session):
    make_student(db_session, "670510003", major="")
    make_activity(db_session, "Coding Day", CS, datetime(2026, 9, 1, 9))

    assert client.get(URL, headers={"X-Student-Id": "670510003"}).json() == {"major": None, "activities": []}


def test_requires_student(client):
    assert client.get(URL).status_code == 401


CALENDAR_URL = "/api/student/me/calendar-activities"


def test_calendar_shows_faculty_and_own_major_activities(client, db_session):
    make_student(db_session, "670510001")
    joined = make_activity(db_session, "Coding Day", CS, datetime(2026, 9, 1, 9))
    make_activity(db_session, "Faculty Day", None, datetime(2026, 10, 6, 9))
    make_activity(db_session, "Blank Major Day", "  ", datetime(2026, 10, 7, 9))
    make_activity(db_session, "Chem Fair", "เคมี", datetime(2026, 9, 5, 9))
    db_session.add(ActivityMember(activity_id=joined.id, student_id="670510001", role="participant"))
    db_session.commit()

    body = client.get(CALENDAR_URL, headers={"X-Student-Id": "670510001"}).json()

    # เรียงตามวันที่ ไม่รวมกิจกรรมของสาขาอื่น
    assert [(item["title"], item["scope"], item["joined"]) for item in body["activities"]] == [
        ("Coding Day", "major", True),
        ("Faculty Day", "faculty", False),
        ("Blank Major Day", "faculty", False),
    ]


def test_calendar_for_student_without_major_shows_faculty_only(client, db_session):
    make_student(db_session, "670510003", major="")
    make_activity(db_session, "Faculty Day", None, datetime(2026, 10, 6, 9))
    make_activity(db_session, "Coding Day", CS, datetime(2026, 9, 1, 9))

    body = client.get(CALENDAR_URL, headers={"X-Student-Id": "670510003"}).json()
    assert [item["title"] for item in body["activities"]] == ["Faculty Day"]
