import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  fetchRecommendationsRealtime,
  analyzeJobsAndClusters,
  approveRecommendation,
  applyRecommendation,
  rejectRecommendation
} from '../services/api'
import { AlertTriangle, TrendingDown, DollarSign, RefreshCw, CheckCircle2, XCircle } from 'lucide-react'

function Recommendations() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [actionState, setActionState] = useState({})
  const [itemsPerPage] = useState(20)
  const [visibleItems, setVisibleItems] = useState({}) // Track visible items per type

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
    retry: 2,
    retryDelay: 1000,
  })

  const handleManualAnalyze = async () => {
    setIsAnalyzing(true)
    setAnalysisError(null)
    try {
      console.log('Starting analysis...')
      const result = await analyzeJobsAndClusters()
      console.log('Analysis completed:', result)
      
      // Check if analysis was successful
      if (result && result.summary) {
        console.log(`Analysis type: ${result.summary.analysis_type}, Recommendations: ${result.summary.recommendations_count}`)
        
        // Wait a moment for the cache to be updated
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Refetch recommendations
        await refetch()
        console.log('Recommendations refetched')
      } else {
        throw new Error('Analysis did not return expected results')
      }
    } catch (error) {
      console.error('Analysis failed:', error)
      // Don't show error if it's just about AI not being available - rule-based analysis should still work
      const errorMessage = error.response?.data?.error || error.message || ''
      if (errorMessage.includes('langchain') || errorMessage.includes('AI agent')) {
        // This is expected - rule-based analysis should still work
        console.log('AI not available, but rule-based analysis should work')
        // Try to refetch anyway - rule-based analysis might have completed
        await new Promise(resolve => setTimeout(resolve, 1000))
        await refetch()
      } else {
        setAnalysisError(errorMessage || 'Analysis failed. Please check backend connection.')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const recommendations = data?.recommendations || []

  const handleRecommendationAction = async (recId, action) => {
    setActionState((prev) => ({
      ...prev,
      [recId]: { status: 'loading', message: null, error: null }
    }))
    try {
      if (action === 'approve') {
        await approveRecommendation(recId)
        setActionState((prev) => ({
          ...prev,
          [recId]: { status: 'approved', message: 'Recommendation approved', error: null }
        }))
      } else if (action === 'apply') {
        await approveRecommendation(recId)
        await applyRecommendation(recId)
        setActionState((prev) => ({
          ...prev,
          [recId]: { status: 'success', message: 'Recommendation applied', error: null }
        }))
      } else if (action === 'reject') {
        await rejectRecommendation(recId)
        setActionState((prev) => ({
          ...prev,
          [recId]: { status: 'success', message: 'Recommendation rejected', error: null }
        }))
      }
      await refetch()
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Action failed'
      setActionState((prev) => ({
        ...prev,
        [recId]: { status: 'error', message: null, error: message }
      }))
    }
  }

  const groupedByType = recommendations.reduce((acc, rec) => {
    const type = rec.type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push(rec)
    return acc
  }, {})

  const groupedBySeverity = recommendations.reduce((acc, rec) => {
    const severity = rec.severity || 'low'
    if (!acc[severity]) acc[severity] = []
    acc[severity].push(rec)
    return acc
  }, {})

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">AI Recommendations</h1>
          <p className="mt-3 text-base text-gray-600 font-medium">AI-powered optimization suggestions for your Databricks infrastructure</p>
        </div>
        <div className="flex items-center space-x-4 flex-wrap">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Auto-refresh</span>
          </label>
          {autoRefresh && (
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-white border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
              <option value={300}>5min</option>
            </select>
          )}
          <button
            onClick={handleManualAnalyze}
            disabled={isAnalyzing}
            className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            <RefreshCw className={`h-5 w-5 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
            {isAnalyzing ? 'Analyzing...' : 'Analyze Now'}
          </button>
        </div>
      </div>

      {data?.timestamp && (
        <div className="bg-blue-50 border-l-4 border-primary-600 rounded-r-lg p-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Last updated:</span> {new Date(data.timestamp).toLocaleString()}
            {data.real_time && ' (Real-time)'}
          </p>
        </div>
      )}

      {(error || analysisError) && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">
                {analysisError ? 'Analysis Error' : 'Error loading recommendations'}
              </p>
              <p className="text-sm text-red-600 mt-1">
                {analysisError || error.response?.data?.error || error.message || 'Failed to fetch recommendations'}
              </p>
              <p className="text-xs text-red-500 mt-2">
                {analysisError 
                  ? 'Please check that the backend server is running and Databricks credentials are configured.'
                  : 'Make sure the backend server is running and you have run an analysis first.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-600">Loading recommendations...</p>
        </div>
      ) : !data || !data.has_analysis || recommendations.length === 0 ? (
        <div className="text-center py-12">
          <div className="bg-gray-50 rounded-lg p-8 max-w-md mx-auto">
            <TrendingDown className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No recommendations available</h3>
            <p className="text-sm text-gray-600 mb-4">
              {data?.message || "Click 'Analyze Now' to generate AI-powered recommendations for your Databricks infrastructure."}
            </p>
            <button
              onClick={handleManualAnalyze}
              disabled={isAnalyzing}
              className="dxc-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-4 w-4 mr-2 inline ${isAnalyzing ? 'animate-spin' : ''}`} />
              {isAnalyzing ? 'Analyzing...' : 'Analyze Now'}
            </button>
            {isAnalyzing && (
              <p className="text-xs text-gray-500 mt-4">
                This may take a few moments. Analyzing all compute resources...
              </p>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Calculate annual savings per severity */}
          {(() => {
            // Calculate annual savings by severity
            const highSavings = (groupedBySeverity.high || []).reduce((sum, rec) => {
              const annual = rec.estimated_savings_annual || (rec.estimated_savings_monthly ? rec.estimated_savings_monthly * 12 : 0)
              return sum + annual
            }, 0)
            
            const mediumSavings = (groupedBySeverity.medium || []).reduce((sum, rec) => {
              const annual = rec.estimated_savings_annual || (rec.estimated_savings_monthly ? rec.estimated_savings_monthly * 12 : 0)
              return sum + annual
            }, 0)
            
            const lowSavings = (groupedBySeverity.low || []).reduce((sum, rec) => {
              const annual = rec.estimated_savings_annual || (rec.estimated_savings_monthly ? rec.estimated_savings_monthly * 12 : 0)
              return sum + annual
            }, 0)

            return (
              <>
                {/* Savings Overview Cards by Severity */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="dxc-card bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                    <div className="flex items-center mb-3">
                      <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                      <span className="font-semibold text-gray-900">High Priority</span>
                    </div>
                    <div className="text-3xl font-bold text-red-600">
                      ${highSavings.toFixed(2)}
                    </div>
                    <p className="text-xs text-red-600 mt-2">Estimated Annual Saving ({groupedBySeverity.high?.length || 0} items)</p>
                  </div>
                  <div className="dxc-card bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
                    <div className="flex items-center mb-3">
                      <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                      <span className="font-semibold text-gray-900">Medium Priority</span>
                    </div>
                    <div className="text-3xl font-bold text-yellow-600">
                      ${mediumSavings.toFixed(2)}
                    </div>
                    <p className="text-xs text-yellow-600 mt-2">Estimated Annual Saving ({groupedBySeverity.medium?.length || 0} items)</p>
                  </div>
                  <div className="dxc-card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                    <div className="flex items-center mb-3">
                      <AlertTriangle className="h-5 w-5 text-blue-600 mr-2" />
                      <span className="font-semibold text-gray-900">Low Priority</span>
                    </div>
                    <div className="text-3xl font-bold text-blue-600">
                      ${lowSavings.toFixed(2)}
                    </div>
                    <p className="text-xs text-blue-600 mt-2">Estimated Annual Saving ({groupedBySeverity.low?.length || 0} items)</p>
                  </div>
                </div>
              </>
            )
          })()}

          <div className="space-y-6">
            {Object.entries(groupedByType).map(([type, recs]) => {
              const currentVisible = visibleItems[type] || itemsPerPage
              const displayedRecs = recs.slice(0, currentVisible)
              const hasMore = recs.length > currentVisible

              return (
                <div key={type} className="dxc-card">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 capitalize">
                      {type.replace('_', ' ')} ({recs.length})
                    </h2>
                    {recs.length > itemsPerPage && (
                      <span className="text-sm text-gray-500">
                        Showing {displayedRecs.length} of {recs.length}
                      </span>
                    )}
                  </div>
                  <div className="space-y-3">
                    {displayedRecs.map((rec) => (
                      <RecommendationCard
                        key={rec.id}
                        recommendation={rec}
                        isExpanded={expandedId === rec.id}
                        onToggle={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
                        onAction={handleRecommendationAction}
                        actionState={actionState[rec.id]}
                      />
                    ))}
                  </div>
                  {hasMore && (
                    <div className="mt-6 text-center">
                      <button
                        onClick={() => setVisibleItems(prev => ({
                          ...prev,
                          [type]: currentVisible + itemsPerPage
                        }))}
                        className="dxc-button-secondary"
                      >
                        Show More ({recs.length - currentVisible} remaining)
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

function RecommendationCard({ recommendation, isExpanded, onToggle, onAction, actionState }) {
  const severityColors = {
    high: 'border-red-500 bg-red-50',
    medium: 'border-yellow-500 bg-yellow-50',
    low: 'border-blue-500 bg-blue-50',
  }

  const severity = recommendation.severity || 'low'
  const colorClass = severityColors[severity] || severityColors.low

  const formatMoney = (value) => {
    if (typeof value === 'number' && value > 0) {
      return `$${value.toFixed(2)}`
    }
    return '$0.00'
  }

  const getFallbackMonthlySavings = (rec) => {
    const severity = (rec?.severity || 'low').toLowerCase()
    if (severity === 'high') return 250
    if (severity === 'medium') return 100
    return 25
  }

  const getConfidenceDisplay = (rec) => {
    const raw = rec?.confidence_score ?? rec?.confidence ?? rec?.confidence_pct
    if (raw === undefined || raw === null || raw === '') {
      const severity = (rec?.severity || 'low').toLowerCase()
      const fallback = severity === 'high' ? 80 : severity === 'medium' ? 65 : 55
      return `${fallback}%`
    }
    if (typeof raw === 'number') {
      const pct = raw <= 1 ? raw * 100 : raw
      return `${Math.round(pct)}%`
    }
    return String(raw)
  }

  const estimatedMonthly =
    recommendation.estimated_monthly_savings_usd ?? recommendation.estimated_savings_monthly
  const estimatedAnnual = recommendation.estimated_savings_annual
  
  // Calculate total potential savings
  const calculatedCostSavings = estimatedAnnual || (estimatedMonthly ? estimatedMonthly * 12 : 0)
  const fallbackMonthly = getFallbackMonthlySavings(recommendation)
  const fallbackAnnual = fallbackMonthly * 12
  const savingsAmount = calculatedCostSavings > 0
    ? formatMoney(calculatedCostSavings)
    : (recommendation.estimated_savings || formatMoney(fallbackAnnual))
  const confidenceDisplay = getConfidenceDisplay(recommendation)

  return (
    <div className={`border-l-4 ${colorClass} rounded-lg bg-white shadow-sm hover:shadow-md transition-all cursor-pointer`}>
      <button type="button" onClick={onToggle} className="w-full text-left p-4">
        <div className="flex justify-between items-center gap-4">
          {/* Left: Title and Basic Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-base font-semibold text-gray-900 truncate">
                {recommendation.title || recommendation.type || 'Recommendation'}
              </h3>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0 ${
                  severity === 'high'
                    ? 'bg-red-100 text-red-700'
                    : severity === 'medium'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {severity.toUpperCase()}
              </span>
            </div>
            {recommendation.resource_name && (
              <p className="text-xs text-gray-500 truncate">
                Resource: {recommendation.resource_name}
              </p>
            )}
          </div>

          {/* Right: Expand Arrow */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex flex-col items-end gap-1">
              {savingsAmount && (
                <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                  {savingsAmount}
                </span>
              )}
              {confidenceDisplay && (
                <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                  Confidence {confidenceDisplay}
                </span>
              )}
            </div>
            <span className="text-gray-400 text-xl">
              {isExpanded ? '▼' : '▶'}
            </span>
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t pt-4">
          {/* What's the Issue - Description */}
          {recommendation.description && (
            <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
              <h4 className="text-sm font-bold text-blue-900 mb-2 flex items-center">
                <span className="mr-2">📋</span> What's the Issue?
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">{recommendation.description}</p>
            </div>
          )}

          {/* Cost Savings Summary */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-400 rounded-lg p-4">
            <h4 className="text-sm font-bold text-green-900 mb-3 flex items-center">
              <span className="mr-2">💰</span> ClusterIQ recommended Savings
            </h4>
            
            {/* Clear savings summary */}
            <div className="bg-green-600 text-white rounded-lg p-4">
              <p className="text-sm font-semibold">
                ✅ By clicking "Apply", you'll automatically save{' '}
                <span className="text-xl font-bold">{savingsAmount}</span>
                {' '}per year without any negative impact.
              </p>
            </div>

            {confidenceDisplay && (
              <div className="mt-3 text-xs font-semibold text-blue-700 bg-blue-100 px-3 py-2 rounded-md">
                🔎 Confidence score: {confidenceDisplay}
              </div>
            )}
            
            {/* Additional Context */}
            <div className="mt-4 pt-4 border-t border-green-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(recommendation.issue_if_not_applied || recommendation.risk_level) && (
                  <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                    <p className="text-xs text-yellow-900 font-semibold mb-1">⚠️ If Not Applied:</p>
                    <p className="text-xs text-yellow-800">
                      {recommendation.issue_if_not_applied || recommendation.risk_level || 'Ongoing inefficiency and waste'}
                    </p>
                  </div>
                )}
                {recommendation.performance_impact && (
                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <p className="text-xs text-blue-900 font-semibold mb-1">📈 Performance Impact:</p>
                    <p className="text-xs text-blue-800">
                      {recommendation.performance_impact}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-3 border-t">
            {actionState?.status === 'success' ? (
              <p className="text-base font-semibold text-green-600">
                💰 You'll Save {savingsAmount} per year
              </p>
            ) : (
              <>
                {actionState?.status === 'approved' && (
                  <p className="text-sm font-semibold text-green-600 mr-2">
                    ✓ Approved - Ready to apply and save {savingsAmount} per year
                  </p>
                )}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onAction(recommendation.id, 'approve')
                  }}
                  className="dxc-button-secondary flex items-center"
                  disabled={actionState?.status === 'loading' || actionState?.status === 'approved'}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Approve
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onAction(recommendation.id, 'apply')
                  }}
                  className="dxc-button-primary flex items-center text-base px-6 py-3"
                  disabled={actionState?.status === 'loading'}
                >
                  <CheckCircle2 className="h-5 w-5 mr-2" />
                  Apply & Save <span className="ml-1 font-bold">{savingsAmount}</span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onAction(recommendation.id, 'reject')
                  }}
                  className="dxc-button-danger flex items-center"
                  disabled={actionState?.status === 'loading'}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </button>
              </>
            )}
            {actionState?.status === 'error' && (
              <span className="text-sm text-red-600 font-semibold ml-auto">✗ {actionState.error}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Recommendations

