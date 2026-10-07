# 시험 결과 / Test Result — impl 15th (Epic 15 어시스턴트 확장)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · 호스트 Ollama(bge-m3·qwen2.5vl:7b·granite4.1:3b) · pypdf
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 12, 통과 Pass: 12, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 216 passed (E15 10 + 회귀 206) · 실 스택(실 임베딩·비전·RAG) 9건 · 콘솔 E2E 1건(스크린샷 3)

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E15-01 | PASS | 실 bge-m3 1024차원(L3 → ollama/bge-m3), 퍼블릭 임베딩 L2 403, 채팅 별칭 404 |
| E15-02 | PASS | 실 스택: "출장비 정산 방법" → 출장 경비 문장 0.75 1위 |
| E15-03 | PASS | txt·md·pdf ready(청크·임베딩), exe failed. 실 검색 "연차 최대" → leave.txt 1위 |
| E15-04 | PASS | 실 granite: "출장 경비 정산 기한" → [1] travel.md 인용 답변("귀국 후 7일"), 남의 컬렉션 404 |
| E15-05 | PASS | 공유만 보임, 일반 사용자 공유 생성·수정 403 |
| E15-06 | PASS (round 2) | 지침·기억 주입, 주민번호 [RRN] 저장, 잊어줘·끄기·전체 삭제(원장). 실 LLM 회상 "서울 강남 지사" |
| E15-07 | PASS | 문서 첨부 → 실 LLM "하루 일비 5만 원", 이미지 → plaza/vision 에 data URL, exe 422, 남의 파일 404 |
| E15-08 | PASS | 비전 대상 없음 → llm_unavailable·RUN_ERROR |
| E15-09 | PASS | 91일 지난 첨부 → 보존 작업이 본문·메타 파기 |
| E15-10 | PASS | 공급자 = mock·ollama 뿐 |
| E15-11 | PASS | 실 qwen2.5vl: 콘솔 스크린샷 → "공급망 신뢰" |
| E15-12 | PASS (round 2) | make test 216 passed · 콘솔: 지식 컬렉션·검색, 메모리, 채팅 지식 선택 → 인용 카드 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 첨부 채팅 RUN_ERROR "datetime is not JSON serializable" | 메시지 meta 에 파일 출력(created_at) 그대로 저장 | meta 에는 id·파일명·종류만 | PASS |
| 1 | P1 i18n 키 23개 누락(빌드 시험 실패) | 사전 삽입 기준 문자열이 줄 가운데에 있어 매칭 실패 | 기준 문자열 수정 후 재삽입 | 웹 빌드 PASS |
| 1 | 실 스택: 맞춤지침 "모든 답변을 '네, 알겠습니다.'로 시작" → 3B 모델이 그 문장만 답함 | 소형 모델의 지침 과적합(주입은 정상) | 지침 예시를 "존댓말로 간단히"로 바꿔 재확인 — 기능 결함 아님, 모델 품질 한계로 기록 | 회상·첨부 PASS |
| 1 | 실 스택: 단색 64px PNG 색을 틀림(흰색·회색) | qwen2.5vl 이 합성 단색 이미지에 불안정 — Ollama 직접 호출에서도 동일(white·회색·빨래) | 의미 있는 이미지(콘솔 스크린샷)로 검증 → 정답 | PASS |
| 1 | 채팅 입력란 레이아웃 깨짐 | 첨부 버튼 추가로 그리드 열이 2→3 | `grid-template-columns: auto 1fr auto` | 스크린샷 확인 |

## 첨부 / Logs

- `logs/make-test.txt`(216 passed), `logs/e15-live.txt`, `logs/e2e/screens/p1-15-*.png`
