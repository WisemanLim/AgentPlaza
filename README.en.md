# AgentPlaza (wise-agentplaza)

A multi-agent platform that puts local LLMs and public AI behind one gateway. It ships an Orchestrator and an AI Assistant,
and lets you pick zip-packaged (agent.zip) add-on agents from a marketplace and run them with docker compose —
**standalone (M1), federated (M2), or ready to use (M3)**.

> Requirements [PRD.md](PRD.md) · implementation plan [.docs/IMPLEMENT_PLAN.md](.docs/IMPLEMENT_PLAN.md) · compliance [COMPLIANCE.md](COMPLIANCE.md) · 한국어 [README.md](README.md)
>
> Status: **the whole PRD scope is implemented — P0 Epics 1–11 · P1 Epics 12–18·20–24 · P2 Epics 19·25** (2026-10-07) — regression 284 passed · console E2E (P0 4 + P1·P2 12 + widget 1) · accessibility (WCAG 2.2 AA) 65 views with 0 violations · prod (PostgreSQL, migration 0015) rehearsal PASS — full regression re-verified in round 26th. Next iteration: plan Epics 26–29 (TODO)

## Architecture

```
browser ─▶ Traefik :8090 (web) ─┬─ /                                     → web  (React 19 console, non-root nginx)
                               ├─ /api /v1 /mcp /registry /widget /.well-known
                               │  /a/{id}/a2a · /a/{id}/.well-known/…     → api
                               └─ /a/{id}/api/… · /a/{id}/health         → {id}-be  (forwardAuth: api checks the user and injects the agent key)
        Traefik :8092 (apps) ── /a/{id}/ui/…                            → {id}-fe  (separate origin for add-on UIs)

api            platform — auth·RBAC·API keys·audit ledger · LLM gateway (/v1, embeddings·rerank·vision) · Orchestrator (LangGraph checkpointer)
               · Assistant (AG-UI SSE, resumable) · 8-stage registration (cosign·syft·trivy supply-chain gate)
               · market (purchase·licenses·publishers·registry API) · MCP/A2A gateway · secret store·policy·guardrails
               · knowledge (RAG)·memory · observability·evals · OTel
runtime        builds, starts and stops agents (only service with docker.sock) · compose lint · per-agent network · reconnect every 10 s · volume backup·restore
bifrost        LLM provider gateway engine (maximhq/bifrost v2.2.6, Apache-2.0) — no published port, the only holder of public keys; sits behind the api's alias·data-class·budget policy
otel-collector · redis (Valkey, rate limits) · db (prod only: pgvector/pgvector:pg17) · volumes trivycache (vulnerability DB)·bifrostdata
optional       compose-optional/ — vllm·llama-server (high-performance serving) · tei (cross-encoder rerank) · cli-bridge (CLI agents NDJSON·ACP) · gpu · mailpit (alert mail testing)
agents         compose project <PLAZA_PROJECT>-agent-<id>, services <id>-be (+ <id>-fe)
LLM            api → bifrost → host Ollama (host.docker.internal:11434)·public providers (only with keys) · direct Ollama call if Bifrost is down · registered OpenAI-compatible servers (vLLM etc.)
```

| | local | prod |
|---|---|---|
| Console and gateway (Traefik web) | http://127.0.0.1:8090 | http://127.0.0.1:8091 |
| Add-on UI origin (Traefik apps) | http://127.0.0.1:8092 | http://127.0.0.1:8093 |
| api direct (development, diagnostics) | http://127.0.0.1:8010 | http://127.0.0.1:8011 |
| Valkey | 127.0.0.1:6390 | 127.0.0.1:6391 |
| DB | SQLite `/app/data/app.db` | PostgreSQL 17 + pgvector (`db` service, no published port) |

Everything runs through **docker compose**. local uses `docker-compose.yml` + `docker-compose.local.yml` + `.env.local` (dev stage, source bind mount);
prod uses `docker-compose.yml` + `docker-compose.prod.yml` + `.env.prod` (runtime stage). `compose/*.yml` is included in both modes.

## Quick start

Requirements: Docker with Compose v2 and GNU Make. Optional: host Ollama with the default models `granite4.1:3b` (chat), `qwen3:8b` (planning), `bge-m3` (embeddings) and `qwen2.5vl:7b` (vision).
Without Ollama, local aliases fall back to the deterministic `mock/echo` model (the prod catalog has no mock).

```bash
make preflight               # check Docker, Compose and env files
make local-all               # start api·runtime·traefik·web·otel-collector·valkey (builds images if missing)
open http://127.0.0.1:8090   # first run opens the setup wizard: admin → LLM connection → models → default agents → done
make trivy-db                # (optional) download the vulnerability DB — without it stage 3 warns "unscanned"
make test                    # platform regression (pytest)
make local-stop
```

prod rehearsal (local Docker):

```bash
cp .env.example .env.prod    # only if missing; replace CHANGE_ME (DB_PASSWORD·JWT_SECRET·RUNTIME_TOKEN) with secrets
make prod-build              # rebuild images and start (prod-all only starts existing images)
make db-migrate ENV=prod     # prod runs with AUTO_MIGRATE=false
make db-ping ENV=prod
make prod-stop
```

## Features and requirements

