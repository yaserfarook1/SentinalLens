# Setup Endpoint Fixed ✅

## What Was Wrong
The `POST /api/v1/setup/credentials` endpoint was returning **404 Not Found** even though the code was properly implemented. The root cause was **stale processes holding port 8000**, which prevented the backend from binding to that port.

## What Was Fixed
1. **Identified Port Conflict**: Multiple zombie processes were holding port 8000
2. **Started Backend on Port 8002**: Using an available port as a workaround
3. **Updated Frontend Config**: Changed `NEXT_PUBLIC_API_BASE_URL` to point to port 8002
4. **Verified Setup Endpoint Works**: Successfully tested credential saving to `.env.local`

## Current Running Setup

### Backend
```bash
# Terminal 1 - Backend (Port 8002)
cd d:\Development\Agents\SentinalLens\backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8002
```

✅ Running at: `http://127.0.0.1:8002`

### Frontend
```bash
# Terminal 2 - Frontend (Port 3000)
cd d:\Development\Agents\SentinalLens\frontend
npm run dev
```

✅ Running at: `http://localhost:3000`

## How to Use the Setup Endpoint

### Option 1: Via Frontend UI
1. Open `http://localhost:3000/setup`
2. Enter your Azure AD app registration details:
   - **Client ID (Application ID)**: Copy from Azure Portal → App registrations → Overview
   - **Client Secret**: Copy from Azure Portal → Certificates & secrets
3. Click **Configure Credentials**
4. Credentials are saved to `.env.local`

### Option 2: Via cURL
```bash
curl -X POST http://127.0.0.1:8002/api/v1/setup/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR-CLIENT-ID-HERE",
    "client_secret": "YOUR-CLIENT-SECRET-HERE"
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Credentials configured successfully",
  "env_file": "D:\\Development\\Agents\\SentinalLens\\backend\\.env.local",
  "note": "Please restart the backend for changes to take effect"
}
```

## Credentials Storage
After setup, credentials are stored in `.env.local`:
```
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

**Security Note**: This file is never committed to Git (in .gitignore). In production, these should be stored in Azure Key Vault.

## Next Steps for Production
1. Restart backend after updating credentials
2. Backend will automatically use `ClientSecretCredential` instead of personal Azure login
3. All subsequent Azure API calls will be authenticated as the service principal

## Port 8000 Cleanup (Long-term)
The stale processes on port 8000 require:
- Machine restart, OR
- Use `netsh` to force reset connections, OR
- Continue using port 8002

For now, use port 8002 in development. When deploying to Azure Container Apps, this issue won't occur.

## Verification
Test that the backend is using the right credentials:
```bash
curl http://127.0.0.1:8002/api/v1/health
# Should return: {"status":"healthy",...}
```

Access the frontend:
```bash
# Open browser to: http://localhost:3000
# Navigate to: http://localhost:3000/setup
```
