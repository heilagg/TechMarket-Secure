# Shared helpers for the Vault lab scripts (sourced, not executed).
set -euo pipefail
umask 077
cd "$(dirname "${BASH_SOURCE[0]}")"

[ -f .env ] || { echo "First: cp infra/vault/.env.example infra/vault/.env and set VAULT_DEV_ROOT_TOKEN"; exit 1; }
set -a; . ./.env; set +a
export HOST_UID HOST_GID
HOST_UID="$(id -u)"; HOST_GID="$(id -g)"
VAULT_HTTP=http://127.0.0.1:8200

# Vault CLI inside the server container as admin. The root token is read from the
# container's own env, so it never appears in a command line on the host.
vault() {
  docker compose exec -T vault sh -c \
    'VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN="$VAULT_DEV_ROOT_TOKEN_ID" exec vault "$@"' vault-cli "$@"
}

gen() { python3 -c 'import secrets; print(secrets.token_urlsafe(50), end="")'; }

fingerprint() { python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()[:12])' "$1"; }