| Epic | Feature | FR | Main paths |
|---|---|---|---|
| 1 | Accounts·RBAC·API keys·audit ledger (hash chain, append-only trigger on PG) | D9-01/02/03/07, D10-06 | `/api/auth/*` `/api/users` `/api/api-keys` `/api/audit` |
| 2 | agent.yaml spec·9 templates·SDK·scaffolding·derive/standalone export | D4-01/02/03/04/07, D8-01 | `/api/agents/scaffold` `make plaza` |
| 3 | LLM gateway (aliases·fallback·data classes L0–L3·metering)·model catalog·license gate | D1-01/03/05/06 | `/v1/chat/completions` `/api/llm/*` |
| 4 | Orchestrator — intent·plan (LLM + rules)·registry routing·sequential/parallel·tool execution·human approval | D2-01/02/03/04/06 | `/api/orchestrate` `/api/approvals` |
| 5 | AI Assistant — AG-UI SSE·sessions·tool/approval cards·scoped chat·retention purge | D3-01/02/03 | `/api/chat/stream` `/api/sessions` |
| 6 | 8-stage registration (upload·structure check·build·register·start/contract test·expose)·versions·rollback·delete within 60 s | D5-01/02/05/06/07 | `/api/agents/upload` `/api/agents/installs/*` |
| 7 | runtime service·compose lint·per-agent isolated network·Traefik·GPU overlay | D8-02/03/04/05 | `runtime/` `compose-optional/` |
| 8 | MCP (2026-07-28·2025-11-25)·A2A 1.0 (signed cards)·remote linking·rug-pull detection | D7-01/02/03/04, D6-04 | `/mcp/{id}` `/a/{id}/a2a` `/api/agents/link` |
| 9 | Market — 3-axis taxonomy·search·path A (catalog)·B (zip upload·zip URL·Git)·C (remote) | D6-01/02/03/04 | `/api/market/*` `/api/agents/install-url` `/api/agents/install-git` |
| 10 | Console dashboard·settings·profile·setup wizard·OTel GenAI spans | D10-01/02/03 | `/api/console/dashboard` `/api/setup/*` |
| 11 | Web console (React 19) — login·wizard·dashboard·chat·agents·market·approvals·LLM·organization·settings·audit·add-on iframe | D3-01, D6-01, D10-01, D5-07 | http://127.0.0.1:8090 |
| 12 | Supply-chain trust — cosign signatures·SBOM (syft)·vulnerabilities (trivy)·license grades G1–G5·egress policy | D4-06, D5-03/04 | `/api/trust/*` `make publish` `make trivy-db` |
| 13 | Governance — secret store (AES-GCM, pull)·policy engine·guardrails (injection·Korean PII)·reviewer gate·rate limits·tool RBAC | D9-04/05/06, D2-05, D7-07 | `/api/policy` `/api/secrets` `/api/guardrails/check` |
| 14 | Durability·operations — checkpoint resume·retries·compensation·pre-upgrade backup/rollback·backups·offline bundle | D2-07, D8-06/07 | `/api/agents/{id}/backup·restore` `make backup` `make offline-bundle` |
| 15 | Assistant extensions — attachments·vision·memory·knowledge collections (RAG)·embeddings·rerank | D3-04/05/06, D1-07 | `/api/kb/*` `/api/me/memories` `/v1/embeddings` `/v1/rerank` |
| 16 | LLM·protocol extensions — OpenAI-compatible servers·CLI bridge·agents as models·OpenAPI→tools·AG-UI resume·ACP | D1-02/04, D7-05/06 | `/api/llm/servers` `/api/chat/streams/{id}` |
| 17 | Observability·evals — traces·usage·cost (own UI)·eval suites·regressions·A/B·`plaza test` | D10-04/05, D4-05 | `/api/obs/*` `/api/evals/*` |
| 18 | Market commerce·publishers — publish·review·mock payment·Ed25519 licenses·seats·updates·MCP-registry-compatible API·bundles | D6-05/06/07 | `/api/market/*` `/api/licenses` `/registry/v0.1/*` |
| 20 | LLM gateway engine switched to Bifrost · force local at 80% of the monthly budget (J05) | D1-01/03/05/06 (Q1·Q15) | `bifrost` service · `/api/llm/budget` |
| 21 | Assistant agent on pydantic-ai (gateway policy kept) | D3-01/02/03 (Q2) | `app/assistant/agent.py` |
| 22 | Payment adapters Stripe·Polar·Lago (hosted checkout + signed webhooks) | D6-05 (Q6) | `/api/market/purchase/{id}` `/api/market/payments/{adapter}/webhook` |
| 23 | Organization/group (department) deployment (deploy_scope) · org screen K02 · adoption flow FL-07 | part of X09, D6-02 (Q7·Q12) | `/api/orgs/*` `/api/agents/{id}/scope` · http://127.0.0.1:8090/orgs |
| 24 | Quality bar — KWCAG 2.2 / WCAG 2.2 AA (axe) · MCP contract on both handshakes (discover·initialize) | NFR-U4, NFR-P1 (Q8·Q9) | `web/e2e/a11y.e2e.mjs` · install stage 7·`plaza test` |
| 19 | Alerts·status (P2) — health dashboard·state-change alerts·notification center B03·Slack/Telegram/mail delivery·usage reports | D10-07 | `/api/status` `/api/notifications/*` · http://127.0.0.1:8090/status |
| 25 | Channels·embed (P2) — web widget (iframe+postMessage)·Slack·Telegram·Kakao i Open Builder → Assistant · settings screen C07 | D3-07 | `/api/channels/*` `/widget/{id}.js` · http://127.0.0.1:8090/settings/channels |

