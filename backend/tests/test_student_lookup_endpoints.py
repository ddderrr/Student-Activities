from models import Student

CS_ADMIN = {"X-Admin-Email": "cs@test.local"}


def make_student(db_session, student_id, first_name, last_name, email, major) -> Student:
    student = Student(
        student_id=student_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        faculty="คณะวิทยาศาสตร์",
        major=major,
    )
    db_session.add(student)
    db_session.commit()
    return student


# ------------------------------------------------------------
# Admin "Add Participant" auto-fill (GET /api/admin/students/lookup, /search)
# ------------------------------------------------------------


def test_admin_lookup_by_student_id_returns_full_record(client, db_session):
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "670510101@test.local", "วิทยาการคอมพิวเตอร์")

    response = client.get(
        "/api/admin/students/lookup",
        params={"student_id": "670510101"},
        headers=CS_ADMIN,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "670510101"
    assert body["first_name"] == "สมชาย"
    assert body["major"] == "วิทยาการคอมพิวเตอร์"


def test_admin_lookup_unknown_student_id_returns_404(client):
    response = client.get(
        "/api/admin/students/lookup",
        params={"student_id": "000000000"},
        headers=CS_ADMIN,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "ไม่พบรหัสนักศึกษานี้ในระบบ"


def test_admin_lookup_requires_admin_header(client):
    client.headers.pop("X-Admin-Email", None)

    response = client.get(
        "/api/admin/students/lookup",
        params={"student_id": "670510101"},
    )
    assert response.status_code == 401


def test_admin_search_matches_name_or_id_across_majors(client, db_session):
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "670510101@test.local", "วิทยาการคอมพิวเตอร์")
    make_student(db_session, "670510201", "กมล", "วิทยา", "670510201@test.local", "เคมี")

    # แอดมิน CS ต้องค้นหาข้ามสาขาได้ (กิจกรรมหนึ่งรับผู้เข้าร่วมข้ามสาขาได้)
    response = client.get(
        "/api/admin/students/search",
        params={"q": "กมล"},
        headers=CS_ADMIN,
    )
    assert response.status_code == 200
    ids = [item["student_id"] for item in response.json()["students"]]
    assert "670510201" in ids


def test_admin_search_empty_query_returns_empty_list(client):
    response = client.get(
        "/api/admin/students/search",
        params={"q": ""},
        headers=CS_ADMIN,
    )
    assert response.status_code == 200
    assert response.json()["students"] == []


# ------------------------------------------------------------
# Student login-by-ID-or-email lookup (GET /api/student/auth/lookup)
# ------------------------------------------------------------


def test_student_auth_lookup_by_student_id(client, db_session):
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "670510101@test.local", "วิทยาการคอมพิวเตอร์")

    response = client.get(
        "/api/student/auth/lookup",
        params={"identifier": "670510101"},
    )
    assert response.status_code == 200
    assert response.json()["student_id"] == "670510101"


def test_student_auth_lookup_by_email(client, db_session):
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "670510101@test.local", "วิทยาการคอมพิวเตอร์")

    response = client.get(
        "/api/student/auth/lookup",
        params={"identifier": "670510101@test.local"},
    )
    assert response.status_code == 200
    assert response.json()["student_id"] == "670510101"


def test_student_auth_lookup_unknown_returns_404(client):
    response = client.get(
        "/api/student/auth/lookup",
        params={"identifier": "nobody@test.local"},
    )
    assert response.status_code == 404


# ------------------------------------------------------------
# GET /api/student/me: used by the student layout's profile widget to show
# who is actually logged in (used to be a hardcoded mock, see StudentLayout.vue)
# ------------------------------------------------------------


def test_student_me_reflects_the_authenticated_session_not_a_hardcoded_value(
    client, db_session
):
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "670510101@test.local", "วิทยาการคอมพิวเตอร์")
    make_student(db_session, "670510201", "กมล", "วิทยา", "670510201@test.local", "เคมี")

    response_a = client.get("/api/student/me", headers={"X-Student-Email": "670510101@test.local"})
    assert response_a.status_code == 200
    assert response_a.json()["student_id"] == "670510101"
    assert response_a.json()["name"] == "สมชาย ใจดี"

    response_b = client.get("/api/student/me", headers={"X-Student-Email": "670510201@test.local"})
    assert response_b.status_code == 200
    assert response_b.json()["student_id"] == "670510201"
    assert response_b.json()["name"] == "กมล วิทยา"
