# SentinelLens Security & OWASP LLM Top 10 Compliance

This document details the security architecture and compliance with OWASP LLM Top 10 risks.

## OWASP LLM Top 10 Mitigations

### LLM01 — Prompt Injection

**Risk**: Attacker crafts malicious prompts to hijack agent behavior.

**Mitigation**:
- Azure Prompt Shield on all user inputs and API responses before LLM ingestion
- Input validation with Pydantic schemas
- Rate limiting on audit job triggers
- Prompt Shield risk score threshold: >0.7 = reject
- All injection attempts logged to audit trail

**Implementation**: [backend/src/security.py](../backend/src/security.py) — `PromptShieldValidator`

### LLM02 — Insecure Output Handling

**Risk**: LLM output parsed as code or executed directly.

**Mitigation**:
- All LLM outputs parsed against strict Pydantic schemas
- Report schema validation enforces table names, tier values, confidence scores
- Invalid output rejected with error, never rendered or executed
- Output sanitized before logging

**Implementation**: [backend/src/models/report.py](../backend/src/models/report.py)

### LLM03 — Training Data Poisoning

**Risk**: Fine-tuned model poisoned with malicious training data.

**Mitigation**:
- N/A — SentinelLens uses Azure OpenAI hosted GPT-4o, not a custom fine-tuned model
- No training happens; model is base GPT-4o from Azure

### LLM04 — Model Denial of Service (DoS)

**Risk**: Attacker exhausts LLM token budget or compute resources.

**Mitigation**:
- Token budget enforcement: 50,000 tokens max per agent run
- Agent timeout: 600 seconds (10 minutes) max
- Tool call batching: complex data summarized before entering LLM
- Rate limiting: 100 API requests/minute per user
- Concurrent audit limit: 5 simultaneous jobs max

**Implementation**: [backend/src/config.py](../backend/src/config.py) — Budget enforcement, [backend/src/agents/orchestrator.py](../backend/src/agents/orchestrator.py) — Timeout handling

### LLM05 — Supply Chain

**Risk**: Vulnerable dependencies in project.

**Mitigation**:
- All dependencies pinned to specific versions in requirements.txt
- Azure Container Registry vulnerability scanning on every push
- SBOM (Software Bill of Materials) generated automatically
- Pre-commit hook: detect-secrets scans for leaked credentials
- Dependabot alerts enabled on GitHub

**Scanning Tools**:
- Trivy (container images)
- Dependabot (dependencies)
- SonarQube (code quality, optional)

### LLM06 — Sensitive Information Disclosure

**Risk**: PII or secrets exposed in LLM context or logs.

**Mitigation**:
- Microsoft Presidio two-stage masking:
  - Stage 1: Detect PII (IPs, emails, UPNs, hostnames, domains)
  - Stage 2: Replace with typed placeholders
- Applied to ALL data before LLM ingestion
- PII entities: EMAIL_ADDRESS, IP_ADDRESS, PERSON, DOMAIN_NAME, URL, PHONE_NUMBER, UPN, HOSTNAME, AZURE_RESOURCE_ID
- Placeholders preserved in final report for user verification
- Logs sanitized: tokens, keys, passwords masked before logging
- No raw API responses logged

**Implementation**: [backend/src/security.py](../backend/src/security.py) — `PiiMaskingPipeline`

### LLM07 — Insecure Plugin Design (Agent Tools)

**Risk**: Agent tools execute unvalidated commands or modify system state unsafely.

**Mitigation**:
- All agent tools are READ-ONLY by design
- Tools: list_tables, get_ingestion_volume, parse_rules, list_connectors, calculate_savings, generate_report
- NO write operations in agent tools
- Tier changes (write) are SEPARATE from agent, require explicit approval
- Tool inputs validated with Pydantic models
- Tool outputs validated and immutable

**Design**: Agent cannot execute tier changes directly; only recommend them.

### LLM08 — Excessive Agency

**Risk**: Agent executes actions beyond intended scope (e.g., deletes data, modifies rules).

**Mitigation**:
- Hard architectural separation:
  - Agent thread: Read-only, generates report only
  - Approval service: Separate FastAPI endpoint, separate service principal
- Tier changes require:
  1. Explicit user approval in frontend
  2. MFA authentication (Entra ID challenge)
  3. Security group membership verification
  4. Rate limiting (1 approval per 60 seconds per user)
- All approvals logged immutably
- User cannot bypass approval gate

**Design**: Two separate code paths, not a guardrail.

### LLM09 — Overreliance on LLM

**Risk**: Users trust recommendations without verification.

**Mitigation**:
- All recommendations include confidence scores (HIGH/MEDIUM/LOW)
- MEDIUM/LOW confidence recommendations marked for human review
- High confidence (zero rule coverage) still requires user approval
- Report includes warnings section for edge cases
- KQL parsing confidence logged (% successful parse)
- Complex KQL flagged for manual verification
- External dependencies (Power BI, external SIEM queries) flagged
- Explicit "verify before acting" disclaimer in approval dialog

**Implementation**: [backend/src/services/report_generator.py](../backend/src/services/report_generator.py)

### LLM10 — Model Theft

**Risk**: Attackers extract/steal the LLM model weights or API access.

**Mitigation**:
- GPT-4o hosted in Azure tenant (not external API)
- No model weights downloaded or exposed
- API calls authenticated via Managed Identity (no bearer token exposure)
- All API calls over HTTPS only
- Rate limiting prevents brute-force API access
- No model fine-tuning (base model only)

---

## Identity & Access Control

### Managed Identity (Production)

Backend runs with **User-Assigned Managed Identity**:
- No stored credentials, passwords, or keys
- Automatic token refresh via Azure
- RBAC scoped to minimum required permissions

