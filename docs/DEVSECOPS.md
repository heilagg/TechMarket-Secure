# TechMarket – DevSecOps pipeline & developer setup

Owner: Student 2 (DevSecOps & Automation Lead)

## 1. Developer workflow (every change)

1. `git switch main && git pull` → `git switch -c feature/<short-name>`
2. Code + tests. Secrets go to `.env` (copy from `.env.example`), never into code.
3. `git commit` → **pre-commit hooks** run: private-key detection, gitleaks, bandit, semgrep custom rules, no direct commits to `main`.
4. `git push -u origin feature/<short-name>` → open a Pull Request (template has a security checklist).
5. **CI `security-pipeline`** runs; the PR can be merged only when `security-gate` is green **and** 1 code-owner approved.
6. Squash-merge, delete the branch.

## 2. Local setup

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt pre-commit
cp .env.example .env                                  # then set DJANGO_SECRET_KEY
pre-commit install
pre-commit run --all-files
python manage.py migrate && python manage.py runserver
```
Semgrep does not run natively on Windows – use WSL, or run `SKIP=semgrep git commit ...`; CI still enforces it.

## 3. Security gates

| Stage | Tool | Where | Fails the build when |
|---|---|---|---|
| Secret scanning | gitleaks (default + custom Django/Keycloak rules) | pre-commit, CI (full history) | any secret found |
| SAST | Bandit | pre-commit, CI | severity ≥ medium and confidence ≥ medium |
| SAST | Semgrep: p/django, p/python, custom `semgrep-rules/` | pre-commit (custom), CI | any ERROR-severity finding |
| SCA | pip-audit | CI | any known vulnerability in `requirements.txt` |
| SCA | Dependency Review, Dependabot | PRs / weekly | new dependency with high CVE |
| Config | `manage.py check --deploy` | CI | any warning for production settings |
| Tests | Django tests incl. IDOR / authz regression tests | CI | any failing test |

Reports: GitHub → Security → Code scanning (SARIF), and workflow artifacts.

## 4. Secrets management

* App configuration comes only from environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`).
* The app refuses to start without `DJANGO_SECRET_KEY`; `DEBUG` defaults to `False`.
* CI secrets are stored in GitHub → Settings → Secrets and variables → Actions (`DJANGO_SECRET_KEY_CI`).
* Infra secrets (Keycloak admin, DB, client secret) live in `infra/.env` (git-ignored).

### Secret rotation log
| Date | Secret | Reason | Action |
|---|---|---|---|
| 2026-10 | Django `SECRET_KEY` | Hardcoded in `settings.py` since the initial commit (found by custom gitleaks rule) | Moved to env var, new key generated, old key invalidated; fingerprint added to `.gitleaksignore` |

## 5. Handling a finding

* **True positive** → fix in the same PR (or open an issue labelled `security` with severity + owner).
* **False positive** → add `# nosemgrep: <rule-id>` / `# nosec <test-id>` **with a comment explaining why**; the reviewer must approve the justification.
* Never weaken a gate in `.github/workflows/` without approval of the DevSecOps lead (enforced by CODEOWNERS).
