# AgentPlaza (wise-agentplaza)

로컬 LLM과 퍼블릭 AI를 하나의 게이트웨이로 쓰는 멀티 에이전트 플랫폼이다. Orchestrator·AI Assistant를 기본 제공하고,
Zip(agent.zip) Addon 에이전트를 마켓플레이스에서 골라 docker compose로 **독립(M1)·연계(M2)·즉시 사용(M3)** 한다.

> 요구사항 [PRD.md](PRD.md) · 구현 계획표 [.docs/IMPLEMENT_PLAN.md](.docs/IMPLEMENT_PLAN.md) · 준법 [COMPLIANCE.md](COMPLIANCE.md) · English [README.en.md](README.en.md)
>
> 상태: **PRD 전 범위 구현 완료 — P0 Epic 1–11 · P1 Epic 12–18·20–24 · P2 Epic 19·25** (2026-10-07) — 회귀 284 passed · 콘솔 E2E(P0 4 + P1·P2 12 + 위젯 1) · 접근성(WCAG 2.2 AA) 65화면 위반 0 · prod(PostgreSQL, 마이그레이션 0015) 리허설 PASS — 26th 전체 회귀 재검증 PASS. 다음 이터레이션: 계획표 Epic 26–29(TODO)

## 구성

```
브라우저 ─▶ Traefik :8090 (web) ─┬─ /                                     → web  (React 19 콘솔, nginx 비루트)
                                ├─ /api /v1 /mcp /registry /widget /.well-known
                                │  /a/{id}/a2a · /a/{id}/.well-known/…     → api
                                └─ /a/{id}/api/… · /a/{id}/health         → {id}-be  (forwardAuth: api가 사용자 확인 + 에이전트 키 주입)
         Traefik :8092 (apps) ── /a/{id}/ui/…                            → {id}-fe  (Addon 화면 전용 오리진)

api            플랫폼 — 인증·RBAC·API 키·감사 원장 · LLM 게이트웨이(/v1, 임베딩·재정렬·비전) · Orchestrator(LangGraph 체크포인터)
               · Assistant(AG-UI SSE, 재연결 재개) · 등록 8단계(cosign·syft·trivy 공급망 게이트) · 마켓(구매·라이선스·퍼블리셔·레지스트리 API)
               · MCP/A2A 게이트웨이 · 시크릿 저장소·정책·가드레일 · 지식(RAG)·메모리 · 관측·평가 · OTel
runtime        에이전트 빌드·기동·정지(docker.sock은 여기만) · compose 린트 · 에이전트 전용 네트워크 · 10초 주기 재연결 · 볼륨 백업·복원
bifrost        LLM 공급자 게이트웨이 엔진(maximhq/bifrost v2.2.6, Apache-2.0) — 포트 미공개, 퍼블릭 키는 여기만. api 의 별칭·데이터 등급·예산 정책 뒤
otel-collector · redis(Valkey, 레이트리밋) · db(prod 전용: pgvector/pgvector:pg17) · 볼륨 trivycache(취약점 DB)·bifrostdata
선택 오버레이  compose-optional/ — vllm·llama-server(고성능 서빙) · tei(교차 인코더 재정렬) · cli-bridge(CLI 에이전트 NDJSON·ACP) · gpu · mailpit(알림 메일 시험)
에이전트        compose 프로젝트 <PLAZA_PROJECT>-agent-<id>, 서비스 <id>-be(+ <id>-fe)
LLM            api → bifrost → 호스트 Ollama(host.docker.internal:11434)·퍼블릭(키가 있을 때만) · Bifrost 장애 시 Ollama 직접 호출 · OpenAI 호환 서버 등록(vLLM 등)
```

| 구분 | local | prod |
|---|---|---|
| 콘솔·게이트웨이 (Traefik web) | http://127.0.0.1:8090 | http://127.0.0.1:8091 |
| Addon 화면 오리진 (Traefik apps) | http://127.0.0.1:8092 | http://127.0.0.1:8093 |
| api 직접 접속 (개발·진단) | http://127.0.0.1:8010 | http://127.0.0.1:8011 |
| Valkey | 127.0.0.1:6390 | 127.0.0.1:6391 |
| DB | SQLite `/app/data/app.db` | PostgreSQL 17 + pgvector (`db` 서비스, 포트 미공개) |

실행은 **docker compose 전용**이다. local은 `docker-compose.yml` + `docker-compose.local.yml` + `.env.local`(dev 스테이지, 소스 바인드)을,
prod는 `docker-compose.yml` + `docker-compose.prod.yml` + `.env.prod`(runtime 스테이지)를 쓴다. `compose/*.yml`은 두 모드에 자동 포함된다.

## 빠른 시작

사전 요구: Docker + Compose v2, GNU Make. 선택: 호스트 Ollama와 기본 모델 `granite4.1:3b`(대화)·`qwen3:8b`(계획)·`bge-m3`(임베딩)·`qwen2.5vl:7b`(비전).
Ollama가 없으면 local 별칭은 결정적 `mock/echo` 모델로 폴백한다(prod 카탈로그에는 mock이 없다).

```bash
make preflight               # Docker·Compose·env 점검
make local-all               # api·runtime·traefik·web·otel-collector·valkey 기동 (이미지 없으면 빌드)
open http://127.0.0.1:8090   # 최초 실행 시 설치 위저드: 관리자 → LLM 연결 → 모델 → 기본 에이전트 → 완료
make trivy-db                # (선택) 취약점 DB 받기 — 없으면 등록 3단계가 '미스캔' 경고
make test                    # 플랫폼 회귀(pytest)
make local-stop
```

prod 리허설(로컬 Docker):

```bash
cp .env.example .env.prod    # 없을 때만. CHANGE_ME(DB_PASSWORD·JWT_SECRET·RUNTIME_TOKEN)를 시크릿으로 교체
make prod-build              # 이미지 다시 빌드 후 기동(prod-all 은 있는 이미지로만 기동)
make db-migrate ENV=prod     # prod는 AUTO_MIGRATE=false
make db-ping ENV=prod
make prod-stop
```

## 기능 ↔ 요구사항

