@description('Azure Container Apps Environment for backend')

param location string
param containerAppEnvName string
param appInsightsInstrumentationKey string
param resourcePrefix string
param tags object

// ===== CONTAINER APPS ENVIRONMENT =====
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  tags: tags

  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerid: split(appInsightsInstrumentationKey, '-')[0]  // Simplified reference
        sharedkey: ''  // Set via ARM template or CLI
      }
    }

    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ===== OUTPUTS =====
output containerAppEnvId string = containerAppEnv.id
output containerAppEnvName string = containerAppEnv.name
