#!/usr/bin/env bash
# 폐쇄망 번들 (D8-07): 연결된 호스트에서 만들어 반입한다.
#   images.tar.gz  플랫폼·인프라·설치 에이전트 이미지 (docker save)
#   market/        정적 카탈로그 + 산출물 zip
#   trivy-db.tar.gz 취약점 DB(trivycache 볼륨, 있으면)
#   models.txt     로컬 LLM 모델 목록(ollama pull 대상) · INCLUDE_MODELS=1 이면 ~/.ollama/models 도 models.tar
#   manifest.sha256 모든 파일 해시 — load.sh 가 먼저 검증한다
# 사용: make offline-bundle ENV=prod [IMAGES="a:1 b:2"] [INCLUDE_MODELS=1]
set -euo pipefail
cd "$(dirname "$0")/../.."
ENV="${ENV:-prod}"; PROJECT="${PROJECT:-wise-agentplaza}"; P="$PROJECT-$ENV"
STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT="dist/offline/$STAMP"; mkdir -p "$OUT"
sha() { if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }
EXTRA=(); for f in compose/*.yml; do EXTRA+=(-f "$f"); done
DC=(docker compose -p "$P" -f docker-compose.yml -f "docker-compose.$ENV.yml" "${EXTRA[@]}" --env-file ".env.$ENV")
if [ -z "${IMAGES:-}" ]; then
  IMAGES="$("${DC[@]}" config --images | sort -u | tr '\n' ' ') $(docker images --format '{{.Repository}}:{{.Tag}}' --filter 'reference=local/agent-*' | tr '\n' ' ')"
fi
missing=""; for i in $IMAGES; do docker image inspect "$i" >/dev/null 2>&1 || missing="$missing $i"; done
[ -z "$missing" ] || { echo "FAIL: 로컬에 없는 이미지:$missing — make $ENV-build 또는 docker pull 후 다시"; exit 1; }
echo "$IMAGES" | tr ' ' '\n' | sed '/^$/d' > "$OUT/images.txt"
echo "== images ($(wc -l < "$OUT/images.txt" | tr -d ' ')) → images.tar.gz"
# shellcheck disable=SC2086
docker save $IMAGES | gzip -1 > "$OUT/images.tar.gz"
cp -R market "$OUT/market"
HELPER="wise-agentplaza-runtime:$ENV"
if docker volume inspect "${P}_trivycache" >/dev/null 2>&1 && docker image inspect "$HELPER" >/dev/null 2>&1; then
  docker run --rm --network none -v "${P}_trivycache:/c:ro" --entrypoint tar "$HELPER" czf - -C /c . > "$OUT/trivy-db.tar.gz"
fi
grep -hE '^LLM_LOCAL_(CHAT|REASONING)_MODEL=' ".env.$ENV" | cut -d= -f2 | sort -u > "$OUT/models.txt"
if [ "${INCLUDE_MODELS:-0}" = 1 ] && [ -d "$HOME/.ollama/models" ]; then tar -C "$HOME/.ollama" -cf "$OUT/models.tar" models; fi
(cd "$OUT" && find . -type f ! -name manifest.sha256 | LC_ALL=C sort | while read -r f; do sha "$f"; done > manifest.sha256)
du -sh "$OUT" | awk '{print "== bundle " $2 " (" $1 ")"}'
