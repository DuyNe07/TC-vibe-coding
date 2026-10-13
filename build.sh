#!/usr/bin/env bash
# Build the app image for a version, then replace the running container with it.
#
#   ./build.sh -v 1.2.0                 image tc-vibe-coding:1.2.0 (+ :latest), container "tc-vibe-coding" on port 8501
#   PORT=8600 ./build.sh --version 1.3.0
#
# Database settings and secrets are read from .env at run time (copy .env.example to .env, fill POSTGRES_*);
# they are never copied into the image. App files written at run time live in Docker volumes <container>-data/-logs.
set -euo pipefail

usage() { echo "usage: ./build.sh -v <version>   (e.g. ./build.sh -v 1.2.0)" >&2; exit 1; }

VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    -v|--version) VERSION="${2:-}"; shift 2 || usage ;;
    *) usage ;;
  esac
done
[[ "$VERSION" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || usage   # a valid Docker tag

IMAGE="${IMAGE:-tc-vibe-coding}"
CONTAINER="${CONTAINER:-tc-vibe-coding}"
PORT="${PORT:-8501}"

cd "$(dirname "$0")"
[ -f .env ] || { echo "Missing .env: copy .env.example to .env and fill POSTGRES_* first." >&2; exit 1; }

echo "==> Building $IMAGE:$VERSION"
docker build -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .

echo "==> Replacing container $CONTAINER"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  --env-file .env \
  -p "$PORT:8501" \
  -v "$CONTAINER-data:/app/data" \
  -v "$CONTAINER-logs:/app/logs" \
  "$IMAGE:$VERSION"

echo "==> $IMAGE:$VERSION is running on http://localhost:$PORT  (logs: docker logs -f $CONTAINER)"
