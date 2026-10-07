# impl 2nd — Epic 2 agent.yaml 규격·템플릿 9유형·스캐폴드·SDK·내보내기·compose 골격

FR: D4-01, D4-02, D4-03, D4-04, D4-07, D8-01 · NFR: NFR-I1(샘플), NFR-I3, NFR-S5(에이전트) · PRD 7.4·10.2·10.3·10.8

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E2-01 | 9유형 스캐폴드 | `scaffold(type)` ×9 | 스키마 통과, 필수 파일, 토큰 치환 완료, app 만 frontend | P0 |
| E2-02 | 무효 매니페스트 거부 | docker:true · dependencies · id/version 형식 · verb 중복 · hitl 무승인 · apiVersion · runtime.mode | 해당 오류 | P0 |
| E2-03 | federation 규칙 | url 없는 federation | 오류 | P1 |
| E2-04 | v1 meta.json 변환 | v1 meta | 유효 agent.yaml, provenance.convertedFrom | P1 |
| E2-05 | 패키징 | pack ×2 | 동일 바이트, checksums.txt 일치 | P0 |
| E2-06 | 파생 export | derive(board→board-hr) | 새 id, provenance.baseAgent, compose 재생성 | P0 |
| E2-07 | Standalone compose 하드닝 | standalone_bundle | profiles=standalone, read_only, cap_drop ALL, limits(pids 포함), docker.sock·host·privileged 없음 | P0 |
| E2-08 | federated compose | compose_for(federated) | 포트 0, 외부 네트워크, Traefik 라벨 | P0 |
| E2-09 | 템플릿 실제 동작 ① | app·rag·memory 를 import 해 호출 | CRUD·스키마 422·BM25 검색·인용·기억/삭제권 | P0 |
| E2-10 | 템플릿 실제 동작 ② | service·reviewer·execution·hitl | wordcount·PII revise·injection block·안전 계산·코드 주입 400·승인 없이 403 | P0 |
| E2-11 | SDK 키 강제·coherence | AGENT_API_KEY · 미구현 capability | /health 공개·키 없이 401·불일치 시 기동 거부 | P0 |
| E2-12 | CLI | `plaza init/validate --strict/pack/export --derive --standalone` | 0 · 0 · 깨진 yaml 1 · zip | P0 |
| E2-13 | 스캐폴드 API | admin / 잘못된 type / user | zip(agent.yaml·checksums) · 422 · 403 | P0 |
| E2-14 | verify-coverage | `plaza verify-coverage` | P0 43 = 계획 43, ok | P1 |
| E2-15 | 실제 M1 단독 구동 | 생성한 app 에이전트 `docker compose --profile standalone up` | be healthy · /health 200 · 키 없이 401 · 키로 생성 200 · UI 200 · UI→/api 프록시 200 · read_only·cap_drop·pids·비루트 | P0 |
