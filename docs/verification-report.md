# รายงานการตรวจสอบระบบ / Verification Report

**โครงการ / Project:** Student Activities (Faculty of Science)
**วันที่ตรวจสอบ / Date:** 2026-10-12
**Commit:** `9c0a3f5` (branch `main`)
**สภาพแวดล้อม / Environment:** Docker Compose — Python 3.12, pytest 9.1.1, FastAPI 0.143.0, SQLAlchemy 2.1.4, Node 22.23.3, Vite 8.2.2

---

## 1. Backend Test Suite (pytest)

**คำสั่ง / Command:** `docker compose exec -T backend pytest -q -p no:cacheprovider`

| รายการ / Item | ผล / Result |
|---|---|
| จำนวนเทสต์ทั้งหมด / Total tests | **515** (in 53 files) |
| ผ่าน / Passed | **515** |
| ไม่ผ่าน / Failed | **0** |
| ข้าม / Skipped | **0** |
| เวลา / Duration | 25.9 s |
| คำเตือน / Warnings | 1: `StarletteDeprecationWarning` (`httpx` + `starlette.testclient` is deprecated; this is a library notice, not a project defect) |

เทสต์ใช้ฐานข้อมูล SQLite in-memory และโฟลเดอร์ upload ชั่วคราว จึงไม่แตะฐานข้อมูล dev จริง
*Tests run against an in-memory SQLite database and a temporary upload folder, isolated from the real PostgreSQL data.*

### Frontend unit tests (`npm test`, node:test)

| รายการ / Item | ผล / Result |
|---|---|
| Total / Passed / Failed / Skipped | **9 / 9 / 0 / 0** |
| ไฟล์ / Files | `activityHours`, `dashboardPeriod`, `skillProfiles`, `skillViews` (`frontend/tests/*.test.mjs`) |

---

## 2. Frontend Build (`npm run build`)

| รายการ / Item | ผล / Result |
|---|---|
| สถานะ / Status | **สำเร็จ / Success** (1,814 modules, built in 0.7 s) |
| ข้อผิดพลาด / Errors | ไม่มี / None |
| คำเตือน / Warnings | 1: *"Some chunks are larger than 500 kB after minification"* |

| ไฟล์ผลลัพธ์ / Output | ขนาด / Size | gzip |
|---|---|---|
| `index.js` | 659.05 kB | 176.18 kB |
| `xlsx.js` | 492.27 kB | 160.41 kB |
| `index.css` | 240.40 kB | 40.70 kB |

**ความหมายของคำเตือน:** ไม่กระทบการทำงาน แต่ไฟล์ JS หลักใหญ่ ทำให้โหลดหน้าแรกช้าลง แก้ได้ด้วยการแยกโหลดหน้า (lazy-load route) ผ่าน `import()`
*Impact: not a functional issue, but the main bundle is large and slows the first page load. It can be fixed by lazy-loading routes with dynamic `import()`.*

---

## 3. Test Coverage by Feature / การครอบคลุมของเทสต์แยกตามฟีเจอร์

ตัวเลขในวงเล็บคือจำนวนเทสต์ในไฟล์นั้น ไฟล์เดียวอาจครอบคลุมได้หลายฟีเจอร์ API endpoint ใน `backend/main.py` มีเทสต์เรียกใช้ 62 จาก 64 ตัว ที่ไม่มีคือ `GET /` (health check) และ `DELETE /api/activities/{id}` (ลบกิจกรรม)
*Numbers in parentheses are test counts per file. One file may cover several features. 62 of the 64 API endpoints in `backend/main.py` are called by at least one test. The two without tests are `GET /` (health check) and `DELETE /api/activities/{id}` (delete activity).*

### 3.1 Authentication & Login — ✅ ผ่าน / Passed
- **Files:** `test_auth_and_admins` (20), `test_auth_secret` (15), `test_login_enumeration` (8), `test_student_mock_login` (11), `test_student_header_bypass` (7), `test_student_lookup_endpoints` (15), `test_create_request_requires_student` (4), `test_evidence_student_auth` (10)
- **TH:** ทดสอบ login แอดมินและนักศึกษา การเซ็นและตรวจ token, การปฏิเสธเมื่อไม่มี `AUTH_SECRET` หรือค่าสั้นเกินไป, การตอบกลับแบบเดียวกันเมื่ออีเมลไม่มีอยู่หรือรหัสผิด (ป้องกันการเดาอีเมล), การรับ header `X-Student-*` เฉพาะในโหมด bypass และการเพิ่ม/ลบบัญชีแอดมิน
- **EN:** Admin and student login, token signing and verification, fail-closed when `AUTH_SECRET` is missing or too short, identical responses for unknown email and wrong password (anti-enumeration), `X-Student-*` headers accepted only in bypass mode, and admin account add/remove.
- **ข้อจำกัด / Limitation:** ยังไม่มี CMU IT Account (OAuth) จริง เทสต์ครอบคลุมเฉพาะระบบ login จำลองที่ใช้อยู่ / CMU OAuth is not implemented yet; only the current mock login is tested.

