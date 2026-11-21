# Vault Agent for TechMarket: AppRole auto-auth + templates that write one secret per file.
# Django reads them via DJANGO_SECRET_KEY_FILE / JWT_SIGNING_KEY_FILE.

vault {
  address = "http://vault:8200"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path                   = "/vault/approle/role_id"
      secret_id_file_path                 = "/vault/approle/secret_id"
      remove_secret_id_file_after_reading = false
    }
  }
}

template_config {
  static_secret_render_interval = "30s" # re-read KV so rotated values reach the files
  exit_on_retry_failure         = true
}

template {
  contents    = "{{ with secret \"secret/data/techmarket/django\" }}{{ .Data.data.secret_key }}{{ end }}"
  destination = "/vault/rendered/django_secret_key"
  perms       = "0600"
}

template {
  contents    = "{{ with secret \"secret/data/techmarket/django\" }}{{ .Data.data.jwt_signing_key }}{{ end }}"
  destination = "/vault/rendered/jwt_signing_key"
  perms       = "0600"
}
