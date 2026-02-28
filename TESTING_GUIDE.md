# Testing Guide - SentinelLens Local Setup

## Quick Start (5 minutes)

### 1. Start the Full Stack
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8002

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Configure Credentials
Navigate to: **http://localhost:3000/setup**

Enter your Azure AD app registration credentials:
- Client ID: Copy from Azure Portal → App registrations
- Client Secret: Copy from Azure Portal → Certificates & secrets

Click **Configure Credentials** → Should see success message

### 3. Test the Full Workflow

#### a) View Dashboard
Go to: **http://localhost:3000/dashboard**
- See list of past audits (initially empty)
- See summary cards

#### b) Start New Audit
Click **New Audit** or go to: **http://localhost:3000/audit/new**
- Select workspace (dropdown populated from Azure)
- Set days lookback (default: 30)
- Click **Start Audit** → Redirected to progress page

#### c) Watch Progress
At: **http://localhost:3000/audit/[jobId]/progress**
- See real-time progress updates via SSE
- Progress bar showing steps completed
- Elapsed time
- Can cancel if needed

#### d) View Report
After completion, auto-redirected to: **http://localhost:3000/audit/[jobId]/report**
- Executive summary with totals
- Tabbed view:
  - Archive Candidates
  - Low Usage
  - Active Tables
  - Warnings
- Charts and detailed tables
- Download options (JSON/PDF)

#### e) Approval Flow
Click **Approve & Migrate** button
- See tier change summary
- Checkboxes to select which tables to migrate
- Live calculation of savings
- Confirmation dialog
- After approval, redirected to dashboard

## API Endpoint Testing

### Health Check
```bash
curl http://127.0.0.1:8002/api/v1/health
```

### Setup Credentials (No Auth Required)
```bash
curl -X POST http://127.0.0.1:8002/api/v1/setup/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR-CLIENT-ID",
    "client_secret": "YOUR-CLIENT-SECRET"
  }'
```

### List Workspaces (Requires Bearer Token)
```bash
# Get token from frontend (localStorage: 'auth_token')
export TOKEN=$(curl -s http://localhost:3000 | grep -o '"auth_token":"[^"]*"' | cut -d'"' -f4)

curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8002/api/v1/workspaces
```

## Troubleshooting

### Issue: "Connection Lost" on Progress Stream
**Fix**: Frontend should be using query parameter token, not Authorization header. Check `.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8002/api/v1
```

### Issue: 404 on Setup Endpoint
**Fix**: Make sure backend is running on port 8002 (not 8000):
```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8002
```

### Issue: Frontend Showing "Not Signed In"
**Fix**: Mock auth should auto-sign in. Check browser localStorage for `auth_token`.
If missing, click any button that requires auth and mock login will trigger.

### Issue: Report Showing "$NaN"
**Fix**: Ensure backend is fully restarted after credential changes:
```bash
# Kill old process
cmd /c taskkill /IM python.exe /F
# Restart backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8002
```

### Issue: Port Already in Use
```bash
# Find what's using port 8002
netstat -ano | grep 8002

# Kill the process
taskkill /PID <PID> /F

# Or use a different port
python -m uvicorn src.main:app --host 127.0.0.1 --port 9000
# Then update frontend .env.local NEXT_PUBLIC_API_BASE_URL
```

## Expected Behavior

### Successful Setup Flow
1. ✅ Frontend form accepts Client ID and Secret
2. ✅ POST to `/api/v1/setup/credentials` succeeds (200 OK)
3. ✅ Credentials saved to `.env.local`
4. ✅ Success message shown: "Credentials configured successfully!"
5. ✅ Auto-redirect to dashboard after 2 seconds

### Successful Audit Flow
1. ✅ Dashboard shows workspace list
2. ✅ New Audit form populated with workspaces
3. ✅ Click "Start Audit" creates job and shows progress
4. ✅ Progress bar updates in real-time (SSE stream)
5. ✅ Report loads with all sections (Archive/Low Usage/Active/Warnings)
6. ✅ Charts and tables render correctly
7. ✅ Approval flow allows selecting tables and approving migration

## Performance Baselines

- Health check: < 50ms
- Setup credentials: < 100ms
- Workspace list: < 500ms (depends on Azure API)
- Start audit: < 200ms
- SSE progress: Real-time updates
- Report generation: < 2 seconds (for small workspaces, scales with table count)

## Security Checks

- [ ] No auth token visible in URLs (query params only for SSE)
- [ ] No secrets logged in console
- [ ] .env.local never committed to Git
- [ ] Setup endpoint has no authentication (for initial setup only)
- [ ] Audit endpoints require Bearer token
- [ ] Approval endpoint requires Bearer token + approval group
