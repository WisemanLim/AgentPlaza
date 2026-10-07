# wise-agentplaza — python-fastapi (multi-stage: dev = local 모드, runtime = prod 모드)
# 공급망 게이트 도구(D5-03·D4-06): 공식 이미지에서 정적 바이너리만 복사(버전 고정)
FROM ghcr.io/sigstore/cosign/cosign:v3.1.3 AS cosign
FROM anchore/syft:v1.54.1 AS syft
FROM aquasec/trivy:0.75.0 AS trivy

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy PATH=/opt/venv/bin:$PATH PYTHONPATH=/app:/app/sdk/python
# git: 마켓 경로 B(Git URL 설치, D6-03)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv
COPY --from=cosign /ko-app/cosign /usr/local/bin/cosign
COPY --from=syft /syft /usr/local/bin/syft
COPY --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy
ENV SYFT_CHECK_FOR_APP_UPDATE=false
WORKDIR /app

# dev: 테스트/개발 의존성 포함, 소스는 local 모드에서 바인드 마운트
FROM base AS dev
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project
COPY . .
EXPOSE 8000
# 재기동 감시는 소스 디렉터리만 — /app/data(설치·스테이징 파일)를 보면 설치 중 재기동이 걸려 api 가 멈춘다
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app", "--reload-dir", "sdk", "--reload-dir", "plaza"]

# runtime: 운영 의존성만
FROM base AS runtime
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project --no-dev
COPY . .
RUN useradd -r -u 10001 app && mkdir -p /app/data /var/cache/trivy && chown -R app /app/data /var/cache/trivy
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