| Epic | 기능 | FR | 주요 경로 |
|---|---|---|---|
| 1 | 계정·RBAC·API 키·감사 원장(해시 체인, PG append-only 트리거) | D9-01/02/03/07, D10-06 | `/api/auth/*` `/api/users` `/api/api-keys` `/api/audit` |
| 2 | agent.yaml 규격·템플릿 9유형·SDK·스캐폴드·파생/Standalone 내보내기 | D4-01/02/03/04/07, D8-01 | `/api/agents/scaffold` `make plaza` |
| 3 | LLM 게이트웨이(별칭·폴백·데이터 등급 L0–L3·계량)·모델 카탈로그·라이선스 게이트 | D1-01/03/05/06 | `/v1/chat/completions` `/api/llm/*` |
| 4 | Orchestrator — 의도·계획(LLM+규칙)·레지스트리 라우팅·순차/병렬·도구 실행·휴먼 승인 | D2-01/02/03/04/06 | `/api/orchestrate` `/api/approvals` |
| 5 | AI Assistant — AG-UI SSE·세션·도구/승인 카드·스코프 채팅·보존 파기 | D3-01/02/03 | `/api/chat/stream` `/api/sessions` |
| 6 | 등록 8단계(업로드·구조 검증·빌드·등록·기동/계약 시험·노출)·버전·롤백·60초 내 삭제 | D5-01/02/05/06/07 | `/api/agents/upload` `/api/agents/installs/*` |
| 7 | runtime 서비스·compose 린트·에이전트 격리 네트워크·Traefik·GPU 오버레이 | D8-02/03/04/05 | `runtime/` `compose-optional/` |
| 8 | MCP(2026-07-28·2025-11-25)·A2A 1.0(서명 카드)·원격 연동·rug-pull 탐지 | D7-01/02/03/04, D6-04 | `/mcp/{id}` `/a/{id}/a2a` `/api/agents/link` |
| 9 | 마켓 — 3축 분류·검색·경로 A(카탈로그)·B(zip 업로드·zip URL·Git)·C(원격) | D6-01/02/03/04 | `/api/market/*` `/api/agents/install-url` `/api/agents/install-git` |
| 10 | 콘솔 대시보드·설정·프로필·셋업 위저드·OTel GenAI 스팬 | D10-01/02/03 | `/api/console/dashboard` `/api/setup/*` |
| 11 | 웹 콘솔(React 19) — 로그인·위저드·대시보드·채팅·에이전트·마켓·승인·LLM·조직·설정·감사·Addon iframe | D3-01, D6-01, D10-01, D5-07 | http://127.0.0.1:8090 |
| 12 | 공급망 신뢰 — cosign 서명·SBOM(syft)·취약점(trivy)·라이선스 G1–G5·egress 정책 | D4-06, D5-03/04 | `/api/trust/*` `make publish` `make trivy-db` |
| 13 | 거버넌스 — 시크릿 저장소(AES-GCM, pull)·정책 엔진·가드레일(인젝션·한국어 PII)·리뷰어 게이트·레이트리밋·툴 RBAC | D9-04/05/06, D2-05, D7-07 | `/api/policy` `/api/secrets` `/api/guardrails/check` |
| 14 | 실행 내구성·운영 — 체크포인트 재개·재시도·보상·업그레이드 사전 백업/롤백·백업·오프라인 번들 | D2-07, D8-06/07 | `/api/agents/{id}/backup·restore` `make backup` `make offline-bundle` |
| 15 | 어시스턴트 확장 — 첨부·비전·메모리·지식 컬렉션(RAG)·임베딩·재정렬 | D3-04/05/06, D1-07 | `/api/kb/*` `/api/me/memories` `/v1/embeddings` `/v1/rerank` |
| 16 | LLM·프로토콜 확장 — OpenAI 호환 서버·CLI 브리지·에이전트=모델·OpenAPI→도구·AG-UI 재연결·ACP | D1-02/04, D7-05/06 | `/api/llm/servers` `/api/chat/streams/{id}` |
| 17 | 관측·평가 — 트레이스·사용량·비용(자체 UI)·평가 묶음·회귀·A/B·`plaza test` | D10-04/05, D4-05 | `/api/obs/*` `/api/evals/*` |
| 18 | 마켓 상거래·퍼블리셔 — 게시·심사·mock 결제·Ed25519 라이선스·좌석·업데이트·MCP registry 호환 API·번들 | D6-05/06/07 | `/api/market/*` `/api/licenses` `/registry/v0.1/*` |
| 20 | LLM 게이트웨이 엔진 Bifrost 전환·월 예산 80% 로컬 강제(J05) | D1-01/03/05/06 (Q1·Q15) | `bifrost` 서비스 · `/api/llm/budget` |
| 21 | Assistant 에이전트 pydantic-ai 전환(게이트웨이 정책 유지) | D3-01/02/03 (Q2) | `app/assistant/agent.py` |
| 22 | 결제 어댑터 Stripe·Polar·Lago(호스티드 결제 + 서명 웹훅) | D6-05 (Q6) | `/api/market/purchase/{id}` `/api/market/payments/{adapter}/webhook` |
| 23 | 조직·그룹(부서) 단위 배치(deploy_scope)·조직 화면 K02·도입 흐름 FL-07 | X09 일부, D6-02 (Q7·Q12) | `/api/orgs/*` `/api/agents/{id}/scope` · http://127.0.0.1:8090/orgs |
| 24 | 품질 기준 상향 — KWCAG 2.2 / WCAG 2.2 AA(axe) · MCP 계약 두 핸드셰이크(discover·initialize) | NFR-U4, NFR-P1 (Q8·Q9) | `web/e2e/a11y.e2e.mjs` · 설치 7단계·`plaza test` |
| 19 | 알림·상태(P2) — 헬스 대시보드·상태 변화 알림·알림 센터 B03·Slack/Telegram/메일 발송·사용량 리포트 | D10-07 | `/api/status` `/api/notifications/*` · http://127.0.0.1:8090/status |
| 25 | 채널·임베드(P2) — 웹 위젯(iframe+postMessage)·Slack·Telegram·카카오 i 오픈빌더 → Assistant · 설정 화면 C07 | D3-07 | `/api/channels/*` `/widget/{id}.js` · http://127.0.0.1:8090/settings/channels |

## API

