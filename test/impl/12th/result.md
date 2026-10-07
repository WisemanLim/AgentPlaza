# 시험 결과 / Test Result — impl 12th (Epic 12 공급망 신뢰 게이트)

- 일자 Date: 2026-10-07
- 대상 Target(profile): `python-fastapi` · cosign v3.1.3 · syft v1.54.1 · trivy 0.75.0(취약점 DB 1.4GB, trivycache 볼륨)
- 커밋 Commit: 없음 (git 미초기화)

## 요약 / Summary

- 전체 Total: 15, 통과 Pass: 15, 실패 Fail: 0, 최종 Verdict: **PASS**
- pytest 169 passed (E12 24 + 회귀 145) · 실 스택(실 runtime·실 trivy) 7건 · 콘솔 E2E 1건(스크린샷 3)

## 케이스 / Cases

| id | 결과 result | 비고 note |
|----|-------------|-----------|
| E12-01 | PASS | 실 `plaza keygen/publish`: checksums.txt·sbom.json(CycloneDX 1.7)·signature.sig, keyId 기록 |
| E12-02 | PASS | 실 설치 8단계 전부 ok — signature=verified·signer=kid·vulns scanned C0 |
| E12-03 | PASS | 변조 → `checksums 불일치`, checksums 재계산 → `서명 불일치`, 철회 키 → `철회된 키` (pytest + 실 스택 변조) |
| E12-04 | PASS | 모르는 키 = 미검증 경고 설치, require_signature 켜면 미서명 거부(실 스택) |
| E12-05 | PASS | 실 trivy: PyYAML==5.3 → CVE-2020-14343·CVE-2020-1747 CRITICAL 2건 설치 거부. HIGH 경고·정책 상향은 주입 시험 |
| E12-06 | PASS | G5 거부·허용목록 예외·AGPL-3.0-only = G4 경고 설치(실 runtime) + 파생 export 403 |
| E12-07 | PASS | egress 정책 거부/통과 |
| E12-08 | PASS | user 403 · 잘못된 PEM·중복·정책 오입력 422 · 원장 기록 |
| E12-09 | PASS | `market-build --key` 카탈로그: 키 신뢰 전 unverified → 후 verified |
| E12-10 | PASS | 원장 agent.installed 에 license·license_grade·signature·signer·vulns·source |
| E12-11 | PASS | 12종 SPDX 식 등급 |
| E12-12 | PASS | dev venv(pytest)·실행 중 api venv: 319 컴포넌트 G4 0 (G3 2·G2 1 은 LGPL·MPL 동적 사용 — 정책상 G4 만 차단). prod 이미지는 완료 게이트에서 재확인 |
| E12-13 | PASS | CLI `export --derive` G4 거부 |
| E12-14 | PASS | `make test` 169 passed |
| E12-15 | PASS | 콘솔: /trust 키·정책, 설치 진행 3·4단계 배지(서명 검증·취약점 C0·H0·라이선스 G1), 버전 배지·SBOM 버튼 |

## 발견 오류 및 수정 / Bugs & Fixes

| round | 오류 bug | 원인 cause | 수정 fix | 재시험 retest |
|-------|----------|-----------|----------|---------------|
| 1 | 설치 시 `'str' object has no attribute 'policy'` | `pipeline.run(trust=…)` 인자가 모듈 이름 `trust` 를 가림 | 모듈을 `sc_trust` 로 별칭 import | PASS |
| 1 | HIGH 취약점 경고가 안 남음 | 차단 등급 분기와 경고 분기가 if/elif 로 묶여 경고 분기 도달 불가 | 차단 판정 후 CRITICAL·HIGH 경고를 별도로 | PASS |
| 1 | syft SBOM 에 components 키 없음 | 템플릿 requirements 가 `>=` (버전 미고정) — syft 는 고정 버전만 컴포넌트로 기록 | 시험을 `.get("components", [])` 로. 실제 고정 의존성(PyYAML==5.3)은 trivy 가 잡음 | PASS |
| 2 | 실 스택: 설치마다 "게이트웨이 라우트 반영 지연" 경고, 설치 중 api 무응답(health 6초 타임아웃) | local dev 의 `uvicorn --reload` 가 /app 전체를 감시 → 설치가 /app/data(스테이징·workdir)에 파일을 쓰면 재기동 시작 → 종료가 진행 중 설치(백그라운드 작업)를 기다리는 동안 새 요청을 못 받음(Traefik forwardAuth 타임아웃) | dev CMD 를 `--reload-dir app/sdk/plaza` 로 한정 | 설치 중 health 200(2ms), 9초 만에 succeeded, 경고 없음 |

## 첨부 / Logs

- `logs/make-test.txt` (169 passed), `logs/e12-live.txt`, `logs/e2e/screens/p1-12-*.png`
