#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No existe .env en la raiz del proyecto." >&2
  exit 1
fi

openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
  -in .env -out .env.enc

echo "Listo: .env.enc creado. Ya puedes commitearlo."
