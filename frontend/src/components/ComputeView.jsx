import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  fetchAllCompute,
  fetchSQLWarehouses,
  fetchPools,
  fetchVectorSearch,
  fetchPolicies,
  fetchApps,
  fetchLakebase,
} from '../services/api'
import { Database, Activity, Search, Shield, Box, Layers, RefreshCw } from 'lucide-react'

import { Brain, FlaskConical } from 'lucide-react'

const computeTypes = [
  { key: 'all_purpose_clusters', label: 'All-Purpose Clusters', icon: Activity, color: 'blue' },
  { key: 'job_clusters', label: 'Job Compute', icon: Activity, color: 'green' },
  { key: 'sql_warehouses', label: 'SQL Warehouses', icon: Database, color: 'purple' },
  { key: 'pools', label: 'Instance Pools', icon: Box, color: 'yellow' },
  { key: 'vector_search', label: 'Vector Search', icon: Search, color: 'indigo' },
  { key: 'policies', label: 'Policies', icon: Shield, color: 'red' },
  { key: 'apps', label: 'Apps', icon: Box, color: 'green' },
  { key: 'lakebase_provisioned', label: 'Lakebase Provisioned', icon: Layers, color: 'blue' },
  { key: 'ml_jobs', label: 'ML/AI Jobs', icon: Brain, color: 'purple' },
  { key: 'mlflow_experiments', label: 'MLflow Experiments', icon: FlaskConical, color: 'indigo' },
  { key: 'mlflow_models', label: 'MLflow Models', icon: Brain, color: 'purple' },
  { key: 'model_serving_endpoints', label: 'Model Serving', icon: Activity, color: 'green' },
  { key: 'feature_store_tables', label: 'Feature Store', icon: Database, color: 'blue' },
]

