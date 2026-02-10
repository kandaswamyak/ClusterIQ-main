import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getSelfHealingConfig, 
  updateSelfHealingConfig, 
  getHealthStatus,
  runSelfHealing,
  getHealingHistory,
  getSelfHealingStats,
  fetchApprovals,
  fetchRecommendationsRealtime,
  fetchLogs
} from '../services/api'
import { 
  Activity, 
  Settings, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Zap,
  Clock,
  TrendingUp,
  Shield
} from 'lucide-react'

function SelfHealing() {
  const queryClient = useQueryClient()
  const [isRunning, setIsRunning] = useState(false)
  const [toggleError, setToggleError] = useState(null)
  const [localEnabled, setLocalEnabled] = useState(false)
  const [localDryRun, setLocalDryRun] = useState(false)
  const [healingResult, setHealingResult] = useState(null)
  const [healingMessage, setHealingMessage] = useState(null)

  // Fetch config
  const { data: configData, isLoading: configLoading } = useQuery({
    queryKey: ['self-healing-config'],
    queryFn: getSelfHealingConfig,
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 5000
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['self-healing-stats'],
    queryFn: getSelfHealingStats,
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 5000
  })

  // Fetch history
  const { data: historyData } = useQuery({
    queryKey: ['healing-history'],
    queryFn: () => getHealingHistory(20),
    refetchInterval: 10000
  })

  // Fetch health status
  const { data: healthData } = useQuery({
    queryKey: ['health-status'],
    queryFn: getHealthStatus,
    refetchInterval: 30000
  })

  // Fetch pending recommendations for actionable issues
  const { data: pendingRecommendations, isLoading: pendingRecsLoading, refetch: refetchPendingRecs } = useQuery({
    queryKey: ['auto-remediation'],
    queryFn: async () => {
      const data = await fetchApprovals('PENDING')
      const allRecs = data?.recommendations || []
      
      // Get all clusters to check their states
      let terminatedClusterIds = new Set()
      try {
        const clustersResponse = await fetch('http://localhost:8000/api/clusters')
        const clusters = await clustersResponse.json()
        terminatedClusterIds = new Set(
          clusters
            .filter(c => ['TERMINATED', 'TERMINATING'].includes(c.state))
            .map(c => c.cluster_id)
        )
      } catch (err) {
        console.warn('Failed to fetch cluster states:', err)
      }
      
      // Filter to only show auto-healable issues (not general optimizations)
      const autoHealableTypes = ['stuck_pending_job', 'idle_cluster', 'execution_error', 'cost_leak', 'long_running_job']
      return allRecs.filter(rec => {
        // Skip recommendations for TERMINATED clusters
        if (rec.resource_type === 'cluster' && terminatedClusterIds.has(rec.resource_id)) {
          return false
        }
        
        // Include auto-healable types
        if (autoHealableTypes.includes(rec.type)) return true
        return false
      })
    },
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 5000
  })

  const { data: realtimeRecommendationsData } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 5000
  })

  // Fetch logs for real-time failed jobs and idle clusters
  const { data: logsData } = useQuery({
    queryKey: ['logs-realtime'],
    queryFn: async () => {
      try {
        const logs = await fetchLogs('ERROR', 50)
        return logs?.logs || []
      } catch (err) {
        console.warn('Failed to fetch logs:', err)
        return []
      }
    },
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 5000
  })

  // Update config mutation
  const updateConfigMutation = useMutation({
    mutationFn: updateSelfHealingConfig,
    onSuccess: () => {
      queryClient.invalidateQueries(['self-healing-config'])
      queryClient.invalidateQueries(['self-healing-stats'])
    }
  })

  // Run healing mutation
  const runHealingMutation = useMutation({
    mutationFn: runSelfHealing,
    onSuccess: (data) => {
      // Show result message
      const summary = data?.summary || {}
      setHealingResult(data)
      
      let message = `Scan complete: ${summary.scanned_clusters || 0} clusters scanned`
      if (summary.actions_taken > 0) {
        message += `, ${summary.actions_taken} actions taken`
      }
      if (summary.failed_clusters > 0) {
        message += `, ${summary.failed_clusters} failed clusters detected`
      }
      setHealingMessage(message)
      
      // Clear message after 5 seconds
      setTimeout(() => setHealingMessage(null), 5000)
      
      // Refresh queries immediately
      queryClient.invalidateQueries(['healing-history'])
      queryClient.invalidateQueries(['self-healing-stats'])
      queryClient.invalidateQueries(['health-status'])
      // Immediately refetch auto-remediation to show updated count and clear content
      queryClient.refetchQueries(['auto-remediation'])
    },
    onError: (error) => {
      setHealingMessage(`Error: ${error?.message || 'Failed to run healing'}`)
      setTimeout(() => setHealingMessage(null), 5000)
    }
  })

  const config = configData?.config || {}
  const stats = statsData || {}
  const history = historyData?.history || []
  const realtimeRecommendations = realtimeRecommendationsData?.recommendations || []
  const failedJobRecommendations = realtimeRecommendations.filter((rec) => {
    const title = (rec.title || '').toLowerCase()
    const description = (rec.description || '').toLowerCase()
    const type = (rec.type || '').toLowerCase()
    const status = (rec.status || '').toLowerCase()

    if (status && status !== 'pending') return false

    return (
      type === 'execution_error' ||
      type === 'job_failure' ||
      type === 'failed_job' ||
      type === 'stuck_pending_job' ||
      type === 'long_running_job' ||
      title.includes('long running') ||
      title.includes('failed') ||
      title.includes('failure') ||
      title.includes('exception') ||
      description.includes('failed') ||
      description.includes('failure') ||
      description.includes('exception')
    )
  })

  const idleClusterRecommendations = realtimeRecommendations.filter((rec) => {
    const title = (rec.title || '').toLowerCase()
    const description = (rec.description || '').toLowerCase()
    const type = (rec.type || '').toLowerCase()
    const resourceType = (rec.resource_type || '').toLowerCase()

    return (
      type === 'idle_cluster' ||
      (type === 'cost_leak' && (title.includes('idle') || description.includes('idle'))) ||
      (resourceType === 'cluster' && (title.includes('idle') || description.includes('idle')))
    )
  })

  // Extract failed jobs from logs - only real job failures
  const failedJobsFromLogs = (logsData || []).filter((log) => {
    const message = (log.message || '').toLowerCase()
    const jobKeywords = message.includes('job') || message.includes('task') || message.includes('run')
    const failureKeywords = message.includes('failed') || message.includes('failure') || message.includes('exception')
    const isNonActionable = message.includes('no tasks') || message.includes('no configured tasks')
    return jobKeywords && failureKeywords && !isNonActionable
  })

  // Extract idle clusters from logs
  const idleClustersFromLogs = (logsData || []).filter((log) => {
    const message = (log.message || '').toLowerCase()
    return message.includes('cluster') && message.includes('idle')
  })

  const getRecommendationTime = (rec) => {
    const dateValue = rec?.created_at || rec?.timestamp
    if (!dateValue) return 0

    if (typeof dateValue === 'string') {
      const parsed = new Date(dateValue).getTime()
      return Number.isFinite(parsed) ? parsed : 0
    }

    if (dateValue instanceof Date) {
      const parsed = dateValue.getTime()
      return Number.isFinite(parsed) ? parsed : 0
    }

    return 0
  }

  const formatIstDate = (value) => {
    if (!value) return null
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return null

    return parsed.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Kolkata'
    })
  }

  const lastFailedJobRecommendation = [...failedJobRecommendations]
    .sort((a, b) => getRecommendationTime(b) - getRecommendationTime(a))
    .at(0) || null

  const lastIdleClusterRecommendation = [...idleClusterRecommendations]
    .sort((a, b) => getRecommendationTime(b) - getRecommendationTime(a))
    .at(0) || null

  const lastFailedJobFromLogs = failedJobsFromLogs.length > 0 ? failedJobsFromLogs[0] : null
  const lastIdleClusterFromLogs = idleClustersFromLogs.length > 0 ? idleClustersFromLogs[0] : null
  const health = healthData?.summary || {}

  // Track successfully healed resources to avoid showing duplicate recommendations
  const successfullyHealedResourceIds = new Set(
    (history || [])
      .filter(action => action.status === 'success')
      .map(action => action.resource_id)
  )

  // Extract resource IDs from log message (look for both numeric IDs and named resources)
  const extractResourceIdsFromLog = (log) => {
    if (!log?.message) return []
    const ids = []
    
    // Match long numeric IDs (15+ digits for job/run IDs)
    const numericMatch = log.message.match(/\b(\d{15,})\b/)
    if (numericMatch) ids.push(numericMatch[1])
    
    // Match job names like "ClusterIQ_Metrics_Loader_4Hours"
    const jobNameMatch = log.message.match(/([A-Za-z0-9_]+)\b/)
    if (jobNameMatch) ids.push(jobNameMatch[1])
    
    return ids
  }

  // Check if cluster recommendation was already successfully healed
  const clusterIdsFromLogs = lastIdleClusterFromLogs ? extractResourceIdsFromLog(lastIdleClusterFromLogs) : []
  const hasClusterBeenHealed = 
    (lastIdleClusterRecommendation && successfullyHealedResourceIds.has(lastIdleClusterRecommendation.resource_id)) ||
    clusterIdsFromLogs.some(id => successfullyHealedResourceIds.has(id))

  // Check if job recommendation was already successfully healed
  const jobIdsFromLogs = lastFailedJobFromLogs ? extractResourceIdsFromLog(lastFailedJobFromLogs) : []
  const hasJobBeenHealed = 
    (lastFailedJobRecommendation && successfullyHealedResourceIds.has(lastFailedJobRecommendation.resource_id)) ||
    jobIdsFromLogs.some(id => successfullyHealedResourceIds.has(id))

  useEffect(() => {
    if (configData?.config) {
      setLocalEnabled(!!configData.config.enabled)
      setLocalDryRun(!!configData.config?.safety?.dry_run)
    }
  }, [configData])

  const handleToggleEnabled = async () => {
    const nextValue = !localEnabled
    setToggleError(null)
    setLocalEnabled(nextValue)
    try {
      await updateConfigMutation.mutateAsync({
        enabled: nextValue
      })
    } catch (error) {
      setLocalEnabled(!nextValue)
      setToggleError(error?.message || 'Failed to update self-healing status')
    }
  }

  const handleToggleDryRun = async () => {
    const nextValue = !localDryRun
    setToggleError(null)
    setLocalDryRun(nextValue)
    try {
      await updateConfigMutation.mutateAsync({
        safety: {
          ...config.safety,
          dry_run: nextValue
        }
      })
    } catch (error) {
      setLocalDryRun(!nextValue)
      setToggleError(error?.message || 'Failed to update dry-run mode')
    }
  }

  const handleToggleFeature = async (feature, enabled) => {
    setToggleError(null)
    try {
      await updateConfigMutation.mutateAsync({
        features: {
          ...config.features,
          [feature]: enabled
        }
      })
    } catch (error) {
      setToggleError(error?.message || 'Failed to update feature settings')
    }
  }

  const handleRunHealing = async () => {
    setIsRunning(true)
    try {
      await runHealingMutation.mutateAsync()
    } finally {
      setIsRunning(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100'
      case 'failed': return 'text-red-600 bg-red-100'
      case 'dry_run': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
            Self-Healing
          </h1>
          <p className="mt-3 text-base text-gray-600 font-medium">
            Automated cluster health monitoring and remediation
          </p>
        </div>
        <button
          onClick={handleRunHealing}
          disabled={isRunning || !config.enabled}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          <RefreshCw className={`h-5 w-5 mr-2 ${isRunning ? 'animate-spin' : ''}`} />
          {isRunning ? 'Running...' : 'Run Healing Now'}
        </button>
      </div>

      {toggleError && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
            <div>
              <p className="text-sm font-semibold text-red-800">Update failed</p>
              <p className="text-xs text-red-600 mt-1">{toggleError}</p>
            </div>
          </div>
        </div>
      )}

      {healingMessage && (
        <div className={`border-l-4 rounded-r-lg p-4 ${
          healingMessage.includes('Error') 
            ? 'bg-red-50 border-red-500'
            : 'bg-green-50 border-green-500'
        }`}>
          <div className="flex items-start">
            {healingMessage.includes('Error') ? (
              <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
            )}
            <div>
              <p className={`text-sm font-semibold ${
                healingMessage.includes('Error') 
                  ? 'text-red-800'
                  : 'text-green-800'
              }`}>
                {healingMessage.includes('Error') ? 'Healing Error' : 'Healing Complete'}
              </p>
              <p className={`text-xs ${
                healingMessage.includes('Error') 
                  ? 'text-red-600'
                  : 'text-green-600'
              } mt-1`}>
                {healingMessage}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="metric-card" style={{ background: config.enabled ? 'linear-gradient(135deg, #065f46 0%, #10b981 100%)' : 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)', border: '1px solid' + (config.enabled ? '#34d399' : '#d1d5db') }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Status</h3>
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {config.enabled ? 'Active' : 'Inactive'}
          </div>
          <p className="text-sm text-white mt-3 font-medium opacity-90">
            {config.safety?.dry_run ? 'Dry-run mode' : 'Live mode'}
          </p>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)', border: '1px solid #60a5fa' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-blue-200 uppercase tracking-wide">Cluster Health</h3>
            <Activity className="h-6 w-6 text-blue-300" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {health.health_percentage !== undefined && health.health_percentage !== null ? `${health.health_percentage.toFixed(0)}%` : '100%'}
          </div>
          <p className="text-sm text-blue-200 mt-3 font-medium">
            {health.healthy || health.total_clusters || 0} / {health.total_clusters || 0} healthy
          </p>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #b45309 0%, #f59e0b 100%)', border: '1px solid #fbbf24' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-amber-200 uppercase tracking-wide">Actions Taken</h3>
            <Zap className="h-6 w-6 text-amber-300" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {historyData?.stats?.total_actions || 0}
          </div>
          <p className="text-sm text-amber-200 mt-3 font-medium">
            {historyData?.stats?.successful || 0} successful
          </p>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%)', border: '1px solid #ef4444' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-red-200 uppercase tracking-wide">Auto-Healable</h3>
            <AlertTriangle className="h-6 w-6 text-red-300" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {pendingRecsLoading ? '...' : (pendingRecommendations?.length || 0)}
          </div>
          <p className="text-sm text-red-200 mt-3 font-medium">
            {pendingRecommendations?.length ? 'Issues detected' : 'No issues detected'}
          </p>
        </div>
      </div>

      {/* Settings */}
      <div className="dxc-card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Settings className="h-6 w-6 mr-3 text-purple-600" />
          Configuration
        </h2>

        <div className="space-y-6">
          {/* Main Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-gray-900">Enable Self-Healing</h3>
                <p className="text-sm text-gray-600">Globally enable or disable auto-healing</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={localEnabled}
                  onChange={handleToggleEnabled}
                  disabled={configLoading || updateConfigMutation.isLoading}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-gray-900">Dry-Run Mode</h3>
                <p className="text-sm text-gray-600">Test without making actual changes</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={localDryRun}
                  onChange={handleToggleDryRun}
                  disabled={configLoading || updateConfigMutation.isLoading}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>

          {/* Feature Toggles */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { key: 'auto_restart_failed_clusters', label: 'Auto-restart Failed Clusters', desc: 'Automatically restart clusters in error state' },
                { key: 'auto_terminate_idle_clusters', label: 'Auto-terminate Idle Clusters', desc: 'Terminate clusters that exceed idle timeout' },
                { key: 'auto_scale_adjustments', label: 'Auto-scale Adjustments', desc: 'Automatically adjust cluster resources' },
                { key: 'auto_apply_optimizations', label: 'Auto-apply Optimizations', desc: 'Apply cost optimization recommendations' },
                { key: 'proactive_health_checks', label: 'Proactive Health Checks', desc: 'Continuous health monitoring' }
              ].map(feature => (
                <div key={feature.key} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 text-sm">{feature.label}</p>
                    <p className="text-xs text-gray-500">{feature.desc}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-3">
                    <input
                      type="checkbox"
                      checked={config.features?.[feature.key] || false}
                      onChange={(e) => handleToggleFeature(feature.key, e.target.checked)}
                      disabled={updateConfigMutation.isLoading}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Current Issue */}
      {pendingRecommendations && pendingRecommendations.length > 0 && (() => {
        // Sort recommendations by priority to show only the most critical
        const sortedRecs = [...pendingRecommendations].sort((a, b) => {
          // Priority order: execution_error > stuck_pending_job > others
          const priorityMap = { 'execution_error': 0, 'stuck_pending_job': 1 }
          const aPriority = priorityMap[a.type] ?? 2
          const bPriority = priorityMap[b.type] ?? 2
          
          if (aPriority !== bPriority) return aPriority - bPriority
          
          // Then by severity: high > medium > low
          const severityMap = { 'high': 0, 'medium': 1, 'low': 2 }
          const aSeverity = severityMap[a.severity] ?? 2
          const bSeverity = severityMap[b.severity] ?? 2
          
          return aSeverity - bSeverity
        })
        
        const topRec = sortedRecs[0]
        const isStuckPending = topRec.type === 'stuck_pending_job'
        const isExecutionError = topRec.type === 'execution_error'
        const isHighPriority = isStuckPending || isExecutionError
        
        return (
          <div className="dxc-card border-l-4 border-purple-500">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <AlertTriangle className="h-6 w-6 mr-3 text-purple-600" />
              Auto-Remediation
            </h2>
            <div 
              className={`p-4 border rounded-lg ${
                isStuckPending ? 'bg-yellow-50 border-yellow-300' :
                isExecutionError ? 'bg-red-50 border-red-300' :
                'bg-gray-50 border-gray-300'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-sm font-semibold text-gray-900">{topRec.title}</h3>
                    <span className={`px-2 py-0.5 text-xs rounded font-semibold ${
                      topRec.severity === 'high' ? 'bg-red-100 text-red-700' :
                      topRec.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {topRec.severity?.toUpperCase()}
                    </span>
                    {isHighPriority && (
                      <span className="px-2 py-0.5 text-xs rounded font-semibold bg-purple-100 text-purple-700">
                        URGENT
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-700 mb-2">{topRec.description}</p>
                  <div className="flex items-center gap-4 text-[11px] text-gray-600">
                    <span>Resource: {topRec.resource_name || topRec.resource_id}</span>
                    {topRec.details?.pending_duration_minutes && (
                      <span className="text-yellow-700 font-semibold">
                        ⏱️ Stuck for {topRec.details.pending_duration_minutes.toFixed(1)} minutes
                      </span>
                    )}
                    {topRec.confidence_score && (
                      <span>Confidence: {(topRec.confidence_score * 100).toFixed(0)}%</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      })()}

      {/* Cluster Recommendation */}
      {(lastIdleClusterRecommendation || lastIdleClusterFromLogs) && !hasClusterBeenHealed && (
        <div className="dxc-card">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-3 text-blue-600" />
            Cluster Recommendation ({idleClusterRecommendations.length})
          </h2>

          {lastIdleClusterRecommendation ? (
            <div className="p-4 border border-blue-200 rounded-lg bg-blue-50">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{lastIdleClusterRecommendation.title}</h3>
                  <p className="text-xs text-gray-700 mt-1">
                    {lastIdleClusterRecommendation.resource_name || lastIdleClusterRecommendation.resource_id || 'Cluster'}
                  </p>
                </div>
                <span className="text-[11px] text-gray-600">
                  {formatIstDate(
                    lastIdleClusterRecommendation.created_at || lastIdleClusterRecommendation.timestamp
                  ) || 'No timestamp'}
                </span>
              </div>
              {lastIdleClusterRecommendation.description && (
                <p className="text-xs text-gray-700 mt-3">{lastIdleClusterRecommendation.description}</p>
              )}
              {lastIdleClusterRecommendation.details?.idle_duration_minutes && (
                <p className="text-[11px] text-gray-600 mt-2">
                  Idle duration: {lastIdleClusterRecommendation.details.idle_duration_minutes.toFixed(1)}m
                </p>
              )}
            </div>
          ) : lastIdleClusterFromLogs ? (
            <div className="p-4 border border-blue-200 rounded-lg bg-blue-50">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">Idle Cluster Detected</h3>
                  <p className="text-xs text-gray-700 mt-1">{lastIdleClusterFromLogs.logger || 'System'}</p>
                </div>
                <span className="text-[11px] text-gray-600">
                  {lastIdleClusterFromLogs.timestamp ? new Date(lastIdleClusterFromLogs.timestamp).toLocaleString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true,
                    timeZone: 'Asia/Kolkata'
                  }) : 'Now'}
                </span>
              </div>
              <p className="text-xs text-gray-700 mt-3">{lastIdleClusterFromLogs.message}</p>
            </div>
          ) : null}
        </div>
      )}

      {/* Job Recommendation */}
      {(lastFailedJobRecommendation || lastFailedJobFromLogs) && !hasJobBeenHealed && (
        <div className="dxc-card">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-3 text-red-600" />
            Job Recommendation
          </h2>

          {lastFailedJobRecommendation ? (
            <div className="p-4 border border-red-200 rounded-lg bg-red-50">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{lastFailedJobRecommendation.title}</h3>
                  <p className="text-xs text-gray-700 mt-1">
                    {lastFailedJobRecommendation.resource_name || lastFailedJobRecommendation.resource_id || 'Job'}
                  </p>
                </div>
                <span className="text-[11px] text-gray-600">
                  {formatIstDate(
                    lastFailedJobRecommendation.created_at || lastFailedJobRecommendation.timestamp
                  ) || 'No timestamp'}
                </span>
              </div>
              {lastFailedJobRecommendation.description && (
                <p className="text-xs text-gray-700 mt-3">{lastFailedJobRecommendation.description}</p>
              )}
              {lastFailedJobRecommendation.details?.reason && (
                <p className="text-[11px] text-gray-600 mt-2">Reason: {lastFailedJobRecommendation.details.reason}</p>
              )}
              {lastFailedJobRecommendation.details?.error_message && (
                <p className="text-[11px] text-gray-600 mt-1">Error: {lastFailedJobRecommendation.details.error_message}</p>
              )}
            </div>
          ) : lastFailedJobFromLogs ? (
            <div className="p-4 border border-red-200 rounded-lg bg-red-50">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">Failed Job Detected</h3>
                  <p className="text-xs text-gray-700 mt-1">{lastFailedJobFromLogs.logger || 'Job Service'}</p>
                </div>
                <span className="text-[11px] text-gray-600">
                  {lastFailedJobFromLogs.timestamp ? new Date(lastFailedJobFromLogs.timestamp).toLocaleString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true,
                    timeZone: 'Asia/Kolkata'
                  }) : 'Now'}
                </span>
              </div>
              <p className="text-xs text-gray-700 mt-3">{lastFailedJobFromLogs.message}</p>
            </div>
          ) : null}
        </div>
      )}

      {/* Activity History */}
      <div className="dxc-card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Clock className="h-6 w-6 mr-3 text-purple-600" />
          Recent Activity
        </h2>

        <div className="space-y-3">
          {history.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No healing actions yet</p>
          ) : (
            history.map((action, idx) => (
              <div key={idx} className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className={`p-2 rounded-lg ${getStatusColor(action.status)}`}>
                  {action.status === 'success' ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">{action.action_type.replace(/_/g, ' ')}</h3>
                    <span className="text-xs text-gray-500">
                      {new Date(action.timestamp).toLocaleString('en-IN', { 
                        month: 'short', 
                        day: 'numeric', 
                        hour: 'numeric', 
                        minute: '2-digit', 
                        hour12: true,
                        timeZone: 'Asia/Kolkata'
                      })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {action.resource_type}: {action.resource_id}
                  </p>
                  {action.details?.reason && (
                    <p className="text-xs text-gray-500 mt-1">{action.details.reason}</p>
                  )}
                  {action.dry_run && (
                    <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                      Dry Run
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default SelfHealing