인증은 `Authorization: Bearer <JWT | ap_sk_…>` 또는 `x-api-key: ap_sk_…` 헤더로 한다. 인증 없이 열리는 경로는 `/health`, Agent Card,
JWKS, 로그인·셋업뿐이다(NFR-S5). 전체 스키마는 `http://127.0.0.1:8010/docs`(OpenAPI)에서 볼 수 있다.

| 그룹 | 엔드포인트 |
|---|---|
| 셋업 | `GET /api/setup/status` `GET /api/setup/progress` `POST /api/setup/admin` `GET·POST /api/setup/llm` `POST /api/setup/models/pull` `POST /api/setup/agents` `POST /api/setup/skip` `POST /api/setup/complete` |
| 인증 | `POST /api/auth/login` `POST /api/auth/logout` `POST /api/auth/token` `POST /api/auth/password` `GET /api/auth/me` `GET /api/auth/forward`(Traefik forwardAuth) |
| 조직·원장 | `GET·POST /api/orgs` `GET·DELETE /api/orgs/{id}` `PUT /api/orgs/{id}/members` `DELETE /api/orgs/{id}/members/{user}` `POST /api/orgs/{id}/groups` `DELETE /api/orgs/{id}/groups/{gid}` `PUT·DELETE /api/orgs/{id}/groups/{gid}/members[/{user}]` · `GET·PUT·DELETE /api/agents/{id}/scope`(배치 범위 org·group·user) · `GET·POST /api/users` `PATCH /api/users/{id}` `GET·POST /api/api-keys` `DELETE /api/api-keys/{id}` `GET /api/audit` `GET /api/audit/verify` |
| LLM | `POST /v1/chat/completions`(OpenAI 호환, stream 지원) `GET /v1/models` `GET·POST /api/llm/models` `PATCH /api/llm/models/{id}` `GET /api/llm/routes` `PUT /api/llm/routes/{alias}` `GET /api/llm/providers`(Bifrost 상태·직접 폴백 수) `GET /api/llm/usage` `GET /api/llm/budget` `PUT /api/llm/budget`(supervisor, 월 예산·로컬 강제 기준) |
| 대화 | `POST /api/chat/stream`(SSE) `GET·POST /api/sessions` `GET·PATCH·DELETE /api/sessions/{id}` `GET /api/sessions/{id}/export` |
| 오케스트레이션 | `POST /api/orchestrate` `GET /api/tasks/{id}` `GET /api/approvals` `POST /api/approvals/{id}/approve` `POST /api/approvals/{id}/reject` |
| 에이전트 | `GET /api/agents` `GET /api/agents/templates` `POST /api/agents/upload·install-url·install-git·link·scaffold` `GET /api/agents/installs[/{id}]` `GET·PATCH·DELETE /api/agents/{id}` `POST /api/agents/{id}/export·export-standalone·rollback·revalidate` `GET /api/agents/{id}/ui·runtime·install-status` |
| 마켓 | `GET /api/market/categories` `GET /api/market/listings[/{id}]` `POST /api/market/install/{id}` |
| 프로토콜 | `/mcp/{id}`(Streamable HTTP, `/mcp/orchestrator` 포함) `GET /a/{id}/.well-known/agent-card.json` `POST /a/{id}/a2a` `GET /a/{id}/mcp/server.json` `GET /.well-known/jwks.json` |
| 공급망 신뢰 | `GET·POST /api/trust/keys` `DELETE /api/trust/keys/{kid}` `GET·PUT /api/trust/policy` `GET /api/agents/{id}/sbom` |
| 프로토콜 확장 | `GET /v1/models`(별칭 + `agent/<id>`) · `POST /v1/chat/completions` model=`agent/<id>` · `GET /api/llm/servers` `PUT·DELETE /api/llm/servers/{name}` `GET /api/llm/servers/{name}/models` · `POST /api/agents/link` kind=`openapi` · `GET /api/chat/streams/{id}?after=`(Last-Event-ID 재개) |
| 관측·평가 | `GET /api/obs/usage?days=`(모델·에이전트·사용자별 호출·토큰·비용·p50/p95) · `GET /api/obs/traces?q=` `GET /api/obs/traces/{trace_id}`(스팬 워터폴) · `GET·POST /api/evals/suites` `DELETE /api/evals/suites/{id}` `POST /api/evals/suites/{id}/runs` `GET /api/evals/runs/{id}`(사례별 판정·회귀) · `POST /api/evals/compare`(별칭 A/B) |
| 마켓 상거래·퍼블리셔 | `GET·POST /api/market/publishers` `PATCH /api/market/publishers/{id}` `POST /api/market/publishers/{id}/keys`(회전) · `POST /api/market/releases`(zip+퍼블리셔 → 자동 검사) `GET /api/market/releases?status=` `POST /api/market/releases/{id}/approve·reject` · `PATCH /api/market/listings/{id}/ops`(추천·검증·숨김) · `POST /api/market/purchase/{id}`(mock = 즉시 발급 201 · Stripe·Polar·Lago = 결제 페이지 URL 202) `GET /api/market/purchases[/{id}[/receipt]]` `POST /api/market/payments/{stripe|polar|lago}/webhook`(결제대행 서명 = 인증) · `POST /api/licenses/verify` `GET·POST /api/licenses` `DELETE /api/licenses/{id}[/seats/{holder}]` · `GET·POST·DELETE /api/market/license-issuers` · `GET /api/market/instance` |
| 업데이트·레지스트리 | `GET /api/market/installed` `POST /api/market/updates/check` `POST /api/market/updates/{agent}`(consent) `PUT /api/market/auto-update/{agent}` · `GET /api/market/registries` `PUT·DELETE /api/market/registries/{name}` `POST /api/market/registries/{name}/sync` · `GET·PUT /api/market/registry-exposure` · `GET·POST /api/market/bundle`(오프라인 번들) · MCP registry 호환 `GET /registry/v0.1/servers?cursor&limit&search&updated_since` `GET /registry/v0.1/servers/{name}/versions[/{version}]` `GET /registry/v0.1/artifacts/{id}/{version}.zip`(유료 = `X-Plaza-License`) |
| 지식·개인화 | `POST /v1/embeddings` `POST /v1/rerank` `GET·POST /api/kb/collections` `DELETE /api/kb/collections/{id}` `GET·POST /api/kb/collections/{id}/documents` `POST /api/kb/search` `GET·POST·DELETE /api/me/memories` `PUT /api/me/memory-settings` `POST·GET /api/files` `GET /api/files/{id}/content` `DELETE /api/files/{id}` · 채팅 `attachments`·`knowledge` |
| 운영 | `POST /api/agents/{id}/backup` `GET /api/agents/{id}/backups` `POST /api/agents/{id}/restore` `POST /api/admin/backup`(supervisor) |
| 거버넌스 | `GET·PUT /api/policy` `GET /api/secrets` `PUT·DELETE /api/secrets/{scope}/{name}` `GET /api/agent/secrets`(에이전트 키) `POST /api/guardrails/check` `POST /api/agents/{id}/rotate-key` |
| 콘솔 | `GET /api/console/dashboard` `GET·PUT /api/settings` `GET·PATCH /api/me/profile` `POST /api/admin/retention/run` |
| 알림·상태 | `GET /api/status`(헬스: 구성요소·LLM·에이전트) `POST /api/status/check` · `GET /api/notifications[?unread=true]` `GET /api/notifications/unread-count` `POST /api/notifications/read` · `GET /api/notifications/channels` `PUT /api/notifications/channels/{slack|telegram|email}` `POST /api/notifications/channels/{name}/test` · `GET /api/status/report?days=` `POST /api/status/report/send` `PUT /api/status/report/settings` |
| 채널·임베드 | `GET·POST /api/channels` `PATCH·DELETE /api/channels/{id}` `POST /api/channels/{id}/rotate` · `POST /api/channels/{id}/slack/events`(서명 v0) `POST /api/channels/{id}/telegram/webhook`(secret token) `POST /api/channels/{id}/kakao/skill`(X-Plaza-Channel-Token) · 웹 위젯 `GET /widget/{id}.js`(삽입) `GET /widget/{id}` `POST /api/widget/{id}/session` `POST /api/widget/{id}/chat`(SSE) |