## API

Authenticate with `Authorization: Bearer <JWT | ap_sk_…>` or `x-api-key: ap_sk_…`. Only `/health`, Agent Cards, JWKS, login and setup
are open without auth (NFR-S5). The full schema is at `http://127.0.0.1:8010/docs` (OpenAPI).

| Group | Endpoints |
|---|---|
| Setup | `GET /api/setup/status` `GET /api/setup/progress` `POST /api/setup/admin` `GET·POST /api/setup/llm` `POST /api/setup/models/pull` `POST /api/setup/agents` `POST /api/setup/skip` `POST /api/setup/complete` |
| Auth | `POST /api/auth/login` `POST /api/auth/logout` `POST /api/auth/token` `POST /api/auth/password` `GET /api/auth/me` `GET /api/auth/forward` (Traefik forwardAuth) |
| Organization·ledger | `GET·POST /api/orgs` `GET·DELETE /api/orgs/{id}` `PUT /api/orgs/{id}/members` `DELETE /api/orgs/{id}/members/{user}` `POST /api/orgs/{id}/groups` `DELETE /api/orgs/{id}/groups/{gid}` `PUT·DELETE /api/orgs/{id}/groups/{gid}/members[/{user}]` · `GET·PUT·DELETE /api/agents/{id}/scope` (deploy scope org·group·user) · `GET·POST /api/users` `PATCH /api/users/{id}` `GET·POST /api/api-keys` `DELETE /api/api-keys/{id}` `GET /api/audit` `GET /api/audit/verify` |
| LLM | `POST /v1/chat/completions` (OpenAI-compatible, streaming) `GET /v1/models` `GET·POST /api/llm/models` `PATCH /api/llm/models/{id}` `GET /api/llm/routes` `PUT /api/llm/routes/{alias}` `GET /api/llm/providers` (Bifrost status·direct fallbacks) `GET /api/llm/usage` `GET /api/llm/budget` `PUT /api/llm/budget` (supervisor, monthly budget·force-local threshold) |
| Chat | `POST /api/chat/stream` (SSE) `GET·POST /api/sessions` `GET·PATCH·DELETE /api/sessions/{id}` `GET /api/sessions/{id}/export` |
| Orchestration | `POST /api/orchestrate` `GET /api/tasks/{id}` `GET /api/approvals` `POST /api/approvals/{id}/approve` `POST /api/approvals/{id}/reject` |
| Agents | `GET /api/agents` `GET /api/agents/templates` `POST /api/agents/upload·install-url·install-git·link·scaffold` `GET /api/agents/installs[/{id}]` `GET·PATCH·DELETE /api/agents/{id}` `POST /api/agents/{id}/export·export-standalone·rollback·revalidate` `GET /api/agents/{id}/ui·runtime·install-status` |
| Market | `GET /api/market/categories` `GET /api/market/listings[/{id}]` `POST /api/market/install/{id}` |
| Protocols | `/mcp/{id}` (Streamable HTTP, including `/mcp/orchestrator`) `GET /a/{id}/.well-known/agent-card.json` `POST /a/{id}/a2a` `GET /a/{id}/mcp/server.json` `GET /.well-known/jwks.json` |
| Supply chain | `GET·POST /api/trust/keys` `DELETE /api/trust/keys/{kid}` `GET·PUT /api/trust/policy` `GET /api/agents/{id}/sbom` |
| Protocol extensions | `GET /v1/models` (aliases + `agent/<id>`) · `POST /v1/chat/completions` model=`agent/<id>` · `GET /api/llm/servers` `PUT·DELETE /api/llm/servers/{name}` `GET /api/llm/servers/{name}/models` · `POST /api/agents/link` kind=`openapi` · `GET /api/chat/streams/{id}?after=` (Last-Event-ID resume) |
| Observability·evals | `GET /api/obs/usage?days=` (calls·tokens·cost·p50/p95 by model·agent·user) · `GET /api/obs/traces?q=` `GET /api/obs/traces/{trace_id}` (span waterfall) · `GET·POST /api/evals/suites` `DELETE /api/evals/suites/{id}` `POST /api/evals/suites/{id}/runs` `GET /api/evals/runs/{id}` (per-case verdicts·regressions) · `POST /api/evals/compare` (alias A/B) |
| Market commerce·publishers | `GET·POST /api/market/publishers` `PATCH /api/market/publishers/{id}` `POST /api/market/publishers/{id}/keys` (rotation) · `POST /api/market/releases` (zip + publisher → automatic checks) `GET /api/market/releases?status=` `POST /api/market/releases/{id}/approve·reject` · `PATCH /api/market/listings/{id}/ops` (featured·validated·hidden) · `POST /api/market/purchase/{id}` (mock = issued at once 201 · Stripe·Polar·Lago = checkout URL 202) `GET /api/market/purchases[/{id}[/receipt]]` `POST /api/market/payments/{stripe|polar|lago}/webhook` (provider signature = auth) · `POST /api/licenses/verify` `GET·POST /api/licenses` `DELETE /api/licenses/{id}[/seats/{holder}]` · `GET·POST·DELETE /api/market/license-issuers` · `GET /api/market/instance` |
| Updates·registry | `GET /api/market/installed` `POST /api/market/updates/check` `POST /api/market/updates/{agent}` (consent) `PUT /api/market/auto-update/{agent}` · `GET /api/market/registries` `PUT·DELETE /api/market/registries/{name}` `POST /api/market/registries/{name}/sync` · `GET·PUT /api/market/registry-exposure` · `GET·POST /api/market/bundle` (offline bundle) · MCP-registry compatible `GET /registry/v0.1/servers?cursor&limit&search&updated_since` `GET /registry/v0.1/servers/{name}/versions[/{version}]` `GET /registry/v0.1/artifacts/{id}/{version}.zip` (paid = `X-Plaza-License`) |
| Knowledge·personal | `POST /v1/embeddings` `POST /v1/rerank` `GET·POST /api/kb/collections` `DELETE /api/kb/collections/{id}` `GET·POST /api/kb/collections/{id}/documents` `POST /api/kb/search` `GET·POST·DELETE /api/me/memories` `PUT /api/me/memory-settings` `POST·GET /api/files` `GET /api/files/{id}/content` `DELETE /api/files/{id}` · chat `attachments`·`knowledge` |
| Operations | `POST /api/agents/{id}/backup` `GET /api/agents/{id}/backups` `POST /api/agents/{id}/restore` `POST /api/admin/backup` (supervisor) |
| Governance | `GET·PUT /api/policy` `GET /api/secrets` `PUT·DELETE /api/secrets/{scope}/{name}` `GET /api/agent/secrets` (agent key) `POST /api/guardrails/check` `POST /api/agents/{id}/rotate-key` |
| Console | `GET /api/console/dashboard` `GET·PUT /api/settings` `GET·PATCH /api/me/profile` `POST /api/admin/retention/run` |
| Alerts·status | `GET /api/status` (health: components·LLM·agents) `POST /api/status/check` · `GET /api/notifications[?unread=true]` `GET /api/notifications/unread-count` `POST /api/notifications/read` · `GET /api/notifications/channels` `PUT /api/notifications/channels/{slack|telegram|email}` `POST /api/notifications/channels/{name}/test` · `GET /api/status/report?days=` `POST /api/status/report/send` `PUT /api/status/report/settings` |
| Channels·embed | `GET·POST /api/channels` `PATCH·DELETE /api/channels/{id}` `POST /api/channels/{id}/rotate` · `POST /api/channels/{id}/slack/events` (signature v0) `POST /api/channels/{id}/telegram/webhook` (secret token) `POST /api/channels/{id}/kakao/skill` (X-Plaza-Channel-Token) · web widget `GET /widget/{id}.js` (embed) `GET /widget/{id}` `POST /api/widget/{id}/session` `POST /api/widget/{id}/chat` (SSE) |

