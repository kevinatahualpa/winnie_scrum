#!/usr/bin/env bash
#
# sync.sh - Traslada Winnie entre PCs (codigo por git + .env y BD cifrados)
#
# Uso:
#   ./scripts/sync.sh push   -> vuelca la BD, cifra .env + dump, commit y push
#   ./scripts/sync.sh pull   -> git pull, descifra .env + dump, recarga la BD
#
set -euo pipefail
cd "$(dirname "$0")/.."

DB_NAME="${DB_NAME:-winnie_db}"
DB_USER="${DB_USER:-winnie_user}"
DB_PASSWORD="${DB_PASSWORD:-winnie69112}"
DB_HOST="${DB_HOST:-localhost}"
DUMP="backups/winnie_backup.sql"
ENC_ITER=200000

usage() {
  echo "Uso: $0 {push|pull}"
  exit 1
}

[ $# -eq 1 ] || usage

case "$1" in
  push)
    echo ">> Volcando base de datos $DB_NAME ..."
    mkdir -p backups
    PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" \
      --no-owner --no-privileges -f "$DUMP"

    echo ">> Cifrando .env y dump (te pedira tu contrasena) ..."
    rm -f .env.enc "${DUMP}.enc"
    openssl enc -aes-256-cbc -pbkdf2 -iter "$ENC_ITER" -salt -in .env -out .env.enc
    openssl enc -aes-256-cbc -pbkdf2 -iter "$ENC_ITER" -salt -in "$DUMP" -out "${DUMP}.enc"

    echo ">> Commit y push ..."
    git add -A
    git commit -m "sync: update code, encrypted env and db backup" || echo "(nada que commitear)"
    git push
    echo ">> Listo. Cambios enviados."
    ;;

  pull)
    echo ">> git pull ..."
    git pull

    echo ">> Descifrando .env y dump (te pedira tu contrasena) ..."
    rm -f .env "$DUMP"
    openssl enc -d -aes-256-cbc -pbkdf2 -iter "$ENC_ITER" -in .env.enc -out .env
    openssl enc -d -aes-256-cbc -pbkdf2 -iter "$ENC_ITER" -in "${DUMP}.enc" -out "$DUMP"

    echo ">> Recreando base de datos $DB_NAME (limpia) ..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
      sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

    echo ">> Cargando datos ..."
    PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -f "$DUMP"
    echo ">> Listo. Proyecto y datos actualizados."
    ;;

  *)
    usage
    ;;
esac
