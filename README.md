# 🔍 SentinelLens

**AI-Powered Microsoft Sentinel Cost Optimization Agent**

Autonomously audit your Sentinel tenant, identify unused/low-frequency Log Analytics tables, calculate savings, and recommend tier migrations. Powered by Azure AI Foundry + GPT-4o.

---

## 🎯 What It Does

- **Discovers** all tables in your Sentinel workspace
- **Analyzes** which analytics rules, workbooks, and hunts use each table
- **Calculates** cost savings (50x delta between Hot and Archive tiers)
- **Generates** a detailed report with HIGH/MEDIUM/LOW confidence recommendations
- **Approves** tier changes through a human-gated approval workflow
- **Migrates** table tiers with one-click action

**Expected savings**: $3,000–$15,000/month for mid-size tenants (30–50% of tables typically unused).

---

## 📋 Prerequisites

### System Requirements
- Python 3.11+ (backend)
- Node.js 18+ (frontend)
- Azure CLI (`az` command)
- Git with pre-commit hooks

### Azure Requirements
- Sentinel workspace (Log Analytics)
- Azure OpenAI resource with GPT-4o deployed
- Azure AI Foundry project
- Azure Key Vault
- User-Assigned Managed Identity
- Appropriate RBAC roles (Reader on Sentinel, Log Analytics Reader)

### Development Setup

```bash
# Clone repo
git clone https://github.com/yourorg/sentinellens.git
cd sentinellens

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Local Environment File

```bash
# Copy the template
cp backend/.env.example backend/.env.local

# Fill in your Azure details (never commit .env.local)
# Get values from: az account show
# AZURE_SUBSCRIPTION_ID=<your-subscription>
# AZURE_TENANT_ID=<your-tenant>
# AZURE_KEY_VAULT_URL=https://<your-vault>.vault.azure.net/
```

---

## 🚀 Quick Start

### Phase 1: Foundation (Current)
- [x] Repository structure
- [x] Git security (pre-commit hooks, .gitignore)
- [x] Backend foundation (config, security, requirements)
- [x] Documentation (CLAUDE_CODE_SECURITY.md, this README)
- [ ] Bicep infrastructure (coming next)
- [ ] GitHub Actions CI/CD (coming next)

### Phase 2: Agent Core
- Azure API service layer (9 tools)
- KQL parser
- AI Foundry agent orchestration
- FastAPI backend
- Unit tests

### Phase 3: Security Hardening
- PII masking (Presidio)
- Prompt Shield integration
- Audit logging
- Secret rotation runbook

### Phase 4: Frontend
- Next.js + ShadCN UI
- 6 screens (Dashboard, New Audit, Progress, Report, Approval, History)
- Entra ID auth (MSAL.js)
- Real-time SSE progress

### Phase 5: Integration & Testing
- End-to-end testing on real Sentinel workspaces
- KQL parser validation (85%+ accuracy target)
- Load testing (1000+ tables)
- Security audit

### Phase 6: Production
- Deploy to production
- Monitoring & alerting
- SLOs & runbooks

---

## 🔐 Security

**SentinelLens is built with security-first approach:**

- ✅ **No secrets in code** — All credentials in Azure Key Vault
- ✅ **Managed Identity** — No service principal passwords stored
- ✅ **PII masking** — Presidio masks sensitive data before LLM
- ✅ **Prompt Shield** — Detects and rejects injection attempts
- ✅ **Audit logging** — All actions logged for compliance
- ✅ **Approval gates** — Hard separation, not guardrails
- ✅ **MFA required** — Production changes require authentication

**See**: [docs/CLAUDE_CODE_SECURITY.md](docs/CLAUDE_CODE_SECURITY.md) for detailed security practices.

---

## 📁 Project Structure

```
sentinellens/
├── backend/                    # FastAPI + Agent orchestration
│   ├── src/
│   │   ├── config.py          # Credential management (Key Vault)
│   │   ├── security.py        # PII masking, Prompt Shield
│   │   ├── agents/            # AI Foundry agent
│   │   ├── services/          # Azure APIs, KQL parser, cost calc
│   │   ├── models/            # Pydantic schemas
│   │   ├── api/               # FastAPI endpoints
│   │   └── utils/             # Logging, errors, sanitization
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example           # Never commit .env
│   └── Dockerfile
│
├── frontend/                  # Next.js + ShadCN UI
│   ├── app/                   # 6 screens + layouts
│   ├── components/            # Reusable components
│   ├── lib/                   # API client, auth, types
│   ├── package.json
│   └── .env.local.example
│
├── infra/                     # Bicep infrastructure-as-code
│   ├── main.bicep
│   ├── modules/               # Container Apps, Static Web Apps, Key Vault, etc
│   └── params.*.json          # dev, staging, prod
│
├── .github/
│   ├── workflows/             # CI/CD: test, build, deploy
│   └── CODEOWNERS             # Code review requirements
│
├── docs/
│   ├── CLAUDE_CODE_SECURITY.md  # This is critical — read it first
│   ├── SECURITY.md              # OWASP LLM Top 10 compliance
│   ├── ARCHITECTURE.md          # System design
│   ├── DEPLOYMENT.md            # Deployment runbook
│   └── CREDENTIAL_ROTATION.md   # Secret rotation procedures
│
└── .gitignore
```

---

## 🛠️ Development Workflow

### Making Changes

1. **Never commit secrets**
   ```bash
   pre-commit run --all-files  # Scan for secrets
   ```

2. **Code formatting**
   ```bash
   black backend/src/
   eslint frontend/
   ```

3. **Run tests**
   ```bash
   pytest backend/tests/ -v
   npm test --prefix frontend
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   git add <files>
   git commit -m "Add my feature"
   git push origin feature/my-feature
   ```

5. **Create a pull request**
   - Requires at least 1 review
   - All checks must pass (tests, linting, secret scan)
   - Security-critical files require @security-team review

---

## 🔧 Configuration

### Environment Variables (Backend)

```bash
# Safe to use env vars:
ENVIRONMENT=dev          # dev, staging, prod
DEBUG=False
AZURE_SUBSCRIPTION_ID=<your-subscription>
AZURE_TENANT_ID=<your-tenant>
AZURE_KEY_VAULT_URL=https://vault.vault.azure.net/

# All secrets fetched from Key Vault at runtime:
# - AZURE_OPENAI_KEY
# - AZURE_OPENAI_ENDPOINT
# - CONTENT_SAFETY_KEY
# - CONTENT_SAFETY_ENDPOINT
```

### Environment Variables (Frontend)

```bash
# Public (safe) variables only:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=<your-tenant-id>
NEXT_PUBLIC_CLIENT_ID=<app-registration-id>
```

---

## 📊 Monitoring

- **Application Insights**: All agent actions, API calls, approvals
- **Audit Logs**: Immutable record in Azure Table Storage
- **Alerts**: Agent failures, API latency, unauthorized access attempts

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Security Issues**: Contact @security-team immediately
- **Runbooks**: [docs/RUNBOOK_*.md](docs/)

---

## 📝 License

[Insert License Here]

---

## 🤝 Contributing

1. Read [docs/CLAUDE_CODE_SECURITY.md](docs/CLAUDE_CODE_SECURITY.md) first
2. All PRs require review
3. Security-critical files require @security-team approval
4. All tests must pass
5. Zero hardcoded secrets

---

**Built with Claude Code AI + Azure AI Foundry**

Last Updated: February 27, 2026
