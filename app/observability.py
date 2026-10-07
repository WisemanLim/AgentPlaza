"""OTel 트레이스 (D10-03, NFR-O1): OpenTelemetry GenAI semconv 속성(PRD 12.6).

필수 속성: gen_ai.system · gen_ai.request.model · gen_ai.usage.input_tokens/output_tokens · gen_ai.agent.id ·
gen_ai.tool.name · plaza.session_id · plaza.capability · plaza.fallback_from. 프롬프트 원문은 수집하지 않는다(opt-in 미구현).
OTEL_EXPORTER_OTLP_ENDPOINT 가 있으면 OTLP/HTTP 로 내보낸다(OTel Collector, P06).
콘솔 관측 화면(D10-04, 자체 경량)을 위해 플랫폼 스팬은 DB(trace_spans)에도 남긴다(OBS_STORE_SPANS, 보존 obs_retention_days).
"""
import os
from datetime import UTC, datetime

from opentelemetry import propagate, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

from app.core.config import settings


class DbSpanExporter(SpanExporter):
    """BatchSpanProcessor 스레드에서 스팬을 trace_spans 로 일괄 저장한다(요청 경로를 막지 않음)."""

    def export(self, spans) -> SpanExportResult:
        from app.db import SessionLocal
        from app.models import TraceSpan
        rows = []
        for s in spans:
            ctx = s.get_span_context()
            rows.append(TraceSpan(
                trace_id=f"{ctx.trace_id:032x}", span_id=f"{ctx.span_id:016x}",
                parent_id=f"{s.parent.span_id:016x}" if s.parent else None, name=s.name[:200],
                kind=s.kind.name.lower(), start=datetime.fromtimestamp(s.start_time / 1e9, UTC),
                duration_ms=int(((s.end_time or s.start_time) - s.start_time) / 1e6),
                status="error" if s.status.status_code == StatusCode.ERROR else "ok",
                attributes={k: (list(v) if isinstance(v, tuple) else v) for k, v in (s.attributes or {}).items()}))
        try:
            with SessionLocal() as db:
                db.add_all(rows)
                db.commit()
        except Exception:  # noqa: BLE001 — 관측 저장 실패가 서비스를 막지 않는다
            return SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None

_provider = TracerProvider(resource=Resource.create({
    "service.name": settings.app_name, "service.namespace": "agentplaza",
    "deployment.environment.name": settings.app_env}))
_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").rstrip("/")
if _endpoint:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    _provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{_endpoint}/v1/traces")))
if settings.obs_store_spans:
    _provider.add_span_processor(BatchSpanProcessor(DbSpanExporter(), schedule_delay_millis=2000))


def provider() -> TracerProvider:
    return _provider


def tracer():
    return _provider.get_tracer("agentplaza", "0.1.0")


def inject(headers: dict) -> dict:
    """W3C traceparent 를 하위 호출(에이전트·원격) 헤더에 싣는다."""
    propagate.inject(headers)
    return headers


def clean(attrs: dict) -> dict:
    return {k: v for k, v in attrs.items() if v is not None}


SpanKind = trace.SpanKind
Status = trace.Status
StatusCode = trace.StatusCode


def flush() -> None:
    _provider.force_flush(5000)
