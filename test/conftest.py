"""공통 픽스처. app 을 import 하기 전에 시험 전용 DB·설정을 env 로 주입한다(local DB 오염 방지)."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.gettempdir()) / "agentplaza-test"
_TMP.mkdir(exist_ok=True)
_DB = _TMP / "test.db"
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_DB}",
    "DB_ENGINE": "sqlite",
    "APP_ENV": "local",
    "AUTO_MIGRATE": "false",
    "JWT_SECRET": "test-secret-at-least-32-bytes-long-xx",
    "PASSWORD_HASH_ITERATIONS": "1000",
    "DATA_DIR": str(_TMP / "data"),  # 서명 키·설치 파일을 실제 로컬 볼륨에 만들지 않는다
    "PUBLIC_BASE_URL": "http://gw.test",
    # 시험 컨테이너에는 OTel Collector 가 없다 — 내보내기 재시도로 느려지지 않게 끈다(스팬은 인메모리로 검증)
    "OTEL_EXPORTER_OTLP_ENDPOINT": "",
    "OTEL_TRACES_EXPORTER": "none",
    "OTEL_METRICS_EXPORTER": "none",
    "OTEL_LOGS_EXPORTER": "none",
    "GATEWAY_INTERNAL_URL": "",  # 시험의 가짜 에이전트는 Traefik 라우트가 없다 — 노출 확인 생략
    "RUNTIME_DRIVER": "none",  # 시험이 로컬 스택의 실제 runtime(에이전트 컨테이너)에 닿지 않게 — 필요한 시험은 Fake 를 꽂는다
    "REDIS_URL": "",  # 레이트리밋은 프로세스 메모리 카운터
    "MARKET_SYNC_INTERVAL": "0",  # 마켓 동기화·자동 갱신 루프는 시험에서 직접 호출한다
    "BIFROST_URL": "",
    "STATUS_CHECK_INTERVAL": "0",  # 상태 감시·알림 발송 루프는 시험에서 직접 호출한다  # 기본은 직접 호출 — Bifrost 경유는 test_e20 이 가짜 Bifrost 로 시험
    "PAYMENT_ADAPTER": "mock",
    "RATE_LIMIT_ENABLED": "false",  # 시험끼리 같은 토큰을 공유해 한도에 걸리지 않게 — 레이트리밋 시험만 켠다
    "SECRETS_MASTER_KEY": "",  # JWT_SECRET 에서 파생
    "TRIVY_CACHE_DIR": str(_TMP / "trivy-none"),  # 취약점 DB 없음 = 'unscanned'. 스캔 시험은 결과를 주입한다
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app import db as appdb  # noqa: E402
from app import models  # noqa: E402, F401
from app.main import app  # noqa: E402
from helpers import SUPERVISOR, auth  # noqa: E402, F401

@pytest.fixture(scope="session", autouse=True)
def _migrated():
    _DB.unlink(missing_ok=True)
    appdb.migrate()
    yield


@pytest.fixture(autouse=True)
def _clean():
    with appdb.engine.begin() as conn:
        for table in reversed(appdb.Base.metadata.sorted_tables):
            conn.execute(delete(table))
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sup_token(client) -> str:
    res = client.post("/api/setup/admin", json=SUPERVISOR)
    assert res.status_code == 201, res.text
    return res.json()["access_token"]
