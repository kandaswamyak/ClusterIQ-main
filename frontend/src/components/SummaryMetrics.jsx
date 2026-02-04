import { useQuery } from '@tanstack/react-query'
import { fetchSummaryMetrics } from '../services/api'
import { 
  DollarSign, 
  TrendingUp, 
  Target, 
  CheckCircle, 
  AlertTriangle, 
  BarChart3,
  Activity,
  Zap,
  Award,
  Calendar
} from 'lucide-react'

function SummaryMetrics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['summary-metrics'],
    queryFn: fetchSummaryMetrics,
    refetchInterval: 60000, // Refresh every minute
  })

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
        <p className="text-gray-600">Loading summary metrics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
          <div>
            <p className="text-sm font-medium text-red-800">Error loading summary</p>
            <p className="text-sm text-red-600 mt-1">
              {error.response?.data?.error || error.message || 'Failed to fetch summary metrics'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!data || (!data.analysis_metadata?.has_analysis && data.total_recommendations === 0)) {
    return (
      <div className="text-center py-12">
        <div className="bg-gray-50 rounded-lg p-8 max-w-md mx-auto">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Summary Available</h3>
          <p className="text-sm text-gray-600 mb-4">
            Run an analysis first to see cost savings and optimization metrics.
          </p>
        </div>
      </div>
    )
  }

  const {
    total_cost_savings = 0,
    total_cost_savings_formatted = '$0.00',
    total_recommendations = 0,
    jobs_identified = 0,
    resources_optimized = 0,
    by_type = {},
    by_severity = {},
    savings_by_type = {},
    resources_by_type = {},
    analysis_metadata = {},
    success_metrics = {}
  } = data

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">ClusterIQ Summary & Metrics</h1>
        <p className="mt-2 text-sm text-gray-600">
          Track cost savings, optimization progress, and success metrics
        </p>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Cost Savings"
          value={total_cost_savings_formatted}
          subtitle="Potential monthly savings"
          icon={<DollarSign className="h-6 w-6" />}
          color="green"
          trend="up"
        />
        <MetricCard
          title="Jobs Identified"
          value={jobs_identified}
          subtitle="Jobs flagged for optimization"
          icon={<Target className="h-6 w-6" />}
          color="blue"
        />
        <MetricCard
          title="Total Recommendations"
          value={total_recommendations}
          subtitle="Optimization opportunities"
          icon={<CheckCircle className="h-6 w-6" />}
          color="purple"
        />
        <MetricCard
          title="Resources Optimized"
          value={resources_optimized}
          subtitle="Unique resources analyzed"
          icon={<Activity className="h-6 w-6" />}
          color="indigo"
        />
      </div>

      {/* Cost Savings Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 flex items-center text-gray-900">
            <DollarSign className="h-5 w-5 mr-2 text-green-600" />
            Cost Savings by Type
          </h2>
          <div className="space-y-4">
            <SavingsBar
              label="Cost Leaks"
              value={savings_by_type.cost_leak || 0}
              total={total_cost_savings}
              color="red"
            />
            <SavingsBar
              label="Value Leaks"
              value={savings_by_type.value_leak || 0}
              total={total_cost_savings}
              color="yellow"
            />
            <SavingsBar
              label="Optimization Opportunities"
              value={savings_by_type.optimization_opportunity || 0}
              total={total_cost_savings}
              color="blue"
            />
          </div>
        </div>

        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 flex items-center text-gray-900">
            <BarChart3 className="h-5 w-5 mr-2 text-purple-600" />
            Recommendations by Severity
          </h2>
          <div className="space-y-4">
            <SeverityBar
              label="High Priority"
              value={by_severity.high || 0}
              total={total_recommendations}
              color="red"
            />
            <SeverityBar
              label="Medium Priority"
              value={by_severity.medium || 0}
              total={total_recommendations}
              color="yellow"
            />
            <SeverityBar
              label="Low Priority"
              value={by_severity.low || 0}
              total={total_recommendations}
              color="blue"
            />
          </div>
        </div>
      </div>

      {/* Recommendations Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <StatBox
          title="Cost Leaks"
          value={by_type.cost_leak || 0}
          icon={<AlertTriangle className="h-5 w-5" />}
          color="red"
          description="Over-provisioned resources"
        />
        <StatBox
          title="Value Leaks"
          value={by_type.value_leak || 0}
          icon={<TrendingUp className="h-5 w-5" />}
          color="yellow"
          description="Inefficient allocations"
        />
        <StatBox
          title="Optimizations"
          value={by_type.optimization_opportunity || 0}
          icon={<Zap className="h-5 w-5" />}
          color="blue"
          description="Right-sizing opportunities"
        />
      </div>

      {/* Success Metrics */}
      <div className="dxc-card">
        <h2 className="text-xl font-semibold mb-6 flex items-center text-gray-900">
          <Award className="h-5 w-5 mr-2 text-primary-600" />
          Success Metrics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <SuccessMetric
            label="Recommendations Generated"
            value={success_metrics.recommendations_generated || 0}
          />
          <SuccessMetric
            label="High Priority Actions"
            value={success_metrics.high_priority_actions || 0}
          />
          <SuccessMetric
            label="Potential Monthly Savings"
            value={`$${(success_metrics.potential_monthly_savings || 0).toLocaleString()}`}
          />
          <SuccessMetric
            label="Optimization Coverage"
            value={success_metrics.optimization_coverage || '0 jobs, 0 resources'}
          />
        </div>
      </div>

      {/* Resources Breakdown */}
      {Object.keys(resources_by_type).length > 0 && (
        <div className="dxc-card">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">Resources by Type</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Object.entries(resources_by_type).map(([type, count]) => (
              <div key={type} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm font-medium text-gray-600 capitalize mb-1">
                  {type.replace('_', ' ')}
                </p>
                <p className="text-2xl font-bold text-gray-900">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Metadata */}
      {analysis_metadata.timestamp && (
        <div className="bg-blue-50 border-l-4 border-primary-600 rounded-r-lg p-4">
          <div className="flex items-center">
            <Calendar className="h-5 w-5 text-primary-600 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-900">Last Analysis</p>
              <p className="text-sm text-gray-600">
                {new Date(analysis_metadata.timestamp).toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Analyzed {analysis_metadata.jobs_analyzed || 0} jobs and{' '}
                {analysis_metadata.clusters_analyzed || 0} clusters
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ title, value, subtitle, icon, color, trend }) {
  const colorClasses = {
    green: 'bg-green-50 border-green-200 text-green-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  }

  const iconColors = {
    green: 'text-green-600',
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    indigo: 'text-indigo-600',
  }

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6 dxc-card`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`${iconColors[color]} opacity-80`}>{icon}</div>
        {trend && (
          <TrendingUp className={`h-4 w-4 ${iconColors[color]} opacity-60`} />
        )}
      </div>
      <div>
        <p className="text-sm font-medium mb-2 opacity-75">{title}</p>
        <p className="text-3xl font-bold">{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-600 mt-2 opacity-75">{subtitle}</p>
        )}
      </div>
    </div>
  )
}

function SavingsBar({ label, value, total, color }) {
  const percentage = total > 0 ? (value / total) * 100 : 0
  const colorClasses = {
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    blue: 'bg-blue-500',
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-gray-900">
          ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`${colorClasses[color]} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% of total savings</p>
    </div>
  )
}

function SeverityBar({ label, value, total, color }) {
  const percentage = total > 0 ? (value / total) * 100 : 0
  const colorClasses = {
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    blue: 'bg-blue-500',
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-gray-900">{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`${colorClasses[color]} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% of recommendations</p>
    </div>
  )
}

function StatBox({ title, value, icon, color, description }) {
  const colorClasses = {
    red: 'bg-red-50 border-red-200 text-red-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
  }

  const iconColors = {
    red: 'text-red-600',
    yellow: 'text-yellow-600',
    blue: 'text-blue-600',
  }

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6 dxc-card`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`${iconColors[color]} opacity-80`}>{icon}</div>
      </div>
      <div>
        <p className="text-sm font-medium mb-2 opacity-75">{title}</p>
        <p className="text-3xl font-bold">{value}</p>
        {description && (
          <p className="text-xs text-gray-600 mt-2 opacity-75">{description}</p>
        )}
      </div>
    </div>
  )
}

function SuccessMetric({ label, value }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

export default SummaryMetrics
