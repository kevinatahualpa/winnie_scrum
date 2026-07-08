#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No existe .env en la raiz del proyecto." >&2
  exit 1
fi

echo "Cifrando .env ..."
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
  -in .env -out .env.enc

if [ -f backups/winnie_backup.sql ]; then
  echo "Cifrando backups/winnie_backup.sql ..."
  openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in backups/winnie_backup.sql -out backups/winnie_backup.sql.enc
fi

echo "Listo. Archivos cifrados creados. Ya puedes commitearlos."
