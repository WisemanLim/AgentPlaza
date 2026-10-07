"""플랫폼 스키마 (PRD 12.1). SQLite(local)·PostgreSQL(prod) 공용 타입만 사용한다(NFR-O5)."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utcnow

ROLES = ("user", "admin", "supervisor")
ROLE_RANK = {r: i for i, r in enumerate(ROLES, start=1)}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    locale: Mapped[str] = mapped_column(String(8), default="ko")
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApiKey(Base):
    """외부 MCP/A2A 클라이언트용 서비스 계정 키(D9-03). 원문은 저장하지 않고 sha256 만 보관."""
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    key_prefix: Mapped[str] = mapped_column(String(16), index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(16), default="user")
    scopes: Mapped[dict] = mapped_column(JSON, default=dict)  # {"agents": ["*"] | [id, ...]}
    owner_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    """append-only 감사 원장 + 해시 체인(D9-07). 프롬프트 원문 대신 해시를 기본으로 둔다."""
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(255))
    actor_type: Mapped[str] = mapped_column(String(16))  # user | service | system
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str] = mapped_column(String(16), default="ok")
    args_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), unique=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class LlmModel(Base):
    """모델 카탈로그(D1-06). 컨텍스트·도구호출·비전·라이선스·로컬 여부는 필수 필드(NFR-L5)."""
    __tablename__ = "llm_models"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)  # "<provider>/<model_id>"
    provider: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(100))
    local: Mapped[bool] = mapped_column(Boolean)
    context: Mapped[int] = mapped_column(Integer)
    tool_call: Mapped[bool] = mapped_column(Boolean)
    vision: Mapped[bool] = mapped_column(Boolean)
    license: Mapped[str] = mapped_column(String(64))
    commercial_use: Mapped[str] = mapped_column(String(16), default="allowed")  # allowed|conditional|prohibited
    cost_in: Mapped[float] = mapped_column(default=0.0)  # USD / 1K tokens
    cost_out: Mapped[float] = mapped_column(default=0.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    kind: Mapped[str] = mapped_column(String(16), default="chat")  # chat | embedding (D1-07)


class LlmRoute(Base):
    """별칭 → 대상 모델 순서(앞이 1순위, 뒤가 폴백). 에이전트는 별칭만 안다(DP3)."""
    __tablename__ = "llm_routes"

    alias: Mapped[str] = mapped_column(String(80), primary_key=True)
    targets: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LlmUsage(Base):
    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    alias: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(120))
    agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    principal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_class: Mapped[str] = mapped_column(String(4))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    fallback_from: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str] = mapped_column(String(16), default="ok")


class Agent(Base):
    """카탈로그(D5-06): 내장·설치·원격 에이전트. manifest 는 agent.yaml 원문(JSON)."""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(24))
    version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="registered")  # registered|healthy|unhealthy|disabled|failed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(16), default="zip")  # builtin|zip|market|git|oci|url|link
    trust: Mapped[str] = mapped_column(String(16), default="community")  # official|partner|community|external
    runtime_mode: Mapped[str] = mapped_column(String(16), default="container")
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 내부 호출 기준 URL
    manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Capability(Base):
    """capability 인덱스(verb·domain). Orchestrator 라우팅의 근거(D2-02)."""
    __tablename__ = "capabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    verb: Mapped[str] = mapped_column(String(64))
    domain: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)


class Task(Base):
    """Orchestrator 실행 단위. 승인 대기 시 계획·중간 결과를 저장해 재개한다(D2-06)."""
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    principal: Mapped[str] = mapped_column(String(255))
    principal_role: Mapped[str] = mapped_column(String(16), default="user")
    message: Mapped[str] = mapped_column(Text)
    data_class: Mapped[str] = mapped_column(String(4), default="L2")  # 요청 데이터 등급(D9-05 정책 판정 기준)
    state: Mapped[str] = mapped_column(String(24), default="running")  # running|waiting_approval|succeeded|failed|canceled
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # 단계마다 갱신(D2-07)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[str] = mapped_column(String(40))
    agent_id: Mapped[str] = mapped_column(String(64))
    capability: Mapped[str] = mapped_column(String(64))
    args: Mapped[dict] = mapped_column(JSON, default=dict)
    requester: Mapped[str] = mapped_column(String(255))
    approver: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected|expired
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatSession(Base):
    """대화 세션(D3-02). 보존 기간 경과 시 파기(NFR-C3, 기본 365일)."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(200), default="새 대화")
    agent_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    folder: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_class: Mapped[str] = mapped_column(String(4), default="L2")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    kind: Mapped[str] = mapped_column(String(16), default="text")  # text | approval | error
    content: Mapped[str] = mapped_column(Text, default="")
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentVersion(Base):
    """설치된 버전 이력(D5-06). artifact 는 롤백용 원본 zip 경로."""
    __tablename__ = "agent_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(40))
    sha256: Mapped[str] = mapped_column(String(64))
    artifact: Mapped[str] = mapped_column(String(255))
    signature_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None = 미검증(서명 없음·모르는 키)
    signer: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 검증에 쓴 신뢰 키 kid
    license_grade: Mapped[str | None] = mapped_column(String(4), nullable=True)  # G1~G5 (PRD 9.7)
    sbom_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # syft CycloneDX JSON 경로
    vulns: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {status, critical, high, medium, low}
    current: Mapped[bool] = mapped_column(Boolean, default=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    installed_by: Mapped[str] = mapped_column(String(255))


class TrustedKey(Base):
    """패키지 서명 검증용 신뢰 공개키(D5-03). 퍼블리셔 키(D6-06)도 여기 둔다. 철회 키로 서명한 패키지는 거부."""
    __tablename__ = "trusted_keys"

    kid: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    publisher_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    public_pem: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Secret(Base):
    """시크릿 저장소(D9-04): AES-GCM 암호문만 저장. scope = agent:{id} | link:{id} | global. 원문은 응답·로그에 없다."""
    __tablename__ = "secrets"
    __table_args__ = (UniqueConstraint("scope", "name", name="uq_secrets_scope_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(80))
    ciphertext: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Install(Base):
    """등록 8단계 작업(D5-01~07, PRD 10.4). steps = [{n, name, status, detail, at}]."""
    __tablename__ = "installs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source: Mapped[str] = mapped_column(String(16))  # zip | market | url | git | oci | link
    source_ref: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|running|succeeded|failed|rolled_back
    step: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    env: Mapped[dict] = mapped_column(JSON, default=dict)  # 비밀 아닌 값만(PRD 12.1)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class KbCollection(Base):
    """지식 컬렉션(D3-06). shared=False 면 소유자만, True 면 같은 조직 사용자 모두 검색."""
    __tablename__ = "kb_collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(255))
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    data_class: Mapped[str] = mapped_column(String(4), default="L2")  # 임베딩·답변 생성에 쓰는 등급
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KbDocument(Base):
    __tablename__ = "kb_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(36), ForeignKey("kb_collections.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="ready")  # ready | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunks: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KbChunk(Base):
    """청크 + 임베딩(JSON 실수 목록 — SQLite·PostgreSQL 공용, 검색은 코사인). pgvector 색인은 규모 확장 시."""
    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("kb_documents.id", ondelete="CASCADE"), index=True)
    collection_id: Mapped[str] = mapped_column(String(36), index=True)
    ord: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(120))