### 예시 (local 스택 실제 응답, 2026-10-07)

```bash
$ curl -s http://127.0.0.1:8090/health
{"status":"ok","env":"local","db":{"engine":"sqlite","status":"ok"}}

# LLM 게이트웨이 — L3(기밀)는 로컬 모델로만 라우팅된다
$ curl -si http://127.0.0.1:8090/v1/chat/completions -H "authorization: Bearer $TOKEN" \
    -H 'content-type: application/json' -H 'X-Plaza-Data-Class: L3' \
    -d '{"model":"plaza/fast","messages":[{"role":"user","content":"한 단어로 인사해줘"}]}'
HTTP/1.1 200 OK
X-Plaza-Data-Class: L3
X-Plaza-Degraded: false
X-Plaza-Model: ollama/granite4.1:3b
{"id":"chatcmpl-…","object":"chat.completion","model":"plaza/fast",
 "choices":[{"index":0,"message":{"role":"assistant","content":"안녕하세요!"},"finish_reason":"stop"}],
 "usage":{"prompt_tokens":18,"completion_tokens":7,"total_tokens":25}}

# 오케스트레이션 — 실 LLM(qwen3:8b)이 계획하고 설치된 board 에이전트를 실행한다
$ curl -s http://127.0.0.1:8090/api/orchestrate -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
    -d '{"message":"게시판에 \"README 예시\" 라는 제목으로 글을 등록해줘"}'
{"task_id":"828188c9-…","state":"succeeded",
 "plan":{"steps":[{"id":"s1","agent":"board","capability":"manage","args":{"action":"create","title":"README 예시"},"depends_on":[]}],
         "pattern":"sequential","source":"llm","model":"ollama/qwen3:8b","misses":[]},
 "results":{"s1":{"ok":true,"result":{"id":4},"latency_ms":12,"agent":"board","capability":"manage",…}},
 "answer":"…", "events":[…], "session_id":"…"}

# MCP(2026-07-28) — Cursor·Claude Desktop 등은 /mcp/{id}에 API 키로 연결한다
$ curl -s http://127.0.0.1:8090/mcp/board -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
    -H 'accept: application/json, text/event-stream' -H 'mcp-protocol-version: 2026-07-28' -H 'mcp-method: tools/list' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
→ tools: ["manage"]

# A2A — 서명된 Agent Card는 공개, server.json·업무 API는 인증 필요
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8090/a/board/.well-known/agent-card.json   # 200 (signatures 포함)
$ curl -s http://127.0.0.1:8090/.well-known/jwks.json      # {"keys":[{"kty":"OKP","crv":"Ed25519","alg":"EdDSA","kid":"plaza-…",…}]}
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8090/a/board/mcp/server.json          # 401
```

## 에이전트 개발 (plaza CLI)

```bash
make plaza ARGS="init inventory --template service --out agents/inventory"
#   유형: app service rag tool-proxy reviewer execution hitl memory federation(--url 원격 Card/MCP)
make plaza ARGS="validate agents/inventory --strict"              # JSON Schema + 의미 규칙 + 선언↔핸들러 일치
make plaza ARGS="pack agents/inventory --out inventory-0.1.0.zip" # checksums.txt 포함 결정적 zip
make plaza ARGS="export inventory-0.1.0.zip --derive inventory-hr --standalone --out dist"
make plaza ARGS="convert-v1 Board-meta.json"                      # v1 meta.json → agent.yaml
make plaza ARGS="market-build --out market"                       # 큐레이션 카탈로그(market/catalog.json + sha256)
make plaza ARGS="verify-coverage"                                 # P0 FR ↔ 계획표 ↔ 시험 추적
make plaza ARGS="test agents/inventory --report out/inventory"     # 구조·문법·SQL·로컬 기동·REST/MCP/A2A 계약·evals/*.yaml → result.md/json
PLAZA_TOKEN=… make plaza ARGS="publish agents/inventory --key keys/acme.key --registry http://127.0.0.1:8090 --publisher acme --listing listing.json"  # 서명 패키지 → 마켓 게시(D6-06)
```

생성된 에이전트는 혼자서도 돈다(M1). `cp .env.example .env && docker compose --profile standalone up -d --build` 후
`/health`, `/api/capabilities`, `/api/invoke/{verb}`, `/mcp`, `/.well-known/agent-card.json`, `/a2a`가 열린다.
플랫폼에 설치하면 federated compose로 다시 생성되어 포트 없이 Traefik 경로와 전용 네트워크로만 노출된다(M2·M3).

