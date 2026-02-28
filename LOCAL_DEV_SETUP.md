# SentinelLens Local Development Setup

## Prerequisites
- Python 3.13+ with venv
- Node.js 18+ with npm
- Git
- Text editor (VS Code recommended)

## Quick Start (2 terminals)

### Terminal 1: Backend (FastAPI)

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv
venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start backend server
python -m uvicorn src.main:app --reload
```

Backend runs on: **http://127.0.0.1:8000**
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Terminal 2: Frontend (Next.js)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start frontend dev server
npm run dev
```

Frontend runs on: **http://localhost:3000**

## Configuration

### Backend (.env.local)
Already created with test values. For production, update:
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`
- `AZURE_KEY_VAULT_URL`

### Frontend (.env.local)
Already created with:
- `NEXT_PUBLIC_TENANT_ID` - test tenant
- `NEXT_PUBLIC_CLIENT_ID` - test client
- `NEXT_PUBLIC_API_BASE_URL` - http://localhost:8000/api/v1

## Testing

### Run Backend Unit Tests
```bash
cd backend
python -m pytest tests/unit/ -v
```

**Current Status:** ✅ 19/19 tests passing

### Frontend Development
```bash
cd frontend
npm run dev        # Development with hot reload
npm run build      # Production build
npm run lint       # ESLint checks
```

## Troubleshooting

### Backend won't start
- Check `.env.local` exists in `backend/`
- Verify Python venv is activated
- Run: `pip install -r requirements.txt`

### Frontend styles not loading
- Clear Tailwind cache: `rm -rf .next/`
- Restart dev server: `npm run dev`

### Port already in use
- Backend port 8000: `lsof -i :8000` then kill process
- Frontend port 3000: `lsof -i :3000` then kill process

## Project Structure

```
backend/
  src/
    main.py              # FastAPI app entry
    config.py            # Configuration & secrets
    security.py          # PII masking & prompt shield
    api/
      auth.py            # Entra ID authentication
      routes.py          # API endpoints
    services/
      azure_api.py       # Azure SDK wrappers
      kql_parser.py      # KQL extraction
      cost_calculator.py # Savings calculation
    agents/
      orchestrator.py    # Agent orchestration
  tests/
    unit/                # Unit tests (19 tests)
    integration/         # Integration tests
  requirements.txt       # Python dependencies
  .env.local            # Local config (not committed)

frontend/
  app/
    layout.tsx          # Root layout
    dashboard/          # Dashboard screen
    audit/new/          # New audit form
    audit/[jobId]/      # Audit progress & report
    history/            # Historical reports
  components/
    auth/               # MSAL authentication
    report/             # Report components
    layout/             # Navigation & layout
  lib/
    auth.ts             # MSAL config
    api-client.ts       # Typed API client
  .env.local            # Local config (not committed)
  package.json          # Dependencies
```

## Key Features Working

✅ **Authentication**
- Mock auth (localStorage) for testing
- Real Entra ID auth via MSAL.js

✅ **API Communication**
- Frontend → Backend proxy configured
- Bearer token passed on all requests

✅ **Security**
- PII masking pipeline (regex-based)
- Prompt shield validator
- Data sanitization for logs

✅ **UI/UX**
- 6 screens fully built
- Tailwind CSS styling
- Responsive design

## Next Steps

1. **Test the Flow**
   - Open http://localhost:3000
   - Click "Sign in" (uses mock auth)
   - Navigate Dashboard → New Audit → Progress → Report → Approve

2. **Check API**
   - Visit http://127.0.0.1:8000/docs
   - Try endpoints (will fail without mock auth token)

3. **Review Logs**
   - Backend logs include [AUDIT] markers for security events
   - Frontend logs in browser console

4. **Phase 5 E2E Testing**
   - Mock Azure API calls to test agent workflow
   - Validate KQL parser with real Sentinel rules
   - Test cost calculation accuracy

## Common Commands

```bash
# Backend
cd backend
python -m uvicorn src.main:app --reload      # Start with hot reload
python -m pytest tests/unit/ -v              # Run tests
pip install <package-name>                   # Add dependency
pip freeze > requirements.txt                # Save versions

# Frontend
cd frontend
npm run dev                                   # Development
npm run build && npm start                   # Production
npm install <package-name>                   # Add dependency
npm list                                     # Check versions
```

## Support

- Backend errors appear in terminal where uvicorn runs
- Frontend errors appear in browser console (F12)
- Check `.env.local` files if services won't start
- Restart both services if making config changes
