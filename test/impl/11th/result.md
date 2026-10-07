# 시험 결과 / Test Result — impl 11th (Epic 11 웹 콘솔)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `web/` React 19 + TypeScript + Vite 7(pnpm 12) → nginx-unprivileged · Traefik 단일 오리진(8090) + Addon 전용 오리진(8092)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 9, 통과 Pass: 9, 실패 Fail: 0, 최종 Verdict: **PASS**
- vitest 6 passed · tsc 0 오류 · Playwright E2E 4 passed(round 4, 24s) · 백엔드 회귀 144 passed · verify-coverage ok(P0 43 추적)

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E11-01 | PASS | |
| E11-02 | PASS | |
| E11-03 | PASS | |
| E11-04 | PASS | JS 284KB(gzip 87KB) |
| E11-05 | PASS | 실 Ollama 스트리밍 |
| E11-06 | PASS | round 1 에서 UI 로 신규 설치(8단계), round 4 는 고유 제목으로 등록 검증 |
| E11-07 | PASS | 실 LLM 계획 → ops-approval.execute_action 승인 카드 |
| E11-08 | PASS | |
| E11-09 | PASS | curl 로 헤더 확인 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 0 (설계) | Addon UI 가 콘솔과 같은 오리진 → 신뢰하지 않는 화면이 콘솔 토큰·DOM 접근 가능 | 단일 진입점 | Traefik apps 진입점(8092)으로 오리진 분리 + Addon CSP frame-ancestors(콘솔) + 콘솔 CSP frame-ancestors 'none' | E11-06 차단 확인 |
| 0 | tsc: `user|assistant` 판별 유니온 미축소, 시험 파일 node 타입 | TS 제약 | 멤버 분리, 시험은 tsc 제외(vitest 가 실행) | tsc 0 |
| 0 | 웹 이미지 빌드 실패 | pnpm 12: lockfile 불일치·승인 안 된 빌드 스크립트(esbuild) 오류 | `allowBuilds: {esbuild: true}`, lockfile 재생성, `--frozen-lockfile` | 빌드 성공 |
| 0 | 채팅 이벤트 업데이터에 부수효과, 스트림 중 세션 이력 재로딩 경쟁 | 설계 | 업데이터 순수화, 스트림이 만든 세션은 이력 재로딩 생략 | E11-05 |
| 0 | 설치 진행 폴링이 렌더마다 재시작 | 콜백 의존성 | ref 로 고정 | — |
| 2 | 대시보드 타일 링크 스타일·"새 대화" 버튼 늘어남·모바일 상단바 넘침·배지 원시 값·상세에 설치됨 표시 없음 | 스타일·UX | a.card 스타일, sessions align-content, 모바일 상단바 축약, 배지 i18n 라벨, 상세 "설치됨 + 에이전트 열기" | 스크린샷 확인 |
| 2 | FL-02 반복 실행 시 실패 / 거짓 양성 | 시험 비멱등·이전 글 일치 | 이미 설치면 진행 대기 생략, 회차별 고유 제목·폼 초기화 단언 | round 4 PASS |
| 3 | 모바일 드로어 잘림처럼 보임 | 슬라이드 애니메이션 중 캡처(버그 아님) | 전환 후 캡처 + x=0 단언 | round 4 PASS |

## 첨부 / Logs

- `logs/e2e.r1~r4.txt`, `logs/e2e/screens/*.png`(대시보드·채팅·마켓·Addon iframe·승인 카드·모바일 드로어), `logs/web-build.r3.txt`, `logs/make-test.txt`
