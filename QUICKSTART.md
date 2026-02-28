# SentinelLens - Quick Start Guide

Get SentinelLens running in 10 minutes (local development).

## Prerequisites

- Node.js 18+
- Python 3.11+
- Git
- Azure subscription (for backend)
- Entra ID tenant

## Quick Start - Local Development

### 1. Clone & Setup

```bash
git clone <repo-url>
cd SentinelLens

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

**Backend:**
```bash
# backend/.env.local
ENVIRONMENT=dev
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
DEBUG=true

# For local dev (these will be fetched from Key Vault in production):
AZURE_OPENAI_KEY=<test-key>
AZURE_OPENAI_ENDPOINT=<test-endpoint>
CONTENT_SAFETY_KEY=<test-key>
CONTENT_SAFETY_ENDPOINT=<test-endpoint>
```

**Frontend:**
```bash
# frontend/.env.local
NEXT_PUBLIC_TENANT_ID=your-tenant-id
NEXT_PUBLIC_CLIENT_ID=your-client-id
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Start Backend

```bash
cd backend
python -m uvicorn src.main:app --reload
```

✅ Backend running: http://localhost:8000
✅ API docs: http://localhost:8000/docs

### 4. Start Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

✅ Frontend running: http://localhost:3000

### 5. Access Application

1. Open http://localhost:3000
2. Click "Sign in with Microsoft"
3. Login with your Azure AD account
4. Navigate to Dashboard
5. Create a test audit

## Running Tests

### Backend Tests

```bash
cd backend

# All tests
pytest -v

# Just unit tests
pytest tests/unit/ -v

# Just integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=src --cov-report=html
```

✅ Expected: 19+ tests passing

### Frontend Tests

```bash
cd frontend

# Run tests
npm run test

# With coverage
npm run test -- --coverage
```

## Project Structure

```
SentinelLens/
├── backend/          # FastAPI + Agent (port 8000)
├── frontend/         # Next.js app (port 3000)
├── infra/            # Bicep templates (Azure IaC)
├── docs/             # Documentation
└── README.md         # Full README
```

## Key Files to Review

**Backend:**
- `backend/src/services/azure_api.py` - Azure SDK integration
- `backend/src/services/kql_parser.py` - KQL table extraction
- `backend/src/agents/orchestrator.py` - Agent 9-step ReAct loop
- `backend/src/services/cost_calculator.py` - Cost calculations

**Frontend:**
- `frontend/app/dashboard/page.tsx` - Main dashboard screen
- `frontend/lib/api-client.ts` - Type-safe API client
- `frontend/components/auth/ProtectedRoute.tsx` - Auth guard

## Common Commands

```bash
# Backend
python -m uvicorn src.main:app --reload  # Start dev server
pytest -v                                  # Run tests
python -m black src/                      # Format code
python -m pylint src/                     # Lint code

# Frontend
npm run dev                               # Start dev server
npm run build                             # Production build
npm run test                              # Run tests
npm run lint                              # Lint code
npm run type-check                        # TypeScript check
```

## Testing the Full Flow

### Manual E2E Test

1. **Login**
   - Click "Sign in with Microsoft"
   - Authenticate with your Azure AD account

2. **Create Audit**
   - Click "New Audit" button
   - Select a test workspace
   - Click "Start Audit"

3. **Monitor Progress**
   - Watch real-time progress updates
   - Monitor elapsed time
   - See each step completed

4. **View Report**
   - After completion, automatically redirected to report
   - Review archive candidates, low usage, active tables

5. **Approve Migration** (if test workspace)
   - Click "Approve & Migrate"
   - Select tables to archive
   - Click "Approve & Migrate"

6. **Check Dashboard**
   - Return to Dashboard
   - Verify audit appears in list
   - Confirm savings calculated

## Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Check port 8000
lsof -i :8000  # Check what's using port 8000

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Frontend Won't Start

```bash
# Check Node version
node --version  # Should be 18+

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Try different port
npm run dev -- --port 3001
```

### Authentication Fails

- Verify `NEXT_PUBLIC_TENANT_ID` is correct
- Verify `NEXT_PUBLIC_CLIENT_ID` is correct
- Check Azure App Registration redirect URI matches `http://localhost:3000/auth/redirect`
- Check browser console for MSAL errors

### API Calls Fail

