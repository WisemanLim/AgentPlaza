#!/usr/bin/env bash
# 콘솔 E2E 실행기: Playwright(Chromium)를 컨테이너에서 실행한다. 로컬 스택이 떠 있어야 한다.
# 사용: E2E_EMAIL=… E2E_PASSWORD=… web/e2e/run.sh   (P1 화면만: E2E_TOKEN=… E2E_SPEC=p1 web/e2e/run.sh)
set -euo pipefail
cd "$(dirname "$0")"
[ -n "${E2E_TOKEN:-}" ] || { : "${E2E_EMAIL:?E2E_EMAIL 필요}" "${E2E_PASSWORD:?E2E_PASSWORD 필요}"; }
OUT="${E2E_OUT_DIR:-$PWD/../../test/impl/latest-e2e}"
mkdir -p "$OUT"
# 저장소 폴더를 더럽히지 않도록 컨테이너 안 /work 로 복사해 실행. 산출물(스크린샷·trace)은 $OUT 으로.
exec docker run --rm --add-host host.docker.internal:host-gateway -e E2E_EMAIL -e E2E_PASSWORD -e E2E_TOKEN -e E2E_SPEC \
  -e E2E_VARS -e E2E_OUT=/out \
  -v "$PWD":/e2e:ro -v "$OUT":/out node:22-bookworm bash -c '
    cp -r /e2e /work && cd /work && npm init -y >/dev/null && npm i -D @playwright/test@1 @axe-core/playwright@4 >/dev/null 2>&1 &&
    npx playwright install --with-deps chromium >/dev/null 2>&1 &&
    (node proxy.mjs &) && sleep 1 && npx playwright test -c playwright.config.mjs $E2E_SPEC'
