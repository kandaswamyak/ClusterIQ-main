import { useState, useMemo, useEffect } from 'react'
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
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [actionError, setActionError] = useState(null)

  // Fetch all recommendations to calculate counts
  const { data: allData, refetch: refetchAll } = useQuery({
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

  // Debug log
  useEffect(() => {
    if (data?.recommendations) {
      const idleCount = data.recommendations.filter(r => r.type === 'idle_cluster').length
      console.log(`[DEBUG] Approvals: Total=${data.recommendations.length}, Idle=${idleCount}`)
      data.recommendations.forEach(r => {
        if (r.type === 'idle_cluster') {
          console.log(`[DEBUG] Idle cluster: ${r.id} - ${r.title}`)
        }
      })
    }
  }, [data])

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
      await Promise.all([refetch(), refetchAll()])
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
      await Promise.all([refetch(), refetchAll()])
    } catch (err) {
      setActionError(err.response?.data?.error || err.message || 'Action failed')
    }
  }

  // Sort recommendations by date (newest first) and optionally filter out applied/approved
  const rawRecommendations = data?.recommendations || []
  const recommendations = useMemo(() => {
    let sorted = [...rawRecommendations].sort((a, b) => {
      // Try to get timestamp from various possible fields
      const dateA = a.created_at || a.timestamp || a.date || new Date(0)
      const dateB = b.created_at || b.timestamp || b.date || new Date(0)
      
      // Parse dates if they're strings
      const timeA = typeof dateA === 'string' ? new Date(dateA).getTime() : (dateA instanceof Date ? dateA.getTime() : 0)
      const timeB = typeof dateB === 'string' ? new Date(dateB).getTime() : (dateB instanceof Date ? dateB.getTime() : 0)
      
      return timeB - timeA // Newest first
    })
    
    // Apply date range filter
    if (fromDate || toDate) {
      sorted = sorted.filter(rec => {
        const recDate = new Date(rec.created_at || rec.timestamp || new Date(0))
        
        if (fromDate) {
          const from = new Date(fromDate)
          from.setHours(0, 0, 0, 0)
          if (recDate < from) return false
        }
        
        if (toDate) {
          const to = new Date(toDate)
          to.setHours(23, 59, 59, 999)
          if (recDate > to) return false
        }
        
        return true
      })
    }
    
    // If viewing PENDING tab, hide APPLIED and some other completed statuses
    if (statusFilter === 'PENDING') {
      sorted = sorted.filter(rec => {
        const status = rec.status || 'PENDING'
        return !['APPLIED', 'REJECTED', 'FAILED'].includes(status)
      })
    }
    
    return sorted
  }, [rawRecommendations, statusFilter, fromDate, toDate])

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

      {/* Filters Row */}
      <div className="flex flex-wrap items-center gap-3 pb-2">
        <label className="text-sm text-gray-700 flex items-center gap-2 font-medium">
          <Filter className="h-5 w-5 text-purple-600" />
          Status
        </label>
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-3 py-1.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 shadow-sm ${
              statusFilter === tab.value
                ? 'text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50 hover:text-gray-900 border border-gray-300'
            }`}
            style={statusFilter === tab.value ? { background: 'linear-gradient(135deg, #9333ea, #c026d3)' } : {}}
          >
            {tab.label}
            <span className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${
              statusFilter === tab.value
                ? 'bg-white bg-opacity-30'
                : 'bg-gray-300'
            }`}>
              {statusCounts[tab.value] || 0}
            </span>
          </button>
        ))}

        {/* Date Filter - appears after status buttons */}
        <div className="h-6 w-px bg-gray-300 mx-1"></div>
        <label className="text-xs text-gray-700 font-medium whitespace-nowrap">
          📅
        </label>
        <input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          placeholder="From"
          className="px-2 py-1.5 border border-gray-300 rounded text-xs w-32 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
        <span className="text-xs text-gray-500">—</span>
        <input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          placeholder="To"
          className="px-2 py-1.5 border border-gray-300 rounded text-xs w-32 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
        {(fromDate || toDate) && (
          <button
            onClick={() => {
              setFromDate('')
              setToDate('')
            }}
            className="px-2 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-xs font-semibold transition-colors"
          >
            ✕
          </button>
        )}
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
                    {(rec.created_at || rec.timestamp) && `• ${new Date(rec.created_at || rec.timestamp).toLocaleString('en-IN', { 
                      timeZone: 'Asia/Kolkata',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}`}
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

                {/* Action buttons - conditional based on status filter */}
                {statusFilter !== 'REJECTED' && statusFilter !== 'APPLIED' && (
                  <div className="flex items-center gap-2">
                    {statusFilter !== 'APPROVED' && (
                      <button
                        onClick={() => handleAction('approve', rec.id)}
                        className="dxc-button-primary flex items-center"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" /> Approve
                      </button>
                    )}
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
                )}
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
