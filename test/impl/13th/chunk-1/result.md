# 시험 결과 — impl 13th · chunk-1 (시크릿·정책 엔진, D9-04·D9-05)

- 일자 Date: 2026-10-07 · 대상: local 스택(실 runtime·Valkey) + pytest

## 요약 / Summary

- 전체 Total: 11, 통과 Pass: 11, 실패 Fail: 0, 최종 Verdict: **PASS**

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E13-01 | PASS | AES-256-GCM 암호문만 저장, version 1→2, AAD 바꿔치기 InvalidTag, 목록·응답에 값 없음, user 403 |
| E13-02 | PASS (round 2) | 실 runtime: Install.env·workdir·compose·docker inspect·에이전트/api 로그 원문 0건, 자기 키 pull 200 · 타 키 401, 회전 후 31초 내 새 값(C), 재설치 시 값 재입력 불필요, 삭제 시 파기 |
| E13-03 | PASS | SDK: env 우선(M1)·캐시 1회 pull·로그 마스킹 |
| E13-04 | PASS | 저장 값·ap_sk_·sk-·JWT·PEM → [REDACTED] |
| E13-05 | PASS | 실 runtime: rotate-key → 컨테이너 재생성, 이전 키 폐기, 호출 정상 |
| E13-06 | PASS | 422·422·403 |
| E13-07 | PASS | L1=local 정책 후 퍼블릭 별칭 403 + llm.policy_denied |
| E13-08 | PASS | 퍼블릭 대상만 [RRN]·[PHONE] (실 퍼블릭 키 없음 — mock 퍼블릭 모델로 확인) |
| E13-09 | PASS | L3 비인가 에이전트 계획 제외(규칙 폴백도 인가 에이전트만), 실 스택 L1 승인 강제 → waiting_approval(board.manage), 툴 RBAC·거부 목록 |
| E13-10 | PASS | 실 스택 L3 세션 export 403 |
| E13-11 | PASS | full 감사: 인자·결과 PII 마스킹 요약, 하한 끌어올림 |
