#!/usr/bin/env bash
# Build the app image and record it in packaging/RELEASE; with --deploy, start it right after (packaging/deploy.sh).
#
#   ./packaging/build.sh -v 1.2.0             image tc-vibe-coding:1.2.0 (+ :latest)
#   ./packaging/build.sh -v 1.2.0 --deploy    build, then deploy it
set -euo pipefail

usage() { echo "usage: ./packaging/build.sh -v <version> [--deploy]   (e.g. ./packaging/build.sh -v 1.2.0 --deploy)" >&2; exit 1; }

VERSION=""
DEPLOY=0
while [ $# -gt 0 ]; do
  case "$1" in
    -v|--version) VERSION="${2:-}"; shift 2 || usage ;;
    --deploy) DEPLOY=1; shift ;;
    *) usage ;;
  esac
done
[[ "$VERSION" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || usage   # a valid Docker tag

IMAGE="${IMAGE:-tc-vibe-coding}"
cd "$(dirname "$0")/.."   # build context = repository root

echo "==> Building $IMAGE:$VERSION"
docker build -f packaging/Dockerfile -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .

# The newest build (deploy.sh adds the deployed_* lines). Server-local, git-ignored.
cat > packaging/RELEASE <<EOF
version=$VERSION
image=$IMAGE:$VERSION
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
commit=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
built_at=$(date '+%Y-%m-%d %H:%M:%S')
EOF
echo "==> Built $IMAGE:$VERSION (packaging/RELEASE)"

if [ "$DEPLOY" = 1 ]; then
  exec ./packaging/deploy.sh -v "$VERSION"
fi
echo "    Start it: ./packaging/deploy.sh -v $VERSION   (or build with --deploy)"
