FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ฟอนต์ Loma (มีทั้งอักษรไทยและอังกฤษ/ตัวเลข) สำหรับ PDF transcript (ดู skill_pdf_font_name ใน main.py)
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-tlwg-loma-ttf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# รันด้วย user ธรรมดา และให้ user นี้เขียนโฟลเดอร์ uploads ได้
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p uploads/external_activities \
    && chown -R appuser:appuser uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
