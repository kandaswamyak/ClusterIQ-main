import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchStats, analyzeJobsAndClusters, fetchRecommendations, fetchLogsStats } from '../services/api'
import { Activity, Database, TrendingDown, AlertCircle, RefreshCw, AlertTriangle } from 'lucide-react'

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
    queryKey: ['recommendations'],
    queryFn: fetchRecommendations,
    enabled: false, // Don't fetch automatically
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

  const highSeverityCount = recommendations?.recommendations?.filter(
    (r) => r.severity === 'high'
  ).length || 0

  const estimatedSavings = recommendations?.recommendations?.reduce((sum, r) => {
    const savings = parseFloat(r.estimated_savings?.replace(/[^0-9.]/g, '') || 0)
    return sum + savings
  }, 0) || 0

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">Monitor your Databricks infrastructure and optimization opportunities</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {lastAnalysis && (
        <div className="bg-blue-50 border-l-4 border-primary-600 rounded-r-lg p-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Last analysis:</span> {lastAnalysis}
          </p>
        </div>
      )}

      {statsLoading ? (
        <div className="text-center py-12 text-gray-500">Loading statistics...</div>
      ) : (
        <>
          {/* Primary Compute Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Jobs"
              value={stats?.total_jobs || 0}
              icon={<Database className="h-6 w-6" />}
              color="blue"
            />
            <StatCard
              title="Total Clusters"
              value={stats?.total_clusters || 0}
              icon={<Activity className="h-6 w-6" />}
              color="green"
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="dxc-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
              <TrendingDown className="h-5 w-5 mr-2 text-red-600" />
              High Priority Issues
            </h2>
            <div className="text-4xl font-bold text-red-600">{highSeverityCount}</div>
            <p className="text-gray-600 mt-2 text-sm">Issues requiring immediate attention</p>
          </div>

          <div className="dxc-card">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-900">
              <TrendingDown className="h-5 w-5 mr-2 text-green-600" />
              Estimated Savings
            </h2>
            <div className="text-4xl font-bold text-green-600">
              ${estimatedSavings.toFixed(2)}
            </div>
            <p className="text-gray-600 mt-2 text-sm">Potential monthly cost savings</p>
          </div>
        </div>
      )}

      {recommendations && recommendations.recommendations?.length > 0 && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">Recent Recommendations</h2>
          <div className="space-y-4">
            {recommendations.recommendations.slice(0, 5).map((rec) => (
              <div
                key={rec.id}
                className="bg-gray-50 rounded-lg p-4 border-l-4 border-primary-600 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{rec.title || rec.type}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {rec.description || 'No description available'}
                    </p>
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
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Summary */}
      {!logsStatsLoading && logsStats?.stats && (
        <div className="dxc-card">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Application Logs Summary</h2>
            <a href="/logs" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View All →
            </a>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-blue-50 rounded p-3 text-center border border-blue-200">
              <p className="text-xs text-gray-600 font-medium">Total Logs</p>
              <p className="text-2xl font-bold text-blue-600">{logsStats.stats.total_logs}</p>
            </div>
            <div className="bg-yellow-50 rounded p-3 text-center border border-yellow-200">
              <p className="text-xs text-gray-600 font-medium">Warnings</p>
              <p className="text-2xl font-bold text-yellow-600">{logsStats.stats.logs_by_level?.WARNING || 0}</p>
            </div>
            <div className="bg-red-50 rounded p-3 text-center border border-red-200">
              <p className="text-xs text-gray-600 font-medium">Errors</p>
              <p className="text-2xl font-bold text-red-600">{logsStats.stats.logs_by_level?.ERROR || 0}</p>
            </div>
            <div className="bg-green-50 rounded p-3 text-center border border-green-200">
              <p className="text-xs text-gray-600 font-medium">Capacity</p>
              <p className="text-2xl font-bold text-green-600">{logsStats.stats.capacity_usage}</p>
            </div>
          </div>
          {(logsStats.stats.logs_by_level?.ERROR > 0 || logsStats.stats.logs_by_level?.CRITICAL > 0) && (
            <div className="bg-red-50 border-l-4 border-red-500 rounded-r p-3 flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">Active Issues Detected</p>
                <p className="text-xs text-red-700 mt-1">
                  {logsStats.stats.logs_by_level?.ERROR || 0} error(s) and {logsStats.stats.logs_by_level?.CRITICAL || 0} critical issue(s) found
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon, color, compact = false }) {
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
        </div>
        <div className={`${iconColors[color]} opacity-80`}>{icon}</div>
      </div>
    </div>
  )
}

export default Dashboard

