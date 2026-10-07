#!/usr/bin/env bash
# 폐쇄망 번들 적재 (D8-07): 해시 검증 → docker load → 취약점 DB 볼륨 → 모델 안내. 네트워크를 쓰지 않는다.
# 사용: make offline-load DIR=dist/offline/<stamp> [ENV=prod]
set -euo pipefail
DIR="${1:?번들 디렉터리 필요 / bundle dir required}"
ENV="${ENV:-prod}"; PROJECT="${PROJECT:-wise-agentplaza}"; P="$PROJECT-$ENV"
check() { if command -v sha256sum >/dev/null; then sha256sum -c --quiet "$@"; else shasum -a 256 -c --quiet "$@"; fi; }
cd "$DIR"
check manifest.sha256 || { echo "FAIL: 해시 불일치 — 변조·손상된 번들은 적재하지 않는다 / checksum mismatch"; exit 1; }
echo "== manifest OK ($(wc -l < manifest.sha256 | tr -d ' ') files)"
gunzip -c images.tar.gz | docker load | sed 's/^/   /'
while read -r img; do docker image inspect "$img" >/dev/null || { echo "FAIL: $img 적재 안 됨"; exit 1; }; done < images.txt
echo "== images OK ($(wc -l < images.txt | tr -d ' '))"
if [ -f trivy-db.tar.gz ]; then
  docker volume create "${P}_trivycache" >/dev/null
  docker run --rm -i --network none -v "${P}_trivycache:/c" --entrypoint sh "wise-agentplaza-runtime:$ENV" -c 'tar xzf - -C /c' < trivy-db.tar.gz
  echo "== trivy DB → ${P}_trivycache"
fi
if [ -f models.tar ]; then echo "== 모델: tar -C ~/.ollama -xf $DIR/models.tar (Ollama 호스트에서)"; fi
echo "== 로컬 LLM 모델: $(tr '\n' ' ' < models.txt) — Ollama 호스트에 있어야 함(ollama list)"
echo "== 카탈로그: $DIR/market (MARKET_CATALOG 로 지정하거나 저장소 market/ 에 복사)"