### Examples (real responses from the local stack, 2026-10-07)

```bash
$ curl -s http://127.0.0.1:8090/health
{"status":"ok","env":"local","db":{"engine":"sqlite","status":"ok"}}

# LLM gateway — L3 (confidential) is routed to local models only
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

# Orchestration — a real LLM (qwen3:8b) plans, then the installed board agent runs
$ curl -s http://127.0.0.1:8090/api/orchestrate -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
    -d '{"message":"게시판에 \"README 예시\" 라는 제목으로 글을 등록해줘"}'
{"task_id":"828188c9-…","state":"succeeded",
 "plan":{"steps":[{"id":"s1","agent":"board","capability":"manage","args":{"action":"create","title":"README 예시"},"depends_on":[]}],
         "pattern":"sequential","source":"llm","model":"ollama/qwen3:8b","misses":[]},
 "results":{"s1":{"ok":true,"result":{"id":4},"latency_ms":12,"agent":"board","capability":"manage",…}},
 "answer":"…", "events":[…], "session_id":"…"}

# MCP (2026-07-28) — Cursor, Claude Desktop and similar clients connect to /mcp/{id} with an API key
$ curl -s http://127.0.0.1:8090/mcp/board -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
    -H 'accept: application/json, text/event-stream' -H 'mcp-protocol-version: 2026-07-28' -H 'mcp-method: tools/list' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
→ tools: ["manage"]

# A2A — signed Agent Cards are public; server.json and business APIs require auth
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8090/a/board/.well-known/agent-card.json   # 200 (with signatures)
$ curl -s http://127.0.0.1:8090/.well-known/jwks.json      # {"keys":[{"kty":"OKP","crv":"Ed25519","alg":"EdDSA","kid":"plaza-…",…}]}
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8090/a/board/mcp/server.json          # 401
```

## Building agents (plaza CLI)

```bash
make plaza ARGS="init inventory --template service --out agents/inventory"
#   templates: app service rag tool-proxy reviewer execution hitl memory federation (--url remote Card/MCP)
make plaza ARGS="validate agents/inventory --strict"              # JSON Schema + semantic rules + declared vs implemented handlers
make plaza ARGS="pack agents/inventory --out inventory-0.1.0.zip" # deterministic zip with checksums.txt
make plaza ARGS="export inventory-0.1.0.zip --derive inventory-hr --standalone --out dist"
make plaza ARGS="convert-v1 Board-meta.json"                      # v1 meta.json → agent.yaml
make plaza ARGS="market-build --out market"                       # curated catalog (market/catalog.json + sha256)
make plaza ARGS="verify-coverage"                                 # trace P0 FRs ↔ plan ↔ tests
make plaza ARGS="test agents/inventory --report out/inventory"     # structure·syntax·SQL·local boot·REST/MCP/A2A contracts·evals/*.yaml → result.md/json
PLAZA_TOKEN=… make plaza ARGS="publish agents/inventory --key keys/acme.key --registry http://127.0.0.1:8090 --publisher acme --listing listing.json"  # signed package → market release (D6-06)
```