**Permissions**:
- **Log Analytics Reader** — Read tables, run queries, fetch ingestion data
- **Sentinel Reader** — Read analytics rules, workbooks, hunt queries, connectors
- **Storage Blob Data Contributor** — Write audit logs and reports to Blob Storage

### Service Principals

- **Backend Identity**: Managed Identity (no password)
- **Approval Service Principal**: Separate SP with write-only access to tier change endpoint

### User Access (Frontend)

- **Authentication**: Entra ID via MSAL.js
- **Audit Access**: All users can view reports (Reader role)
- **Approval Access**: Entra security group membership required
- **MFA**: Optional (recommended for prod)

---

## Secrets Management

### Azure Key Vault

**What's stored**:
- AZURE_OPENAI_KEY — GPT-4o API key
- AZURE_OPENAI_ENDPOINT — Azure OpenAI endpoint
- CONTENT_SAFETY_KEY — Prompt Shield API key
- CONTENT_SAFETY_ENDPOINT — Prompt Shield endpoint

**Access**:
- Managed Identity: `get` permission only
- Approval SP: `get` + `list` permissions
- Humans: Access via Azure Portal (with RBAC)

**Rotation**:
- Every 90 days (or per compliance)
- No code changes required (Key Vault reference)
- See [CREDENTIAL_ROTATION.md](./CREDENTIAL_ROTATION.md)

**Never stored in**:
- Environment variables
- Configuration files
- Git repositories
- Container images
- Logs

---

## Data Flow Security

```
User Input
    ↓
[1] Prompt Shield (injection detection)
    ↓ (if safe)
[2] Pydantic Validation (input schema)
    ↓ (if valid)
[3] PII Masking (Presidio Stage 1 & 2)
    ↓ (masked)
[4] LLM Processing (GPT-4o in Azure tenant)
    ↓ (output)
[5] Pydantic Schema Validation (output schema)
    ↓ (if valid)
[6] Report Assembly (with confidence scores)
    ↓
[7] User Approval (MFA required)
    ↓ (approved)
[8] Tier Change Execution (separate service path)
    ↓
[9] Audit Logging (immutable)
    ↓
Report Generated
```

---

## Audit Logging

### Events Logged

- ✅ Secret access from Key Vault (metadata only, not value)
- ✅ Agent tool execution (tool name, result count)
- ✅ Authentication attempts (success/failure, user ID)
- ✅ Approval execution (user, tables modified, timestamp)
- ✅ API errors (sanitized message, no sensitive data)
- ✅ Prompt Shield rejections (risk score, reason)
- ✅ PII masking events (count of entities masked)

### Retention

- **Application Insights**: 90 days (searchable)
- **Audit logs (Table Storage)**: 365 days (immutable, compliance)
- **Approved reports**: 365 days (Blob Storage)

### Audit Log Table Schema

```sql
SentinelLensAudit_CL:
  - TimeGenerated (datetime)
  - EventType (string): SECRET_ACCESS, TOOL_EXECUTION, APPROVAL_EXECUTED, etc
  - Resource (string): What was accessed (e.g., "AZURE_OPENAI_KEY")
  - Status (string): SUCCESS, FAILURE
  - Details (string): Additional context (no sensitive data)
  - UserId (string): Entra ID object ID
```

---

## Network Security

- ✅ HTTPS only (no HTTP)
- ✅ CORS restricted to frontend domain only
- ✅ API Gateway rate limiting
- ✅ DDoS protection (Azure DDoS Standard)
- ✅ Firewall rules (restrictive, allow specific IPs if needed)
- ✅ Container Apps: No public ingress by default (API gateway only)

---

## Compliance & Standards

- ✅ OWASP LLM Top 10 (all 10 addressed)
- ✅ OWASP Top 10 (web app security)
- ✅ CWE/SANS Top 25 (common weaknesses)
- ✅ SOC 2 Type II controls (if applicable)
- ✅ Azure security best practices

---

## Security Code Review Checklist

Before merge, verify:

- [ ] No hardcoded secrets (detect-secrets passes)
- [ ] All credentials from Key Vault via `config.get_secret()`
- [ ] Managed Identity used (no SP passwords)
- [ ] All LLM inputs go through Prompt Shield
- [ ] All LLM outputs parsed against Pydantic schema
- [ ] PII masking applied before LLM ingestion
- [ ] Audit logging for all sensitive operations
- [ ] Error messages sanitized (no secrets, tokens, keys)
- [ ] HTTPS-only for all external calls
- [ ] CORS headers restrictive
- [ ] Rate limiting enabled
- [ ] Input validation with Pydantic
- [ ] RBAC roles scoped (least privilege)
- [ ] Pre-commit hooks pass (Black, Flake8, detect-secrets)
- [ ] Tests >80% coverage (especially security code)

---

## Incident Response

### If Secret is Compromised

1. **Revoke immediately**:
   ```bash
   # Regenerate the key in Azure
   az keyvault secret set --vault-name <vault> --name <secret> --value <new-value>
   ```

2. **Alert team**: @security-team
3. **Check audit logs** (last 24 hours)
4. **Update monitoring** (if needed)
5. **Post-incident review** (what happened, how to prevent)

### If Agent Behaves Unexpectedly

1. Check audit logs in Application Insights
2. Review LLM outputs (should match Pydantic schema)
3. Check Prompt Shield evaluations
4. Verify token budget was not exceeded
5. Restart agent thread if needed

---

## References

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Microsoft Security Best Practices](https://learn.microsoft.com/en-us/security/best-practices)
- [Azure OpenAI Security](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/safety-risk-assessment)
- [Microsoft Presidio](https://github.com/Microsoft/presidio)
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview)

---

**Last Updated**: February 27, 2026
**Maintained By**: Security Team
**Review Frequency**: Quarterly