## 환경 변수

| 변수 | local | prod |
|------|-------|------|
| `APP_ENV` | `local` | `prod` |
| `DB_ENGINE` | `sqlite` | `postgres` |
| `DATABASE_URL` | SQLite 파일 | `db` 서비스 접속 문자열 |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | — | RDBMS 계정 (CHANGE_ME → 주입) |
| `API_PORT`, `BIND_HOST` | `8010`, `127.0.0.1` | `8011`, `127.0.0.1` |
| `REDIS_PORT` (Valkey) | `6390` | `6391` |
| `DB_IMAGE` | — | `pgvector/pgvector:pg17` |
| `JWT_SECRET` | 로컬 전용 고정값 | CHANGE_ME → 주입 |
| `AUTO_MIGRATE` | `true` (기동 시 alembic upgrade) | `false` (`make db-migrate ENV=prod`) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` (호스트 Ollama) | 동일 또는 GPU 서버 |
| `LLM_LOCAL_CHAT_MODEL` / `LLM_LOCAL_REASONING_MODEL` | `granite4.1:3b` / `qwen3:8b` | 동일 |
| `PUBLIC_MODELS`, `OPENAI_API_KEY`·`ANTHROPIC_API_KEY`·`GEMINI_API_KEY` | 비움(로컬 전용) | 필요 시 주입 — 게이트웨이(api)만 보유 |
| `PLAZA_PROJECT` | `wise-agentplaza-local` | `wise-agentplaza-prod` (에이전트 프로젝트·네트워크 접두어, Traefik 제약) |
| `GATEWAY_PORT` (Traefik web) | `8090` | `8091` |
| `APPS_PORT` · `PUBLIC_APPS_URL` (Addon 화면 오리진) | `8092` · `http://127.0.0.1:8092` | `8093` · `http://127.0.0.1:8093` |
| `RUNTIME_DRIVER` / `RUNTIME_URL` / `RUNTIME_TOKEN` | `remote` / `http://runtime:9000` / 로컬 고정값 | 동일 / CHANGE_ME |
| `HITL_ALLOW_SELF_APPROVAL` | `true` (1인 개발) | `false` (four-eyes) |
| `PUBLIC_BASE_URL` (Agent Card·server.json 외부 주소) | `http://127.0.0.1:8090` | `http://127.0.0.1:8091` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318` | 동일(수집기 exporters로 백엔드 선택) |
| `GATEWAY_INTERNAL_URL` (설치 후 노출 확인) | `http://traefik` | 동일 |
| `LLM_LOCAL_EMBED_MODEL` / `LLM_LOCAL_VISION_MODEL` | `bge-m3` / `qwen2.5vl:7b` | 동일 |
| `TEI_RERANK_URL` (선택, 교차 인코더 재정렬) | 비움(임베딩 코사인) | 필요 시 |
| `BIFROST_URL` (공급자 게이트웨이 엔진, PRD Q1 — 퍼블릭 키는 bifrost 서비스에만) | `http://bifrost:8080` | `http://bifrost:8080` |
| `PAYMENT_ADAPTER` (결제 어댑터, D6-05) | `mock`(실결제 없음) | `none`(키 직접 입력만) — `stripe`·`polar`·`lago` 는 아래 키가 있을 때만 |
| `STRIPE_SECRET_KEY`·`STRIPE_WEBHOOK_SECRET` · `POLAR_ACCESS_TOKEN`·`POLAR_WEBHOOK_SECRET`·`POLAR_PRODUCT_ID`·`POLAR_API_URL` · `LAGO_API_URL`·`LAGO_API_KEY`·`LAGO_WEBHOOK_HMAC_KEY`·`LAGO_ADD_ON_CODE` | 비움(시험 모드 키만, Polar 는 sandbox URL) | 사용하는 어댑터만 주입 |
| `MARKET_SYNC_INTERVAL` (원격 레지스트리 동기화·자동 갱신 주기, 초, 0=끔) | `3600` | `3600` |
| `STATUS_CHECK_INTERVAL` (상태 감시·알림 발송·주간 리포트 주기, 초, 0=끔) | `60` | `60` |
| `REDIS_URL` (레이트리밋 카운터, Valkey) | `redis://redis:6379/0` | 동일 |
| `SECRETS_MASTER_KEY` (시크릿 암호화 키, base64 32바이트) | 비움(JWT_SECRET 에서 파생, 로컬 전용) | CHANGE_ME → 주입 |

> 시크릿은 `.env.prod`에 두고 커밋하지 않는다(`.gitignore`). `.env.local`은 로컬 전용 고정값만 담으므로 커밋한다(CI `make test`).

## Make 타겟

| 타겟 | 설명 |
|------|------|
| `make <mode>-all` · `-build` · `-logs [SVC=]` · `-stop` · `-restart [SVC=]` · `-ps` | 스택 수명주기 (`mode` = local \| prod) |
| `make test` | 플랫폼 회귀(pytest, local dev 컨테이너) |
| `make e2e` | 콘솔 E2E(Playwright 컨테이너). 로컬 스택 기동 후, `E2E_EMAIL`·`E2E_PASSWORD` 필요(P1 화면: `E2E_TOKEN`·`E2E_SPEC=p1`, 접근성 WCAG 2.2 AA: `E2E_SPEC=a11y`, 웹 위젯: `E2E_SPEC=widget`) |
| `make plaza ARGS="…"` | plaza CLI |
| `make publish SRC=… KEY=… [OUT=]` | 서명 패키지(zip·checksums·sbom.json·signature.sig) |
| `make backup [ENV=]` | 플랫폼 DB + 설치 에이전트 볼륨 백업 → data/backups/ (업그레이드 전 필수) |
| `make offline-bundle [ENV=] [IMAGES=]` · `make offline-load DIR=…` | 폐쇄망 번들 생성·적재(이미지·카탈로그·취약점 DB·모델 목록, sha256 검증) |
| `make trivy-db [ENV=]` | 취약점 DB 받기·갱신(trivycache 볼륨, 약 1.4GB) — 등록 3단계 스캔에 필요 |
| `make shell [ENV=]` | 앱 컨테이너 셸 |
| `make db-ping` · `db-shell` · `db-migrate` · `db-seed [ENV=]` | DB 확인·클라이언트·마이그레이션·시드 |
| `make db-reset` · `db-fresh` | local SQLite 초기화(+시드). prod는 거부 |
| `make deploy` | prod 롤아웃 (CHANGE_ME가 남아 있으면 거부) |
| `make preflight` · `help` | 점검 · 목록 |

