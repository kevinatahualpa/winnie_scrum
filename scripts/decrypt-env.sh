#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.enc ]; then
  echo "No existe .env.enc en la raiz del proyecto." >&2
  exit 1
fi

if [ -f .env ]; then
  echo "Ya existe .env. Renombralo o borralo antes de continuar." >&2
  exit 1
fi

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -in .env.enc -out .env

echo "Listo: .env restaurado."
