#!/usr/bin/env bash
# Build the app image. Nothing is started: packaging/deploy.sh does that.
#
#   ./packaging/build.sh -v 1.2.0       image tc-vibe-coding:1.2.0 (+ :latest)
set -euo pipefail

usage() { echo "usage: ./packaging/build.sh -v <version>   (e.g. ./packaging/build.sh -v 1.2.0)" >&2; exit 1; }

VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    -v|--version) VERSION="${2:-}"; shift 2 || usage ;;
    *) usage ;;
  esac
done
[[ "$VERSION" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || usage   # a valid Docker tag

IMAGE="${IMAGE:-tc-vibe-coding}"
cd "$(dirname "$0")/.."   # build context = repository root

echo "==> Building $IMAGE:$VERSION"
docker build -f packaging/Dockerfile -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .
echo "==> Built $IMAGE:$VERSION. Start it: ./packaging/deploy.sh -v $VERSION"
