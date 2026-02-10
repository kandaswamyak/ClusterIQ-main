import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchStats, analyzeJobsAndClusters, fetchRecommendationsRealtime, fetchLogsStats, getSelfHealingStats, getHealingHistory } from '../services/api'
import { Activity, Database, TrendingDown, AlertCircle, RefreshCw, AlertTriangle, Lightbulb, Shield, CheckCircle, XCircle } from 'lucide-react'

function Dashboard() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [lastAnalysis, setLastAnalysis] = useState(null)

  const { data: stats, isLoading: statsLoading, refetch: refetchStats, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Debug: Log stats to see what we're getting
  if (stats) {
    console.log('Dashboard Stats:', stats)
  }
  if (statsError) {
    console.error('Stats Error:', statsError)
  }

  const { data: recommendations, refetch: refetchRecommendations } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    refetchInterval: 30000,
  })

  const { data: logsStats, isLoading: logsStatsLoading } = useQuery({
    queryKey: ['logs-stats'],
    queryFn: fetchLogsStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: healingStats } = useQuery({
    queryKey: ['self-healing-stats'],
    queryFn: getSelfHealingStats,
    refetchInterval: 30000,
  })

  const { data: healingHistory } = useQuery({
    queryKey: ['healing-history'],
    queryFn: () => getHealingHistory(10),
    refetchInterval: 30000,
  })

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      await analyzeJobsAndClusters()
      setLastAnalysis(new Date().toLocaleString())
      refetchRecommendations()
      refetchStats()
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const getFallbackMonthlySavings = (rec) => {
    const severity = (rec?.severity || 'low').toLowerCase()
    if (severity === 'high') return 250
    if (severity === 'medium') return 100
    return 25
  }

  const parseMonthlySavings = (rec) => {
    if (!rec) return 0
    const directMonthly = rec.estimated_monthly_savings_usd ?? rec.estimated_savings_monthly
    if (typeof directMonthly === 'number') return directMonthly

    const annual = rec.estimated_savings_annual ?? rec.estimated_annual_savings_usd
    if (typeof annual === 'number') return annual / 12

    if (typeof rec.estimated_savings === 'string' && rec.estimated_savings.trim()) {
      const value = parseFloat(rec.estimated_savings.replace(/[^0-9.]/g, '')) || 0
      const label = rec.estimated_savings.toLowerCase()
      if (label.includes('year') || label.includes('annual')) return value / 12
      return value
    }
    if (typeof rec.estimated_savings === 'number') return rec.estimated_savings
    const fallback = getFallbackMonthlySavings(rec)
    return fallback
  }

  const getConfidenceValue = (rec) => {
    const raw = rec?.confidence_score ?? rec?.confidence ?? rec?.confidence_pct
    if (raw === undefined || raw === null || raw === '') return null
    if (typeof raw === 'number') return raw <= 1 ? raw * 100 : raw
    const parsed = parseFloat(String(raw).replace(/[^0-9.]/g, ''))
    return Number.isFinite(parsed) ? parsed : null
  }

  const getConfidenceWithFallback = (rec) => {
    const value = getConfidenceValue(rec)
    if (value !== null) return value
    const severity = (rec?.severity || 'low').toLowerCase()
    if (severity === 'high') return 80
    if (severity === 'medium') return 65
    return 55
  }

  const successfullyHealedResourceIds = new Set(
    (healingHistory?.history || [])
      .filter((action) => action.status === 'success')
      .map((action) => String(action.resource_id))
  )

  const isHealedRecommendation = (rec) => {
    if (!rec) return false
    const candidates = []
    if (rec.resource_id !== undefined && rec.resource_id !== null) {
      candidates.push(String(rec.resource_id))
    }
    if (rec.resource_name) candidates.push(String(rec.resource_name))
    return candidates.some((id) => successfullyHealedResourceIds.has(id))
  }

  const isActiveRecommendation = (rec) => {
    const status = (rec?.status || '').toLowerCase()
    if (!status) return true
    // Show pending and failed items (failed can be retried)
    return status === 'pending' || status === 'failed'
  }

  // Get unique recommendations by deduplicating based on resource_id + type
  const getUniqueRecommendations = (recs) => {
    const uniqueMap = new Map()
    for (const rec of recs) {
      const resourceId = rec.resource_id || rec.resource_name || 'unknown'
      const type = rec.type || 'other'
      const key = `${resourceId}_${type}`
      
      // Keep the most recent recommendation for each resource+type combination
      if (!uniqueMap.has(key)) {
        uniqueMap.set(key, rec)
      } else {
        const existing = uniqueMap.get(key)
        const existingDate = new Date(existing.created_at || existing.updated_at || 0)
        const newDate = new Date(rec.created_at || rec.updated_at || 0)
        if (newDate > existingDate) {
          uniqueMap.set(key, rec)
        }
      }
    }
    return Array.from(uniqueMap.values())
  }

  const allRecommendations = (recommendations?.recommendations || []).filter(
    (rec) => isActiveRecommendation(rec) && !isHealedRecommendation(rec)
  )
  const recommendationsList = getUniqueRecommendations(allRecommendations)
  const estimatedSavings = recommendationsList.reduce((sum, r) => sum + parseMonthlySavings(r), 0)
  const confidenceValues = recommendationsList
    .map((rec) => getConfidenceWithFallback(rec))
    .filter((val) => typeof val === 'number')
  const averageConfidence = confidenceValues.length
    ? confidenceValues.reduce((sum, v) => sum + v, 0) / confidenceValues.length
    : null
  const executionErrorRecs = recommendationsList.filter(
    (rec) => (rec.type || '').toLowerCase() === 'execution_error'
  )
  const executionErrorConfidenceValues = executionErrorRecs
    .map((rec) => getConfidenceWithFallback(rec))
    .filter((val) => typeof val === 'number')
  const executionErrorConfidence = executionErrorConfidenceValues.length
    ? executionErrorConfidenceValues.reduce((sum, v) => sum + v, 0) / executionErrorConfidenceValues.length
    : null
  const jobRecommendationCount = recommendationsList.filter((rec) => {
    const resourceType = (rec.resource_type || '').toLowerCase()
    return resourceType === 'job' || resourceType === 'jobs'
  }).length
  const jobRecommendationSavings = recommendationsList
    .filter((rec) => {
      const resourceType = (rec.resource_type || '').toLowerCase()
      return resourceType === 'job' || resourceType === 'jobs'
    })
    .reduce((sum, rec) => sum + parseMonthlySavings(rec), 0)
  const clusterRecommendationCount = recommendationsList.filter((rec) => {
    const resourceType = (rec.resource_type || '').toLowerCase()
    return resourceType === 'cluster' || resourceType === 'clusters'
  }).length
  const recentRecommendations = [...recommendationsList].sort((a, b) => {
    const typeOrder = {
      execution_error: 0,
      stuck_pending_job: 1,
      frequent_retries: 2,
      cost_leak: 3,
      idle_cluster: 4,
      optimization: 5,
      other: 6
    }
    const severityOrder = { high: 0, medium: 1, low: 2 }
    const aType = (a.type || 'other').toLowerCase()
    const bType = (b.type || 'other').toLowerCase()
    const typeDiff = (typeOrder[aType] ?? 99) - (typeOrder[bType] ?? 99)
    if (typeDiff !== 0) return typeDiff
    const aSev = (a.severity || 'low').toLowerCase()
    const bSev = (b.severity || 'low').toLowerCase()
    return (severityOrder[aSev] ?? 99) - (severityOrder[bSev] ?? 99)
  })

  return (
    <div className="space-y-8">
      {/* Error Display */}
      {statsError && (
        <div className="bg-red-900 border-l-4 border-red-500 rounded-r-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 mr-3 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-200">Error loading statistics</p>
              <p className="text-xs text-red-300 mt-1">{statsError.message || 'Failed to connect to backend'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">Dashboard</h1>
          <p className="mt-3 text-base text-gray-600 font-medium">Monitor your Databricks infrastructure and optimization opportunities</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          <RefreshCw className={`h-5 w-5 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {lastAnalysis && (
        <div className="bg-purple-900 border-l-4 border-purple-500 rounded-r-lg p-4">
          <p className="text-sm text-purple-200">
            <span className="font-medium">Last analysis:</span> {lastAnalysis}
          </p>
        </div>
      )}

      {recommendations && (
        <Link to="/recommendations" className="block cursor-pointer">
          <div className="dxc-card hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 border-purple-700">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
              <TrendingDown className="h-5 w-5 mr-2 text-purple-600" />
              📊 Total Recommendations
            </h2>
            <div className="text-4xl font-bold text-purple-600">{recommendationsList.length}</div>
            <p className="text-gray-600 mt-2 text-sm">✨ Click to view all AI-powered optimization suggestions with savings in $</p>
          </div>
        </Link>
      )}

      {statsLoading ? (
        <div className="text-center py-12 text-gray-400">Loading statistics...</div>
      ) : (
        <>
          {/* Primary Compute Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Jobs"
              value={stats?.total_jobs || 0}
              icon={<Database className="h-6 w-6" />}
              color="blue"
              footer={
                <div className="mt-2 space-y-1">
                  {executionErrorRecs.length > 0 && (
                    <>
                      <Link to="/recommendations" className="inline-flex items-center text-xs text-red-600 hover:text-red-800 font-semibold hover:underline">
                        🔴 {executionErrorRecs.length} execution errors detected
                      </Link>
                      {executionErrorConfidence !== null && (
                        <div className="text-xs text-red-600 font-semibold">
                          🔎 Confidence {Math.round(executionErrorConfidence)}%
                        </div>
                      )}
                    </>
                  )}
                  <Link to="/recommendations" className="inline-flex items-center text-xs text-green-600 hover:text-green-800 hover:underline">
                    <Lightbulb className="h-4 w-4 mr-1 text-amber-500" />
                    💰 {jobRecommendationCount} $ recommendations
                  </Link>
                  {jobRecommendationSavings > 0 && (
                    <div className="text-xs text-green-700 font-semibold">
                      ${jobRecommendationSavings.toFixed(2)}/mo potential savings
                    </div>
                  )}
                </div>
              }
            />
            <StatCard
              title="Total Clusters"
              value={stats?.total_clusters || 0}
              icon={<Activity className="h-6 w-6" />}
              color="green"
              footer={
                <Link to="/recommendations" className="mt-2 inline-flex items-center text-xs text-green-600 hover:text-green-800 font-semibold hover:underline">
                  <Lightbulb className="h-4 w-4 mr-1 text-amber-500" />
                  💰 {clusterRecommendationCount} $ recommendations
                </Link>
              }
            />
            <StatCard
              title="Running Clusters"
              value={stats?.running_clusters || 0}
              icon={<Activity className="h-6 w-6" />}
              color="yellow"
            />
            <StatCard
              title="Idle Clusters"
              value={stats?.idle_clusters || 0}
              icon={<AlertCircle className="h-6 w-6" />}
              color="red"
            />
          </div>

          {/* All Compute Types Overview */}
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">All Compute Resources</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
              <StatCard
                title="SQL Warehouses"
                value={stats?.sql_warehouses || 0}
                icon={<Database className="h-5 w-5" />}
                color="blue"
                compact
              />
              <StatCard
                title="Pools"
                value={stats?.pools || 0}
                icon={<Activity className="h-5 w-5" />}
                color="green"
                compact
              />
              <StatCard
                title="Vector Search"
                value={stats?.vector_search_endpoints || 0}
                icon={<Database className="h-5 w-5" />}
                color="purple"
                compact
              />
              <StatCard
                title="Policies"
                value={stats?.policies || 0}
                icon={<Activity className="h-5 w-5" />}
                color="yellow"
                compact
              />
              <StatCard
                title="Apps"
                value={stats?.apps || 0}
                icon={<Database className="h-5 w-5" />}
                color="blue"
                compact
              />
              <StatCard
                title="Lakebase"
                value={stats?.lakebase_resources || 0}
                icon={<Activity className="h-5 w-5" />}
                color="green"
                compact
              />
            </div>
          </div>

          {/* AI/ML Resources Section */}
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">AI/ML Resources</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              <StatCard
                title="ML/AI Jobs"
                value={stats?.ml_jobs || 0}
                icon={<Database className="h-5 w-5" />}
                color="purple"
                compact
              />
              <StatCard
                title="MLflow Experiments"
                value={stats?.mlflow_experiments || 0}
                icon={<Database className="h-5 w-5" />}
                color="indigo"
                compact
              />
              <StatCard
                title="MLflow Models"
                value={stats?.mlflow_models || 0}
                icon={<Database className="h-5 w-5" />}
                color="purple"
                compact
              />
              <StatCard
                title="Model Serving"
                value={stats?.model_serving_endpoints || 0}
                icon={<Activity className="h-5 w-5" />}
                color="green"
                compact
              />
              <StatCard
                title="Feature Store"
                value={stats?.feature_store_tables || 0}
                icon={<Database className="h-5 w-5" />}
                color="blue"
                compact
              />
            </div>
          </div>
        </>
      )}

      {recommendations && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
            <TrendingDown className="h-5 w-5 mr-2 text-green-600" />
            Estimated Savings
          </h2>
          <div className="text-4xl font-bold text-green-600">
            ${estimatedSavings.toFixed(2)}
          </div>
          <p className="text-gray-600 mt-2 text-sm">Potential monthly cost savings</p>
          {averageConfidence !== null && (
            <p className="text-xs text-blue-600 mt-2 font-semibold">
              🔎 Average confidence: {Math.round(averageConfidence)}%
            </p>
          )}
        </div>
      )}

      {recommendations && executionErrorRecs.length > 0 && (
        <div className="dxc-card border-l-4 border-red-500">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold flex items-center text-gray-900">
              <AlertTriangle className="h-5 w-5 mr-2 text-red-600" />
              Execution Errors
            </h2>
            <Link to="/recommendations" className="text-xs font-semibold text-red-600 hover:text-red-800 hover:underline">
              View all →
            </Link>
          </div>
          <p className="text-sm text-red-700">
            🔴 {executionErrorRecs.length} failed jobs detected
          </p>
          {executionErrorConfidence !== null && (
            <p className="text-xs text-red-600 mt-1 font-semibold">
              🔎 Average confidence: {Math.round(executionErrorConfidence)}%
            </p>
          )}
          <div className="mt-3 space-y-2">
            {executionErrorRecs.slice(0, 3).map((rec) => (
              <Link
                key={rec.id}
                to="/recommendations"
                className="block bg-red-50 rounded-lg p-3 border border-red-200 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                      {rec.title || 'Execution error detected'}
                    </p>
                    {rec.resource_name && (
                      <p className="text-xs text-gray-600 truncate">Job: {rec.resource_name}</p>
                    )}
                  </div>
                  <span className="text-xs font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded-full">
                    {Math.round(getConfidenceWithFallback(rec))}%
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {recommendations && recommendations.recommendations?.length > 0 && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">Recent Recommendations</h2>
          <div className="space-y-4">
            {recentRecommendations.slice(0, 5).map((rec) => (
              (() => {
                const monthlySavings = parseMonthlySavings(rec)
                const confidence = getConfidenceWithFallback(rec)
                return (
              <Link
                key={rec.id}
                to="/recommendations"
                className="block bg-gray-50 rounded-lg p-4 border-l-4 border-primary-600 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{rec.title || rec.type}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {rec.description || 'No description available'}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {monthlySavings > 0 && (
                        <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                          ${monthlySavings.toFixed(2)}/mo
                        </span>
                      )}
                      {confidence !== null && (
                        <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                          Confidence {Math.round(confidence)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <span
                    className={`ml-4 px-3 py-1 rounded-full text-xs font-semibold ${
                      rec.severity === 'high'
                        ? 'bg-red-100 text-red-700'
                        : rec.severity === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {rec.severity || 'low'}
                  </span>
                </div>
              </Link>
                )
              })()
            ))}
          </div>
        </div>
      )}

      {/* Self-Healing Activity */}
      <div className="dxc-card border-l-4 border-green-500">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center text-gray-900">
            <Shield className="h-5 w-5 mr-2 text-green-600" />
            Self-Healing Status
          </h2>
          <Link to="/self-healing" className="text-xs font-semibold text-green-600 hover:text-green-800 hover:underline">
            View Details →
          </Link>
        </div>

        {healingStats ? (
          <div className="space-y-4">
            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-4">
                <p className="text-xs text-green-700 font-semibold uppercase tracking-wide mb-2">Status</p>
                <p className="text-2xl font-bold text-green-700">{healingStats.enabled ? '🟢 Active' : '🔴 Inactive'}</p>
                <p className="text-xs text-green-600 mt-2">{healingStats.dry_run ? 'Dry-run mode' : 'Live mode'}</p>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-4">
                <p className="text-xs text-blue-700 font-semibold uppercase tracking-wide mb-2">Cluster Health</p>
                <p className="text-2xl font-bold text-blue-700">{healingStats.health_summary?.health_percentage?.toFixed(0) || '0'}%</p>
                <p className="text-xs text-blue-600 mt-2">{healingStats.health_summary?.healthy || 0}/{healingStats.health_summary?.total_clusters || 0} healthy</p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-4">
                <p className="text-xs text-purple-700 font-semibold uppercase tracking-wide mb-2">Actions Taken</p>
                <p className="text-2xl font-bold text-purple-700">{healingStats.healing_stats?.total_actions || 0}</p>
                <p className="text-xs text-purple-600 mt-2">{healingStats.healing_stats?.successful || 0} successful</p>
              </div>
            </div>

            {/* Recent Activity */}
            {healingHistory?.history && healingHistory.history.length > 0 ? (
              <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm">Recent Activity</h3>
                <div className="space-y-2">
                  {healingHistory.history.slice(0, 3).map((action, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-2 bg-white rounded border border-gray-100 text-sm">
                      {action.status === 'success' ? (
                        <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 capitalize truncate">{action.action_type.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-gray-500">{action.resource_type}: {action.resource_id}</p>
                      </div>
                      <span className="text-xs text-gray-500 flex-shrink-0 whitespace-nowrap">
                        {new Date(action.timestamp).toLocaleString('en-US', { 
                          month: 'short', 
                          day: 'numeric', 
                          hour: 'numeric', 
                          minute: '2-digit', 
                          hour12: true 
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 text-center">
                <p className="text-sm text-gray-600">No healing actions yet</p>
              </div>
            )}
          </div>
        ) : (
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, compact = false, footer }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  }

  const iconColors = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    indigo: 'text-indigo-600',
  }

  if (compact) {
    return (
      <div className={`${colorClasses[color]} border rounded-lg p-4 dxc-card`}>
        <div className="flex flex-col items-center text-center">
          <div className={`${iconColors[color]} opacity-80 mb-2`}>{icon}</div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs font-medium mt-1 opacity-75">{title}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6 dxc-card`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium mb-2 opacity-75">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
          {footer}
        </div>
        <div className={`${iconColors[color]} opacity-80`}>{icon}</div>
      </div>
    </div>
  )
}

export default Dashboard