class Memory(Base):
    """사용자 맞춤지침·장기 기억(D3-05). 본인만 보고 지운다(삭제권, NFR-C3)."""
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # instruction | fact
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16), default="manual")  # manual | chat
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StoredFile(Base):
    """대화 첨부(D3-04). 본문은 data/files/<id> — 보존 기간(파일 90일) 지나면 파기."""
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(16))  # image | document
    bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RunEvent(Base):
    """AG-UI 이벤트 기록(NFR-P4): 클라이언트가 끊겨도 실행은 계속되고, 재연결하면 마지막 seq 다음부터 다시 받는다. 1일 뒤 파기."""
    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("stream_id", "seq", name="uq_run_events_stream_seq"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[str] = mapped_column(String(36), index=True)
    owner: Mapped[str] = mapped_column(String(255))
    seq: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TraceSpan(Base):
    """LLM 관측(D10-04, 자체 경량): OTel 스팬을 DB 에도 남겨 콘솔에서 트레이스·세션·비용을 본다. 보존 obs_retention_days."""
    __tablename__ = "trace_spans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    span_id: Mapped[str] = mapped_column(String(16))
    parent_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(16))
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(8))  # ok | error
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)


class EvalSuite(Base):
    """평가 시나리오 묶음(D10-05). cases = [{id, input, expect:{contains, not_contains, regex, tool, state, judge}}]."""
    __tablename__ = "eval_suites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    agent_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cases: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    suite_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_suites.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running | done | failed
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    results: Mapped[list] = mapped_column(JSON, default=list)
    started_by: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Publisher(Base):
    """마켓 퍼블리셔(D6-06). 서명 키는 trusted_keys.publisher_id 로 묶는다. members = 게시할 수 있는 계정(actor)."""
    __tablename__ = "publishers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    members: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketListing(Base):
    """DB 리스팅(D6-06·D6-07): 승인된 게시(origin=release)·원격 레지스트리 동기화(registry:<이름>)·오프라인 번들(bundle).
    data = catalog.json 리스팅과 같은 모양. 정적 카탈로그와 합쳐 보여 준다."""
    __tablename__ = "market_listings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    origin: Mapped[str] = mapped_column(String(80))
    publisher_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketRelease(Base):
    """게시 → 심사 → 릴리스(D6-06). status = pending | published | rejected | blocked(자동 검사 실패)."""
    __tablename__ = "market_releases"
    __table_args__ = (UniqueConstraint("listing_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(40))
    publisher_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16))
    artifact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer, default=0)
    listing: Mapped[dict] = mapped_column(JSON, default=dict)
    gate: Mapped[dict] = mapped_column(JSON, default=dict)
    submitted_by: Mapped[str] = mapped_column(String(255))
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class License(Base):
    """등록된 라이선스(D6-05). token = Ed25519 서명 토큰 원문(오프라인 검증), payload = 검증된 본문."""
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(64), index=True)
    token: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    issuer: Mapped[str] = mapped_column(String(64))
    seats: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | revoked
    registered_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LicenseSeat(Base):
    """좌석 배정(D6-05): 유료 에이전트를 처음 쓰는 사용자(actor)에게 남은 좌석을 배정한다."""
    __tablename__ = "license_seats"
    __table_args__ = (UniqueConstraint("license_id", "holder"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_id: Mapped[str] = mapped_column(String(64), ForeignKey("licenses.id", ondelete="CASCADE"), index=True)
    holder: Mapped[str] = mapped_column(String(255))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Purchase(Base):
    """구매·영수증(D6-05, NFR-C4). 결제는 어댑터(mock)가 처리하고 영수증·발급 라이선스를 증적으로 남긴다."""
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(40))
    buyer: Mapped[str] = mapped_column(String(255))
    seats: Mapped[int] = mapped_column(Integer, default=1)
    months: Mapped[int] = mapped_column(Integer, default=1)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8))
    adapter: Mapped[str] = mapped_column(String(32))
    adapter_ref: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16))
    license_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receipt: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketDownload(Base):
    """다운로드·설치 통계(D6-06). kind = download(레지스트리 산출물) | install | update."""
    __tablename__ = "market_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(16))
    actor: Mapped[str] = mapped_column(String(255))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Org(Base):
    """조직(PRD Q7·Q12, UI K02) — 단일 테넌트 안의 배치 단위. 데이터 분리(멀티테넌시 X09)는 아니다."""
    __tablename__ = "orgs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OrgMember(Base):
    """조직 구성원. role = member | admin(조직 admin — 그 조직의 구성원·그룹 관리)."""
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("orgs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="member")


class OrgGroup(Base):
    """그룹(부서)."""
    __tablename__ = "org_groups"
    __table_args__ = (UniqueConstraint("org_id", "name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("orgs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("org_groups.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)


class AgentScope(Base):
    """에이전트 배치 범위(deploy_scope). 행이 없으면 모든 사용자. kind = org | group | user, ids = 그룹 id·사용자 id 목록."""
    __tablename__ = "agent_scopes"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("orgs.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(8))
    ids: Mapped[list] = mapped_column(JSON, default=list)
    updated_by: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    """알림(D10-07, UI B03). audience = admins | all | user:<actor>. deliveries = 채널별 발송 결과(디스패처가 채운다)."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(8))  # info | warn | error
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    resource: Mapped[str | None] = mapped_column(String(200), nullable=True)
    audience: Mapped[str] = mapped_column(String(255), default="admins")
    dedup_key: Mapped[str] = mapped_column(String(255), index=True)
    deliveries: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class NotificationRead(Base):
    __tablename__ = "notification_reads"
    __table_args__ = (UniqueConstraint("notification_id", "reader"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int] = mapped_column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), index=True)
    reader: Mapped[str] = mapped_column(String(255), index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Channel(Base):
    """대화 채널(D3-07, UI C07): web(위젯) | slack | telegram | kakao. 비밀값은 시크릿 저장소(scope channel:<id>).
    config = {agent_scope, data_class, allowed_origins(web), greeting}."""
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelThread(Base):
    """채널의 외부 대화(슬랙 스레드·텔레그램 채팅·카카오 사용자·위젯 방문자) ↔ 플랫폼 세션."""
    __tablename__ = "channel_threads"
    __table_args__ = (UniqueConstraint("channel_id", "external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(40), ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
