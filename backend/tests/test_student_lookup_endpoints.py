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
# Student mock login (POST /api/student/auth/login)
# นักศึกษาสาขาเดียวกันใช้อีเมลร่วมกัน login แล้วได้คนตาม STUDENT_LOGIN_ACCOUNTS
# ------------------------------------------------------------


def make_branch_mock_students(db_session):
    make_student(db_session, "670510001", "นักศึกษา", "เคมี", "chem@test.com", "เคมี")
    make_student(db_session, "670510201", "กมล", "วิทยา", "chem@test.com", "เคมี")
    make_student(db_session, "670510002", "นักศึกษา", "คอมพิวเตอร์", "cs@test.com", "วิทยาการคอมพิวเตอร์")
    make_student(db_session, "670510101", "สมชาย", "ใจดี", "cs@test.com", "วิทยาการคอมพิวเตอร์")


def test_student_login_chem_email_returns_chemistry_student(client, db_session):
    make_branch_mock_students(db_session)

    response = client.post("/api/auth/login", json={"email": "chem@test.com", "password": "1234"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "student"
    assert body["token"]
    assert body["student"]["student_id"] == "670510001"
    assert body["student"]["major"] == "เคมี"
    assert body["student"]["email"] == "chem@test.com"


def test_student_login_cs_email_is_case_insensitive(client, db_session):
    make_branch_mock_students(db_session)

    response = client.post("/api/auth/login", json={"email": "  CS@Test.com ", "password": "1234"})
    assert response.status_code == 200
    assert response.json()["student"]["student_id"] == "670510002"
    assert response.json()["student"]["major"] == "วิทยาการคอมพิวเตอร์"


def test_student_login_demo_email_returns_transcript_demo_student(client, db_session):
    make_student(db_session, "670510999", "สมหญิง", "ใจดีมีน้ำใจ", "demo@test.com", "เคมี")

    response = client.post("/api/auth/login", json={"email": "demo@test.com", "password": "1234"})
    assert response.status_code == 200
    assert response.json()["student"]["student_id"] == "670510999"


def test_student_login_wrong_password_returns_401(client, db_session):
    make_branch_mock_students(db_session)

    response = client.post("/api/auth/login", json={"email": "chem@test.com", "password": "0000"})
    assert response.status_code == 401
    assert response.json()["detail"] == "อีเมลหรือรหัสผ่านไม่ถูกต้อง"


def test_student_login_unknown_email_returns_401(client, db_session):
    # ตอบเหมือนรหัสผิด ไม่บอกว่าอีเมลนี้ไม่มีในระบบ
    make_branch_mock_students(db_session)

    response = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "1234"})
    assert response.status_code == 401
    assert response.json()["detail"] == "อีเมลหรือรหัสผ่านไม่ถูกต้อง"


def test_student_login_imported_student_by_own_email(client, db_session):
    # นักศึกษาที่นำเข้าจากหน้า Settings ไม่อยู่ใน STUDENT_LOGIN_ACCOUNTS
    make_student(db_session, "670510676", "สมชาย", "สะอาดดี", "Test01@Gmail.com ", "")

    response = client.post("/api/auth/login", json={"email": "test01@gmail.com", "password": "1234"})
    assert response.status_code == 200
    assert response.json()["student"]["student_id"] == "670510676"

    wrong = client.post("/api/auth/login", json={"email": "test01@gmail.com", "password": "0000"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "อีเมลหรือรหัสผ่านไม่ถูกต้อง"

    # session หลัง login (อีเมลตามที่เก็บ + student_id) ใช้ endpoint นักศึกษาได้
    me = client.get("/api/student/me", headers={"Authorization": f"Bearer {response.json()['token']}"})
    assert me.status_code == 200
    assert me.json()["student_id"] == "670510676"


def test_student_login_requires_email_and_password(client):
    response = client.post("/api/auth/login", json={"email": "chem@test.com", "password": ""})
    assert response.status_code == 400


def test_old_student_lookup_endpoints_are_removed(client):
    # หน้า login เดิมใช้ 2 endpoint นี้ (ไม่ตรวจรหัสผ่าน) ตอนนี้ใช้ /login แทน
    assert client.get("/api/student/auth/lookup", params={"identifier": "670510001"}).status_code in (404, 405)
    assert client.get("/api/student/auth/bypass").status_code in (404, 405)
    assert client.post("/api/student/auth/login", json={"email": "x", "password": "y"}).status_code in (404, 405)


def test_shared_email_session_uses_student_id_header_to_pick_the_student(client, db_session):
    make_branch_mock_students(db_session)

    primary = client.get("/api/student/me", headers={"X-Student-Email": "chem@test.com", "X-Student-Id": "670510001"})
    assert primary.status_code == 200
    assert primary.json()["student_id"] == "670510001"

    other = client.get("/api/student/me", headers={"X-Student-Email": "chem@test.com", "X-Student-Id": "670510201"})
    assert other.status_code == 200
    assert other.json()["student_id"] == "670510201"

    # อีเมลต้องตรงกับคนนั้นด้วย ไม่ใช่ใส่ id ของสาขาอื่นได้
    mismatch = client.get("/api/student/me", headers={"X-Student-Email": "chem@test.com", "X-Student-Id": "670510002"})
    assert mismatch.status_code == 401


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