### 3.2 Activity Management — ✅ ผ่าน / Passed
- **Files:** `test_activity_hours` (18), `test_activities_list_queries` (2), `test_activity_source` (13), `test_remove_participant` (3), `test_participants_import_keeps_existing_data` (4), `test_participants_import_legacy_xls` (5), `test_import_file_limits` (27), `test_major_normalization` (18), `test_cancelled_activity_skills` (7)
- **TH:** ทดสอบการสร้างและแก้ไขกิจกรรม (`POST`/`PATCH /api/activities`), ชั่วโมงกิจกรรม, การนำเข้าผู้เข้าร่วมจาก .xlsx และ .xls รุ่นเก่า, การจำกัดขนาดไฟล์/จำนวนแถว/คอลัมน์, การลบผู้เข้าร่วม และการตัดกิจกรรมที่ถูกยกเลิกออกจากการคำนวณ
- **EN:** Activity create/edit, activity hours, participant import (.xlsx and legacy .xls), file size/row/column limits, participant removal, and cancelled activities excluded from calculations.
- **ยังไม่ได้ทดสอบอัตโนมัติ / Not automated:** การลบกิจกรรม (`DELETE /api/activities/{id}`) ยังไม่มีเทสต์ ส่วนการยกเลิกกิจกรรม (สถานะ `cancelled`) มีเทสต์แล้ว / Deleting an activity has no test. Cancelling an activity (status `cancelled`) is tested.

### 3.3 Student Management — ✅ ผ่าน / Passed
- **Files:** `test_students_import` (7), `test_students_import_legacy_xls` (7), `test_settings_student_import` (13), `test_settings_student_manage` (11), `test_faculty_normalization` (20), `test_admin_student_activities` (3), `test_student_faculty_activities` (2)
- **TH:** ทดสอบการนำเข้ารายชื่อนักศึกษา (รวมไฟล์ template), การแสดงรายชื่อพร้อมตัวกรอง, การลบทีละคน/หลายคน/ทั้งหมด และการปรับชื่อคณะให้เป็นรูปแบบเดียวกัน
- **EN:** Student import (including the template file), list with filters, single/bulk/all delete, and faculty name normalization.

### 3.4 Skill Mapping & Calculation — ✅ ผ่าน / Passed
- **Files (backend):** `test_skill_sources` (8), `test_skill_tracks` (7), `test_skill_comparisons` (8), `test_weighted_skill_profiles` (12), `test_admin_student_skills_cohorts` (7), `test_skills_pdf_markup` (4), `test_cancelled_activity_skills` (7)
- **Files (frontend):** `skillProfiles.test.mjs`, `skillViews.test.mjs`
- **TH:** ทดสอบการคำนวณคะแนนทักษะแบบถ่วงน้ำหนัก, การแยกแหล่งที่มา (คณะ/สาขา/ภายนอก), การเทียบกับค่าเฉลี่ยคณะหรือสาขา, ค่า benchmark, การ export PDF "My Skills" (escape ข้อความผู้ใช้) และการสลับมุมมองทักษะในหน้าเว็บ
- **EN:** Weighted skill scoring, source separation (faculty/major/external), comparison with faculty or major averages, benchmark settings, "My Skills" PDF export (user text escaped), and the skill view toggle in the UI.

### 3.5 External Activity Submission & Approval — ✅ ผ่าน / Passed
- **Files:** `test_external_activity_evidence_files` (20), `test_external_activity_delete` (7), `test_external_activity_resubmit` (4), `test_create_request_requires_student` (4), `test_evidence_student_auth` (10), `test_migrate_evidence_files` (4), `test_my_activities_category` (6), `test_student_notifications` (8)
- **TH:** ทดสอบการส่งคำขอพร้อมหลักฐานสูงสุด 10 ไฟล์, การอนุมัติ/ปฏิเสธพร้อมเหตุผล, การแก้ไขและส่งใหม่, การลบคำขอที่รออนุมัติหรือถูกปฏิเสธ และสิทธิ์การเข้าถึงไฟล์หลักฐาน
- **EN:** Submission with up to 10 evidence files, approve/reject with reason, edit and resubmit, deleting pending or rejected requests, and access control on evidence files.

