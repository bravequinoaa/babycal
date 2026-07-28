#!/bin/sh
# Convenience wrapper around `docker compose exec db psql`.
#
# Usage:
#   scripts/db.sh              interactive psql shell
#   scripts/db.sh ls           list table names
#   scripts/db.sh "<SQL>"      run one SQL statement and exit
set -e

cd "$(dirname "$0")/.."

if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

DB_USER="${POSTGRES_USER:-babycal}"
DB_NAME="${POSTGRES_DB:-babycal}"

if [ "$#" -eq 0 ]; then
    exec docker compose exec db psql -U "$DB_USER" -d "$DB_NAME"
elif [ "$1" = "ls" ]; then
    exec docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c '\dt'
else
    exec docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c "$*"
fi
