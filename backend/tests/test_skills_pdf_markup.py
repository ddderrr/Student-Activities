"""PDF ทักษะ (GET /api/student/me/skills/export) ต้องแสดงข้อความจากผู้ใช้ตามตัวอักษร

ReportLab Paragraph อ่านข้อความเป็น markup (<b>, <img src=...>, <a href=...>)
ถ้าไม่ escape ชื่อกิจกรรม / ชื่อนักศึกษาก่อน จะอ่านไฟล์บนเซิร์ฟเวอร์ เรียก URL
ภายใน หรือทำให้สร้าง PDF ไม่ได้ (ดู docs/security-review.md ข้อ ก1)
"""

import http.server
import json
import threading
from io import BytesIO

from PIL import Image
from pypdf import PdfReader

from models import Student
from tests.test_external_activity_evidence_files import PNG_BYTES

STUDENT_ID = "670510999"
HEADERS = {"X-Student-Id": STUDENT_ID}


def submit_and_approve(client, title):
    form = {
        "title": title,
        "organization": "Org",
        "activity_type": "อบรม / Workshop",
        "start_date": "2026-02-01",
        "end_date": "2026-02-01",
        "location": "CM",
        "role": "participant",
        "description": "",
        "skills": json.dumps({"volunteerism": 4}),
    }
    response = client.post(
        "/api/student/me/external-activities",
        data=form,
        files=[("evidence", ("a.png", PNG_BYTES, "image/png"))],
        headers=HEADERS,
    )
    assert response.status_code == 201, response.text

    response = client.patch(
        f"/api/external-activities/{response.json()['id']}/decision",
        json={"status": "approved"},
    )
    assert response.status_code == 200, response.text


def export(client):
    return client.get(
        "/api/student/me/skills/export?period=year-2026&include_chart=false",
        headers=HEADERS,
    )


def pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_img_tag_in_title_does_not_embed_server_file(client, tmp_path):
    secret = tmp_path / "secret.png"
    Image.new("RGB", (50, 50), (255, 0, 0)).save(secret)
    submit_and_approve(client, f'<img src="{secret}" width="100" height="100"/>')

    response = export(client)

    assert response.status_code == 200
    assert b"/Subtype /Image" not in response.content
    assert "<img" in pdf_text(response.content)


def test_img_tag_in_title_does_not_fetch_url(client):
    hits = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            self.wfile.write(PNG_BYTES)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        submit_and_approve(
            client,
            f'<img src="http://127.0.0.1:{port}/internal" width="10" height="10"/>',
        )

        response = export(client)
    finally:
        server.shutdown()

    assert response.status_code == 200
    assert hits == []


def test_unclosed_tag_in_title_still_exports(client):
    submit_and_approve(client, "<b>Workshop & Q<A")

    response = export(client)

    assert response.status_code == 200
    assert "<b>Workshop & Q<A" in pdf_text(response.content)


def test_markup_in_student_name_still_exports(client, db_session):
    db_session.add(
        Student(
            student_id=STUDENT_ID,
            first_name="</b>Somying",
            last_name='<font name="/etc/passwd">',
            email="",
            faculty="Faculty of Science",
            major="เคมี",
        )
    )
    db_session.commit()
    submit_and_approve(client, "Workshop")

    response = export(client)

    assert response.status_code == 200
    assert "</b>Somying" in pdf_text(response.content)