### 3.6 Transcript PDF Generation — ✅ ผ่าน / Passed
- **Files:** `test_transcript` (36), `test_transcript_language` (8), `test_transcript_matches_my_skills` (11), `test_transcript_settings` (8)
- **TH:** ทดสอบการสร้าง PDF รูปแบบ A/B ภาษาไทยและอังกฤษ, ตัวเลือกการดาวน์โหลด, การตั้งค่า transcript ของแอดมิน, การ preview และตรวจว่าข้อมูลใน PDF ตรงกับหน้า My Skills โดยไม่นับกิจกรรมที่ยกเลิก (อ่านข้อความจาก PDF ด้วย `pypdf`)
- **EN:** PDF styles A/B in Thai and English, download options, admin transcript settings, preview, and a check that PDF data matches My Skills and excludes cancelled activities (PDF text read with `pypdf`).
- **ข้อจำกัด / Limitation:** เทสต์ตรวจ *เนื้อหาข้อความ* ไม่ได้ตรวจ *หน้าตา* (การวางสระ/วรรณยุกต์ไทย, ระยะห่าง) / Tests check text content, not visual layout (Thai vowel/tone mark placement, spacing).

### 3.7 Admin Branch Scoping & Permissions — ✅ ผ่าน / Passed
- **Files:** `test_admin_major_scope` (40), `test_central_admin_branch_filter` (7), `test_participant_import_scope` (5)
- **TH:** ทดสอบว่าแอดมินสาขาเห็นและแก้ไขได้เฉพาะนักศึกษาในสาขาตัวเอง, แอดมินส่วนกลางเลือกดูทุกสาขาหรือสาขาเดียวได้ และการนำเข้าผู้เข้าร่วมเขียนทับข้อมูลนักศึกษาสาขาอื่นไม่ได้
- **EN:** Branch admins see and edit only their own branch's students, the central admin can view all branches or filter to one, and participant import cannot overwrite other branches' students.

### 3.8 Notifications (Admin & Student) — ✅ ผ่าน / Passed
- **Files:** `test_admin_notifications` (12), `test_student_notifications` (8), `test_notifications_and_bypass` (5), `test_bangkok_timestamps` (3)
- **TH:** ทดสอบการสร้างแจ้งเตือนเมื่อมีคำขอใหม่หรือมีผลอนุมัติ, การอ่านทีละรายการ/อ่านทั้งหมด, การลบ และเวลาเป็นโซน Asia/Bangkok
- **EN:** Notifications created on new requests and on decisions, mark one/all as read, delete, and timestamps in Asia/Bangkok time.

### 3.9 Dashboard Stats & Charts — ✅ ผ่าน / Passed
- **Files (backend):** `test_admin_dashboard_cancelled` (4), `test_admin_dashboard_external_activities` (3), `test_admin_dashboard_months_filter` (3), `test_dashboard_skill_distribution` (15)
- **Files (frontend):** `dashboardPeriod.test.mjs`
- **TH:** ทดสอบตัวเลข KPI, กราฟ Activity Growth และ Skill Distribution, กราฟกิจกรรมภายนอก, ตัวกรองช่วงเดือน และการตัดกิจกรรมที่ยกเลิกออก
- **EN:** KPI numbers, Activity Growth and Skill Distribution data, external activity chart data, month-range filter, and cancelled activities excluded.
- **ข้อจำกัด / Limitation:** เทสต์ตรวจ *ข้อมูล* ที่ API ส่งให้กราฟ ไม่ได้ตรวจการแสดงผลกราฟในหน้าเว็บ / Tests verify the data sent to charts, not how the charts render.

### 3.10 Activity Calendar — ⚠️ ผ่าน (ครอบคลุมน้อย) / Passed (limited coverage)
- **Files:** `test_admin_calendar` (3), `test_student_major_activities` (5, includes `/api/student/me/calendar-activities`)
- **TH:** ทดสอบ API ปฏิทินฝั่งแอดมิน (ดูทุกสาขา/สาขาเดียว, ตรวจ input และสิทธิ์) และ API ปฏิทินฝั่งนักศึกษา
- **EN:** Admin calendar API (all branches vs. one branch, input validation, auth) and the student calendar API.
- **ยังไม่ได้ทดสอบอัตโนมัติ / Not automated:** UI ปฏิทิน (`CalendarMonth.vue`, `ActivityCalendar.vue`, `StudentActivityCalendar.vue`) รวมถึงสีของปฏิทินนักศึกษาและตัวกรองช่วงเวลาที่เพิ่งเพิ่มเมื่อ 2026-10-09 ถึง 2026-10-12 / Calendar UI components, including the student calendar colors and period filter added 2026-10-09 to 2026-10-12.

