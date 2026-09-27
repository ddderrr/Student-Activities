FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ฟอนต์ Loma (มีทั้งอักษรไทยและอังกฤษ/ตัวเลข) สำหรับ PDF transcript (ดู skill_pdf_font_name ใน main.py)
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-tlwg-loma-ttf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- dev: ใช้กับ compose.override.yml (uvicorn --reload, mount โค้ดจากเครื่อง) ----------
FROM base AS dev

COPY . .

RUN mkdir -p uploads/external_activities \
    && chown -R appuser:appuser uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ---------- production (default) ----------
FROM base

COPY . .

# รันด้วย user ธรรมดา และให้ user นี้เขียนโฟลเดอร์ uploads ได้
RUN mkdir -p uploads/external_activities \
    && chown -R appuser:appuser uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