## 보안 모델

- **격리** — 업로드 코드는 컨테이너로만 실행한다(in-process 모드는 등록 2단계에서 거부). docker.sock은 runtime(과 Traefik 읽기 전용)만 마운트한다.
  기동 전 compose 린트가 privileged, host 네트워크/PID/IPC, cap_add, 장치·GPU 예약, 호스트 bind 마운트, docker.sock, federated 포트 공개를 거부하고
  `cap_drop: [ALL]`, `read_only`, `no-new-privileges`, cpus·memory·pids 제한을 요구한다.
- **네트워크** — 에이전트마다 전용 네트워크를 만들고 api·traefik만 연결한다. 에이전트끼리는 서로 닿지 않는다. egress를 선언하지 않으면 `--internal`(외부 차단)이다.
- **키** — 퍼블릭 LLM 키는 api만 가진다. 에이전트 내부 키는 HMAC(secret, `agent:{id}`)로 파생해 저장하지 않는다. 게이트웨이 호출용 키는 설치 때 발급하고 원문은 workdir/.env(0600)에만 둔다.
- **경로 인증** — `/a/{id}/…`는 Traefik forwardAuth로 api가 사용자·키 범위·활성 여부를 확인한 뒤 에이전트 키를 주입한다.
  Addon 화면은 별도 오리진(apps)에서 열고, 콘솔은 CSP `frame-ancestors 'none'; frame-src 'self' <apps>`를 쓴다.
- **데이터 등급** — 헤더가 없으면 L2로 본다. L2 이상은 로컬 모델만 쓰며 이 규칙이 폴백보다 우선한다. 거부는 원장에 기록한다.
- **승인** — `humanApprovalRequired` capability는 MCP·A2A·REST 어느 경로로도 우회할 수 없다(DP8). 대화 안 승인 카드나 승인함에서 처리한다.
- **원장** — 도구 호출과 관리 작업을 해시 체인으로 기록한다. PostgreSQL에서는 트리거가 UPDATE/DELETE를 막는다.
- **카드 서명** — Agent Card는 agent.yaml에서 생성하고 플랫폼 Ed25519 키로 JWS 서명한다(`/.well-known/jwks.json`).
- **공급망** — 등록 3·4단계가 checksums·cosign 서명(신뢰 키)·SBOM·취약점(Critical 차단)·라이선스 등급·egress 정책을 본다. 마켓 게시는 퍼블리셔 키 서명이 필수다.
- **시크릿** — AES-256-GCM 암호문만 DB에 둔다(scope·이름이 AAD). 에이전트는 자기 키로 선언한 secretRefs만 pull 한다. 로그는 알려진 시크릿 값을 가린다.
- **가드레일** — 입력 인젝션 차단·한국어 PII 마스킹(외부 LLM 전송 전), 외부 결과는 리뷰어 게이트, 게이트웨이 레이트리밋·툴 단위 RBAC.
- **라이선스·결제** — 유료 에이전트는 Ed25519 서명 토큰(오프라인 검증: 대상·버전 범위·좌석·만료·호스트)이 있어야 설치·실행·갱신된다.
  결제는 호스티드(Stripe·Polar·Lago 결제 페이지)만 쓰고 카드 정보를 받지 않는다. 결제대행 웹훅은 서명(HMAC)으로 인증하고 금액·통화를 구매 기록과 대조한다.
- **LLM 키 격리** — 퍼블릭 LLM 키는 bifrost 서비스에만 주입된다(api 의 값은 비워 덮어씀). bifrost 는 포트를 열지 않고 api 만 부른다.
- **채널** — 메신저 웹훅은 서명(Slack v0)·비밀 헤더(Telegram·카카오)로 인증하고 틀리면 401. 웹 위젯은 플랫폼 오리진 iframe 이며 CSP frame-ancestors 로 허용 오리진에서만 뜬다.
  위젯 세션 토큰(aud=widget:<id>)은 플랫폼 API 에 쓸 수 없다. 채널 사용자는 플랫폼 계정이 아니며 승인은 콘솔에서만 한다. 카카오 콜백은 카카오 도메인만 부른다.
- **조직 배치 범위** — 에이전트를 조직·그룹·사용자 단위로 배치하면 범위 밖 사용자에게는 목록·네비·계획·MCP·A2A·Addon 화면에서 빠진다(supervisor 제외). 데이터 분리는 아니다.

## 시험

`test/` 단일 트리를 쓴다. `test/dev-env/`는 환경 검증 1회, `test/impl/<Nth>/`는 구현 차수별 기록이다. 규칙은 `test/README.md`에 있다.