- Verify backend is running on http://localhost:8000
- Check `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`
- Check browser console Network tab for failed requests
- Verify CORS headers (should be `*` in dev)

## Next Steps

1. **Read Documentation**
   - [Project Summary](./PROJECT_SUMMARY.md)
   - [Architecture](./docs/ARCHITECTURE.md)
   - [Security](./docs/SECURITY.md)

2. **Explore Code**
   - Start with `backend/src/main.py` (entry point)
   - Review `backend/src/agents/orchestrator.py` (agent logic)
   - Check `frontend/app/dashboard/page.tsx` (main UI)

3. **Run Tests**
   - `pytest tests/unit/ -v` (backend unit tests)
   - `npm run test` (frontend tests)

4. **Deploy**
   - See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for production setup
   - Review Bicep templates in `infra/` folder

## Useful Links

- **Backend API Docs:** http://localhost:8000/docs
- **Azure Portal:** https://portal.azure.com
- **GitHub Repo:** (see README)
- **Documentation:** See `/docs` folder

## Performance Tips

### For Faster Builds

```bash
# Frontend - skip type checking during dev
SKIP_ENV_VALIDATION=1 npm run dev

# Backend - use uvloop for faster event loop
pip install uvloop
```

### For Better DevEx

```bash
# Frontend - install VSCode extensions
# - ES7+ React/Redux/React-Native snippets
# - Tailwind CSS IntelliSense
# - TypeScript Vue Plugin

# Backend - install VSCode extensions
# - Python
# - Pylance
# - Python Docstring Generator
```

## What's Happening Under the Hood

### When you click "Start Audit":

```
1. Frontend sends POST /audits with workspace ID
2. Backend creates job ID
3. Frontend navigates to progress page
4. Backend starts Agent with 9 steps:
   - List tables from workspace
   - Get ingestion volume per table
   - Parse analytics rules for table refs
   - Parse workbooks for table refs
   - Parse hunt queries for table refs
   - Map data connectors to tables
   - Calculate tier migration savings
   - Generate structured report
   - Store report to database
5. Frontend streams real-time progress via SSE
6. On completion, frontend auto-redirects to report
7. User reviews recommendations & approves
```

### Cost Calculation Example:

```
Table: AuditLogs
Current tier: Hot ($0.10/GB/day)
Ingestion: 0.1 GB/day
Coverage: 0 analytics rules

Archive tier: Archive ($0.002/GB/day)
Monthly savings: (0.1 × 0.10 × 30) - (0.1 × 0.002 × 30) = $0.294
Annual savings: $0.294 × 12 = $3.53

Recommendation: Archive (0 rule coverage, HIGH confidence)
```

## Architecture Overview

```
                Frontend (Next.js)
                    ↓ HTTPS
                [MSAL Auth]
                    ↓
                Backend (FastAPI)
             [Security Middleware]
                    ↓
            [Agent Orchestrator]
           (9-step ReAct loop)
                 /  |  \
                /   |   \
         Azure API  KQL   Cost
         Service  Parser  Calc
              ↓      ↓      ↓
         [Real APIs - Managed Identity]
```

## Getting Help

1. **Check Logs**
   - Backend: Check console for error traces
   - Frontend: Check browser DevTools
   - API: Check backend logs for failed requests

2. **Read Docs**
   - API endpoints: See `/docs` on backend
   - Component props: Check component imports
   - Type definitions: Check `lib/types.ts`

3. **Run Tests**
   - Unit tests verify core logic
   - Integration tests verify workflows

## Resources

- **Next.js Docs:** https://nextjs.org/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Azure SDK:** https://learn.microsoft.com/en-us/azure/developer/python/
- **MSAL.js:** https://github.com/AzureAD/microsoft-authentication-library-for-js
- **TailwindCSS:** https://tailwindcss.com/docs

## Production Checklist

Before deploying to production, verify:

- [ ] All tests passing (`pytest -v` and `npm run test`)
- [ ] No secrets in `.env` files
- [ ] Environment variables configured in Azure Key Vault
- [ ] Backend Docker image builds
- [ ] Frontend Docker image builds
- [ ] Bicep templates validate
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Monitoring configured (Application Insights)
- [ ] Runbooks documented

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for full production setup.

---

**Happy coding! 🚀**

Questions? See documentation or open a GitHub issue.
