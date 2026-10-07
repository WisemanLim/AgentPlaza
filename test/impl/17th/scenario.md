# impl 17th — Epic 17 관측·평가

FR: D10-04(LLM 관측 UI — 자체 경량), D10-05(평가·시험 표준), D4-05(`plaza test`) · NFR: NFR-O1 · UI '/observe'·'/evals'

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E17-01 | 트레이스 저장·조회 (D10-04) | 오케스트레이션 1건(계획 → 도구 → 합성) · 트레이스 목록·상세 | trace_spans 저장, 목록에 도구·모델·토큰, 상세에서 부모-자식 트리(워터폴) | P0 |
| E17-02 | 사용량·비용 (NFR-O1) | /api/obs/usage?days=1 | 모델·에이전트·사용자별 호출·토큰·비용·p50/p95·오류 | P0 |
| E17-03 | 평가 묶음 실행·회귀 (D10-05) | contains/tool/state/judge 사례 · 같은 묶음 재실행 | 사례별 PASS/FAIL·점수, 직전 실행 대비 회귀 표시 | P0 |
| E17-04 | 묶음 검증·권한 | 잘못된 사례(JSON·검사 종류) · 일반 사용자 | 422 · 403 | P1 |
| E17-05 | 플레이그라운드 A/B | 프롬프트 + 별칭 2개 | 별칭별 모델·지연·비용·답변 | P1 |
| E17-06 | `plaza test` (D4-05) | 마켓 board 1.0.0 산출물 · 새 service 스캐폴드(evals/*.yaml) | 구조·문법·react export·SQL DDL·런타임 계약(REST·MCP·A2A 카드)·eval 통과, `--report` result.md/json | P0 |
| E17-07 | 스팬 보존 기간 | 보존 기간 지난 스팬 · retention 실행 | 삭제 | P1 |
| E17-08 | 회귀·콘솔 | make test · /observe 상세 워터폴 · /evals 묶음·비교 | 전체 통과 · 스크린샷 | P0 |
