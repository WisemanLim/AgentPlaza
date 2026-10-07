# AgentPlaza runtime — docker CLI + compose 플러그인 + 파이썬 표준 라이브러리만. docker.sock 은 이 컨테이너에만 마운트한다.
FROM docker:cli
RUN apk add --no-cache python3
WORKDIR /srv
COPY app/runtime/lint.py runtime/service.py ./
EXPOSE 9000
HEALTHCHECK --interval=10s --timeout=3s --retries=6 CMD wget -qO- http://127.0.0.1:9000/health || exit 1
CMD ["python3", "service.py"]
