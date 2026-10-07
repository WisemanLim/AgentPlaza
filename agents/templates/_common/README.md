# {{AGENT_NAME}} (`{{AGENT_ID}}`)

AgentPlaza Addon 에이전트 v{{VERSION}} — `plaza scaffold` 로 생성.

## 단독 실행 (M1)

```bash
cp .env.example .env
docker compose --profile standalone up -d --build
curl http://127.0.0.1:8001/health
curl -X POST http://127.0.0.1:8001/api/invoke/<capability> -H 'content-type: application/json' -d '{}'
docker compose --profile standalone down -v
```

## 구성

| 경로 | 내용 |
|---|---|
| `agent.yaml` | 정체·capabilities·거버넌스·권한·자원 (AgentPlaza 규격) |
| `backend/` | FastAPI 앱 (`main.py` 의 capability 핸들러) + 벤더링된 `agentplaza_sdk` |
| `database/migrations/` | 멱등 SQL (DDL 만) |
| `frontend/` | 화면이 있는 유형만. 콘솔이 iframe 으로 마운트 |
| `compose.yaml` | standalone 프로파일 (플랫폼 설치 시 federated 로 재생성) |

라이선스: {{LICENSE}} · 게시자: {{PUBLISHER}}
