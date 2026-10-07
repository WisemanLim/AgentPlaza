# impl 12th — Epic 12 공급망 신뢰 게이트

FR: D4-06, D5-03, D5-04 · NFR: NFR-S2, NFR-C1, NFR-C2 · UI D05(설치 진행 3·4단계)·D02(버전·SBOM)·신뢰 키/정책 화면
도구: cosign v3.1.3 · syft v1.54.1 · trivy 0.75.0(이미지 포함) · 취약점 DB = trivycache 볼륨(`make trivy-db`)

| id | 목적 | 입력 | 기대 | 우선 |
|----|------|------|------|------|
| E12-01 | 서명 패키징 (D4-06) | `plaza keygen` → `plaza publish <dir> --key` | zip 에 checksums.txt·sbom.json(CycloneDX)·signature.sig, agent.yaml publisher.keyId=kid, cosign 검증 OK·다른 키 NG | P0 |
| E12-02 | 서명 검증 설치 (D5-03) | 신뢰 키 등록 → 서명 zip 업로드(실 runtime) | 3단계 signature=verified·signer=kid, 버전 기록·SBOM 조회, succeeded | P0 |
| E12-03 | 변조·철회 거부 (NFR-S2) | 파일 변조 / checksums 재계산 / 철회 키 | 3단계 failed: checksums 불일치 / 서명 불일치 / 철회된 키, 카탈로그 흔적 없음 | P0 |
| E12-04 | 미검증·서명 필수 정책 | 모르는 키 서명 / require_signature=true | 미검증 경고로 설치 · 정책 켜면 거부 | P0 |
| E12-05 | 취약점 게이트 (NFR-S2) | 실 trivy: PyYAML==5.3 고정 패키지 / HIGH 만 / block_severity=HIGH | CRITICAL 거부(CVE 표시) · HIGH 경고 설치 · 정책 상향 시 거부 | P0 |
| E12-06 | 라이선스 등급 (D5-04) | LicenseRef-Proprietary / 허용목록 / AGPL-3.0-only | G5 거부 · 예외 허용 · G4 경고 + 파생 export 403 | P0 |
| E12-07 | 선언 egress vs 조직 정책 | egress_allow=*.corp.internal, 선언 api.example.com / erp.corp.internal | 4단계 거부 / 통과 | P1 |
| E12-08 | 신뢰 API RBAC·검증 | user 접근 · 잘못된 PEM · 중복 · 정책 오입력 | 403 · 422 · 422 · 422, 원장 trust.key_added | P0 |
| E12-09 | 마켓 서명 배지 | `market-build --key` 카탈로그 · 키 신뢰 전/후 | signature:unverified → signature:verified | P1 |
| E12-10 | 출처·라이선스 증적 (NFR-C2) | 설치 후 원장 agent.installed | license·license_grade·signature·source·sha256 기록 | P0 |
| E12-11 | 라이선스 등급표 | SPDX 식 12종(OR/AND/WITH/이름) | G1~G5 기대값 | P1 |
| E12-12 | 플랫폼 이미지 G4 0건 (NFR-C1) | `plaza sbom-check` (dev venv · prod runtime 이미지) | G4 컴포넌트 0, exit 0 | P0 |
| E12-13 | CLI 파생 금지 | `plaza export AGPL.zip --derive` | exit 1, G4 사유 | P1 |
| E12-14 | 회귀 | `make test` | 전체 통과 | P0 |
| E12-15 | 콘솔 화면 | /trust 키 등록·정책 · 설치 진행 3·4단계 · 에이전트 버전 배지·SBOM | 화면 표시(스크린샷) | P1 |
