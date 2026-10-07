# PRD 입력 문서 / PRD sources

| # | 원본 / source | 역할 / role | 방법 / method | 추출본 / extracted | 글자수 / chars |
|---|---------------|-------------|---------------|--------------------|----------------|
| 1 | `.docs/AgentPlaza_PRD.v2.pdf` | main | pdftotext | `.wds/prd-sources/1-AgentPlaza_PRD.v2.md` | 322327 |
| 2 | `.docs/AgentPlaza_UI_Design.pdf` | design | pdftotext | `.wds/prd-sources/2-AgentPlaza_UI_Design.md` | 617849 |

- NEEDS_MODEL_READ: 추출 도구 없음/스캔본 → 에이전트가 원본 파일을 직접 읽는다.
- 역할(role)은 파일명 추정값이다. design → PRD 디자인 요구, api → 외부 연동, nfr → 비기능/규제 섹션에 우선 반영.
