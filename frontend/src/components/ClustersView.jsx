import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchClusters, fetchJobRuns, startCluster, terminateCluster, fetchRecommendationsRealtime } from '../services/api'
import { Activity, Server, Clock, ChevronDown, ChevronUp, Zap, AlertCircle, Play, Square, Lightbulb } from 'lucide-react'

function ClustersView() {
  const [expandedCluster, setExpandedCluster] = useState(null)
  const queryClient = useQueryClient()
  const { data: clusters, isLoading, error } = useQuery({
    queryKey: ['clusters'],
    queryFn: fetchClusters,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: recData } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    refetchInterval: 60000,
  })

  const clusterRecommendationCounts = useMemo(() => {
    const counts = {}
    const recommendations = recData?.recommendations || []
    recommendations.forEach((rec) => {
      if (rec.resource_type === 'cluster' && rec.resource_id != null) {
        const key = String(rec.resource_id)
        counts[key] = (counts[key] || 0) + 1
      }
    })
    return counts
  }, [recData])

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading clusters...</div>
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        Error loading clusters: {error.message}
      </div>
    )
  }

  const getStateColor = (state) => {
    switch (state) {
      case 'RUNNING':
        return 'text-green-700 bg-green-100'
      case 'TERMINATED':
        return 'text-gray-700 bg-gray-100'
      case 'PENDING':
        return 'text-yellow-700 bg-yellow-100'
      case 'ERROR':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  const getRunStateColor = (state) => {
    switch (state) {
      case 'SUCCESS':
        return 'text-green-700 bg-green-50 border-green-200'
      case 'RUNNING':
        return 'text-blue-700 bg-blue-50 border-blue-200'
      case 'FAILED':
        return 'text-red-700 bg-red-50 border-red-200'
      case 'SKIPPED':
        return 'text-gray-700 bg-gray-50 border-gray-200'
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200'
    }
  }

  const formatDuration = (milliseconds) => {
    if (!milliseconds || milliseconds < 0) return 'N/A'
    const totalSeconds = Math.floor(milliseconds / 1000)
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const getServerDetails = (cluster) => {
    const nodeType = cluster.node_type_id || 'N/A'
    const spark = cluster.spark_version || 'N/A'
    const autoscale = cluster.autoscale
    const workers = autoscale
      ? `${autoscale.min_workers || 0}-${autoscale.max_workers || 0}`
      : `${cluster.num_workers || 0}`
    return { nodeType, spark, workers, autoscale: !!autoscale }
  }

  // Group clusters by configuration
  const groupByConfiguration = (clusters) => {
    const groups = {}
    clusters?.forEach((cluster) => {
      const details = getServerDetails(cluster)
      const key = `${details.nodeType}_${details.workers}_${details.spark}`
      if (!groups[key]) {
        groups[key] = {
          config: details,
          clusters: []
        }
      }
      groups[key].clusters.push(cluster)
    })
    return groups
  }

  const configGroups = groupByConfiguration(clusters)

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Databricks Clusters</h1>
          <p className="mt-2 text-sm text-gray-600">Monitor and manage clusters organized by configuration</p>
        </div>
        <div className="text-sm font-medium text-gray-700 bg-gray-100 px-4 py-2 rounded-md">
          Total: {clusters?.length || 0} clusters | {Object.keys(configGroups).length} configurations
        </div>
      </div>

      {/* Group by Configuration */}
      <div className="space-y-6">
        {Object.entries(configGroups).map(([configKey, { config, clusters: clusterList }]) => (
          <div key={configKey} className="dxc-card overflow-hidden">
            {/* Configuration Header */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <Zap className="h-5 w-5 text-blue-600 mt-1 flex-shrink-0" />
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                      {config.nodeType} • {config.workers} Workers • Spark {config.spark}
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      {clusterList.length} cluster{clusterList.length !== 1 ? 's' : ''} 
                      {config.autoscale && ' • Auto-scaling enabled'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Clusters in this configuration */}
            <div className="divide-y divide-gray-200">
              {clusterList.map((cluster) => {
                const startTime = cluster.start_time ? new Date(cluster.start_time).getTime() : null
                const isRunning = cluster.state === 'RUNNING'
                const currentRuntime = isRunning && startTime 
                  ? formatDuration(Date.now() - startTime) 
                  : (cluster.state === 'TERMINATED' ? 'Stopped' : 'N/A')
                const isExpanded = expandedCluster === cluster.cluster_id

                return (
                  <div key={cluster.cluster_id} className="hover:bg-gray-50 transition-colors">
                    {/* Cluster Row */}
                    <div className="p-4 cursor-pointer flex items-center justify-between">
                      <div
                        className="flex-1 flex items-center gap-4"
                        onClick={() => setExpandedCluster(isExpanded ? null : cluster.cluster_id)}
                      >
                        <div className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        </div>
                        <Server className="h-5 w-5 text-primary-600 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900">
                            {cluster.cluster_name || 'Unknown'}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            ID: {cluster.cluster_id}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 ml-4">
                        <div className="text-right hidden sm:block">
                          <div className="flex items-center text-sm text-gray-700">
                            <Clock className="h-4 w-4 mr-1 text-gray-400" />
                            {currentRuntime}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {cluster.autotermination_minutes
                              ? `Auto-term: ${cluster.autotermination_minutes} min`
                              : 'No auto-term'}
                          </p>
                        </div>
                        <div className="flex items-center text-sm text-gray-700">
                          <Lightbulb className="h-4 w-4 mr-1 text-amber-500" />
                          {clusterRecommendationCounts[String(cluster.cluster_id)] || 0}
                        </div>
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getStateColor(
                            cluster.state
                          )}`}
                        >
                          {cluster.state || 'UNKNOWN'}
                        </span>
                        <ClusterActionButtons 
                          clusterId={cluster.cluster_id}
                          clusterName={cluster.cluster_name}
                          state={cluster.state}
                          onSuccess={() => queryClient.invalidateQueries({ queryKey: ['clusters'] })}
                        />
                      </div>
                    </div>

                    {/* Expanded Details - Job Runs */}
                    {isExpanded && (
                      <ClusterJobRuns clusterId={cluster.cluster_id} clusterName={cluster.cluster_name} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {(!clusters || clusters.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          No clusters found
        </div>
      )}
    </div>
  )
}

function ClusterActionButtons({ clusterId, clusterName, state, onSuccess }) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [action, setAction] = useState(null)

  const handleStartCluster = async () => {
    try {
      console.log(`Attempting to start cluster: ${clusterId}`)
      const result = await startCluster(clusterId)
      if (result.success) {
        alert(`✓ Started cluster: ${clusterName}`)
        onSuccess()
      } else {
        alert(`✗ Failed to start cluster: ${result.message || result.error}`)
      }
    } catch (err) {
      console.error('Error starting cluster:', err)
      alert(`Error starting cluster: ${err.message}`)
    }
  }

  const handleTerminateCluster = async () => {
    try {
      console.log(`Attempting to terminate cluster: ${clusterId}`)
      const result = await terminateCluster(clusterId)
      if (result.success) {
        alert(`✓ Terminated cluster: ${clusterName}`)
        onSuccess()
      } else {
        alert(`✗ Failed to terminate cluster: ${result.message || result.error}`)
      }
    } catch (err) {
      console.error('Error terminating cluster:', err)
      alert(`Error terminating cluster: ${err.message}`)
    }
  }

  const handleConfirm = () => {
    if (action === 'start') {
      handleStartCluster()
    } else if (action === 'terminate') {
      handleTerminateCluster()
    }
    setShowConfirm(false)
    setAction(null)
  }

  return (
    <>
      <div className="flex gap-2 flex-shrink-0">
        {state === 'TERMINATED' && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setAction('start')
              setShowConfirm(true)
            }}
            className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
            title="Start cluster"
          >
            <Play className="h-4 w-4" />
          </button>
        )}
        {state === 'RUNNING' && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setAction('terminate')
              setShowConfirm(true)
            }}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Terminate cluster"
          >
            <Square className="h-4 w-4" />
          </button>
        )}
      </div>

      {showConfirm && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-sm w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {action === 'start' ? 'Start Cluster?' : 'Terminate Cluster?'}
              </h3>
              <p className="text-gray-600 mb-6">
                {action === 'start'
                  ? `Are you sure you want to start "${clusterName}"? This will start the cluster and incur costs.`
                  : `Are you sure you want to terminate "${clusterName}"? This action cannot be undone.`}
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => {
                    setShowConfirm(false)
                    setAction(null)
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirm}
                  className={`px-4 py-2 text-white rounded-lg transition-colors ${
                    action === 'start'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  {action === 'start' ? 'Start' : 'Terminate'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function ClusterJobRuns({ clusterId, clusterName }) {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['job-runs', clusterId],
    queryFn: () => fetchJobRuns(parseInt(clusterId)),
    enabled: !!clusterId,
  })

  if (isLoading) {
    return (
      <div className="bg-gray-50 p-4 text-center text-sm text-gray-500">
        Loading job runs...
      </div>
    )
  }

  if (!runs || runs.length === 0) {
    return (
      <div className="bg-gray-50 p-4 text-center text-sm text-gray-500">
        No recent job runs on this cluster
      </div>
    )
  }

  return (
    <div className="bg-gray-50 p-4 border-t border-gray-200">
      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
        <Activity className="h-4 w-4 mr-2" />
        Job Runs ({runs.length})
      </h4>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {runs.map((run, idx) => {
          const runState = run.state || 'UNKNOWN'
          const stateColor = getRunStateColor(runState)
          const startTime = run.start_time ? new Date(run.start_time) : null
          const endTime = run.end_time ? new Date(run.end_time) : null
          const duration = startTime && endTime ? endTime - startTime : null

          return (
            <div key={idx} className={`border rounded-lg p-3 ${stateColor}`}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    Run ID: {run.run_id || 'N/A'}
                  </p>
                  {run.task_key && (
                    <p className="text-xs text-gray-600 mt-1">
                      Task: {run.task_key}
                    </p>
                  )}
                  {startTime && (
                    <p className="text-xs text-gray-600 mt-1">
                      Started: {startTime.toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-xs font-semibold">
                    {runState}
                  </span>
                  {duration && (
                    <p className="text-xs text-gray-600 mt-1">
                      Duration: {formatRunDuration(duration)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function getRunStateColor(state) {
  switch (state) {
    case 'SUCCESS':
      return 'text-green-700 bg-green-50 border-green-200'
    case 'RUNNING':
      return 'text-blue-700 bg-blue-50 border-blue-200'
    case 'FAILED':
      return 'text-red-700 bg-red-50 border-red-200'
    case 'SKIPPED':
      return 'text-gray-700 bg-gray-50 border-gray-200'
    default:
      return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

function formatRunDuration(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  
  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m ${seconds}s`
  return `${seconds}s`
}

export default ClustersView

