#!/usr/bin/env bash
# The centralized flow from the lecture, step by step over the Vault HTTP API:
# login -> token -> get secret -> least privilege check -> revoke -> audit log.
# Secret values are never printed. Run after bootstrap.sh.
source "$(dirname "$0")/lib.sh"

py() { python3 -c "import json,sys; d=json.load(sys.stdin); $1"; }

echo "1) AppRole login: role_id + secret_id -> short-lived token"
login=$(python3 -c 'import json; print(json.dumps({"role_id": open("approle/role_id").read().strip(), "secret_id": open("approle/secret_id").read().strip()}))' \
  | curl -sf -X POST --data @- "$VAULT_HTTP/v1/auth/approle/login")
token=$(printf '%s' "$login" | py 'print(d["auth"]["client_token"])')
printf '%s' "$login" | py 'a=d["auth"]; print("   OK, policies=%s, ttl=%ss" % (a["token_policies"], a["lease_duration"]))'
auth() { printf 'X-Vault-Token: %s\n' "$token"; }

echo "2) GET secret/techmarket/django with the token (values masked)"
curl -sf -H @<(auth) "$VAULT_HTTP/v1/secret/data/techmarket/django" \
  | py 'm=d["data"]["metadata"]; [print("   %s = **** (%d chars)" % (k, len(v))) for k, v in d["data"]["data"].items()]; print("   version %s, created %s" % (m["version"], m["created_time"][:19]))'

echo "3) GET secret/techmarket/keycloak (outside the policy)"
echo "   HTTP $(curl -s -o /dev/null -w '%{http_code}' -H @<(auth) "$VAULT_HTTP/v1/secret/data/techmarket/keycloak") (expected 403)"

echo "4) POST new value to secret/techmarket/django (policy is read-only)"
echo "   HTTP $(curl -s -o /dev/null -w '%{http_code}' -H @<(auth) -X POST --data '{"data":{"secret_key":"x"}}' "$VAULT_HTTP/v1/secret/data/techmarket/django") (expected 403)"

echo "5) revoke the token"
curl -sf -o /dev/null -X POST -H @<(auth) "$VAULT_HTTP/v1/auth/token/revoke-self" && echo "   revoked"
echo "   GET with the revoked token: HTTP $(curl -s -o /dev/null -w '%{http_code}' -H @<(auth) "$VAULT_HTTP/v1/secret/data/techmarket/django") (expected 403)"

echo "6) audit log: who did what (last 6 responses)"
docker compose exec -T vault tail -n 40 /vault/logs/audit.log | python3 -c '
import json, sys
rows = [json.loads(l) for l in sys.stdin if l.strip()]
for e in [r for r in rows if r.get("type") == "response"][-6:]:
    req, auth = e.get("request", {}), e.get("auth", {})
    print("   %s  %-6s %-34s policies=%s  %s" % (e.get("time", "")[11:19], req.get("operation"),
          req.get("path"), auth.get("token_policies") or auth.get("policies"), e.get("error") or "ok"))'
