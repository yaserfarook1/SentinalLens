# Live Tenant Testing Setup

## Prerequisites

Before connecting to your test tenant, you'll need:

1. **Azure CLI installed**: https://docs.microsoft.com/cli/azure/install-azure-cli
2. **Logged in to Azure**:
   ```bash
   az login
   ```
3. Your test tenant details:
   - Azure Subscription ID
   - Tenant ID
   - Resource Group Name
   - Sentinel Workspace Name (Log Analytics workspace name)

## Step 1: Gather Tenant Information

### Get Your Subscription ID
```bash
az account show --query id -o tsv
```
Save this as: `AZURE_SUBSCRIPTION_ID`

### Get Your Tenant ID
```bash
az account show --query tenantId -o tsv
```
Save this as: `AZURE_TENANT_ID`

### Get Resource Group Name
```bash
# List all resource groups
az group list --query "[].name" -o table

# Or if you know the workspace name:
az resource list --query "[?type=='Microsoft.OperationalInsights/workspaces' && name=='YOUR_WORKSPACE_NAME'] | [0].resourceGroup" -o tsv
```
Save this as: `RESOURCE_GROUP_NAME`

### Get Sentinel Workspace Name
```bash
# List all Log Analytics workspaces in your subscription
az monitor log-analytics workspace list --query "[].name" -o table
```
Save this as: `WORKSPACE_NAME`

## Step 2: Update Backend Configuration

Edit `backend/.env.local`:

```env
# Live Tenant Configuration
ENVIRONMENT=dev
DEBUG=true
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_KEY_VAULT_URL=https://test-vault.vault.azure.net/

# Optional - workspace IDs for direct API testing
AZURE_SENTINEL_WORKSPACE_ID=<workspace-name>
AZURE_LOG_ANALYTICS_WORKSPACE_ID=<workspace-name>
```

## Step 3: Verify Azure CLI Authentication

```bash
# Check if authenticated
az account show

# If not logged in, authenticate:
az login

# Switch to your test tenant if needed
az account set --subscription "<AZURE_SUBSCRIPTION_ID>"
```

The backend will automatically use `DefaultAzureCredential()` in dev mode, which will:
1. Check environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
2. Fall back to Azure CLI credentials (from `az login`)
3. Use Managed Identity in production

## Step 4: Restart Backend

```bash
cd backend
# Make sure venv is activated
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Restart with new config
python -m uvicorn src.main:app --reload
```

You should see in logs:
```
[AUDIT] Settings initialized for environment: dev
[AUDIT] Using DefaultAzureCredential (dev mode)
```

## Step 5: Test Connection

### Option A: Direct API Test (Recommended)

```bash
# Get access token
TOKEN=$(az account get-access-token --query accessToken -o tsv)

# Test listing workspaces
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/v1/workspaces

# Should return JSON with available workspaces
```

### Option B: Frontend UI Test

1. Open http://localhost:3000
2. Click "Sign in" (use mock auth or provide Bearer token)
3. Go to "New Audit"
4. Select your test workspace
5. Click "Start Audit"

## Step 6: Monitor Live Audit

Once audit starts, you'll see:

### Backend Logs
```
[AUDIT] Audit started: workspace=<name>
[AUDIT] Fetching tables from workspace...
[AUDIT] Analyzing analytics rules (X rules found)
[AUDIT] Calculating costs...
[AUDIT] Generating report...
```

### Frontend
- Progress screen updates with agent steps
- Real-time streaming via SSE
- Report appears automatically when complete

## Troubleshooting

### Error: "Cannot authenticate to Azure"
```
Fix: Run `az login` and make sure you're in the correct subscription
az account set --subscription "<SUBSCRIPTION_ID>"
```

### Error: "Workspace not found"
```
Fix: Verify the workspace name in your subscription
az monitor log-analytics workspace list --query "[].name" -o table
```

### Error: "Access denied / Insufficient permissions"
```
Fix: Ensure your user has:
- Reader role on the subscription
- Log Analytics Reader role on the workspace
- Microsoft Sentinel Contributor (if using newer RBAC)

Check with:
az role assignment list --subscription "<SUBSCRIPTION_ID>" --query "[?principalId=='<YOUR_OBJECT_ID>'] | [].roleDefinitionName"
```

### Logs show "DefaultAzureCredential" but tests fail
```
Fix: Restart backend after Azure CLI login
The credential instance is cached at startup
```

## What Gets Tested

### Live Data Collection
- ✅ List all tables in workspace
- ✅ Get ingestion volume (last 30 days)
- ✅ Extract analytics rules (KQL parsing)
- ✅ Analyze workbooks
- ✅ Check hunt queries
- ✅ Map data connectors

### Cost Calculation
- ✅ Real Azure pricing API data
- ✅ Daily/monthly/annual cost breakdown
- ✅ Savings by tier migration
- ✅ Multi-table aggregation

### Report Generation
- ✅ Archive candidates (0 rule coverage)
- ✅ Low usage candidates (1-2 rules)
- ✅ Active tables (3+ rules)
- ✅ Confidence scoring
- ✅ Warnings & manual review items

## Security Note

⚠️ **Development Only**

This setup uses your local Azure credentials. For production:
- Use Azure Key Vault for secrets
- Use Managed Identity in Container Apps
- Never commit Azure credentials to Git
- Rotate access keys every 90 days

## Common Azure CLI Commands

```bash
# List subscriptions
az account list --output table

# Show current subscription
az account show

# Switch subscription
az account set --subscription "<SUBSCRIPTION_ID>"

# List all resources of a type
az resource list --query "[?type=='Microsoft.OperationalInsights/workspaces']" -o table

# Show workspace details
az monitor log-analytics workspace show \
  --resource-group "<RESOURCE_GROUP>" \
  --workspace-name "<WORKSPACE_NAME>"

# Get latest activity log
az monitor activity-log list --max-items 10
```

## Next: Run Your First Live Audit

Once configured, test the full workflow:

1. **Frontend**: http://localhost:3000 → Dashboard
2. **New Audit**: Select your test workspace → Start
3. **Progress**: Watch real-time updates
4. **Report**: Review findings
5. **Approval**: (Optional) Execute tier changes

Expected duration: **2-5 minutes** depending on:
- Number of analytics rules (typical: 50-200)
- Workspace size (tables count)
- Network latency

Let me know if you hit any issues!
