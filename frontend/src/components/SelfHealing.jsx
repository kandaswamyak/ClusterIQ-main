import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getSelfHealingConfig, 
  updateSelfHealingConfig, 
  getHealthStatus,
  runSelfHealing,
  getHealingHistory,
  getSelfHealingStats
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
    refetchInterval: 30000
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['self-healing-stats'],
    queryFn: getSelfHealingStats,
    refetchInterval: 10000
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
      
      // Refresh queries
      queryClient.invalidateQueries(['healing-history'])
      queryClient.invalidateQueries(['self-healing-stats'])
      queryClient.invalidateQueries(['health-status'])
    },
    onError: (error) => {
      setHealingMessage(`Error: ${error?.message || 'Failed to run healing'}`)
      setTimeout(() => setHealingMessage(null), 5000)
    }
  })

  const config = configData?.config || {}
  const stats = statsData || {}
  const history = historyData?.history || []
  const health = healthData?.summary || {}

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
        <div className="metric-card" style={{ background: stats.enabled ? 'linear-gradient(135deg, #065f46 0%, #10b981 100%)' : 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)', border: '1px solid' + (stats.enabled ? '#34d399' : '#d1d5db') }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Status</h3>
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {stats.enabled ? 'Active' : 'Inactive'}
          </div>
          <p className="text-sm text-white mt-3 font-medium opacity-90">
            {stats.dry_run ? 'Dry-run mode' : 'Live mode'}
          </p>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)', border: '1px solid #60a5fa' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-blue-200 uppercase tracking-wide">Cluster Health</h3>
            <Activity className="h-6 w-6 text-blue-300" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            {health.health_percentage ? `${health.health_percentage.toFixed(0)}%` : '-'}
          </div>
          <p className="text-sm text-blue-200 mt-3 font-medium">
            {health.healthy || 0} / {health.total_clusters || 0} healthy
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
            {stats.auto_healable_issues || 0}
          </div>
          <p className="text-sm text-red-200 mt-3 font-medium">
            Issues detected
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
                      {new Date(action.timestamp).toLocaleString()}
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

      {/* Health Issues */}
      {healthData?.auto_healable && healthData.auto_healable.length > 0 && (
        <div className="dxc-card border-l-4 border-amber-500">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-3 text-amber-600" />
            Auto-Healable Issues
          </h2>
          <div className="space-y-3">
            {healthData.auto_healable.map((issue, idx) => (
              <div key={idx} className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-amber-900">{issue.cluster_name}</h3>
                    <p className="text-sm text-amber-700 mt-1">{issue.issue.message}</p>
                    <p className="text-xs text-amber-600 mt-1">Severity: {issue.issue.severity}</p>
                  </div>
                  <span className="px-2 py-1 bg-amber-200 text-amber-800 text-xs rounded font-semibold">
                    {issue.issue.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SelfHealing
