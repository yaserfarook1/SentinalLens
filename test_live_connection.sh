#!/bin/bash
# Test Live Connection to PCS-Sentinel-Demo Workspace

echo "🔍 Testing SentinelLens Live Connection..."
echo ""

# Step 1: Verify subscription
echo "📋 Step 1: Verifying Azure subscription..."
CURRENT_SUB=$(az account show --query id -o tsv)
if [ "$CURRENT_SUB" == "b8f99f9f-c121-422b-a657-c999df2c5296" ]; then
    echo "✅ Correct subscription set"
else
    echo "⚠️  Wrong subscription. Switching..."
    az account set --subscription "b8f99f9f-c121-422b-a657-c999df2c5296"
fi

# Step 2: List workspaces
echo ""
echo "📦 Step 2: Listing workspaces in rg-jayesh..."
az monitor log-analytics workspace list \
    --resource-group "rg-jayesh" \
    --query "[].{Name: name, ResourceGroup: resourceGroup}" -o table

# Step 3: Get workspace details
echo ""
echo "📊 Step 3: Getting workspace details for PCS-Sentinel-Demo..."
az monitor log-analytics workspace show \
    --resource-group "rg-jayesh" \
    --workspace-name "PCS-Sentinel-Demo" \
    --query "{Workspace: name, ResourceGroup: resourceGroup, RetentionDays: retentionInDays, Location: location}" -o table

# Step 4: List tables in workspace
echo ""
echo "📑 Step 4: Querying tables in workspace..."
WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group "rg-jayesh" \
    --workspace-name "PCS-Sentinel-Demo" \
    --query id -o tsv)

echo "Workspace ID: $WORKSPACE_ID"

# Step 5: Test KQL query
echo ""
echo "🔎 Step 5: Running test KQL query..."
az monitor log-analytics query \
    --workspace "$WORKSPACE_ID" \
    --analytics-query "
        union withsource=TableName *
        | where TimeGenerated > ago(1d)
        | summarize Count=count() by TableName
        | order by Count desc
        | limit 20
    " \
    --query "[].{Table: TableName, RowCount: Count}" -o table 2>/dev/null || echo "⏳ Note: Tables may be empty or loading..."

# Step 6: Test connection for backend
echo ""
echo "✨ Step 6: Testing backend connection..."
TOKEN=$(az account get-access-token --query accessToken -o tsv)
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    http://127.0.0.1:8000/api/v1/workspaces)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Backend API responding correctly (HTTP $HTTP_CODE)"
    echo "Workspaces response:"
    echo "$RESPONSE" | head -n -1 | jq . 2>/dev/null || echo "$RESPONSE" | head -n -1
else
    echo "⚠️  Backend API returned HTTP $HTTP_CODE"
    echo "Make sure backend is running: python -m uvicorn src.main:app --reload"
fi

echo ""
echo "🎉 Connection test complete!"
