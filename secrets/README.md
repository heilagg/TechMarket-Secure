# Encrypted secrets (SOPS + age)

Files here are encrypted with [SOPS](https://github.com/getsops/sops) and [age](https://github.com/FiloSottile/age).
Variable names stay readable, every value is `ENC[AES256_GCM,...]`, so the files are safe to commit and review.
Only `*.enc.env` files are allowed here; CI fails on anything else.

| File | Contains | Who can decrypt |
|---|---|---|
| `app.enc.env` | `DJANGO_SECRET_KEY`, `JWT_SIGNING_KEY` | developers, CI |
| `infra.enc.env` | `KC_DB_PASSWORD`, `KC_ADMIN_PASSWORD`, `TECHMARKET_CLIENT_SECRET` | developers |

Recipients are defined in `/.sops.yaml`.

```bash
# run Django with secrets injected as env vars (nothing decrypted to disk)
sops exec-env secrets/app.enc.env 'python manage.py runserver'

# start Keycloak with its secrets
sops exec-env secrets/infra.enc.env 'docker compose -f infra/docker-compose.yml up -d'

# change or rotate a value (opens $EDITOR on a decrypted temp copy, re-encrypts on save)
sops edit secrets/app.enc.env
```
