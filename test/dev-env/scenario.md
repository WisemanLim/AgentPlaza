# dev-env 시나리오 / scenario — wise-agentplaza (python-fastapi)

| id | 목적 / purpose | 명령 / command | 기대 / expected | 우선 |
|----|----------------|----------------|-----------------|------|
| ENV-01 | 도구·설정 점검 | `make preflight` | `Preflight OK` | P0 |
| ENV-02 | local 기동 | `make local-all` | 컨테이너 running/healthy | P0 |
| ENV-03 | 헬스 체크 | `curl -fsS http://127.0.0.1:8010/health` | HTTP 200, `env=local` | P0 |
| ENV-04 | local DB | `make db-ping` | `sqlite OK` | P0 |
| ENV-05 | 테스트 진입점 | `make test` | exit 0 | P0 |
| ENV-06 | prod 기동 (postgres) | `make prod-all` | app + db healthy | P1 |
| ENV-07 | prod DB | `make db-ping ENV=prod` | `postgres OK` | P1 |
| ENV-08 | 정리 | `make local-stop && make prod-stop` | 컨테이너 없음 | P1 |
| ENV-09 | Valkey 캐시 (extras, 이미지 교체 검증) | `docker compose … exec redis valkey-cli ping` (local) | `PONG` | P1 |
| ENV-10 | pgvector 확장 (prod DB 이미지 교체 검증) | `docker compose … exec db psql -c "CREATE EXTENSION IF NOT EXISTS vector"` (prod) | `CREATE EXTENSION`, `extversion` 조회 | P1 |
| ENV-11 | prod 헬스 | `curl -fsS http://127.0.0.1:8011/health` | HTTP 200, `env=prod`, DB 연결 | P1 |

> 포트: local API 8010·Valkey 6390 / prod API 8011·Valkey 6391. 같은 호스트의 다른 프로젝트(8000·6379 점유)와 local↔prod 동시 기동 충돌을 피하려고 스캐폴드 기본값(8000·6379)에서 변경했다.
> 실행 순서: ENV-01~05·09 → ENV-06·07·10·11 → ENV-08.