---

## 4. ส่วนที่ยังไม่ได้ทดสอบอัตโนมัติ / Areas Without Automated Tests

ทุกฟีเจอร์หลักมีเทสต์ระดับ API แล้ว ส่วนที่ยังไม่มีเทสต์อัตโนมัติคือ **ชั้นหน้าเว็บ (UI)** และ **สภาพแวดล้อมจริง**
*Every major feature has API-level tests. What has no automated tests is the **UI layer** and the **real runtime environment**.*

| ส่วน / Area | สถานะ / Status | เหตุผล / Reason |
|---|---|---|
| การทำงานของหน้าเว็บตั้งแต่ต้นจนจบ (E2E) / End-to-end UI flows | ยังไม่ได้ทดสอบอัตโนมัติ | ไม่มี Playwright/Cypress / No browser test framework |
| UI ปฏิทินและสี / Calendar UI & colors | ยังไม่ได้ทดสอบอัตโนมัติ | เทสต์มีแค่ระดับ API / API-level tests only |
| การแสดงผลกราฟ Dashboard / Dashboard chart rendering | ยังไม่ได้ทดสอบอัตโนมัติ | เทสต์ตรวจแค่ข้อมูล / Data tested, not rendering |
| หน้าตา PDF ภาษาไทย / Thai PDF visual layout | ยังไม่ได้ทดสอบอัตโนมัติ | ตรวจแค่ข้อความ / Text only |
| การแสดงผลบนมือถือ, สลับภาษา / Mobile layout, language switch | ยังไม่ได้ทดสอบอัตโนมัติ | — |
| พฤติกรรมเฉพาะของ PostgreSQL / PostgreSQL-specific behaviour | ยังไม่ได้ทดสอบอัตโนมัติ | เทสต์รันบน SQLite / Tests run on SQLite |
| เปอร์เซ็นต์ line coverage / Line coverage % | ยังไม่ได้วัด / Not measured | ไม่ได้ติดตั้ง `pytest-cov` / `pytest-cov` not installed |

### การทดสอบด้วยมือ / Manual Testing

> **ทีมต้องกรอก / To be completed by the team:** รายงานฉบับนี้สร้างจากการรันเทสต์อัตโนมัติเท่านั้น ใน repo ไม่มีบันทึกการทดสอบด้วยมือ ให้ทีมกรอกคอลัมน์ "ผล" และ "ผู้ทดสอบ" ตามที่ทดสอบจริง และลบแถวที่ไม่ได้ทดสอบออก
> *This report was produced from automated test runs only, and the repo has no record of manual testing. The team should fill in the "Result" and "Tester" columns from testing actually done, and remove rows that were not tested.*

| # | ขั้นตอน / Steps | ผลที่คาดหวัง / Expected | ผล / Result | ผู้ทดสอบ / Tester |
|---|---|---|---|---|
| M1 | แอดมินสร้างกิจกรรมและนำเข้าผู้เข้าร่วมจาก Excel / Admin creates an activity and imports participants | กิจกรรมแสดงในรายการและปฏิทิน / Shown in list and calendar | | |
| M2 | นักศึกษาส่งกิจกรรมภายนอกพร้อมไฟล์ แล้วแอดมินอนุมัติ / Student submits external activity, admin approves | กระดิ่งแจ้งเตือนแสดง ชั่วโมงอัปเดต / Bell shows notification, hours update | | |
| M3 | เปิดปฏิทินทั้งสองฝั่ง เปลี่ยนเดือนและช่วงเวลา / Open both calendars, change month and period | กิจกรรมตรงวันที่และสีถูกต้อง / Correct dates and colors | | |
| M4 | ดาวน์โหลด transcript PDF (A/B, TH/EN) / Download transcript PDF | ตัวอักษรไทยไม่เพี้ยน จัดหน้าถูกต้อง / Thai text renders correctly | | |
| M5 | เปิด Dashboard แล้วเปลี่ยนช่วงเดือน / Open Dashboard and change month range | กราฟเปลี่ยนตาม / Charts update | | |
| M6 | ใช้งานบนมือถือ (sidebar drawer) / Use on mobile | เมนูเปิดปิดได้ ไม่ล้นจอ / Menu works, no overflow | | |
| M7 | login ด้วยแอดมินสาขา / Log in as a branch admin | เห็นเฉพาะนักศึกษาในสาขา / Sees own branch only | | |

---

