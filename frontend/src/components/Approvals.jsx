import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  analyzeDeltaTables,
  fetchApprovals,
  approveRecommendation,
  rejectRecommendation,
  applyRecommendation,
} from '../services/api'
import { CheckCircle, XCircle, PlayCircle, RefreshCw, Filter } from 'lucide-react'

const STATUS_TABS = [
  { value: '', label: 'All', icon: null },
  { value: 'PENDING', label: 'Pending', icon: '⏳' },
  { value: 'APPROVED', label: 'Approved', icon: '✓' },
  { value: 'REJECTED', label: 'Rejected', icon: '✕' },
  { value: 'APPLIED', label: 'Applied', icon: '▶' },
  { value: 'FAILED', label: 'Failed', icon: '✗' },
]

function Approvals() {
  const [statusFilter, setStatusFilter] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [actionError, setActionError] = useState(null)

  // Fetch all recommendations to calculate counts
  const { data: allData } = useQuery({
    queryKey: ['approvals-all'],
    queryFn: () => fetchApprovals(''),
    refetchInterval: 30000,
  })

  // Fetch filtered recommendations based on selected status
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['approvals', statusFilter],
    queryFn: () => fetchApprovals(statusFilter),
    refetchInterval: 30000,
  })

  // Calculate status counts
  const statusCounts = useMemo(() => {
    const allRecs = allData?.recommendations || []
    const counts = {
      '': allRecs.length,
      PENDING: 0,
      APPROVED: 0,
      REJECTED: 0,
      APPLIED: 0,
      FAILED: 0,
    }
    allRecs.forEach((rec) => {
      const status = rec.status || 'PENDING'
      if (counts[status] !== undefined) counts[status]++
    })
    return counts
  }, [allData])

  const handleAnalyzeDelta = async () => {
    setIsAnalyzing(true)
    setActionError(null)
    try {
      await analyzeDeltaTables({})
      await refetch()
    } catch (err) {
      setActionError(err.response?.data?.error || err.message || 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleAction = async (action, recId) => {
    setActionError(null)
    try {
      if (action === 'approve') await approveRecommendation(recId)
      if (action === 'reject') await rejectRecommendation(recId)
      if (action === 'apply') await applyRecommendation(recId)
      await refetch()
    } catch (err) {
      setActionError(err.response?.data?.error || err.message || 'Action failed')
    }
  }

  const recommendations = data?.recommendations || []

  const getSavingsDisplay = (rec) => {
    if (!rec) return null
    let value = rec.estimated_savings
    if (value === undefined || value === null || value === '') {
      const fallbackKeys = [
        'estimated_savings_monthly',
        'estimated_monthly_savings_usd',
        'estimated_savings_annual',
        'estimated_annual_savings_usd'
      ]
      for (const key of fallbackKeys) {
        if (rec[key] !== undefined && rec[key] !== null) {
          value = rec[key]
          break
        }
      }
    }
    if (value === undefined || value === null || value === '') return null
    if (typeof value === 'number') return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    return String(value)
  }

  const getConfidenceDisplay = (rec) => {
    if (!rec) return null
    const raw = rec.confidence_score ?? rec.confidence ?? rec.confidence_pct
    if (raw === undefined || raw === null || raw === '') return null
    if (typeof raw === 'number') {
      const pct = raw <= 1 ? raw * 100 : raw
      return `${Math.round(pct)}%`
    }
    return String(raw)
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">Approvals</h1>
          <p className="mt-3 text-base text-gray-600 font-medium">
            Review Delta‑based recommendations, approve, and apply changes to Databricks
          </p>
        </div>
        <button
          onClick={handleAnalyzeDelta}
          disabled={isAnalyzing}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          <RefreshCw className={`h-5 w-5 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Analyzing...' : 'Analyze Delta Logs'}
        </button>
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-700 flex items-center gap-2 font-medium">
          <Filter className="h-5 w-5 text-purple-600" />
          Status Filter
        </label>
        <div className="flex flex-wrap gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all transform hover:scale-105 flex items-center gap-2 shadow-md ${
                statusFilter === tab.value
                  ? 'text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:text-gray-900 border border-gray-300'
              }`}
              style={statusFilter === tab.value ? { background: 'linear-gradient(135deg, #9333ea, #c026d3)' } : {}}
            >
              {tab.label}
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                statusFilter === tab.value
                  ? 'bg-white bg-opacity-30'
                  : 'bg-gray-300'
              }`}>
                {statusCounts[tab.value] || 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      {(error || actionError) && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4">
          <p className="text-sm text-red-700">
            {actionError || error.response?.data?.error || error.message}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading approvals...</div>
      ) : recommendations.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No recommendations found.</div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            (() => {
              const savingsDisplay = getSavingsDisplay(rec)
              const confidenceDisplay = getConfidenceDisplay(rec)
              return (
            <div key={rec.id} className="dxc-card">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-900">{rec.title}</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                      {rec.status || 'PENDING'}
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700">
                      {rec.severity || 'medium'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{rec.description}</p>
                  <div className="text-xs text-gray-500 mt-2">
                    Resource: {rec.resource_type || 'N/A'} {rec.resource_id ? `• ${rec.resource_id}` : ''}
                  </div>
                  {savingsDisplay !== null && (
                    <div className="text-xs text-green-600 mt-1 font-medium">
                      💰 Estimated Savings: {savingsDisplay}
                    </div>
                  )}
                  {confidenceDisplay && (
                    <div className="text-xs text-blue-600 mt-1 font-medium">
                      🔎 Confidence: {confidenceDisplay}
                    </div>
                  )}
                  {rec.status_note && (
                    <div className={`text-xs mt-2 p-2 rounded ${
                      rec.status === 'FAILED' ? 'bg-red-50 text-red-600' :
                      rec.status === 'APPLIED' ? 'bg-green-50 text-green-600' :
                      'bg-yellow-50 text-yellow-600'
                    }`}>
                      📝 {rec.status_note}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAction('approve', rec.id)}
                    className="dxc-button-primary flex items-center"
                  >
                    <CheckCircle className="h-4 w-4 mr-1" /> Approve
                  </button>
                  <button
                    onClick={() => handleAction('reject', rec.id)}
                    className="dxc-button-secondary flex items-center"
                  >
                    <XCircle className="h-4 w-4 mr-1" /> Reject
                  </button>
                  <button
                    onClick={() => handleAction('apply', rec.id)}
                    className="dxc-button-primary flex items-center"
                  >
                    <PlayCircle className="h-4 w-4 mr-1" /> Apply
                  </button>
                </div>
              </div>
            </div>
              )
            })()
          ))}
        </div>
      )}
    </div>
  )
}

export default Approvals
