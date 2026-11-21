# TechMarket - secrets management (Lab 10)

## 1. Secrets inventory

| Secret | Used by | Dev | CI | Provisioning |
|---|---|---|---|---|
| `DJANGO_SECRET_KEY` | Django sessions, CSRF, signing | `secrets/app.enc.env` (SOPS) or Vault `secret/techmarket/django` | `secrets/app.enc.env` via `SOPS_AGE_KEY` | env or file (`DJANGO_SECRET_KEY_FILE`) |
| `JWT_SIGNING_KEY` | SimpleJWT access/refresh tokens | same as above | same as above | env or file (`JWT_SIGNING_KEY_FILE`) |
| `KC_DB_PASSWORD` | Keycloak PostgreSQL | `secrets/infra.enc.env` | not needed | env for docker compose |
| `KC_ADMIN_PASSWORD` | Keycloak admin console | `secrets/infra.enc.env` | not needed | env for docker compose |
| `TECHMARKET_CLIENT_SECRET` | OIDC client in Keycloak | `secrets/infra.enc.env`, Vault `secret/techmarket/keycloak` | not needed | env for docker compose |
| `SOPS_AGE_KEY` | decrypts `app.enc.env` in CI | - | GitHub Actions secret | env (masked) |
| `DJANGO_SECRET_KEY_CI` | existing test job | - | GitHub Actions secret | env (masked) |
| Vault root token, AppRole `secret_id` | Vault bootstrap / Vault Agent login | `infra/vault/.env`, `infra/vault/approle/` (git-ignored) | - | file |

Not secrets (plain config, may stay in `.env` or CI env): `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DJANGO_SECURE_SSL_REDIRECT`.

## 2. How the app reads secrets

`techmarket_project/settings.py` -> `secret(NAME)`:

1. `NAME_FILE` is set -> read the value from that file (file provisioning). Warns if the file is readable by group/others.
2. otherwise -> read `NAME` from the environment (env provisioning).
3. both set -> `ImproperlyConfigured` (ambiguous config fails closed). Required secret missing -> app does not start.

`.env` is only a local convenience; a key from `.env` is skipped when `NAME_FILE` is set.

## 3. Decentralized: SOPS + age

Encrypt locally with public keys, store the encrypted file in Git, decrypt only where the private key is.

```bash
brew install sops age
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt                # personal key (private part stays on the laptop)
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt     # add to ~/.zshrc
age-keygen -o ci.agekey                                  # CI key -> GitHub secret SOPS_AGE_KEY, then delete the file
# put both public keys (age1...) into .sops.yaml
scripts/secrets/sops-generate.sh                         # creates secrets/app.enc.env and secrets/infra.enc.env

sops exec-env secrets/app.enc.env 'python manage.py runserver'
sops exec-env secrets/infra.enc.env 'docker compose -f infra/docker-compose.yml up -d'
```

CI: `.github/workflows/secrets-provisioning.yml` checks that every value is encrypted, decrypts `app.enc.env` with `SOPS_AGE_KEY`, runs `check --deploy`, and verifies that the CI key cannot open `infra.enc.env`.

Rotation: `sops edit secrets/app.enc.env` -> commit -> redeploy. Revoking a person: remove their public key from `.sops.yaml`, `sops updatekeys`, and rotate the values (they could have copied them before).

## 4. Centralized: HashiCorp Vault

Store secrets in Vault, the app authenticates and gets only what its policy allows.

```bash
cp infra/vault/.env.example infra/vault/.env    # set VAULT_DEV_ROOT_TOKEN
infra/vault/bootstrap.sh                         # Vault + audit log + secrets + policy + AppRole + Vault Agent
DJANGO_SECRET_KEY_FILE=infra/vault/rendered/django_secret_key \
JWT_SIGNING_KEY_FILE=infra/vault/rendered/jwt_signing_key python manage.py runserver
infra/vault/demo-api.sh                          # login -> read -> 403 outside policy -> revoke -> audit log
infra/vault/rotate.sh                            # new value in Vault -> Agent re-renders the file
infra/vault/down.sh
```

| Piece | What it does |
|---|---|
| KV v2 `secret/techmarket/django` | `secret_key`, `jwt_signing_key`, versioned |
| Policy `techmarket-app` | `read` on `secret/data/techmarket/django` only |
| AppRole `techmarket-app` | machine login, token TTL 1h (max 4h), `secret_id` TTL 24h |
| Vault Agent | logs in with AppRole, renders each secret into a 0600 file, re-reads every 30s |
| Audit device | logs every request (secret values HMAC-hashed) |

The lab Vault runs in dev mode (in-memory, HTTP, root token). Production: server mode with storage, TLS, unseal/auto-unseal, root token revoked after setup.

## 5. Comparison

| | SOPS + age (decentralized) | Vault (centralized) |
|---|---|---|
| Where secrets live | Git, encrypted | Vault server |
| Extra infrastructure | none | Vault cluster (HA, backups, unseal) |
| Access control | per file, by list of public keys | policies per path, per identity |
| Audit | Git history (who changed), not who read | every read/write logged |
| Revoking access | remove key + re-encrypt + rotate values | revoke token / role immediately |
| Rotation | manual edit + redeploy | central update, Agent re-renders; dynamic secrets possible |
| Works offline / in CI | yes, only needs the private key | needs network access to Vault |
| Fits | small teams, GitOps, few secrets | many services, compliance, short-lived credentials |
