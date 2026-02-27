# Claude Code Security Guidelines for SentinelLens

This document establishes security practices specific to Claude Code AI-assisted development on the SentinelLens project.

## ✅ Core Principles

### 1. No Secrets in Code or Git

**RULE**: Secrets NEVER leave Azure Key Vault. Period.

- ❌ **DO NOT** store API keys, connection strings, or credentials in:
  - Environment variables (except safe values like ENVIRONMENT)
  - `.env` files (which can be accidentally committed)
  - Code comments or docstrings
  - Configuration files
  - Test fixtures

- ✅ **DO** store all secrets in Azure Key Vault
- ✅ Use Managed Identity for all Azure API authentication
- ✅ Fetch secrets at runtime using `config.get_secret()`
- ✅ Cache secrets in memory after fetching (don't refetch per request)

**Example** ✅ (CORRECT):
```python
from src.config import settings

api_key = settings.get_secret("AZURE_OPENAI_KEY")  # Fetched from Key Vault
```

**Example** ❌ (WRONG):
```python
import os
api_key = os.environ["AZURE_OPENAI_KEY"]  # Never do this
```

### 2. Managed Identity is the Auth Mechanism

**RULE**: Use Managed Identity (User-Assigned) for all Azure API calls in production. Never store service principal credentials.

- In **production**: Managed Identity credential
- In **local dev**: DefaultAzureCredential (falls back to local auth)
- In **tests**: Mocked credentials (never real ones)

**File**: [backend/src/config.py](../backend/src/config.py) — handles all credential management

### 3. Audit Logging for All Sensitive Operations

**RULE**: Every credential access, API call, and approval action must be logged (metadata only, never values).

Sensitive operations requiring audit logs:
- Secret fetch from Key Vault
- Agent tool execution
- Approval execution (tier changes)
- API calls from backend to Azure services
- Failed authentication attempts
- Prompt injection rejections

**Format**: All audit events logged with `[AUDIT]` tag in logs and searchable in Application Insights.

**Example** ✅:
```python
logger.info(f"[AUDIT] Secret fetched: AZURE_OPENAI_KEY (version: abc123...)")
logger.info(f"[AUDIT] Agent tool executed: list_analytics_rules (result_count: 42)")
logger.error(f"[AUDIT] Secret fetch FAILED: AZURE_OPENAI_KEY - Auth error")
```

### 4. Pre-commit Hooks Detect Secrets

**RULE**: Git pre-commit hooks scan all staged files for secret patterns before allowing commits.

**Patterns detected**:
- AWS keys (AKIA...)
- Azure connection strings
- JWT tokens
- Private keys (.key, .pem, .cer)
- Passwords in code

**Setup**:
```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

**Before committing**:
```bash
git add <files>
detect-secrets scan  # Runs automatically via pre-commit hook
git commit -m "..."
```

If secrets are detected:
1. Remove the secret immediately
2. Revoke the leaked credential
3. Re-add to Key Vault
4. Try commit again

### 5. Code Review Required for Security-Sensitive Files

**RULE**: Any changes to credential/secret handling require peer review.

**Files requiring review**:
- `backend/src/config.py` — credential management
- `backend/src/security.py` — PII masking, injection detection
- `backend/src/api/auth.py` — authentication logic
- `infra/modules/key-vault.bicep` — secrets infrastructure
- `infra/modules/identities.bicep` — RBAC role assignments
- `.github/workflows/*.yml` — CI/CD security

**Review checklist**:
- [ ] No hardcoded secrets
- [ ] All secrets fetched from Key Vault
- [ ] Managed Identity credentials used (not service principal passwords)
- [ ] Audit logging present
- [ ] Error messages don't leak sensitive data
- [ ] HTTPS-only for external calls
- [ ] Rate limiting / request throttling

### 6. MFA Required for Production Deployments

**RULE**: Tier changes in production require multi-factor authentication.

- Frontend approval flow triggers Entra ID MFA challenge
- Approval service principal has write access only to tier-change endpoint
- All approval actions logged with user identity and timestamp

**Cannot be bypassed** — approval gate is architectural separation, not a guardrail.

### 7. GitHub Security

**RULE**: Protect the main branch and use GitHub security features.

**Setup**:
```bash
# Install GitHub CLI
gh auth login
gh repo edit --enable-branch-protection=main

# Require:
# - At least 1 review before merge
# - Status checks must pass (tests, secret scan, linting)
# - Dismiss stale reviews on push
# - Require branches up-to-date before merge
# - Restrict who can force push (admins only)
```

**Code owners** (in `.github/CODEOWNERS`):
```
# Security-critical files require specific team approval
backend/src/config.py @security-team
backend/src/security.py @security-team
infra/modules/key-vault.bicep @infra-team
.github/workflows/ @devops-team
```

**No personal access tokens** — use GitHub App tokens instead:
```bash
# ❌ Never: git clone https://<PAT>@github.com/...
# ✅ Always: Use GitHub App tokens or SSH keys for automation
```

### 8. Secret Rotation Schedule

**RULE**: Rotate secrets every 90 days (or per compliance requirements).

**Schedule**:
- Azure OpenAI keys: Every 90 days
- Database passwords: Every 120 days
- Service principal credentials: Every 90 days
- Certificates: Before expiration (set up alerts 30 days before)

**Rotation procedure** (no code changes required):
1. Generate new secret in Azure Portal / Key Vault
2. Update Key Vault secret value
3. Verify backend can access new secret (test in dev first)
4. Delete old secret from Key Vault
5. Document in CHANGELOG

**File**: [docs/CREDENTIAL_ROTATION.md](./CREDENTIAL_ROTATION.md) — detailed runbook

### 9. No Environment Variable Secrets

**RULE**: Environment variables in Container Apps, CI/CD, or local dev must never contain secrets.

❌ **DO NOT**:
```bash
export AZURE_OPENAI_KEY="sk-..."  # Wrong!
docker run -e AZURE_OPENAI_KEY="sk-..." myapp  # Wrong!
AZURE_OPENAI_KEY: "sk-..." # In deployment manifest # Wrong!
```

✅ **DO**:
```bash
# In Container Apps: Mount secret from Key Vault reference
"secureEnvironmentVariables": {
  "AZURE_KEY_VAULT_URL": "@Microsoft.KeyVault(SecretUri=https://vault.vault.azure.net/secrets/KEY_VAULT_URL/)"
}

# In GitHub Actions: Use GitHub Secrets, not env vars
- name: Deploy
  env:
    DEPLOYMENT_KEY: ${{ secrets.DEPLOYMENT_KEY }}  # GitHub secret
```

### 10. Data Sanitization in Logs

**RULE**: Never log API responses, error messages, or data containing secrets.

**Sanitize before logging**:
- Bearer tokens → `[REDACTED_BEARER_TOKEN]`
- API keys → `[REDACTED_API_KEY]`
- Connection strings → `[REDACTED_CONNECTION_STRING]`
- Passwords → `[REDACTED_PASSWORD]`

**Use the sanitizer**:
```python
from src.utils.sanitizer import data_sanitizer

try:
    response = call_azure_api()  # May contain secrets
except Exception as e:
    # Sanitize error before logging
    logger.error(f"API call failed: {data_sanitizer.sanitize_error(e)}")
```

---

## 📋 Claude Code Workflow Checklist

When Claude Code makes changes, verify:

### Before Coding
- [ ] Read CLAUDE_CODE_SECURITY.md (this file)
- [ ] Check if changes touch security-critical files (config.py, security.py, auth.py)
- [ ] Identify secrets that might be involved

### During Coding
- [ ] No hardcoded secrets anywhere
- [ ] All credential access goes through `config.get_secret()`
- [ ] Audit logging present for sensitive operations
- [ ] Error messages sanitized before logging
- [ ] HTTPS-only for all external calls
- [ ] Request validation with Pydantic (all inputs typed)
- [ ] LLM outputs parsed, never executed

### Before Committing
- [ ] Run `detect-secrets scan` — must find zero secrets
- [ ] Run `black` formatter on Python code
- [ ] Run `flake8` linter
- [ ] Run unit tests: `pytest backend/tests/unit -v`
- [ ] Review code for sensitive data leaks

### Before Creating PR
- [ ] Security-critical file changes? Tag @security-team
- [ ] Infrastructure changes? Tag @infra-team
- [ ] Add tests for new auth/credential logic
- [ ] Update CHANGELOG with security notes if applicable

### Code Review
- [ ] Peer reviews all changes to security files
- [ ] CI/CD checks pass (tests, linting, secret scan)
- [ ] At least 1 approval before merge

---

## 🚨 Emergency Response

### If a Secret is Accidentally Committed

**IMMEDIATE ACTIONS** (within 5 minutes):
1. Do NOT push to main
2. Revoke the leaked credential immediately (e.g., regenerate API key)
2. Remove secret from the commit:
   ```bash
   git reset --soft HEAD~1  # Undo last commit
   # Remove the secret from files
   git add <fixed-files>
   git commit -m "Remove accidentally committed secret"
   ```
3. Force push to your branch (not main): `git push -f origin feature/my-branch`
4. Update Key Vault with new secret value
5. Inform @security-team immediately
6. Create incident report

### If Credentials Are Compromised

1. **Alert @security-team immediately**
2. Revoke all credentials immediately:
   - Regenerate Azure OpenAI keys
   - Rotate service principal credentials
   - Regenerate any leaked API keys
3. Check audit logs for unauthorized access (last 24 hours)
4. Update monitoring/alerts
5. Post-incident: Review what happened and update safeguards

---

## 📚 Related Documentation

- [SECURITY.md](./SECURITY.md) — OWASP LLM Top 10 compliance
- [CREDENTIAL_ROTATION.md](./CREDENTIAL_ROTATION.md) — Secret rotation runbook
- [backend/src/config.py](../backend/src/config.py) — Credential management code
- [backend/src/security.py](../backend/src/security.py) — PII masking and Prompt Shield
- [.gitignore](../.gitignore) — Git ignore patterns (secrets, env files)

---

## Questions?

- **Credential/Secret Questions**: Refer to config.py code + docstrings
- **Audit Logging**: Check logger calls with `[AUDIT]` tag in all sensitive functions
- **OWASP LLM Issues**: See SECURITY.md
- **Emergency**: Contact @security-team

---

**Last Updated**: February 27, 2026
**Maintained By**: Security Team
**Review Frequency**: Quarterly
