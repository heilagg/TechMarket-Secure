#!/usr/bin/env bash
# Lab 10 - centralized provisioning with HashiCorp Vault.
# Starts Vault, enables the audit log, stores TechMarket secrets, creates a read-only
# policy + AppRole for the app and starts Vault Agent, which renders secrets to files.
# Usage (from anywhere):  infra/vault/bootstrap.sh
source "$(dirname "$0")/lib.sh"

echo "[1/6] starting Vault (dev mode)"
docker compose up -d --wait vault >/dev/null

echo "[2/6] audit device: every request is logged, secret values are HMAC-hashed"
{ vault audit list 2>/dev/null || true; } | grep -q '^file/' \
  || vault audit enable file file_path=/vault/logs/audit.log >/dev/null

echo "[3/6] storing secrets in KV v2: secret/techmarket/django, secret/techmarket/keycloak"
if ! vault kv get -mount=secret techmarket/django >/dev/null 2>&1; then
  gen | vault kv put   -mount=secret techmarket/django secret_key=-      >/dev/null
  gen | vault kv patch -mount=secret techmarket/django jwt_signing_key=- >/dev/null
  gen | vault kv put   -mount=secret techmarket/keycloak client_secret=- >/dev/null
fi

echo "[4/6] policy techmarket-app: read-only access to secret/techmarket/django only"
vault policy write techmarket-app - >/dev/null <<'HCL'
path "secret/data/techmarket/django" {
  capabilities = ["read"]
}
HCL

echo "[5/6] AppRole techmarket-app: machine login, tokens live 1h (max 4h)"
{ vault auth list 2>/dev/null || true; } | grep -q '^approle/' || vault auth enable approle >/dev/null
vault write auth/approle/role/techmarket-app \
  token_policies=techmarket-app token_ttl=1h token_max_ttl=4h secret_id_ttl=24h >/dev/null
mkdir -p approle rendered
vault read  -field=role_id      auth/approle/role/techmarket-app/role-id   > approle/role_id
vault write -f -field=secret_id auth/approle/role/techmarket-app/secret-id > approle/secret_id

echo "[6/6] starting Vault Agent"
rm -f rendered/*
docker compose up -d --force-recreate vault-agent >/dev/null
for _ in $(seq 1 30); do [ -s rendered/jwt_signing_key ] && break; sleep 1; done
[ -s rendered/jwt_signing_key ] || { echo "Agent did not render secrets: docker compose -f infra/vault/compose.yml logs vault-agent"; exit 1; }

echo
ls -l rendered/
echo
echo "Done. Run Django with file-provisioned secrets (from the repo root):"
echo "  DJANGO_SECRET_KEY_FILE=infra/vault/rendered/django_secret_key \\"
echo "  JWT_SIGNING_KEY_FILE=infra/vault/rendered/jwt_signing_key python manage.py runserver"