A generated agent runs on its own (M1): `cp .env.example .env && docker compose --profile standalone up -d --build` opens
`/health`, `/api/capabilities`, `/api/invoke/{verb}`, `/mcp`, `/.well-known/agent-card.json` and `/a2a`.
When installed on the platform, its compose file is regenerated as federated: no published ports, reachable only via Traefik paths and its own network (M2·M3).

## Environment

| Variable | local | prod |
|----------|-------|------|
| `APP_ENV` | `local` | `prod` |
| `DB_ENGINE` | `sqlite` | `postgres` |
| `DATABASE_URL` | SQLite file | connection string to the `db` service |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | — | RDBMS account (CHANGE_ME → injected) |
| `API_PORT`, `BIND_HOST` | `8010`, `127.0.0.1` | `8011`, `127.0.0.1` |
| `REDIS_PORT` (Valkey) | `6390` | `6391` |
| `DB_IMAGE` | — | `pgvector/pgvector:pg17` |
| `JWT_SECRET` | fixed local-only value | CHANGE_ME → injected |
| `AUTO_MIGRATE` | `true` (alembic upgrade on start) | `false` (`make db-migrate ENV=prod`) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` (host Ollama) | same or a GPU server |
| `LLM_LOCAL_CHAT_MODEL` / `LLM_LOCAL_REASONING_MODEL` | `granite4.1:3b` / `qwen3:8b` | same |
| `PUBLIC_MODELS`, `OPENAI_API_KEY`·`ANTHROPIC_API_KEY`·`GEMINI_API_KEY` | empty (local only) | inject if needed — only the gateway (api) holds them |
| `PLAZA_PROJECT` | `wise-agentplaza-local` | `wise-agentplaza-prod` (agent project/network prefix, Traefik constraint) |
| `GATEWAY_PORT` (Traefik web) | `8090` | `8091` |
| `APPS_PORT` · `PUBLIC_APPS_URL` (add-on UI origin) | `8092` · `http://127.0.0.1:8092` | `8093` · `http://127.0.0.1:8093` |
| `RUNTIME_DRIVER` / `RUNTIME_URL` / `RUNTIME_TOKEN` | `remote` / `http://runtime:9000` / fixed local value | same / CHANGE_ME |
| `HITL_ALLOW_SELF_APPROVAL` | `true` (single developer) | `false` (four-eyes) |
| `PUBLIC_BASE_URL` (external URL in Agent Cards·server.json) | `http://127.0.0.1:8090` | `http://127.0.0.1:8091` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318` | same (pick a backend via collector exporters) |
| `GATEWAY_INTERNAL_URL` (post-install exposure check) | `http://traefik` | same |
| `LLM_LOCAL_EMBED_MODEL` / `LLM_LOCAL_VISION_MODEL` | `bge-m3` / `qwen2.5vl:7b` | same |
| `TEI_RERANK_URL` (optional cross-encoder rerank) | empty (embedding cosine) | if needed |
| `BIFROST_URL` (provider gateway engine, PRD Q1 — public keys live only in the bifrost service) | `http://bifrost:8080` | `http://bifrost:8080` |
| `PAYMENT_ADAPTER` (payment adapter, D6-05) | `mock` (no real payment) | `none` (key entry only) — `stripe`·`polar`·`lago` only when the keys below are set |
| `STRIPE_SECRET_KEY`·`STRIPE_WEBHOOK_SECRET` · `POLAR_ACCESS_TOKEN`·`POLAR_WEBHOOK_SECRET`·`POLAR_PRODUCT_ID`·`POLAR_API_URL` · `LAGO_API_URL`·`LAGO_API_KEY`·`LAGO_WEBHOOK_HMAC_KEY`·`LAGO_ADD_ON_CODE` | empty (test-mode keys only, Polar sandbox URL) | inject only for the adapter in use |
| `MARKET_SYNC_INTERVAL` (remote registry sync·auto-update period, seconds, 0=off) | `3600` | `3600` |
| `STATUS_CHECK_INTERVAL` (status watch·alert dispatch·weekly report period, seconds, 0=off) | `60` | `60` |
| `REDIS_URL` (rate-limit counters, Valkey) | `redis://redis:6379/0` | same |
| `SECRETS_MASTER_KEY` (secret encryption key, base64 32 bytes) | empty (derived from JWT_SECRET, local only) | CHANGE_ME → injected |

> Secrets live in `.env.prod`, which is never committed (`.gitignore`). `.env.local` holds only fixed local values and is committed (CI `make test`).

## Make targets

