# CLI 에이전트 브리지(D1-04·D7-06) — 표준 라이브러리 파이썬 + (선택) 에이전트형 CLI.
# 실제 CLI 는 빌드 인자로 설치하고, 로그인은 사용자가 직접 한다(자격 증명은 cli-home 볼륨에만):
#   docker compose … -f compose-optional/cli-bridge.yml build --build-arg NPM_CLIS="@anthropic-ai/claude-code @google/gemini-cli"
#   docker compose … run --rm cli-bridge claude login
FROM python:3.12-slim
ARG NPM_CLIS=""
RUN if [ -n "$NPM_CLIS" ]; then apt-get update && apt-get install -y --no-install-recommends nodejs npm \
      && npm install -g $NPM_CLIS && rm -rf /var/lib/apt/lists/* /root/.npm; fi \
    && useradd -m -u 10002 bridge
WORKDIR /srv
COPY bridge/cli_bridge.py ./
COPY bridge/fake ./fake
USER bridge
EXPOSE 8787
HEALTHCHECK --interval=10s --timeout=3s --retries=6 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health')"
CMD ["python", "cli_bridge.py"]
