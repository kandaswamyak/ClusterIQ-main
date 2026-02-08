import React, { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchJobs, fetchRecommendationsRealtime } from '../services/api'
import { Database, Clock, User, Lightbulb, ChevronDown, ChevronRight, CheckCircle, XCircle, Clock as ClockIcon, PlayCircle } from 'lucide-react'

function JobsView() {
  const [expandedJobId, setExpandedJobId] = useState(null)
  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: recData } = useQuery({
    queryKey: ['recommendations-realtime'],
    queryFn: fetchRecommendationsRealtime,
    refetchInterval: 60000,
  })

  const jobRecommendationCounts = useMemo(() => {
    const counts = {}
    const recommendations = recData?.recommendations || []
    recommendations.forEach((rec) => {
      if (rec.resource_type === 'job' && rec.resource_id != null) {
        const key = String(rec.resource_id)
        counts[key] = (counts[key] || 0) + 1
      }
    })
    return counts
  }, [recData])

  if (isLoading) {
    return (
      <div className="text-center py-20">
        <div className="loading-spinner h-16 w-16 mx-auto mb-6"></div>
        <p className="text-gray-600 text-lg font-medium">Loading jobs...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="glass-card" style={{ background: 'linear-gradient(135deg, rgba(127, 29, 29, 0.9), rgba(220, 38, 38, 0.9))', border: '1px solid #ef4444' }}>
          <div className="flex items-start">
            <Database className="h-8 w-8 text-red-300 flex-shrink-0 mr-4" />
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Error Loading Jobs</h3>
              <p className="text-red-200">{error.message}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">Databricks Jobs</h1>
          <p className="mt-3 text-base text-gray-600 font-medium">View and manage your Databricks jobs</p>
        </div>
        <div className="stat-badge" style={{ background: 'linear-gradient(135deg, #581c87, #7e22ce)', color: 'white' }}>
          Total: {jobs?.length || 0} jobs
        </div>
      </div>

      <div className="dxc-card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Job Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Job ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Creator
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Tasks
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Schedule
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Recommendations
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {jobs?.map((job) => {
                const isExpanded = expandedJobId === job.job_id
                
                return (
                  <React.Fragment key={job.job_id}>
                    <tr className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => setExpandedJobId(isExpanded ? null : job.job_id)}
                          className="flex items-center text-left hover:text-primary-600 focus:outline-none"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 mr-2 text-primary-600" />
                          ) : (
                            <ChevronRight className="h-4 w-4 mr-2 text-gray-500" />
                          )}
                          <Database className="h-4 w-4 mr-2 text-primary-600" />
                          <span className="font-medium text-gray-900">{job.job_name}</span>
                        </button>
                      </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {job.job_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-700">
                      <User className="h-4 w-4 mr-2 text-gray-500" />
                      {job.creator_user_name || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {job.settings?.tasks?.length || 0} tasks
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {job.schedule?.quartz_cron_expression ? (
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1 text-gray-500" />
                        {job.schedule.quartz_cron_expression}
                      </div>
                    ) : (
                      <span className="text-gray-500">Manual</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {job.created_time
                      ? new Date(job.created_time).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })
                      : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-700">
                      <Lightbulb className="h-4 w-4 mr-2 text-amber-500" />
                      {jobRecommendationCounts[String(job.job_id)] || 0}
                    </div>
                  </td>
                </tr>
                
                {/* Expanded Row - Show Job Runs */}
                {isExpanded && (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 bg-gray-50">
                      <JobRunsDetails jobId={job.job_id} jobName={job.job_name} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            )})}
            </tbody>
          </table>
        </div>
      </div>

      {(!jobs || jobs.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          No jobs found
        </div>
      )}
    </div>
  )
}

function JobRunsDetails({ jobId, jobName }) {
  const { data: jobRunsData, isLoading, error } = useQuery({
    queryKey: ['job-runs', jobId],
    queryFn: async () => {
      const response = await fetch(`/api/jobs/${jobId}/runs?limit=3`)
      if (!response.ok) throw new Error('Failed to fetch job runs')
      return response.json()
    },
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <div className="text-center py-4">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-primary-600 border-r-transparent"></div>
        <p className="text-sm text-gray-600 mt-2">Loading recent runs...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-600 py-2">
        Error loading runs: {error.message}
      </div>
    )
  }

  const runs = Array.isArray(jobRunsData) ? jobRunsData : (jobRunsData?.runs || [])

  if (runs.length === 0) {
    return (
      <div className="text-sm text-gray-500 py-4 text-center">
        <p className="mb-2">No recent runs found for this job</p>
        <p className="text-xs text-gray-400">Job ID: <span className="font-mono">{jobId}</span></p>
        <p className="text-xs text-gray-400 mt-1">Check Databricks directly using Run ID for this job</p>
      </div>
    )
  }

  const getStateIcon = (state) => {
    const resultState = state?.result_state
    const lifecycleState = state?.life_cycle_state
    
    if (resultState === 'SUCCESS') {
      return <CheckCircle className="h-4 w-4 text-green-600" />
    } else if (resultState === 'FAILED' || resultState === 'TIMEDOUT' || resultState === 'CANCELED') {
      return <XCircle className="h-4 w-4 text-red-600" />
    } else if (lifecycleState === 'RUNNING') {
      return <PlayCircle className="h-4 w-4 text-blue-600" />
    } else {
      return <ClockIcon className="h-4 w-4 text-gray-400" />
    }
  }

  const getStateColor = (state) => {
    const resultState = state?.result_state
    const lifecycleState = state?.life_cycle_state
    
    if (resultState === 'SUCCESS') return 'text-green-700 bg-green-50'
    if (resultState === 'FAILED' || resultState === 'TIMEDOUT' || resultState === 'CANCELED') return 'text-red-700 bg-red-50'
    if (lifecycleState === 'RUNNING') return 'text-blue-700 bg-blue-50'
    return 'text-gray-700 bg-gray-50'
  }

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A'
    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : new Date()
    const durationMs = end - start
    const minutes = Math.floor(durationMs / 60000)
    const seconds = Math.floor((durationMs % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">Latest 3 Runs for {jobName}</h4>
      <div className="grid gap-2">
        {runs.map((run) => {
          const state = run.state || {}
          const hasRetries = run.tasks?.some(task => task.attempt_number > 0)
          
          return (
            <div key={run.run_id} className="border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="mt-1">
                    {getStateIcon(state)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center flex-wrap gap-2">
                      <span className="text-sm font-bold text-primary-700">Run ID: {run.run_id}</span>
                      <span className="text-xs text-gray-500">#{run.number_in_job || 'N/A'}</span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStateColor(state)}`}>
                        {state.result_state || state.life_cycle_state || 'PENDING'}
                      </span>
                      {hasRetries && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full text-orange-700 bg-orange-50 flex items-center">
                          🔄 Retries
                        </span>
                      )}
                    </div>
                    <div className="mt-1 text-xs text-gray-600 space-y-1">
                      <div className="flex items-center space-x-4">
                        <span>Duration: {formatDuration(run.start_time, run.end_time)}</span>
                      </div>
                      {run.start_time && (
                        <div>
                          Started: {new Date(run.start_time).toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      )}
                      {state.state_message && (
                        <div className="mt-1 text-xs text-gray-500 italic">
                          {state.state_message.substring(0, 200)}
                          {state.state_message.length > 200 ? '...' : ''}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default JobsView

