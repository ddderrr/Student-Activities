from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import event

from models import Activity, ActivityMember, ActivitySkill, Student


def seed_activities(db_session, count):
    for index in range(count):
        student_id = f"67000{index:04d}"
        db_session.add(
            Student(
                student_id=student_id,
                first_name="Test",
                last_name=str(index),
                email="",
                faculty="Faculty of Science",
                major="",
            )
        )
        activity = Activity(
            activity_type="Workshop",
            name=f"Activity {index}",
            start_at=datetime(2026, 3, 1 + index, 9),
            end_at=datetime(2026, 3, 1 + index, 12),
            responsible_person="Staff",
            location="Room",
        )
        db_session.add(activity)
        db_session.flush()
        db_session.add_all([
            ActivityMember(activity_id=activity.id, student_id=student_id, role="participant"),
            ActivitySkill(activity_id=activity.id, skill_key="volunteerism", target_role="participant", level=4),
            ActivitySkill(activity_id=activity.id, skill_key="innovation", target_role="staff", level=2),
        ])
    db_session.commit()


@contextmanager
def count_queries(engine):
    statements = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_list_activities_query_count_does_not_grow_with_activities(client, db_session, test_engine):
    seed_activities(db_session, 1)
    with count_queries(test_engine) as one:
        assert client.get("/api/activities").status_code == 200

    db_session.query(ActivitySkill).delete()
    db_session.query(ActivityMember).delete()
    db_session.query(Activity).delete()
    db_session.query(Student).delete()
    db_session.commit()
    seed_activities(db_session, 10)

    with count_queries(test_engine) as ten:
        response = client.get("/api/activities")

    assert response.status_code == 200
    assert len(response.json()["activities"]) == 10
    assert len(ten) == len(one), f"1 activity: {len(one)} queries, 10 activities: {len(ten)} queries"


def test_list_activities_still_returns_counts_and_skills(client, db_session):
    seed_activities(db_session, 2)
    db_session.add(
        Student(student_id="670009999", first_name="Org", last_name="X", email="", faculty="Faculty of Science", major="")
    )
    first = db_session.query(Activity).filter_by(name="Activity 0").one()
    db_session.add(ActivityMember(activity_id=first.id, student_id="670009999", role="organizer"))
    db_session.commit()

    activities = {item["name"]: item for item in client.get("/api/activities").json()["activities"]}

    assert activities["Activity 0"]["participants"] == 1
    assert activities["Activity 0"]["organizers"] == 1
    assert activities["Activity 1"]["organizers"] == 0
    assert activities["Activity 0"]["participant_skills"] == {"volunteerism": 4}
    assert activities["Activity 0"]["staff_skills"] == {"innovation": 2}
    assert activities["Activity 0"]["status"] == "active"
