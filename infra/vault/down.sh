#!/usr/bin/env bash
# Stop the lab Vault and wipe local credentials and rendered secrets.
source "$(dirname "$0")/lib.sh"
docker compose down -v
rm -rf approle rendered
echo "Vault stopped, approle/ and rendered/ removed"
