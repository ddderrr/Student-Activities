"""หน้า /login เดียว (POST /api/auth/login) + จัดการแอดมินสาขาในหน้า Settings"""

import pytest

import main as main_module
from auth_tokens import hash_password, issue_token
from models import Admin, Student
from seed_admins import seed_admins


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def no_bypass(client):
    # จำลองการใช้งานจริง: ไม่ส่ง X-Admin-Email ใช้ token จากการ login อย่างเดียว
    client.headers.pop("X-Admin-Email", None)
    return client


@pytest.fixture()
def seeded(db_session):
    seed_admins(db_session)
    db_session.add(
        Student(student_id="670510676", first_name="สมชาย", last_name="สะอาดดี",
                email="test01@gmail.com", faculty="Faculty of Science", major="วิทยาการคอมพิวเตอร์")
    )
    db_session.commit()


def login(client, email, password="1234"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize(
    "email, major, is_central",
    [
        ("central@gmail.com", None, True),
        ("cs@gmail.com", "วิทยาการคอมพิวเตอร์", False),
        ("chem@gmail.com", "เคมี", False),
    ],
)
def test_admin_login_returns_admin_role_and_working_token(no_bypass, seeded, email, major, is_central):
    response = login(no_bypass, f"  {email.upper()} ")

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert (body["admin"]["email"], body["admin"]["major"], body["admin"]["is_central"]) == (email, major, is_central)

    me = no_bypass.get("/api/admin/me", headers=bearer(body["token"]))
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_student_login_returns_student_role_and_working_token(no_bypass, seeded):
    body = login(no_bypass, "test01@gmail.com").json()

    assert body["role"] == "student"
    assert body["student"]["student_id"] == "670510676"
    me = no_bypass.get("/api/student/me", headers=bearer(body["token"]))
    assert me.status_code == 200
    assert me.json()["student_id"] == "670510676"


def test_wrong_password_and_unknown_email(no_bypass, seeded):
    admin = login(no_bypass, "cs@gmail.com", "0000")
    student = login(no_bypass, "test01@gmail.com", "0000")
    unknown = login(no_bypass, "nobody@gmail.com")

    # ตอบเหมือนกันทุกกรณี ไม่บอกว่าอีเมลไหนมีในระบบ
    for response in (admin, student, unknown):
        assert (response.status_code, response.json()["detail"]) == (401, "อีเมลหรือรหัสผ่านไม่ถูกต้อง")


def test_tokens_are_role_specific_and_tamper_proof(no_bypass, seeded):
    student_token = login(no_bypass, "test01@gmail.com").json()["token"]
    admin_token = login(no_bypass, "central@gmail.com").json()["token"]

    assert no_bypass.get("/api/admin/me", headers=bearer(student_token)).status_code == 401
    assert no_bypass.get("/api/student/me", headers=bearer(admin_token)).status_code == 401
    assert no_bypass.get("/api/admin/me", headers=bearer(admin_token[:-3] + "abc")).status_code == 401
    assert no_bypass.get("/api/admin/me").status_code == 401


def test_branch_admin_token_is_scoped_to_its_major(no_bypass, seeded):
    token = login(no_bypass, "cs@gmail.com").json()["token"]

    students = no_bypass.get("/api/admin/student-skills", headers=bearer(token))
    assert students.status_code == 200
    assert no_bypass.get("/api/admin/admins", headers=bearer(token)).status_code == 403


def test_central_admin_creates_branch_admin_who_can_login(no_bypass, seeded):
    central = bearer(login(no_bypass, "central@gmail.com").json()["token"])

    created = no_bypass.post(
        "/api/admin/admins",
        json={"first_name": "แอดมิน", "last_name": "สถิติ", "email": "Stat@Gmail.com", "password": "abcd", "major": "สถิติ"},
        headers=central,
    )
    assert created.status_code == 201
    assert created.json()["email"] == "stat@gmail.com"

    listed = no_bypass.get("/api/admin/admins", headers=central).json()["admins"]
    assert {admin["email"] for admin in listed} == {"cs@gmail.com", "chem@gmail.com", "stat@gmail.com"}
    assert all(not admin["is_central"] for admin in listed)

    new_login = login(no_bypass, "stat@gmail.com", "abcd").json()
    assert new_login["admin"]["major"] == "สถิติ"


def test_create_admin_with_only_email_and_branch(no_bypass, seeded):
    # หน้า Settings ส่งแค่อีเมล + สาขา: ชื่ออัตโนมัติ รหัสผ่านเริ่มต้น 1234
    central = bearer(login(no_bypass, "central@gmail.com").json()["token"])

    created = no_bypass.post("/api/admin/admins", json={"email": "bio@gmail.com", "major": "ชีววิทยา"}, headers=central)

    assert created.status_code == 201
    assert created.json()["name"] == "แอดมินสาขา ชีววิทยา"
    new_login = login(no_bypass, "bio@gmail.com", "1234")
    assert new_login.status_code == 200
    assert new_login.json()["admin"]["major"] == "ชีววิทยา"


def test_deleted_admin_cannot_login_or_use_old_token(no_bypass, seeded, db_session):
    central = bearer(login(no_bypass, "central@gmail.com").json()["token"])
    chem_token = login(no_bypass, "chem@gmail.com").json()["token"]
    chem_id = db_session.query(Admin).filter_by(email="chem@gmail.com").one().id

    assert no_bypass.delete(f"/api/admin/admins/{chem_id}", headers=central).status_code == 200

    assert login(no_bypass, "chem@gmail.com").status_code == 401
    assert no_bypass.get("/api/admin/me", headers=bearer(chem_token)).status_code == 401


def test_cannot_delete_central_admin_or_self(no_bypass, seeded, db_session):
    other_central = Admin(email="central2@gmail.com", first_name="กลาง", last_name="สอง", password_hash=hash_password("1234"), major=None)
    db_session.add(other_central)
    db_session.commit()
    me = db_session.query(Admin).filter_by(email="central@gmail.com").one()
    central = bearer(issue_token("admin", me.id))

    assert no_bypass.delete(f"/api/admin/admins/{me.id}", headers=central).status_code == 400
    assert no_bypass.delete(f"/api/admin/admins/{other_central.id}", headers=central).status_code == 400
    assert no_bypass.delete("/api/admin/admins/99999", headers=central).status_code == 404


@pytest.mark.parametrize(
    "payload, status",
    [
        ({"email": "a@gmail.com"}, 422),
        ({"first_name": "ก", "email": "not-an-email", "password": "1234", "major": "เคมี"}, 400),
        ({"first_name": "ก", "email": "a@gmail.com", "password": "123", "major": "เคมี"}, 400),
        ({"first_name": "ก", "email": "a@gmail.com", "password": "1234", "major": "ไม่มีสาขานี้"}, 400),
        ({"first_name": "ก", "email": "cs@gmail.com", "password": "1234", "major": "เคมี"}, 409),
        ({"first_name": "ก", "email": "test01@gmail.com", "password": "1234", "major": "เคมี"}, 409),
    ],
)
def test_create_admin_validation(no_bypass, seeded, payload, status):
    central = bearer(login(no_bypass, "central@gmail.com").json()["token"])

    assert no_bypass.post("/api/admin/admins", json=payload, headers=central).status_code == status


def test_seed_admins_is_idempotent(db_session):
    assert len(seed_admins(db_session)) == 3
    assert seed_admins(db_session) == []
    assert db_session.query(Admin).count() == 3


def test_student_token_opens_own_evidence_list(no_bypass, seeded):
    token = login(no_bypass, "test01@gmail.com").json()["token"]

    response = no_bypass.get("/api/student/me/external-activities", headers=bearer(token))
    assert response.status_code == 200


def test_evidence_opens_with_login_tokens(no_bypass, seeded, db_session):
    # หลัง merge: endpoint ไฟล์หลักฐานใช้ get_optional_student (ของเพื่อน) ซึ่งรับ token ด้วย
    from tests.test_settings_student_manage import add_related_data, make_student

    make_student(db_session, "670510999", major="เคมี", email="other@gmail.com")
    _, external_id, _ = add_related_data(db_session, "670510676")
    evidence_id = db_session.query(main_module.ExternalActivityEvidence).filter_by(external_activity_id=external_id).one().id
    url = f"/api/external-activities/{external_id}/evidence/{evidence_id}"

    owner = bearer(login(no_bypass, "test01@gmail.com").json()["token"])
    other = bearer(login(no_bypass, "other@gmail.com").json()["token"])
    central = bearer(login(no_bypass, "central@gmail.com").json()["token"])
    chem = bearer(login(no_bypass, "chem@gmail.com").json()["token"])

    assert no_bypass.get(url, headers=owner).status_code == 200
    assert no_bypass.get(url, headers=other).status_code == 403
    assert no_bypass.get(url, headers=central).status_code == 200
    # test01 อยู่สาขาวิทยาการคอมพิวเตอร์: แอดมินเคมีเปิดไม่ได้
    assert no_bypass.get(url, headers=chem).status_code == 403
    assert no_bypass.get(url).status_code == 401