| 차수 | 일자 | 판정 | 결과 |
|------|------|------|------|
| dev-env 1st | 2026-10-06 | PASS (11/11) | [test/dev-env/result.md](test/dev-env/result.md) |
| impl 1st — Epic 1 플랫폼 기반 | 2026-10-06 | PASS (13/13) | [test/impl/1st/result.md](test/impl/1st/result.md) |
| impl 2nd — Epic 2 agent.yaml·템플릿·SDK | 2026-10-06 | PASS (15/15) | [test/impl/2nd/result.md](test/impl/2nd/result.md) |
| impl 3rd — Epic 3 LLM 게이트웨이 | 2026-10-06 | PASS (16/16) | [test/impl/3rd/result.md](test/impl/3rd/result.md) |
| impl 4th — Epic 4 Orchestrator | 2026-10-06 | PASS (13/13) | [test/impl/4th/result.md](test/impl/4th/result.md) |
| impl 5th — Epic 5 Assistant | 2026-10-06 | PASS (10/10) | [test/impl/5th/result.md](test/impl/5th/result.md) |
| impl 6th — Epic 6 등록 8단계 | 2026-10-06 | PASS (17/17) | [test/impl/6th/result.md](test/impl/6th/result.md) |
| impl 7th — Epic 7 런타임·격리 | 2026-10-06 | PASS (15/15) | [test/impl/7th/result.md](test/impl/7th/result.md) |
| impl 8th — Epic 8 MCP·A2A | 2026-10-06 | PASS (13/13) | [test/impl/8th/result.md](test/impl/8th/result.md) |
| impl 9th — Epic 9 마켓 3경로 | 2026-10-06 | PASS (11/11) | [test/impl/9th/result.md](test/impl/9th/result.md) |
| impl 10th — Epic 10 콘솔 API·OTel | 2026-10-06 | PASS (9/9) | [test/impl/10th/result.md](test/impl/10th/result.md) |
| impl 11th — Epic 11 웹 콘솔 | 2026-10-07 | PASS (9/9) | [test/impl/11th/result.md](test/impl/11th/result.md) |
| 완료 게이트 — 전체 회귀 + prod 리허설 | 2026-10-07 | PASS | [test/impl/final/result.md](test/impl/final/result.md) |
| impl 12th — Epic 12 공급망 신뢰 | 2026-10-07 | PASS (15/15) | [test/impl/12th/result.md](test/impl/12th/result.md) |
| impl 13th — Epic 13 거버넌스·보안 | 2026-10-07 | PASS (20/20) | [test/impl/13th/result.md](test/impl/13th/result.md) |
| impl 14th — Epic 14 실행 내구성·운영 | 2026-10-07 | PASS (12/12) | [test/impl/14th/result.md](test/impl/14th/result.md) |
| impl 15th — Epic 15 어시스턴트 확장 | 2026-10-07 | PASS (12/12) | [test/impl/15th/result.md](test/impl/15th/result.md) |
| impl 16th — Epic 16 LLM·프로토콜 확장 | 2026-10-07 | PASS (11/11) | [test/impl/16th/result.md](test/impl/16th/result.md) |
| impl 17th — Epic 17 관측·평가 | 2026-10-07 | PASS (8/8) | [test/impl/17th/result.md](test/impl/17th/result.md) |
| impl 18th — Epic 18 마켓 상거래·퍼블리셔 (+ P1 완료 게이트: 250 passed·prod 리허설 0012) | 2026-10-07 | PASS (14/14) | [test/impl/18th/result.md](test/impl/18th/result.md) |
| impl 19th — Epic 24 품질 기준 상향(접근성·MCP 계약) | 2026-10-07 | PASS (7/7) | [test/impl/19th/result.md](test/impl/19th/result.md) |
| impl 20th — Epic 20 Bifrost 전환·월 예산 로컬 강제 | 2026-10-07 | PASS (8/8) | [test/impl/20th/result.md](test/impl/20th/result.md) |
| impl 21st — Epic 21 Assistant pydantic-ai 전환 | 2026-10-07 | PASS (6/6) | [test/impl/21st/result.md](test/impl/21st/result.md) |
| impl 22nd — Epic 22 결제 어댑터 Stripe·Polar·Lago | 2026-10-07 | PASS (8/8, MANUAL 1: 실 테스트 키) | [test/impl/22nd/result.md](test/impl/22nd/result.md) |
| impl 23rd — Epic 23 조직·부서 배치 (+ 완료 게이트: 272 passed·접근성 57화면·prod 리허설 0013) | 2026-10-07 | PASS (7/7) | [test/impl/23rd/result.md](test/impl/23rd/result.md) · [게이트](test/impl/23rd/logs/gate/result.md) |
| impl 24th — Epic 19 알림·상태(P2) | 2026-10-07 | PASS (7/7) | [test/impl/24th/result.md](test/impl/24th/result.md) |
| impl 25th — Epic 25 채널·임베드(P2) (+ 완료 게이트: 284 passed·접근성 65화면·prod 리허설 0015) | 2026-10-07 | PASS (9/9, MANUAL 1: 실 메신저) | [test/impl/25th/result.md](test/impl/25th/result.md) · [게이트](test/impl/25th/logs/gate/result.md) |
| impl 26th — 문서 정리 + 전체 회귀 재검증(구현 없음): 284 passed·콘솔 E2E 17·접근성 65화면·prod 리허설 0015 | 2026-10-07 | PASS (12/12, round 2: E18 시험 데이터) | [test/impl/26th/result.md](test/impl/26th/result.md) |

## 트러블슈팅 (실제로 겪은 것)