## 5. ตารางสรุป / Summary Table

| Feature | Test File | Status | Notes |
|---|---|---|---|
| Authentication & Login | `test_auth_and_admins`, `test_auth_secret`, `test_login_enumeration`, `test_student_mock_login`, `test_student_header_bypass`, `test_student_lookup_endpoints`, `test_evidence_student_auth`, `test_create_request_requires_student` | ✅ ผ่าน (90/90) | ยังไม่มี CMU OAuth จริง / Mock login only |
| Activity Management | `test_activity_hours`, `test_activities_list_queries`, `test_activity_source`, `test_remove_participant`, `test_participants_import_*`, `test_import_file_limits`, `test_major_normalization`, `test_cancelled_activity_skills` | ✅ ผ่าน | ลบกิจกรรมยังไม่มีเทสต์ / Activity delete untested |
| Student Management | `test_students_import`, `test_students_import_legacy_xls`, `test_settings_student_import`, `test_settings_student_manage`, `test_faculty_normalization`, `test_admin_student_activities`, `test_student_faculty_activities` | ✅ ผ่าน | Import, filter, single/bulk delete |
| Skill Mapping & Calculation | `test_skill_sources`, `test_skill_tracks`, `test_skill_comparisons`, `test_weighted_skill_profiles`, `test_admin_student_skills_cohorts`, `test_skills_pdf_markup`; FE `skillProfiles`, `skillViews` | ✅ ผ่าน | มีเทสต์ทั้ง backend และ frontend / Backend + frontend |
| External Activity Flow | `test_external_activity_evidence_files`, `test_external_activity_delete`, `test_external_activity_resubmit`, `test_evidence_student_auth`, `test_migrate_evidence_files`, `test_my_activities_category` | ✅ ผ่าน | สูงสุด 10 ไฟล์, ส่งใหม่ได้ / Up to 10 files, resubmit |
| Transcript PDF | `test_transcript`, `test_transcript_language`, `test_transcript_matches_my_skills`, `test_transcript_settings` | ✅ ผ่าน (63/63) | ตรวจข้อความ ไม่ได้ตรวจหน้าตา / Text, not visuals |
| Admin Branch Scoping | `test_admin_major_scope`, `test_central_admin_branch_filter`, `test_participant_import_scope` | ✅ ผ่าน (52/52) | — |
| Notifications | `test_admin_notifications`, `test_student_notifications`, `test_notifications_and_bypass`, `test_bangkok_timestamps` | ✅ ผ่าน (28/28) | — |
| Dashboard Stats & Charts | `test_admin_dashboard_cancelled`, `test_admin_dashboard_external_activities`, `test_admin_dashboard_months_filter`, `test_dashboard_skill_distribution`; FE `dashboardPeriod` | ✅ ผ่าน | ตรวจข้อมูล ไม่ได้ตรวจการแสดงกราฟ / Data, not rendering |
| Activity Calendar (API) | `test_admin_calendar`, `test_student_major_activities` | ✅ ผ่าน (8/8) | ฟีเจอร์ใหม่ มีเทสต์น้อยที่สุด / Newest, fewest tests |
| Activity Calendar (UI) | — | ⬜ ยังไม่ได้ทดสอบ | ต้องทดสอบด้วยมือ (M3) / Manual test M3 |
| UI / E2E ทุกหน้า / All pages | — | ⬜ ยังไม่ได้ทดสอบ | ไม่มี Playwright/Cypress / No browser tests |
| Frontend Build | `npm run build` | ✅ ผ่าน | 1 warning: chunk > 500 kB |

**ภาพรวม / Overall:** Backend 515/515 ผ่าน, Frontend unit 9/9 ผ่าน, Build สำเร็จ ไม่มีเทสต์ใดล้มเหลว
*Backend 515/515 passed, frontend unit 9/9 passed, build succeeded. No test failures.*

### ข้อเสนอแนะ / Recommendations
1. เพิ่มเทสต์ E2E (Playwright) สำหรับ core loop: สร้างกิจกรรม → ส่งคำขอ → อนุมัติ → transcript / *Add Playwright E2E tests for the core loop.*
2. เพิ่มเทสต์ปฏิทิน (กรณีขอบ เช่น กิจกรรมข้ามเดือน) / *Add calendar edge-case tests (e.g. activities spanning months).*
3. ติดตั้ง `pytest-cov` เพื่อวัด % coverage / *Install `pytest-cov` to measure coverage %.*
4. แยกโหลดหน้าด้วย lazy-load route เพื่อแก้คำเตือนขนาด bundle / *Lazy-load routes to fix the bundle-size warning.*
