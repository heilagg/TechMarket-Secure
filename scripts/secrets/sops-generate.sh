#!/usr/bin/env bash
# Generate fresh random secrets and encrypt them with SOPS + age.
# Plaintext is piped straight into sops and never written to disk.
# Usage (from the repo root):  scripts/secrets/sops-generate.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

command -v sops >/dev/null || { echo "sops not found: brew install sops age"; exit 1; }
if grep -q "REPLACE_WITH" .sops.yaml; then
  echo "Put your real age public keys into .sops.yaml first"; exit 1
fi

gen() { python3 -c 'import secrets; print(secrets.token_urlsafe(50))'; }

encrypt() {  # $1 = target file, stdin = plaintext dotenv
  if [ -e "$1" ]; then echo "$1 already exists, edit it with: sops edit $1"; return 0; fi
  sops encrypt --filename-override "$1" --input-type dotenv --output-type dotenv /dev/stdin > "$1"
  echo "created $1"
}

encrypt secrets/app.enc.env <<ENV
DJANGO_SECRET_KEY=$(gen)
JWT_SIGNING_KEY=$(gen)
ENV

encrypt secrets/infra.enc.env <<ENV
KC_DB_PASSWORD=$(gen)
KC_ADMIN_PASSWORD=$(gen)
TECHMARKET_CLIENT_SECRET=$(gen)
ENV