function ComputeView() {
  const [activeTab, setActiveTab] = useState('all_purpose_clusters')

  const { data: allCompute, isLoading, refetch } = useQuery({
    queryKey: ['allCompute'],
    queryFn: fetchAllCompute,
    refetchInterval: 30000,
  })

  const renderComputeList = (items, type) => {
    if (!items || items.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg font-medium mb-2">No {computeTypes.find(t => t.key === type)?.label || type} found</p>
          <p className="text-sm">This could mean:</p>
          <ul className="text-sm mt-2 space-y-1 list-disc list-inside">
            <li>No resources of this type exist in your workspace</li>
            <li>The API endpoint may require additional permissions</li>
            <li>Check the browser console for API errors</li>
          </ul>
        </div>
      )
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, index) => {
          // Handle different resource types with different field names
          const resourceName = item.name || 
                              item.cluster_name || 
                              item.instance_pool_name || 
                              item.endpoint_name ||
                              item.policy_name ||
                              item.app_name ||
                              item.warehouse_name ||
                              `Resource ${index + 1}`
          
          const resourceId = item.id || 
                            item.cluster_id || 
                            item.instance_pool_id ||
                            item.endpoint_id ||
                            item.policy_id ||
                            item.warehouse_id ||
                            index
          
          // Debug: Log SQL warehouse items
          if (type === 'sql_warehouses') {
            console.log('SQL Warehouse Item:', item)
          }

          return (
            <div key={resourceId} className="dxc-card">
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-2">{resourceName}</h3>
                <div className="space-y-2 text-sm text-gray-600">
                  {/* State/Status */}
                  {(item.state || item.status) && (
                    <div className="flex items-center justify-between">
                      <span>State:</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        (item.state === 'RUNNING' || item.status === 'RUNNING') ? 'bg-green-100 text-green-700' :
                        (item.state === 'STOPPED' || item.status === 'STOPPED') ? 'bg-gray-100 text-gray-700' :
                        (item.state === 'STARTING' || item.status === 'STARTING') ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {item.state || item.status}
                      </span>
                    </div>
                  )}
                  
                  {/* SQL Warehouse specific fields */}
                  {item.cluster_size && (
                    <div className="flex items-center justify-between">
                      <span>Cluster Size:</span>
                      <span className="font-medium">{item.cluster_size}</span>
                    </div>
                  )}
                  {item.warehouse_type && (
                    <div className="flex items-center justify-between">
                      <span>Type:</span>
                      <span className="font-medium">{item.warehouse_type}</span>
                    </div>
                  )}
                  {item.auto_stop_mins !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Auto-stop (mins):</span>
                      <span className="font-medium">{item.auto_stop_mins || 'Disabled'}</span>
                    </div>
                  )}
                  
                  {/* ML/AI specific fields */}
                  {item.ml_category && (
                    <div className="flex items-center justify-between">
                      <span>Category:</span>
                      <span className="font-medium">{item.ml_category}</span>
                    </div>
                  )}
                  {item.lifecycle_stage && (
                    <div className="flex items-center justify-between">
                      <span>Lifecycle:</span>
                      <span className="font-medium">{item.lifecycle_stage}</span>
                    </div>
                  )}
                  {item.latest_versions !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Versions:</span>
                      <span className="font-medium">{item.latest_versions}</span>
                    </div>
                  )}
                  {item.primary_keys && item.primary_keys.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span>Primary Keys:</span>
                      <span className="font-medium text-xs">{item.primary_keys.join(', ')}</span>
                    </div>
                  )}
                  
                  {/* Cluster specific fields */}
                  {item.num_workers !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Workers:</span>
                      <span className="font-medium">{item.num_workers}</span>
                    </div>
                  )}
                  {item.node_type_id && (
                    <div className="flex items-center justify-between">
                      <span>Node Type:</span>
                      <span className="font-medium text-xs truncate max-w-[200px]" title={item.node_type_id}>
                        {item.node_type_id}
                      </span>
                    </div>
                  )}
                  
                  {/* Pool specific fields */}
                  {item.min_idle_instances !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Min Idle:</span>
                      <span className="font-medium">{item.min_idle_instances}</span>
                    </div>
                  )}
                  {item.max_capacity !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Max Capacity:</span>
                      <span className="font-medium">{item.max_capacity}</span>
                    </div>
                  )}
                  
                  {/* ID field */}
                  {resourceId && (
                    <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                      <span className="text-xs text-gray-500">ID:</span>
                      <span className="font-mono text-xs text-gray-600 truncate max-w-[200px]" title={resourceId}>
                        {resourceId}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // Get active data - handle both direct access and nested structure
  const activeData = allCompute?.[activeTab] || []
  
  // Calculate total resources
  const totalResources = computeTypes.reduce((sum, type) => {
    return sum + (allCompute?.[type.key]?.length || 0)
  }, 0)
  
  // Debug: Log the data structure
  if (allCompute && !activeData.length && activeTab === 'sql_warehouses') {
    console.log('SQL Warehouses Debug:', {
      allCompute,
      activeTab,
      sql_warehouses: allCompute?.sql_warehouses,
      keys: Object.keys(allCompute || {})
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Compute Resources</h1>
          <p className="mt-2 text-sm text-gray-600">View and manage all Databricks compute resources</p>
        </div>
        <button
          onClick={() => refetch()}
          className="dxc-button-primary flex items-center"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Summary Card */}
      {allCompute && (
        <div className="dxc-card bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Total Compute Resources</p>
              <p className="text-3xl font-bold text-blue-600 mt-1">{totalResources}</p>
            </div>
            <div className="text-right space-y-2">
              {computeTypes.slice(0, 3).map((type) => {
                const count = allCompute?.[type.key]?.length || 0
                return count > 0 ? (
                  <div key={type.key} className="text-sm">
                    <span className="text-gray-600">{type.label}:</span>
                    <span className="font-semibold text-gray-900 ml-2">{count}</span>
                  </div>
                ) : null
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {computeTypes.map((type) => {
            const Icon = type.icon
            const count = allCompute?.[type.key]?.length || 0
            const isActive = activeTab === type.key

            return (
              <button
                key={type.key}
                onClick={() => setActiveTab(type.key)}
                className={`flex items-center whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  isActive
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {type.label}
                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                  isActive ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {count}
                </span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading compute resources...</div>
      ) : allCompute ? (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {computeTypes.find(t => t.key === activeTab)?.label}
            </h2>
            <span className="text-sm text-gray-600">
              {activeData.length} {activeData.length === 1 ? 'resource' : 'resources'}
            </span>
          </div>
          {renderComputeList(activeData, activeTab)}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg font-medium mb-2">Unable to load compute resources</p>
          <p className="text-sm">Please check your backend connection and try refreshing.</p>
          <button
            onClick={() => refetch()}
            className="mt-4 dxc-button-primary"
          >
            <RefreshCw className="h-4 w-4 mr-2 inline" />
            Retry
          </button>
        </div>
      )}
    </div>
  )
}

export default ComputeView

