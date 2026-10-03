"""สร้าง Transcript PDF จากข้อมูลของ transcript_data.collect_transcript()

ใช้ WeasyPrint (HTML/CSS -> PDF) เพราะจัดวางสระ/วรรณยุกต์ไทยถูกต้องผ่าน Pango/HarfBuzz
template อยู่ใน templates/transcript_<style>.html
ข้อความในเอกสารเป็นภาษาเดียวทั้งฉบับตาม lang ("th" | "en") ดู transcript_i18n.py
"""

import secrets
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from weasyprint.urls import URLFetcher

import transcript_config
import transcript_i18n as i18n
from transcript_data import academic_year_of, today


BACKEND_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BACKEND_DIR / "templates"

STYLES = {
    "A": {"label": "แบบ A คลาสสิก", "template": "transcript_a.html"},
    "B": {"label": "แบบ B ทันสมัย", "template": "transcript_b.html"},
}

# autoescape: ชื่อกิจกรรม/องค์กรมาจากผู้ใช้ ห้ามให้กลายเป็น HTML
environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def thai_date(value: date) -> str:
    return i18n.format_date(value, "th")


def thai_date_short(value: date) -> str:
    return i18n.format_date_short(value, "th")


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


def year_levels_label(year_levels: list[int] | None, lang: str = "th") -> str:
    return i18n.year_levels_label(year_levels, lang)


def localize(data: dict, lang: str) -> dict:
    """ป้ายทุกอย่างของเอกสารเป็นภาษาเดียว (ข้อมูลที่ผู้ใช้กรอกคงไว้ตามเดิม)"""
    text = i18n.TEXT[lang]

    def organizer(item: dict) -> str:
        if item["source"] == "external":
            return item["organizer"]
        if item.get("organizer_major"):
            return text["major_organizer"].format(major=i18n.major_name(item["organizer_major"], lang))
        return item.get("organizer_department") or text["faculty"]

    groups = [
        {
            **group,
            "label": i18n.academic_year_label(group["academic_year"], lang),
            "year_level_label": (
                text["year_level_n"].format(level=group["year_level"]) if group["year_level"] else ""
            ),
            "activities": [
                {
                    **item,
                    "organizer": organizer(item),
                    "activity_type": i18n.activity_type_name(item.get("activity_type"), lang),
                    "role_label": text["roles"].get(item["role"], item["role"]),
                    "source_label": text["sources"].get(item["source"], item["source"]),
                }
                for item in group["activities"]
            ],
        }
        for group in data["groups"]
    ]

    return {
        "student": {**data["student"], "major": i18n.major_name(data["student"]["major"], lang)},
        "groups": groups,
        "skill_rows": [
            {**row, "label_local": i18n.SKILL_LABELS[lang].get(row["key"], row["label"])}
            for row in data["skill_rows"]
        ],
        "scope_label": text["scopes"][data["filters"]["scope"]],
        "year_levels_label": i18n.year_levels_label(data["filters"]["year_levels"], lang),
    }


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


def render_transcript_html(
    data: dict, style: str, issued_on: date | None = None, lang: str = "th"
) -> str:
    if style not in STYLES:
        raise ValueError(f"style ต้องเป็น {', '.join(STYLES)}")
    if lang not in i18n.LANGUAGES:
        raise ValueError(f"lang ต้องเป็น {', '.join(i18n.LANGUAGES)}")

    issued_on = issued_on or today()
    logo_path = transcript_config.LOGO_PATH
    local = localize(data, lang)

    return environment.get_template(STYLES[style]["template"]).render(
        config=transcript_config,
        lang=lang,
        tx=i18n.TEXT[lang],
        fmt_date=lambda value: i18n.format_date(value, lang),
        fmt_date_short=lambda value: i18n.format_date_short(value, lang),
        font_dir=transcript_config.FONT_DIR.as_uri(),
        logo_uri=Path(logo_path).resolve().as_uri() if logo_path else None,
        data=data,
        student=local["student"],
        groups=local["groups"],
        summary=data["summary"],
        skill_rows=local["skill_rows"],
        scope_label=local["scope_label"],
        year_levels_label=local["year_levels_label"],
        document_number=new_document_number(issued_on),
        issued_on=issued_on,
    )


def render_transcript_pdf(
    data: dict, style: str, issued_on: date | None = None, lang: str = "th"
) -> bytes:
    html = render_transcript_html(data, style, issued_on, lang)

    return HTML(
        string=html,
        base_url=str(TEMPLATE_DIR),
        url_fetcher=LocalFileFetcher(),
    ).write_pdf()
