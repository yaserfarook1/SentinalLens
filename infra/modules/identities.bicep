@description('User-Assigned Managed Identity for SentinelLens backend')

param location string
param managedIdentityName string
param resourcePrefix string
param tags object

// ===== MANAGED IDENTITY =====
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// ===== ROLE ASSIGNMENTS =====
// These roles allow the backend to:
// - Read Sentinel rules, workbooks, connectors
// - Query Log Analytics tables
// - Read table tier configuration
// - Access Key Vault secrets

// Role: Log Analytics Reader (built-in)
// Allows reading tables, schemas, and running queries
var logAnalyticsReaderId = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

// Role: Sentinel Reader (built-in)
// Allows reading analytics rules, workbooks, hunt queries
var sentinelReaderId = '8d289c81-5859-4e34-8d97-83e9c41e8e9e'

// Note: Actual RBAC assignments should be done at subscription/workspace scope
// via Azure Portal or Azure CLI. These are placeholders for documentation.
// Example:
// az role assignment create \
//   --assignee <managed-identity-object-id> \
//   --role "Log Analytics Reader" \
//   --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace>

// ===== OUTPUTS =====
output managedIdentityId string = managedIdentity.id
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output managedIdentityClientId string = managedIdentity.properties.clientId
output managedIdentityResourceId string = managedIdentity.id