| Target | Description |
|--------|-------------|
| `make <mode>-all` · `-build` · `-logs [SVC=]` · `-stop` · `-restart [SVC=]` · `-ps` | Stack lifecycle (`mode` = local \| prod) |
| `make test` | Platform regression (pytest in the local dev container) |
| `make e2e` | Console E2E (Playwright container). Needs the local stack running and `E2E_EMAIL`·`E2E_PASSWORD` (P1 screens: `E2E_TOKEN`·`E2E_SPEC=p1`, WCAG 2.2 AA accessibility: `E2E_SPEC=a11y`, web widget: `E2E_SPEC=widget`) |
| `make plaza ARGS="…"` | plaza CLI |
| `make publish SRC=… KEY=… [OUT=]` | Signed package (zip·checksums·sbom.json·signature.sig) |
| `make backup [ENV=]` | Back up the platform DB and installed agent volumes → data/backups/ (required before upgrades) |
| `make offline-bundle [ENV=] [IMAGES=]` · `make offline-load DIR=…` | Build and load an air-gapped bundle (images, catalog, vulnerability DB, model list, sha256 checked) |
| `make trivy-db [ENV=]` | Download or refresh the vulnerability DB (trivycache volume, about 1.4GB) — needed for the stage 3 scan |
| `make shell [ENV=]` | Shell into the app container |
| `make db-ping` · `db-shell` · `db-migrate` · `db-seed [ENV=]` | DB check·client·migrations·seed |
| `make db-reset` · `db-fresh` | Reset local SQLite (+ seed); refused for prod |
| `make deploy` | Roll out prod (refused while CHANGE_ME remains) |
| `make preflight` · `help` | Checks · target list |

## Security model

- **Isolation** — uploaded code runs only in containers (in-process mode is rejected at stage 2). Only runtime (and Traefik, read-only) mounts docker.sock.
  Before start, the compose lint rejects privileged, host network/PID/IPC, cap_add, device or GPU reservations, host bind mounts, docker.sock and published ports for federated agents,
  and requires `cap_drop: [ALL]`, `read_only`, `no-new-privileges` and cpus·memory·pids limits.
- **Network** — each agent gets its own network with only api and traefik attached, so agents cannot reach each other. Without declared egress the network is `--internal` (no outbound traffic).
- **Keys** — only api holds public LLM keys. An agent's internal key is derived as HMAC(secret, `agent:{id}`) and never stored. The gateway key an agent uses is issued at install time, with the plaintext only in workdir/.env (0600).
- **Path auth** — for `/a/{id}/…`, Traefik forwardAuth lets api check the user, key scope and active state, then inject the agent key.
  Add-on UIs load from a separate origin (apps), and the console sends CSP `frame-ancestors 'none'; frame-src 'self' <apps>`.
- **Data classes** — a request without the header counts as L2. L2 and above use local models only, and this rule wins over fallback. Denials are written to the ledger.
- **Approval** — a `humanApprovalRequired` capability cannot be bypassed through MCP, A2A or REST (DP8). It is handled by an approval card in chat or the approvals inbox.
- **Ledger** — tool calls and admin actions are recorded in a hash chain. On PostgreSQL, triggers block UPDATE/DELETE.
- **Card signing** — Agent Cards are generated from agent.yaml and JWS-signed with the platform Ed25519 key (`/.well-known/jwks.json`).
- **Supply chain** — registration stages 3·4 check checksums·cosign signatures (trusted keys)·SBOM·vulnerabilities (Critical blocks)·license grade·egress policy. Market releases must be signed with the publisher key.
- **Secrets** — only AES-256-GCM ciphertext is stored (scope·name as AAD). Agents pull only their declared secretRefs with their own key. Logs mask known secret values.
- **Guardrails** — input injection blocking·Korean PII masking (before external LLM calls), reviewer gate for external results, gateway rate limits·per-tool RBAC.
- **Licenses·payments** — paid agents need an Ed25519-signed token (offline check: target·version range·seats·expiry·host) to install, run and update.
  Payments use hosted checkout only (Stripe·Polar·Lago pages); no card data is collected. Provider webhooks authenticate by signature (HMAC) and amounts·currency are matched against the purchase record.
