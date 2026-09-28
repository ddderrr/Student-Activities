"""สร้าง Transcript PDF จากข้อมูลของ transcript_data.collect_transcript()

ใช้ WeasyPrint (HTML/CSS -> PDF) เพราะจัดวางสระ/วรรณยุกต์ไทยถูกต้องผ่าน Pango/HarfBuzz
template อยู่ใน templates/transcript_<style>.html
"""

import secrets
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from weasyprint.urls import URLFetcher

import transcript_config
from transcript_data import academic_year_of, today


BACKEND_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BACKEND_DIR / "templates"

STYLES = {
    "A": {"label": "แบบ A คลาสสิก", "template": "transcript_a.html"},
    "B": {"label": "แบบ B ทันสมัย", "template": "transcript_b.html"},
}

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
THAI_MONTHS_SHORT = [
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]

# autoescape: ชื่อกิจกรรม/องค์กรมาจากผู้ใช้ ห้ามให้กลายเป็น HTML
environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def thai_date(value: date) -> str:
    return f"{value.day} {THAI_MONTHS[value.month - 1]} {value.year + 543}"


def thai_date_short(value: date) -> str:
    return f"{value.day} {THAI_MONTHS_SHORT[value.month - 1]} {value.year + 543}"


def format_score(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


environment.filters["thai_date"] = thai_date
environment.filters["thai_date_short"] = thai_date_short
environment.filters["score"] = format_score


def new_document_number(issued_on: date) -> str:
    # เดโม: ไม่ได้บันทึกลง DB จึงยังใช้ตรวจสอบย้อนหลังไม่ได้
    return (
        f"{transcript_config.DOCUMENT_NUMBER_PREFIX}-"
        f"{academic_year_of(issued_on)}-{secrets.token_hex(3).upper()}"
    )


def year_levels_label(year_levels: list[int] | None) -> str:
    if not year_levels:
        return "ทุกชั้นปี"

    return "ชั้นปีที่ " + ", ".join(str(level) for level in year_levels)


class LocalFileFetcher(URLFetcher):
    """โหลดได้เฉพาะไฟล์ในโฟลเดอร์ backend (ฟอนต์) และไฟล์โลโก้ ไม่ออกไปนอกเครื่อง"""

    def __init__(self):
        super().__init__(allowed_protocols={"file"}, allow_redirects=False)

    def fetch(self, url, headers=None):
        path = Path(unquote(urlparse(url).path)).resolve()
        logo_path = transcript_config.LOGO_PATH

        allowed = path.is_relative_to(BACKEND_DIR) or (
            logo_path is not None and path == Path(logo_path).resolve()
        )

        if not allowed:
            raise ValueError(f"ไม่อนุญาตให้โหลด {url}")

        return super().fetch(url, headers)


def render_transcript_html(data: dict, style: str, issued_on: date | None = None) -> str:
    if style not in STYLES:
        raise ValueError(f"style ต้องเป็น {', '.join(STYLES)}")

    issued_on = issued_on or today()
    logo_path = transcript_config.LOGO_PATH

    return environment.get_template(STYLES[style]["template"]).render(
        config=transcript_config,
        font_dir=transcript_config.FONT_DIR.as_uri(),
        logo_uri=Path(logo_path).resolve().as_uri() if logo_path else None,
        data=data,
        student=data["student"],
        groups=data["groups"],
        summary=data["summary"],
        skill_rows=data["skill_rows"],
        scope_label=data["filters"]["scope_label"],
        year_levels_label=year_levels_label(data["filters"]["year_levels"]),
        document_number=new_document_number(issued_on),
        issued_on=issued_on,
    )


def render_transcript_pdf(data: dict, style: str, issued_on: date | None = None) -> bytes:
    html = render_transcript_html(data, style, issued_on)

    return HTML(
        string=html,
        base_url=str(TEMPLATE_DIR),
        url_fetcher=LocalFileFetcher(),
    ).write_pdf()
