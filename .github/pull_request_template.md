## What does this PR change?
<!-- Short description + link to the task/issue -->

## Type
- [ ] Feature  - [ ] Bug fix  - [ ] Security fix  - [ ] Pipeline / infra  - [ ] Docs

## Security checklist (author)
- [ ] No secrets, tokens, passwords or `.env` files are committed
- [ ] All user input is validated on the server (forms / serializers)
- [ ] New endpoints have explicit authentication + permission classes
- [ ] Objects are always looked up with the current user (no IDOR)
- [ ] New dependencies are pinned in `requirements.txt` and pass `pip-audit`
- [ ] Tests added/updated for the change (incl. negative / abuse cases)
- [ ] `pre-commit run --all-files` passes locally

## Reviewer checklist
- [ ] CI `security-gate` is green; any new SAST finding is fixed or justified below
- [ ] Threat model updated if a new data flow / trust boundary is added

## Security findings justification (if any)
<!-- e.g. "semgrep techmarket-drf-allowany on login_view: intentional, login must be public; rate limited in #12" -->
