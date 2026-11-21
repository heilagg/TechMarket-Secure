#!/usr/bin/env bash
# Rotation demo: write a new DJANGO secret_key to Vault and watch Vault Agent
# update the rendered file without anyone touching the app server.
source "$(dirname "$0")/lib.sh"

before=$(fingerprint rendered/django_secret_key)
echo "current file fingerprint: $before"
gen | vault kv patch -mount=secret techmarket/django secret_key=- >/dev/null
echo "new version: $(vault kv metadata get -mount=secret -format=json techmarket/django | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["current_version"])')"
echo "waiting for Vault Agent to re-render (up to 60s)..."
for _ in $(seq 1 60); do
  after=$(fingerprint rendered/django_secret_key)
  [ "$after" != "$before" ] && { echo "file fingerprint: $before -> $after"; break; }
  sleep 1
done
[ "$after" != "$before" ] || { echo "not re-rendered yet, check: docker compose -f infra/vault/compose.yml logs vault-agent"; exit 1; }
echo "Restart Django to load the new key (old sessions are invalidated, see SECRET_KEY_FALLBACKS)."