| 증상 | 원인 | 해결 |
|---|---|---|
| 기동 시 `port is already allocated` | 같은 호스트의 다른 프로젝트나 macOS launchd 소켓이 포트를 점유. 사용자 권한 `lsof`에는 안 보일 수 있다 | `nc -z 127.0.0.1 <port>`로 확인하고 `.env.*`의 포트를 바꾼다 |
| compose가 `pids_limit`과 `deploy.resources.limits.pids` 충돌로 거부 | Compose v5는 둘 다 지정하면 오류 | pids는 `deploy.resources.limits.pids` 하나만 쓴다 |
| Addon 화면 응답 없음(nginx) | read_only + root 소유 tmpfs 때문에 비루트 nginx가 파일을 못 씀 | tmpfs에 `uid=101,gid=101` 지정(생성기에 반영됨) |
| api 재생성 후 설치 에이전트 호출이 DNS 실패 | 새 api 컨테이너에 에이전트 전용 네트워크 연결이 없음 | runtime이 10초 주기와 api 기동 시 재연결한다(자동) |
| 설치 직후 `/a/{id}/…`가 콘솔(405)로 감 | Traefik 라우터 반영 지연 | 8단계(노출)가 게이트웨이 경로를 확인한 뒤 완료한다(자동) |
| prod 첫 기동에 워커 일부가 서명 키 오류 | 워커 2개가 동시에 키 파일 생성 | 임시 파일 작성 후 `os.link`로 원자적 게시(반영됨) |
| `make test`가 수 분간 멈춘 듯 보임 | 시험 컨테이너에 수집기·Traefik이 없는데 OTLP 내보내기·노출 확인을 재시도 | conftest가 `OTEL_*`·`GATEWAY_INTERNAL_URL`을 끈다(반영됨) |
| web 이미지 빌드에서 pnpm이 빌드 스크립트 실행 거부 | pnpm 12 빌드 스크립트 승인제 | `web/pnpm-workspace.yaml`의 `allowBuilds: {esbuild: true}` |
| 설치 중 api 가 재시작되며 진행이 멈춤(local) | uvicorn --reload 가 /app/data(설치 산출물)까지 감시 | `--reload-dir app --reload-dir sdk --reload-dir plaza`(반영됨) |
| 에이전트 시크릿을 compose secrets 로 못 넣음 | Compose 5.5 는 read_only 서비스에 file 시크릿만 허용, DinD 에는 호스트 경로가 없음 | 에이전트가 자기 키로 `/api/agent/secrets` 에서 pull(SDK `ctx.secret`, 반영됨) |
| 등록 3단계가 늘 '미스캔' 경고 | 취약점 DB(약 1.4GB)를 이미지에 넣지 않음 | `make trivy-db` 로 trivycache 볼륨에 받는다 |
| 관측 화면 트레이스 목록이 빔(pytest 는 통과) | FastAPI 0.142 가 자체 공급자로 요청 스팬을 만들어 우리 스팬의 부모가 외부에 있음 | 부모가 저장소에 없는 스팬을 '로컬 루트'로 묶음(반영됨) |
| prod 리허설 스모크가 404(새 API 없음) | `make prod-all` 은 빌드하지 않고 예전 prod 이미지로 기동 | `make prod-build` 후 `make db-migrate ENV=prod` |
| 소형 로컬 모델이 목록 요청을 생성(create)으로 계획 | few-shot 예시 편향 | 계획 프롬프트에 list 예시 추가(반영됨). 남는 변동은 평가 묶음(`/evals`)으로 회귀를 잡는다 |
| Bifrost 가 호스트 Ollama 호출에 502 `connection to private IP … is not allowed` | Bifrost 기본 SSRF 차단 | `ops/bifrost/config.json` 의 ollama `network_config.allow_private_network: true`(반영됨) |
| Assistant 답변이 한 번에 몰려 옴 | pydantic-ai `stream_text` 기본 0.1초 묶음 | `debounce_by=None`(반영됨) |
| 상태 배지 글자가 흐림(접근성 대비 2.2:1) | 채움용 상태색을 글자에도 씀 | 글자용 토큰 `--ok-text`·`--warn-text`·`--danger-text`·`--on-primary`(반영됨) |
| 위젯 E2E 에서 브라우저가 위젯 스크립트를 막음 | Chromium Local Network Access — 가짜 고객 사이트(공개 취급)가 루프백(127.0.0.1)을 부름 | 위젯 E2E(`web/e2e/widget.e2e.mjs`)만 LNA 검사 끔. 실제 배포는 공개 주소라 해당 없음 |
| 카카오 동기 블록이 "답변이 길어지고 있어요" | 카카오 스킬 5초 제한, 오케스트레이션(계획 LLM)은 수 초 | 오픈빌더 블록에서 콜백 사용, 또는 채널 에이전트 범위를 좁혀 LLM 단독으로 |
| 콘솔 E2E E18 에서 라이선스 검증 뒤 '등록' 버튼이 켜져 실패 | 넘긴 라이선스가 카탈로그 현재 버전을 덮어 검증 6개가 모두 통과(정상 동작) | `E2E_VARS.lic` 에 현재 버전을 덮지 않는 키(예: ^0.x)를 넘긴다 |
| 콘솔 E2E 일부가 데이터 없음으로 실패 | 차수별 라이브 시험 데이터(에이전트·시크릿·서버)가 로컬 DB 에서 사라짐 | 그 차수 라이브 스크립트의 적재 부분을 다시 실행한 뒤 E2E |

## 남은 범위·알려진 한계

계획표 기준 BLOCKED는 없다. 아래는 범위 밖이거나 가정으로 기록한 항목이다([.docs/IMPLEMENT_PLAN.md](.docs/IMPLEMENT_PLAN.md) 가정 표).

- **다음 이터레이션(계획표 Epic 26–29, TODO)** — 아래 가정 중 4건을 구현하기로 함: 경로 B OCI 아티팩트·사설 미러 설치(D6-03),
  OIDC SSO 로그인, 메모리 LLM 자동 추출(D3-05, 사용자 승인 후 저장), 기본 에이전트(Orchestrator·Assistant) 컨테이너 분리. 다음 `wds-implement` 실행에서 순서 확정.
- **P2(Epic 19·25) 완료** — 알림·상태, 채널·임베드. 실 Slack 앱·Telegram 봇·카카오 채널 연결은 계정·공개 HTTPS 가 필요한 사용자 수행 항목(MANUAL, [25th 절차](test/impl/25th/scenario.md)).
- **P1 추가 범위(Epic 20–24) 완료** — Bifrost·예산 로컬 강제, pydantic-ai Assistant, Stripe·Polar·Lago 어댑터, 조직·부서 배치, WCAG 2.2 AA·MCP 두 핸드셰이크.
  실 결제대행 테스트 모드 키로 하는 결제 확인은 사용자 수행 항목(MANUAL, [22nd 절차](test/impl/22nd/scenario.md)).
- **P1 가정·부분 구현** — 결제는 호스티드 일회성 결제만(구독 갱신·환불·정산·세금 X12 없음), OIDC SSO 미포함(게이트웨이 인증은 API 키·JWT),
  키리스(Fulcio)·OCI 푸시 서명 미구현, Temporal 대신 LangGraph 체크포인터, Langfuse·Opik 대신 자체 관측 UI,
  STT/TTS 는 Addon(X03) 연계 대상. 세부 근거는 계획표 가정 표.
- **P0 중 부분 구현** — 경로 B의 OCI 아티팩트·사설 미러 미구현. 기본 에이전트(Orchestrator·Assistant)는 플랫폼 프로세스 안의 모듈이다.
  gVisor(runsc)가 없는 호스트에서는 runc로 실행하고 경고를 남긴다. 멀티테넌시(X09)는 범위 밖이다.
- **대체 구현** — 채팅 UI는 assistant-ui 대신 AG-UI 이벤트를 직접 소비하는 경량 컴포넌트다. 계약 시험은 MCP Inspector CLI 대신 공식 python-sdk 클라이언트를 쓴다.
- **알려진 동작** — A2A Data Part에서 정수가 실수로 바뀐다(protobuf Struct). 소형 로컬 모델은 계획·요약 품질이 들쭉날쭉하므로
  규칙 폴백·`registry_miss` 안내·"도구 미실행" 정직 응답으로 보완한다.
