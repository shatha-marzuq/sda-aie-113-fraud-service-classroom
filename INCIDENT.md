# Incident Report — Leaked Secret (Drill)

## Summary
A fake `FRAUD_REGISTRY_TOKEN` was committed to `leaked_secret_test.txt`
(commit `ea4d4b4`) as part of Lab 6's secret-handling drill.
gitleaks detected it via the `generic-api-key` rule.

## Response — correct order

1. **Rotate first.**
   The moment a secret is committed, treat it as compromised — even if
   the branch is later deleted or the commit is removed. Clones, forks,
   CI caches, and the local reflog may already hold it. Rotation must
   happen before any history cleanup, because deleting a commit does
   NOT un-leak the secret.

2. **Rotate everything related, not just the one key.**
   Assume lateral discovery: if this token could unlock other systems
   or was issued alongside other credentials, rotate those too.

3. **Only then clean history.**
   Rewrite git history (e.g. `git filter-repo` or BFG) to remove the
   secret from all commits, then force-push and require every
   collaborator to re-clone.

4. **Add a preventive control.**
   Require `gitleaks` as a mandatory CI check and/or a pre-commit hook
   so this class of incident cannot land in `main` again.

## What NOT to do
- Do not simply delete the commit or force-push a "fix" and consider
  the incident closed — the secret is already burned.
- Do not skip rotation because the leak was "only for a few minutes."

## Outcome of this drill
- Fake token removed from the working tree.
- Rotation step is illustrative only (no real credential was ever valid).
- `gitleaks detect` confirmed detection; masking behaviour (structlog)
  verified separately to ensure real secrets never reach log output.