- **LLM key isolation** — public LLM keys are injected only into the bifrost service (the api's values are overridden with empty). Bifrost publishes no port; only the api calls it.
- **Channels** — messenger webhooks authenticate by signature (Slack v0) or secret header (Telegram·Kakao), 401 otherwise. The web widget is an iframe on the platform origin, framed only by allowed origins (CSP frame-ancestors).
  Widget session tokens (aud=widget:<id>) cannot call platform APIs. Channel users are not platform accounts and approvals happen only in the console. Kakao callbacks only go to Kakao domains.
- **Org deploy scope** — when an agent is scoped to an organization·group·users, users outside the scope do not see it in lists, navigation, planning, MCP, A2A or add-on UIs (supervisors excepted). This is not data isolation.

## Tests

A single `test/` tree: `test/dev-env/` (one-time environment check) and `test/impl/<Nth>/` (one directory per implementation round). See `test/README.md`.

| Round | Date | Verdict | Result |
|-------|------|---------|--------|
| dev-env 1st | 2026-10-06 | PASS (11/11) | [test/dev-env/result.md](test/dev-env/result.md) |
| impl 1st — Epic 1 platform foundation | 2026-10-06 | PASS (13/13) | [test/impl/1st/result.md](test/impl/1st/result.md) |
| impl 2nd — Epic 2 agent.yaml·templates·SDK | 2026-10-06 | PASS (15/15) | [test/impl/2nd/result.md](test/impl/2nd/result.md) |
| impl 3rd — Epic 3 LLM gateway | 2026-10-06 | PASS (16/16) | [test/impl/3rd/result.md](test/impl/3rd/result.md) |
| impl 4th — Epic 4 Orchestrator | 2026-10-06 | PASS (13/13) | [test/impl/4th/result.md](test/impl/4th/result.md) |
| impl 5th — Epic 5 Assistant | 2026-10-06 | PASS (10/10) | [test/impl/5th/result.md](test/impl/5th/result.md) |
| impl 6th — Epic 6 8-stage registration | 2026-10-06 | PASS (17/17) | [test/impl/6th/result.md](test/impl/6th/result.md) |
| impl 7th — Epic 7 runtime·isolation | 2026-10-06 | PASS (15/15) | [test/impl/7th/result.md](test/impl/7th/result.md) |
| impl 8th — Epic 8 MCP·A2A | 2026-10-06 | PASS (13/13) | [test/impl/8th/result.md](test/impl/8th/result.md) |
| impl 9th — Epic 9 market, 3 paths | 2026-10-06 | PASS (11/11) | [test/impl/9th/result.md](test/impl/9th/result.md) |
| impl 10th — Epic 10 console API·OTel | 2026-10-06 | PASS (9/9) | [test/impl/10th/result.md](test/impl/10th/result.md) |
| impl 11th — Epic 11 web console | 2026-10-07 | PASS (9/9) | [test/impl/11th/result.md](test/impl/11th/result.md) |
| Completion gate — full regression + prod rehearsal | 2026-10-07 | PASS | [test/impl/final/result.md](test/impl/final/result.md) |
| impl 12th — Epic 12 supply-chain trust | 2026-10-07 | PASS (15/15) | [test/impl/12th/result.md](test/impl/12th/result.md) |
| impl 13th — Epic 13 governance·security | 2026-10-07 | PASS (20/20) | [test/impl/13th/result.md](test/impl/13th/result.md) |
| impl 14th — Epic 14 durability·operations | 2026-10-07 | PASS (12/12) | [test/impl/14th/result.md](test/impl/14th/result.md) |
| impl 15th — Epic 15 assistant extensions | 2026-10-07 | PASS (12/12) | [test/impl/15th/result.md](test/impl/15th/result.md) |
| impl 16th — Epic 16 LLM·protocol extensions | 2026-10-07 | PASS (11/11) | [test/impl/16th/result.md](test/impl/16th/result.md) |
| impl 17th — Epic 17 observability·evals | 2026-10-07 | PASS (8/8) | [test/impl/17th/result.md](test/impl/17th/result.md) |
| impl 18th — Epic 18 market commerce·publishers (+ P1 completion gate: 250 passed·prod rehearsal 0012) | 2026-10-07 | PASS (14/14) | [test/impl/18th/result.md](test/impl/18th/result.md) |
| impl 19th — Epic 24 quality bar (accessibility·MCP contract) | 2026-10-07 | PASS (7/7) | [test/impl/19th/result.md](test/impl/19th/result.md) |
| impl 20th — Epic 20 Bifrost·budget-based local forcing | 2026-10-07 | PASS (8/8) | [test/impl/20th/result.md](test/impl/20th/result.md) |
| impl 21st — Epic 21 Assistant on pydantic-ai | 2026-10-07 | PASS (6/6) | [test/impl/21st/result.md](test/impl/21st/result.md) |
| impl 22nd — Epic 22 payment adapters Stripe·Polar·Lago | 2026-10-07 | PASS (8/8, MANUAL 1: real test keys) | [test/impl/22nd/result.md](test/impl/22nd/result.md) |
| impl 23rd — Epic 23 org/department deployment (+ completion gate: 272 passed·accessibility 57 views·prod rehearsal 0013) | 2026-10-07 | PASS (7/7) | [test/impl/23rd/result.md](test/impl/23rd/result.md) · [gate](test/impl/23rd/logs/gate/result.md) |
| impl 24th — Epic 19 alerts·status (P2) | 2026-10-07 | PASS (7/7) | [test/impl/24th/result.md](test/impl/24th/result.md) |
| impl 25th — Epic 25 channels·embed (P2) (+ completion gate: 284 passed·accessibility 65 views·prod rehearsal 0015) | 2026-10-07 | PASS (9/9, MANUAL 1: real messengers) | [test/impl/25th/result.md](test/impl/25th/result.md) · [gate](test/impl/25th/logs/gate/result.md) |
| impl 26th — doc cleanup + full regression re-check (no implementation): 284 passed·console E2E 17·accessibility 65 views·prod rehearsal 0015 | 2026-10-07 | PASS (12/12, round 2: E18 test data) | [test/impl/26th/result.md](test/impl/26th/result.md) |

## Troubleshooting (issues actually hit)

| Symptom | Cause | Fix |
|---|---|---|
| `port is already allocated` on start | another project on the host or a macOS launchd socket holds the port; user-level `lsof` may not show it | check with `nc -z 127.0.0.1 <port>` and change the port in `.env.*` |
| compose rejects `pids_limit` together with `deploy.resources.limits.pids` | Compose v5 errors when both are set | use only `deploy.resources.limits.pids` |
| add-on UI does not respond (nginx) | read_only plus a root-owned tmpfs keeps non-root nginx from writing | mount tmpfs with `uid=101,gid=101` (built into the generator) |
| calls to installed agents fail DNS after api is recreated | the new api container is not attached to the per-agent networks | runtime reattaches every 10 s and when api starts (automatic) |
| `/a/{id}/…` hits the console (405) right after install | Traefik picks up the new router with a delay | stage 8 (expose) waits until the gateway path answers (automatic) |
| some prod workers fail on the signing key at first start | two workers created the key file at the same time | write a temp file and publish it atomically with `os.link` (fixed) |
| `make test` seems to hang for minutes | the test container has no collector or Traefik but retried OTLP export and exposure checks | conftest disables `OTEL_*` and `GATEWAY_INTERNAL_URL` (fixed) |
| pnpm refuses to run build scripts in the web image build | pnpm 12 requires build scripts to be approved | `allowBuilds: {esbuild: true}` in `web/pnpm-workspace.yaml` |
| Installs stall because api restarts mid-install (local) | uvicorn --reload also watched /app/data (install artifacts) | `--reload-dir app --reload-dir sdk --reload-dir plaza` (applied) |
| Agent secrets cannot be injected as compose secrets | Compose 5.5 allows only file secrets on read_only services, and DinD has no host paths | agents pull from `/api/agent/secrets` with their own key (SDK `ctx.secret`, applied) |
| Stage 3 always warns "unscanned" | the vulnerability DB (~1.4 GB) is not baked into the image | `make trivy-db` downloads it into the trivycache volume |
| Observability trace list is empty (pytest passes) | FastAPI 0.142 creates request spans with its own provider, so our spans have external parents | spans whose parent is not stored are grouped as "local roots" (applied) |
| prod rehearsal smoke returns 404 (new APIs missing) | `make prod-all` does not build and starts the old prod image | `make prod-build`, then `make db-migrate ENV=prod` |
| Small local models plan a list request as create | few-shot example bias | added a list example to the planner prompt (applied); remaining variance is caught by eval suites (`/evals`) |
| Bifrost returns 502 `connection to private IP … is not allowed` for host Ollama | Bifrost's default SSRF guard | `network_config.allow_private_network: true` for ollama in `ops/bifrost/config.json` (applied) |
| Assistant replies arrive in one burst | pydantic-ai `stream_text` debounces by 0.1 s | `debounce_by=None` (applied) |
| Status badge text is faint (contrast 2.2:1) | fill status colors were also used for text | text tokens `--ok-text`·`--warn-text`·`--danger-text`·`--on-primary` (applied) |
| The browser blocks the widget script in the widget E2E | Chromium Local Network Access — a fake customer site (treated as public) calls loopback (127.0.0.1) | LNA checks are disabled only for the widget E2E (`web/e2e/widget.e2e.mjs`); real deployments serve the widget from a public URL |
| A Kakao sync block replies "the answer is taking long" | Kakao skills have a 5 s limit, orchestration (planner LLM) takes seconds | use callback in the Open Builder block, or narrow the channel's agent scope to LLM-only |
| Console E2E E18 fails because the 'Register' button stays enabled after license verification | the license passed in covers the catalog's current version, so all six checks pass (correct behavior) | pass a key in `E2E_VARS.lic` that does not cover the current version (e.g. ^0.x) |
| Some console E2E specs fail for missing data | per-round live fixtures (agents·secrets·servers) disappeared from the local DB | rerun the seeding part of that round's live script, then the E2E |

## Remaining scope and known limits

Nothing in the plan is BLOCKED. The items below are out of scope or recorded as assumptions (assumption table in [.docs/IMPLEMENT_PLAN.md](.docs/IMPLEMENT_PLAN.md)).

- **Next iteration (plan Epics 26–29, TODO)** — four of the assumptions below are scheduled: path B OCI artifacts·private mirror install (D6-03),
  OIDC SSO login, LLM memory extraction (D3-05, saved only after user approval), default agents (Orchestrator·Assistant) as separate containers. Order is set on the next `wds-implement` run.
- **P2 (Epics 19·25) done** — alerts·status and channels·embed. Connecting a real Slack app·Telegram bot·Kakao channel needs accounts and a public HTTPS URL and is a user step (MANUAL, see the [25th procedure](test/impl/25th/scenario.md)).
- **P1 additions (Epics 20–24) done** — Bifrost·budget forcing, pydantic-ai Assistant, Stripe·Polar·Lago adapters, org/department deployment, WCAG 2.2 AA·MCP dual handshake.
  Checking payments with real provider test-mode keys is a user step (MANUAL, see the [22nd procedure](test/impl/22nd/scenario.md)).
- **P1 assumptions·partial** — payments are hosted one-off charges only (no subscription renewal·refunds·settlement·tax, X12), no OIDC SSO (gateway auth is API keys·JWT),
  no keyless (Fulcio)·OCI-push signing,
  LangGraph checkpointer instead of Temporal, own observability UI instead of Langfuse·Opik, STT/TTS left to the add-on (X03).
  Details are in the plan's assumptions table.
- **Partly implemented in P0** — path B does not support OCI artifacts or private mirrors yet. The default agents (Orchestrator, Assistant) are modules inside the platform process.
  On hosts without gVisor (runsc), agents run on runc with a warning. Multi-tenancy (X09) is out of scope.
- **Substitutes** — the chat UI is a lightweight component that consumes AG-UI events directly instead of assistant-ui. Contract tests use the official python-sdk client instead of the MCP Inspector CLI.
- **Known behavior** — integers in A2A Data Parts come back as floats (protobuf Struct). Small local models plan and summarize unevenly,
  so rule-based fallback, `registry_miss` notices and honest "no tool was run" answers cover for them.
