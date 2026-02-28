# Pull Instructions for VM Deployment

Everything has been committed and pushed to GitHub. You can now pull this on your VM.

## Quick Start on VM

```bash
# Clone or pull the latest
git clone https://github.com/yaserfarook1/SentinalLens.git
cd SentinalLens

# Or if already cloned:
git pull origin main
```

## Setup Credentials on VM

### Step 1: Configure Backend Credentials
```bash
cd backend
# Create .env.local with your Azure credentials
cat > .env.local << EOF
ENVIRONMENT=dev
DEBUG=false
APP_NAME=SentinelLens
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
FRONTEND_URL=http://localhost:3000
AZURE_CLIENT_ID=<your-app-registration-client-id>
AZURE_CLIENT_SECRET=<your-app-registration-client-secret>
EOF
```

### Step 2: Start Backend
```bash
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
# Backend will be available at: http://<vm-ip>:8000
```

### Step 3: Configure Frontend
```bash
cd frontend
# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_TENANT_ID=<your-tenant-id>
NEXT_PUBLIC_CLIENT_ID=<your-app-registration-client-id>
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
EOF

# Install dependencies
npm install

# Start frontend
npm run dev
# Frontend will be available at: http://localhost:3000
```

## What's Included

✅ **Backend (FastAPI)**
- All 9 Azure API integrations working
- KQL parser with confidence scoring
- Cost calculator using real Azure pricing
- Agent orchestrator (ReAct loop)
- SSE progress streaming
- Setup endpoint for credential management

✅ **Frontend (Next.js)**
- 6 complete screens: Dashboard, New Audit, Progress, Report, Approval, History
- Real-time progress updates
- Complete report analysis with tabs and charts
- Authentication with Azure AD (MSAL.js)

✅ **Security**
- No secrets in code (all in .env.local)
- ClientSecretCredential authentication
- PII masking before LLM
- Audit logging
- Bearer token validation

## Key Endpoints

```
POST   /api/v1/setup/credentials          - Configure credentials (no auth)
GET    /api/v1/health                     - Health check
GET    /api/v1/workspaces                 - List workspaces (auth required)
POST   /api/v1/audits                     - Start audit (auth required)
GET    /api/v1/audits/{job_id}            - Get audit status
GET    /api/v1/audits/{job_id}/stream     - SSE progress stream
GET    /api/v1/audits/{job_id}/report     - Get full report
POST   /api/v1/audits/{job_id}/approve    - Approve tier changes
```

## Running the Full Stack

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Testing the System

1. Open `http://localhost:3000/setup`
2. Enter your Azure AD credentials
3. Go to `http://localhost:3000/dashboard`
4. Click "New Audit" and select a workspace
5. Watch the progress in real-time
6. View the complete report with all analysis
7. Approve and execute tier migrations

## Real Azure Tenants Working

✅ Tested with real Azure credentials
✅ Returns real workspaces (50+ in demo tenant)
✅ Authentic authentication with Azure AD
✅ Production-ready code with no mocks

## Documentation Files

- `SETUP_ENDPOINT_FIXED.md` - What was fixed and why
- `TESTING_GUIDE.md` - Complete testing procedures
- `PROJECT_SUMMARY.md` - Project overview
- `EXECUTIVE_SUMMARY.md` - High-level summary

## Notes

- All files are UTF-8 with LF line endings
- No database required (uses Azure APIs directly)
- No external dependencies beyond requirements.txt
- All tests are in `backend/tests/`
- Run `pytest backend/tests/` to verify

Enjoy! 🚀
