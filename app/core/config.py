"""wise-agentplaza — settings (env 주입: .env.local | .env.prod 는 compose env_file 로 전달)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "wise-agentplaza"
    app_env: str = "local"
    db_engine: str = "sqlite"
    database_url: str = "sqlite:////app/data/app.db"
    auto_migrate: bool = False

    # 인증 (D9-01·D9-03)
    jwt_secret: str = "CHANGE_ME"
    jwt_ttl_minutes: int = 60
    service_token_ttl_minutes: int = 15
    password_hash_iterations: int = 600_000
    login_max_failures: int = 5
    login_lock_minutes: int = 15

    # LLM 게이트웨이 (D1-05)
    llm_target_timeout: float = 20.0
    llm_fallback_budget: float = 30.0  # NFR-L1: 퍼블릭 장애 시 30초 내 로컬 폴백
    mock_slow_seconds: float = 5.0
    obs_store_spans: bool = True  # 콘솔 관측(D10-04) — 스팬을 DB 에도
    obs_retention_days: int = 7
    tei_rerank_url: str = ""  # 선택: TEI 교차 인코더(compose-optional/tei.yml). 비우면 임베딩 코사인 재정렬
    upload_file_max_mb: int = 20  # 대화 첨부(D3-04)

    # Orchestrator·HITL (D2-01~06)
    agent_key_secret: str = ""  # 비우면 jwt_secret 에서 파생. 에이전트별 내부 키 = HMAC(secret, agent:{id})
    agent_call_timeout: float = 30.0
    hitl_ttl_minutes: int = 30
    hitl_allow_self_approval: bool = False
    step_max_attempts: int = 3  # 일시 장애 재시도(D2-07): 연결 실패는 항상, 5xx·시간 초과는 idempotent capability 만
    step_retry_backoff: float = 0.5  # 지수 백오프 기준(초)
    task_stale_seconds: int = 120  # 이 시간 넘게 진행 신호가 없는 running 작업은 체크포인트에서 재개(크래시 복구)

    # Assistant·보존 (D3-02, NFR-C3 — UI L01 기본값 대화 365일)
    chat_history_turns: int = 10
    retention_chat_days: int = 365

    # 패키지·레지스트리·런타임 (D5-01~07, D8)
    data_dir: str = "/app/data"
    upload_max_mb: int = 100
    unpacked_max_mb: int = 500
    unpacked_max_files: int = 2000
    unpacked_max_ratio: int = 200
    runtime_driver: str = "none"  # none | fake | remote
    runtime_url: str = "http://runtime:9000"
    runtime_token: str = ""
    plaza_project: str = "plaza"  # compose 프로젝트 접두어(에이전트 프로젝트·네트워크 이름, Traefik 제약)
    agent_gateway_url: str = "http://api:8000/v1"  # 에이전트 컨테이너가 보는 LLM 게이트웨이
    health_timeout_seconds: float = 120.0
    gateway_internal_url: str = ""  # 노출 확인용 Traefik 내부 주소(예: http://traefik). 비우면 확인 생략

    # 거버넌스·보안 (D9-04~06, D7-07)
    secrets_master_key: str = ""  # base64 32바이트. 비우면 jwt_secret 에서 HKDF 파생(로컬 전용)
    redis_url: str = ""  # 레이트리밋 카운터(Valkey). 비우면 프로세스 메모리
    rate_limit_enabled: bool = True
    platform_internal_url: str = "http://api:8000"  # 에이전트 컨테이너가 보는 플랫폼 주소(시크릿 pull)

    # 공급망 게이트 (D5-03·D5-04): cosign·syft·trivy 는 이미지에 포함, 취약점 DB 는 볼륨(make trivy-db)
    trivy_cache_dir: str = "/var/cache/trivy"
    supply_chain_timeout: float = 300.0

    # 표준 프로토콜 (D7-01~04): 카드·server.json 에 쓰는 외부 기준 URL(Traefik 단일 진입점)
    public_base_url: str = "http://127.0.0.1:8090"
    public_apps_url: str = "http://127.0.0.1:8092"  # Addon UI 전용 오리진(Traefik apps 진입점)

    # 마켓 (D6-01~04): P0 정적 카탈로그
    market_catalog: str = "/app/market/catalog.json"
    # 마켓 상거래·업데이트 (D6-05~07): 결제 어댑터(none = 키 직접 입력만, mock = 실결제 없는 시험용) · 동기화 주기(초, 0 = 끔)
    # 알림·상태 (D10-07): 상태 감시·알림 발송 주기(초, 0 = 끔) · Telegram API 기준 URL(시험용 교체)
    status_check_interval: int = 60
    telegram_api_base: str = "https://api.telegram.org"
    slack_api_base: str = "https://slack.com/api"  # 채널(D3-07) Slack Web API(시험용 교체)
    payment_adapter: str = "none"  # none | mock | stripe | polar | lago
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_api_base: str = "https://api.stripe.com"
    polar_access_token: str = ""
    polar_webhook_secret: str = ""
    polar_product_id: str = ""  # custom price 상품(구매 금액을 amount 로 넘긴다)
    polar_api_url: str = "https://api.polar.sh"  # 시험 모드: https://sandbox-api.polar.sh
    lago_api_url: str = ""
    lago_api_key: str = ""
    lago_webhook_hmac_key: str = ""
    lago_add_on_code: str = "agentplaza_license"
    market_sync_interval: int = 3600


settings = Settings()
