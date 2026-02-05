import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchRecommendationsRealtime, analyzeJobsAndClusters } from '../services/api'
import { AlertTriangle, TrendingDown, DollarSign, Clock, RefreshCw } from 'lucide-react'

function Recommendations() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Recommendations</h1>
          <p className="mt-2 text-sm text-gray-600">AI-powered optimization suggestions for your Databricks infrastructure</p>
        </div>
        <div className="flex items-center space-x-4">
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
            className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
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
          {/* Calculate total savings */}
          {(() => {
            const totalMonthlySavings = recommendations.reduce(
              (sum, rec) => sum + (rec.estimated_savings_monthly || 0),
              0
            )
            const totalAnnualSavings = recommendations.reduce(
              (sum, rec) => sum + (rec.estimated_savings_annual || 0),
              0
            )
            return (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="dxc-card bg-gradient-to-br from-green-50 to-emerald-100 border-green-200">
                  <div className="flex items-center mb-3">
                    <DollarSign className="h-5 w-5 text-green-600 mr-2" />
                    <span className="font-semibold text-gray-900">Total Monthly Savings</span>
                  </div>
                  <div className="text-3xl font-bold text-green-600">
                    ${totalMonthlySavings.toFixed(2)}
                  </div>
                </div>
                <div className="dxc-card bg-gradient-to-br from-emerald-50 to-teal-100 border-emerald-200">
                  <div className="flex items-center mb-3">
                    <DollarSign className="h-5 w-5 text-emerald-600 mr-2" />
                    <span className="font-semibold text-gray-900">Total Annual Savings</span>
                  </div>
                  <div className="text-3xl font-bold text-emerald-600">
                    ${totalAnnualSavings.toFixed(2)}
                  </div>
                </div>
                <div className="dxc-card bg-red-50 border-red-200">
                  <div className="flex items-center mb-3">
                    <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                    <span className="font-semibold text-gray-900">High Priority</span>
                  </div>
                  <div className="text-3xl font-bold text-red-600">
                    {groupedBySeverity.high?.length || 0}
                  </div>
                </div>
                <div className="dxc-card bg-yellow-50 border-yellow-200">
                  <div className="flex items-center mb-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                    <span className="font-semibold text-gray-900">Medium Priority</span>
                  </div>
                  <div className="text-3xl font-bold text-yellow-600">
                    {groupedBySeverity.medium?.length || 0}
                  </div>
                </div>
                <div className="dxc-card bg-blue-50 border-blue-200">
                  <div className="flex items-center mb-3">
                    <AlertTriangle className="h-5 w-5 text-blue-600 mr-2" />
                    <span className="font-semibold text-gray-900">Low Priority</span>
                  </div>
                  <div className="text-3xl font-bold text-blue-600">
                    {groupedBySeverity.low?.length || 0}
                  </div>
                </div>
              </div>
            )
          })()}

          <div className="space-y-6">
            {Object.entries(groupedByType).map(([type, recs]) => (
              <div key={type} className="dxc-card">
                <h2 className="text-xl font-semibold mb-6 text-gray-900 capitalize">
                  {type.replace('_', ' ')} ({recs.length})
                </h2>
                <div className="space-y-4">
                  {recs.map((rec) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function RecommendationCard({ recommendation }) {
  const severityColors = {
    high: 'border-red-500 bg-red-50',
    medium: 'border-yellow-500 bg-yellow-50',
    low: 'border-blue-500 bg-blue-50',
  }

  const severity = recommendation.severity || 'low'
  const colorClass = severityColors[severity] || severityColors.low

  return (
    <div className={`border-l-4 ${colorClass} rounded-lg p-6 bg-white shadow-sm hover:shadow-lg transition-shadow`}>
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold">
          {recommendation.title || recommendation.type || 'Recommendation'}
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
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

      {recommendation.description && (
        <p className="text-gray-600 mb-4">{recommendation.description}</p>
      )}

      {/* Prominent Savings Display */}
      {recommendation.estimated_savings && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500 rounded-r-lg p-4 mb-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium mb-1">Potential Savings</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-green-600">{recommendation.estimated_savings}</span>
              </div>
            </div>
            <DollarSign className="h-8 w-8 text-green-500 opacity-20" />
          </div>
          {recommendation.estimated_savings_monthly && (
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div className="bg-white bg-opacity-60 rounded p-2">
                <p className="text-gray-600">Monthly</p>
                <p className="font-bold text-green-600">${recommendation.estimated_savings_monthly.toFixed(2)}</p>
              </div>
              <div className="bg-white bg-opacity-60 rounded p-2">
                <p className="text-gray-600">Annual</p>
                <p className="font-bold text-green-700">${recommendation.estimated_savings_annual.toFixed(2)}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {recommendation.current_config && (
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Current Configuration</h4>
            <div className="bg-gray-50 rounded p-3 text-sm border border-gray-200">
              <pre className="text-gray-700 text-xs overflow-x-auto">
                {JSON.stringify(recommendation.current_config, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {recommendation.recommended_config && (
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Recommended Configuration</h4>
            <div className="bg-gray-50 rounded p-3 text-sm border border-gray-200">
              <pre className="text-gray-700 text-xs overflow-x-auto">
                {JSON.stringify(recommendation.recommended_config, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-4">
        {recommendation.risk && (
          <div className="flex items-center text-yellow-700">
            <AlertTriangle className="h-4 w-4 mr-1" />
            <span className="text-sm">Risk: {recommendation.risk}</span>
          </div>
        )}

        {recommendation.resource_type && (
          <div className="flex items-center text-blue-700">
            <span className="text-sm">
              {recommendation.resource_type}: {recommendation.resource_id}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default Recommendations

