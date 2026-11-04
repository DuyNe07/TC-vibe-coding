#!/usr/bin/env bash
# Replace the running app with an image built by packaging/build.sh (packaging/docker-compose.yml):
# migrate the database once, recreate the 3 app replicas, wait until they are healthy, then restart nginx
# (the only published port).
#
#   ./packaging/deploy.sh -v 1.2.0      http://<server-ip>/home
#   PORT=8080 ./packaging/deploy.sh -v 1.2.0
set -euo pipefail

usage() { echo "usage: ./packaging/deploy.sh -v <version>   (e.g. ./packaging/deploy.sh -v 1.2.0)" >&2; exit 1; }

VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    -v|--version) VERSION="${2:-}"; shift 2 || usage ;;
    *) usage ;;
  esac
done
[[ "$VERSION" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || usage
export VERSION

cd "$(dirname "$0")"
[ -f ../.env ] || { echo "Missing .env: copy .env.example to .env (repository root) and fill POSTGRES_* first." >&2; exit 1; }
docker image inspect "tc-vibe-coding:$VERSION" >/dev/null 2>&1 \
  || { echo "No image tc-vibe-coding:$VERSION: run ./packaging/build.sh -v $VERSION first." >&2; exit 1; }

compose() { docker compose -f docker-compose.yml "$@"; }

echo "==> Migrating the database (tc-vibe-coding:$VERSION)"
compose run --rm migrate

echo "==> Replacing the app replicas and nginx"
docker rm -f tc-vibe-coding >/dev/null 2>&1 || true   # the single container of the former build.sh, if any
compose up -d --force-recreate --remove-orphans --wait app-1 app-2 app-3 nginx

echo "==> tc-vibe-coding:$VERSION is running on http://<server-ip>:${PORT:-80}/home"
echo "    status: docker compose -f packaging/docker-compose.yml ps   |   logs: docker logs -f tc-vibe-coding-1"
