@description('Backend FastAPI container app deployment')

param location string
param backendAppName string
param containerAppEnvId string
param containerRegistryLoginServer string
param containerRegistryUsername string
param managedIdentityClientId string
param managedIdentityId string
param keyVaultUrl string
param appInsightsInstrumentationKey string
param resourcePrefix string
param environment string
param tags object

// ===== BACKEND CONTAINER APP =====
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: backendAppName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }

  properties: {
    managedEnvironmentId: containerAppEnvId
    workloadProfileName: 'Consumption'

    configuration: {
      activeRevisionsMode: 'Single'

      ingress: {
        external: true
        targetPort: 8000
        exposedPort: 8000
        transport: 'http'
        allowInsecure: false
      }

      registries: [
        {
          server: containerRegistryLoginServer
          username: containerRegistryUsername
          passwordSecretRef: 'registry-password'
        }
      ]

      secrets: [
        {
          name: 'registry-password'
          value: ''  // To be set via Azure CLI
        }
      ]

      dapr: {
        enabled: false
      }
    }

    template: {
      containers: [
        {
          image: '${containerRegistryLoginServer}/sentinellens-backend:latest'
          name: 'backend'
          resources: {
            cpu: '0.5'
            memory: '1Gi'
          }

          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'AZURE_KEY_VAULT_URL'
              value: keyVaultUrl
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentityClientId
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: 'InstrumentationKey=${appInsightsInstrumentationKey}'
            }
            {
              name: 'ENABLE_PRESIDIO_MASKING'
              value: 'True'
            }
            {
              name: 'ENABLE_PROMPT_SHIELD'
              value: 'True'
            }
            {
              name: 'ENABLE_AUDIT_LOGGING'
              value: 'True'
            }
          ]

          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
        }
      ]

      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
          {
            name: 'cpu'
            custom: {
              metadata: {
                type: 'cpu'
                value: '70'
              }
            }
          }
        ]
      }
    }
  }
}

// ===== OUTPUTS =====
output containerAppId string = backendApp.id
output containerAppName string = backendApp.name
output backendUrl string = backendApp.properties.configuration.ingress.fqdn
output containerAppManagedEnvironmentId string = containerAppEnvId
