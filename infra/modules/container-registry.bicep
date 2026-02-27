@description('Azure Container Registry for backend Docker images')

param location string
param containerRegistryName string
param resourcePrefix string
param tags object

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags

  sku: {
    name: 'Basic'
  }

  properties: {
    adminUserEnabled: true  // For local dev; use managed identity in prod
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      retentionPolicy: {
        status: 'enabled'
        days: 30
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
    }
  }
}

// ===== VULNERABILITY SCANNING =====
// Azure will automatically scan pushed images for vulnerabilities
// Results appear in Azure Defender for Containers

// ===== OUTPUTS =====
output loginServer string = containerRegistry.properties.loginServer
output adminUsername string = containerRegistry.name
output acrId string = containerRegistry.id
