@description('Application Insights and monitoring for SentinelLens')

param location string
param appInsightsName string
param resourcePrefix string
param tags object

// ===== LOG ANALYTICS WORKSPACE =====
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: '${resourcePrefix}-logs'
  location: location
  tags: tags

  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30  // Audit logs retained longer
  }
}

// ===== APPLICATION INSIGHTS =====
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'

  properties: {
    Application_Type: 'web'
    RetentionInDays: 90
    WorkspaceResourceId: logAnalyticsWorkspace.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ===== AUDIT LOG TABLE (in Log Analytics) =====
// Custom table for immutable audit logs
resource auditLogsTable 'Microsoft.OperationalInsights/workspaces/tables@2021-12-01-preview' = {
  name: '${logAnalyticsWorkspace.name}/SentinelLensAudit_CL'

  properties: {
    schema: {
      name: 'SentinelLensAudit_CL'
      columns: [
        {
          name: 'TimeGenerated'
          type: 'datetime'
        }
        {
          name: 'EventType'
          type: 'string'
        }
        {
          name: 'Resource'
          type: 'string'
        }
        {
          name: 'Status'
          type: 'string'
        }
        {
          name: 'Details'
          type: 'string'
        }
        {
          name: 'UserId'
          type: 'string'
        }
      ]
    }
    totalRetentionInDays: 365  // 1 year for compliance
    plan: 'Analytics'
  }
}

// ===== ALERT RULES =====
// High-severity alerts for operational issues

resource agentFailureAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${resourcePrefix}-agent-failures'
  location: 'global'
  tags: tags

  properties: {
    description: 'Alert when agent fails 3+ times in 10 minutes'
    severity: 2
    enabled: true
    scopes: [appInsights.id]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT10M'
    criteria: {
      allOf: [
        {
          metricName: 'customMetrics/agent_failure_count'
          operator: 'GreaterThanOrEqual'
          threshold: 3
          timeAggregation: 'Total'
        }
      ]
      'odata.type': 'Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria'
    }
  }
}

resource apiLatencyAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${resourcePrefix}-api-latency'
  location: 'global'
  tags: tags

  properties: {
    description: 'Alert when API response time exceeds 2 seconds'
    severity: 2
    enabled: true
    scopes: [appInsights.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      allOf: [
        {
          metricName: 'serverResponseTime'
          operator: 'GreaterThan'
          threshold: 2000
          timeAggregation: 'Average'
        }
      ]
      'odata.type': 'Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria'
    }
  }
}

// ===== OUTPUTS =====
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsId string = appInsights.id
