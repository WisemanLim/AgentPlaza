# AgentPlaza Addon backend — 빌드 컨텍스트는 에이전트 루트(agent.yaml·database/ 포함)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY backend/ ./
COPY agent.yaml ./agent.yaml
COPY database/ ./database/
# 플랫폼이 서명한 Agent Card(설치·내보내기 시 생성, 수정 금지)
COPY a2a/ ./a2a/
RUN useradd -r -u 10001 agent && mkdir -p /data && chown agent /data
USER agent
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
