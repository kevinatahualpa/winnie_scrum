#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env.enc ]; then
  if [ -f .env ]; then
    echo "Ya existe .env; se omite (borralo si quieres restaurarlo)."
  else
    echo "Restaurando .env ..."
    openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
      -in .env.enc -out .env
  fi
fi

if [ -f backups/winnie_backup.sql.enc ]; then
  mkdir -p backups
  if [ -f backups/winnie_backup.sql ]; then
    echo "Ya existe backups/winnie_backup.sql; se omite."
  else
    echo "Restaurando backups/winnie_backup.sql ..."
    openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
      -in backups/winnie_backup.sql.enc -out backups/winnie_backup.sql
  fi
fi

echo "Listo."
echo "Para cargar la base de datos en la PC principal:"
echo "  1) createdb / crear rol segun .env"
echo "  2) psql -U winnie_user -h localhost -d winnie_db -f backups/winnie_backup.sql"
