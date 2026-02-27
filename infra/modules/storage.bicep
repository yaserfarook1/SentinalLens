@description('Azure Blob Storage for report storage')

param location string
param storageAccountName string
param managedIdentityPrincipalId string
param resourcePrefix string
param tags object

// ===== STORAGE ACCOUNT =====
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'

  sku: {
    name: 'Standard_LRS'
  }

  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

// ===== BLOB CONTAINER FOR REPORTS =====
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
}

resource reportsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'reports'
  parent: blobService

  properties: {
    publicAccess: 'None'
  }
}

// ===== BLOB CONTAINER FOR AUDIT LOGS =====
resource auditLogsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'audit-logs'
  parent: blobService

  properties: {
    publicAccess: 'None'
  }
}

// ===== RBAC: Grant Managed Identity access =====
// Role: Storage Blob Data Contributor
// Allows read/write to blobs
var storageBlobDataContributorId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

resource managedIdentityStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, managedIdentityPrincipalId, storageBlobDataContributorId)
  scope: storageAccount

  properties: {
    roleDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/${storageBlobDataContributorId}'
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ===== OUTPUTS =====
output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output reportsContainerName string = reportsContainer.name
output auditLogsContainerName string = auditLogsContainer.name
