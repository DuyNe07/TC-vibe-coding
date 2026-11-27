#!/usr/bin/env bash
# Copy the whole production database onto the dev database (same PostgreSQL server, credentials from ../.env).
# Nothing is destroyed: the current dev database is RENAMED to <dev>_bak_<timestamp>, then a fresh dev database
# is created and filled from a pg_dump of prod. Prod is only read.
#
#   ./packaging/copy_prod_to_dev.sh                      prod = POSTGRES_DB, dev = POSTGRES_DB-dev
#   DEV_DB=tc-vibe-coding-dev ./packaging/copy_prod_to_dev.sh
#   PG_IMAGE=postgres:16-alpine ./packaging/copy_prod_to_dev.sh   (no local pg_dump: tools run in docker)
set -euo pipefail
cd "$(dirname "$0")"
[ -f ../.env ] || { echo "Missing ../.env (POSTGRES_*)." >&2; exit 1; }

env_val() { grep -E "^$1=" ../.env | tail -1 | cut -d= -f2- | sed -E 's/^["'\'']//; s/["'\'']$//'; }
HOST=$(env_val POSTGRES_IP); PORT=$(env_val POSTGRES_PORT); USER=$(env_val POSTGRES_USER)
export PGPASSWORD=$(env_val POSTGRES_PASSWORD)
PROD_DB=${PROD_DB:-$(env_val POSTGRES_DB)}
DEV_DB=${DEV_DB:-${PROD_DB}-dev}
PORT=${PORT:-5432}
BAK_DB="${DEV_DB}_bak_$(date +%Y%m%d_%H%M%S)"

[ -n "$HOST" ] && [ -n "$PROD_DB" ] || { echo "POSTGRES_IP / POSTGRES_DB missing in .env." >&2; exit 1; }
[ "$PROD_DB" != "$DEV_DB" ] || { echo "PROD_DB and DEV_DB are the same ($PROD_DB): refusing." >&2; exit 1; }

# pg tools: local ones if installed, else a postgres image (must be >= the server's major version)
pg() {
  if command -v "$1" >/dev/null; then "$@"
  else docker run --rm -i --network host -e PGPASSWORD "${PG_IMAGE:-postgres:17-alpine}" "$@"; fi
}
CONN=(-h "$HOST" -p "$PORT" -U "$USER")
sql() { pg psql "${CONN[@]}" -d postgres -v ON_ERROR_STOP=1 -qc "$1"; }

echo "Copy  $PROD_DB  ->  $DEV_DB   on $HOST:$PORT"
echo "Current $DEV_DB is kept as $BAK_DB. Stop apps using $DEV_DB first."
read -r -p "Type yes to continue: " ok; [ "$ok" = yes ] || exit 1

if [ "$(pg psql "${CONN[@]}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DEV_DB'")" = 1 ]; then
  echo "==> Renaming $DEV_DB -> $BAK_DB"
  sql "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DEV_DB' AND pid <> pg_backend_pid()"
  sql "ALTER DATABASE \"$DEV_DB\" RENAME TO \"$BAK_DB\""
fi

echo "==> Creating $DEV_DB and restoring $PROD_DB into it"
sql "CREATE DATABASE \"$DEV_DB\""
pg pg_dump "${CONN[@]}" -d "$PROD_DB" -Fc --no-owner --no-acl \
  | pg pg_restore "${CONN[@]}" -d "$DEV_DB" --no-owner --no-acl --exit-on-error

echo "==> Done. $DEV_DB = copy of $PROD_DB (old dev kept as $BAK_DB)"
