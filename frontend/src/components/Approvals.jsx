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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Approvals</h1>
          <p className="mt-2 text-sm text-gray-600">
            Review Delta‑based recommendations, approve, and apply changes to Databricks.
          </p>
        </div>
        <button
          onClick={handleAnalyzeDelta}
          disabled={isAnalyzing}
          className="dxc-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Analyzing...' : 'Analyze Delta Logs'}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-700 flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Status
        </label>
        <div className="flex flex-wrap gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${
                statusFilter === tab.value
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
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
                  {rec.estimated_savings && (
                    <div className="text-xs text-green-600 mt-1 font-medium">
                      💰 Estimated Savings: {rec.estimated_savings}
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
          ))}
        </div>
      )}
    </div>
  )
}

export default Approvals
