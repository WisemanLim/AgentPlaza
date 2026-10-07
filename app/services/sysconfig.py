"""시스템 설정(UI L01) — env 기본값 위에 DB(settings 테이블) 값을 덮어쓴다. 키는 허용목록만."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Setting

KEY = "system"
# 키 → (기본값 함수, 검증)
SCHEMA = {
    "retention_chat_days": (lambda: settings.retention_chat_days, lambda v: isinstance(v, int) and 1 <= v <= 3650),
    "retention_file_days": (lambda: 90, lambda v: isinstance(v, int) and 1 <= v <= 3650),
    "hitl_ttl_minutes": (lambda: settings.hitl_ttl_minutes, lambda v: isinstance(v, int) and 1 <= v <= 10080),
    "default_data_class": (lambda: "L2", lambda v: v in ("L0", "L1", "L2", "L3")),
    "default_locale": (lambda: "ko", lambda v: v in ("ko", "en")),
    "brand_color": (lambda: "#3F51E5", lambda v: isinstance(v, str) and len(v) == 7 and v.startswith("#")),
    "site_name": (lambda: "AgentPlaza", lambda v: isinstance(v, str) and 1 <= len(v) <= 60),
}


def _stored(db: Session, key: str = KEY) -> dict:
    row = db.get(Setting, key)
    return dict(row.value) if row else {}


def effective(db: Session) -> dict:
    stored = _stored(db)
    return {k: stored.get(k, default()) for k, (default, _) in SCHEMA.items()}


def get(db: Session, key: str):
    return effective(db)[key]


def update(db: Session, changes: dict) -> dict:
    bad = [k for k, v in changes.items() if k not in SCHEMA or not SCHEMA[k][1](v)]
    if bad:
        raise ValueError(f"허용되지 않은 값 / invalid: {bad}")
    row = db.get(Setting, KEY) or Setting(key=KEY, value={})
    row.value = {**dict(row.value or {}), **changes}
    db.add(row)
    db.commit()
    return effective(db)


def blob(db: Session, key: str) -> dict:
    return _stored(db, key)


def put_blob(db: Session, key: str, value: dict) -> dict:
    row = db.get(Setting, key) or Setting(key=key, value={})
    row.value = value
    db.add(row)
    db.commit()
    return value
