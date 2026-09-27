"""
Dev server สำหรับ compose.override.yml (ไม่ได้ใช้ใน production)

รัน uvicorn แล้ว restart ให้เมื่อไฟล์ .py ใน backend/ เปลี่ยน ใช้แทน uvicorn --reload
เพราะ watcher ของ uvicorn หยุดทำงานถาวรเมื่อเจอ error ชั่วคราวแค่ครั้งเดียว
(เช่น "Cannot allocate memory" ตอน Docker memory ไม่พอ) แล้วแก้โค้ดต่อจากนั้นจะไม่ reload
โดยไม่มีอะไรเตือน ตัวนี้ถ้าตรวจไฟล์รอบไหนไม่สำเร็จจะข้ามไปลองใหม่รอบถัดไป
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
IGNORED_DIRS = {"uploads", "tests", "__pycache__", ".venv", ".pytest_cache"}
POLL_SECONDS = 1.0

UVICORN_COMMAND = [
    sys.executable,
    "-m",
    "uvicorn",
    "main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
]


def log(message: str) -> None:
    print(f"[dev_server] {message}", flush=True)


def snapshot_py_files() -> dict[str, int] | None:
    """mtime ของไฟล์ .py ทั้งหมด หรือ None ถ้าอ่านไม่สำเร็จ (ให้ลองใหม่รอบหน้า)"""
    mtimes = {}
    errors = []

    for root, dirs, files in os.walk(APP_DIR, onerror=errors.append):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]

        for name in files:
            if not name.endswith(".py"):
                continue

            path = os.path.join(root, name)

            try:
                mtimes[path] = os.stat(path).st_mtime_ns
            except FileNotFoundError:
                # ไฟล์ถูกลบระหว่างสแกน
                continue
            except OSError as exc:
                errors.append(exc)

    if errors:
        log(f"อ่านไฟล์ไม่สำเร็จ จะลองใหม่: {errors[0]}")
        return None

    return mtimes


def changed_files(before: dict[str, int], after: dict[str, int]) -> list[str]:
    paths = set(before) | set(after)

    return sorted(
        os.path.relpath(path, APP_DIR)
        for path in paths
        if before.get(path) != after.get(path)
    )


def start_server() -> subprocess.Popen:
    return subprocess.Popen(UVICORN_COMMAND, cwd=APP_DIR)


def stop_server(server: subprocess.Popen) -> None:
    if server.poll() is not None:
        return

    server.terminate()

    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


def main() -> None:
    server = start_server()
    last_snapshot = snapshot_py_files()
    reported_exit = False

    def shutdown(signum, frame):
        stop_server(server)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        time.sleep(POLL_SECONDS)

        # เช่น import ไม่ผ่านเพราะ syntax error: รอให้แก้ไฟล์แล้วค่อยเริ่มใหม่ (เหมือน uvicorn --reload)
        if server.poll() is not None and not reported_exit:
            log(f"server หยุดทำงาน (exit code {server.returncode}) จะเริ่มใหม่เมื่อแก้ไฟล์")
            reported_exit = True

        current = snapshot_py_files()

        if current is None:
            continue

        if last_snapshot is None:
            last_snapshot = current
            continue

        changes = changed_files(last_snapshot, current)

        if not changes:
            continue

        log(f"พบไฟล์เปลี่ยน: {', '.join(changes)} กำลัง restart")
        last_snapshot = current
        stop_server(server)
        server = start_server()
        reported_exit = False


if __name__ == "__main__":
    main()
