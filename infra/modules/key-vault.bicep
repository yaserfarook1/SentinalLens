@description('Azure Key Vault for SentinelLens secrets management')

param location string
param keyVaultName string
param managedIdentityPrincipalId string
param resourcePrefix string
param environment string
param tags object

// ===== KEY VAULT =====
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags

  properties: {
    // Enable soft delete and purge protection
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true

    // Access control
    enableRbacAuthorization: true  // Use RBAC instead of access policies
    tenantId: subscription().tenantId

    // SKU
    sku: {
      family: 'A'
      name: environment == 'prod' ? 'premium' : 'standard'
    }

    // Network
    publicNetworkAccess: 'Enabled'  // Can be restricted to specific IPs in prod
  }
}

// ===== RBAC: Grant Managed Identity access to secrets =====
// Role: Key Vault Secrets User
// Allows the managed identity to GET secrets
var secretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource managedIdentitySecretsAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentityPrincipalId, secretsUserRoleId)
  scope: keyVault

  properties: {
    roleDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/${secretsUserRoleId}'
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ===== PLACEHOLDER SECRETS =====
// In production, populate these via Azure Portal or CLI:
// az keyvault secret set --vault-name <vault-name> --name <secret-name> --value <secret-value>

// Placeholder: Azure OpenAI Key
resource openaiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-KEY'
  properties: {
    value: '[POPULATE_IN_PRODUCTION]'
  }
}

// Placeholder: Content Safety Key (Prompt Shield)
resource contentSafetyKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'CONTENT-SAFETY-KEY'
  properties: {
    value: '[POPULATE_IN_PRODUCTION]'
  }
}

// ===== AUDIT LOGGING =====
// Enable Key Vault diagnostic settings
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${keyVaultName}-diagnostics'
  scope: keyVault

  properties: {
    workspaceId: ''  // Will be connected to Application Insights in monitoring module
    logs: [
      {
        category: 'AuditEvent'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 365  // 1 year retention
        }
      }
    ]
    metrics: []
  }
}

// ===== OUTPUTS =====
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
