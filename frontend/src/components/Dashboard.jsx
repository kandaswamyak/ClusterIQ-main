import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchStats, analyzeJobsAndClusters, fetchRecommendationsRealtime, fetchLogsStats } from '../services/api'
import { Activity, Database, TrendingDown, AlertCircle, RefreshCw, AlertTriangle, Lightbulb } from 'lucide-react'

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

  const recommendationsList = recommendations?.recommendations || []
  const estimatedSavings = recommendationsList.reduce((sum, r) => sum + parseMonthlySavings(r), 0)
  const confidenceValues = recommendationsList
    .map((rec) => getConfidenceWithFallback(rec))
    .filter((val) => typeof val === 'number')
  const averageConfidence = confidenceValues.length
    ? confidenceValues.reduce((sum, v) => sum + v, 0) / confidenceValues.length
    : null
  const jobRecommendationCount = recommendationsList.filter((rec) => {
    const resourceType = (rec.resource_type || '').toLowerCase()
    return resourceType === 'job' || resourceType === 'jobs'
  }).length
  const clusterRecommendationCount = recommendationsList.filter((rec) => {
    const resourceType = (rec.resource_type || '').toLowerCase()
    return resourceType === 'cluster' || resourceType === 'clusters'
  }).length

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
            <h2 className="text-xl font-semibold mb-4 flex items-center text-white">
              <TrendingDown className="h-5 w-5 mr-2 text-purple-400" />
              📊 Total Recommendations
            </h2>
            <div className="text-4xl font-bold text-purple-400">{recommendations.recommendations?.length || 0}</div>
            <p className="text-gray-300 mt-2 text-sm">✨ Click to view all AI-powered optimization suggestions with savings in $</p>
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
                <Link to="/recommendations" className="mt-2 inline-flex items-center text-xs text-blue-600 hover:text-blue-800 font-semibold hover:underline">
                  <Lightbulb className="h-4 w-4 mr-1 text-amber-500" />
                  💰 {jobRecommendationCount} $ recommendations
                </Link>
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

      {recommendations && recommendations.recommendations?.length > 0 && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">Recent Recommendations</h2>
          <div className="space-y-4">
            {recommendations.recommendations.slice(0, 5).map((rec) => (
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

