FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# - fonts-tlwg-loma-ttf: ฟอนต์ PDF ของหน้า My Skills (ดู skill_pdf_font_name ใน main.py)
# - pango/harfbuzz: WeasyPrint ใช้สร้าง Transcript PDF (ฟอนต์อยู่ใน backend/fonts)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-tlwg-loma-ttf \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- dev: ใช้กับ compose.override.yml (auto reload, mount โค้ดจากเครื่อง) ----------
FROM base AS dev

COPY . .

RUN mkdir -p uploads/external_activities \
    && chown -R appuser:appuser uploads
USER appuser

EXPOSE 8000

# dev_server.py รัน uvicorn และ restart เมื่อไฟล์ .py เปลี่ยน (ทนต่อ error ชั่วคราวมากกว่า --reload)
CMD ["python", "dev_server.py"]


# ---------- production (default) ----------
FROM base

COPY . .

# รันด้วย user ธรรมดา และให้ user นี้เขียนโฟลเดอร์ uploads ได้
RUN mkdir -p uploads/external_activities \
    && chown -R appuser:appuser uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
