FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY scripts/ ./scripts/

# 환경 변수는 런타임에 주입
ENV PYTHONUNBUFFERED=1

# Gunicorn으로 서버 실행
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]






