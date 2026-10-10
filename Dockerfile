FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

# tzdata, damit "heute" und die Log-Zeiten in deutscher Zeit stimmen
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY login.py fetch_timetable.py check_changes.py alert.py run.sh ./

# Ohne Root laufen; data/ enthält den gespeicherten Stand (als Volume gemountet)
RUN useradd --uid 1000 --create-home app \
    && mkdir -p /app/data \
    && chown app:app /app/data \
    && chmod +x run.sh
USER app

VOLUME ["/app/data"]

CMD ["./run.sh"]
