@description('SentinelLens Infrastructure as Code (IaC)')
@description('Deploys all Azure resources required for the SentinelLens application')
@minLength(1)
@maxLength(64)
param location string = 'eastus'

@description('Environment: dev, staging, prod')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Application name (used for naming all resources)')
param appName string = 'sentinellens'

@description('Resource group tags')
param tags object = {
  environment: environment
  application: appName
  managedBy: 'terraform'
  costCenter: 'security'
}

// ===== NAMING CONVENTION =====
// All resources follow pattern: <appName>-<resource-type>-<env>
// Example: sentinellens-kv-dev, sentinellens-ca-dev

var resourcePrefix = '${appName}-${environment}'

// ===== STORAGE NAMES (must be globally unique, no hyphens) =====
var storageAccountName = '${appName}${environment}storage${uniqueString(resourceGroup().id)}'
var keyVaultName = '${appName}-kv-${environment}'
var appInsightsName = '${resourcePrefix}-ai'
var containerRegistryName = '${appName}${environment}acr'
var containerAppEnvName = '${resourcePrefix}-cae'
var backendAppName = '${resourcePrefix}-backend'
var frontendAppName = '${resourcePrefix}-frontend'
var managedIdentityName = '${resourcePrefix}-identity'

// ===== DEPLOYMENT SEQUENCE =====
// 1. Managed Identity
// 2. Key Vault (with identity permissions)
// 3. Container Registry
// 4. Application Insights
// 5. Container Apps Environment
// 6. Backend Container App
// 7. Frontend Static Web App
// 8. AI Foundry (separate deployment)

module identities 'modules/identities.bicep' = {
  name: 'identities-deployment'
  params: {
    location: location
    managedIdentityName: managedIdentityName
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

module keyVault 'modules/key-vault.bicep' = {
  name: 'keyvault-deployment'
  params: {
    location: location
    keyVaultName: keyVaultName
    managedIdentityPrincipalId: identities.outputs.managedIdentityPrincipalId
    resourcePrefix: resourcePrefix
    environment: environment
    tags: tags
  }
  dependsOn: [identities]
}

module containerRegistry 'modules/container-registry.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    containerRegistryName: containerRegistryName
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

module appInsights 'modules/monitoring.bicep' = {
  name: 'appinsights-deployment'
  params: {
    location: location
    appInsightsName: appInsightsName
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    location: location
    storageAccountName: storageAccountName
    managedIdentityPrincipalId: identities.outputs.managedIdentityPrincipalId
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

module containerAppsEnv 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env-deployment'
  params: {
    location: location
    containerAppEnvName: containerAppEnvName
    appInsightsInstrumentationKey: appInsights.outputs.instrumentationKey
    resourcePrefix: resourcePrefix
    tags: tags
  }
}

module backend 'modules/backend-container-app.bicep' = {
  name: 'backend-deployment'
  params: {
    location: location
    backendAppName: backendAppName
    containerAppEnvId: containerAppsEnv.outputs.containerAppEnvId
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryUsername: containerRegistry.outputs.adminUsername
    managedIdentityClientId: identities.outputs.managedIdentityClientId
    managedIdentityId: identities.outputs.managedIdentityId
    keyVaultUrl: keyVault.outputs.keyVaultUri
    appInsightsInstrumentationKey: appInsights.outputs.instrumentationKey
    resourcePrefix: resourcePrefix
    environment: environment
    tags: tags
  }
  dependsOn: [
    containerAppsEnv
    keyVault
    identities
  ]
}

// ===== OUTPUTS =====
@description('Outputs for next deployment steps')
output keyVaultUri string = keyVault.outputs.keyVaultUri
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output backendUrl string = backend.outputs.backendUrl
output backendContainerAppId string = backend.outputs.containerAppId
output managedIdentityClientId string = identities.outputs.managedIdentityClientId
output storageAccountName string = storage.outputs.storageAccountName
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey
