import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchJobs, fetchRecommendationsRealtime } from '../services/api'
import { Database, Clock, User, Lightbulb } from 'lucide-react'

function JobsView() {
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
    return <div className="text-center py-12 text-gray-500">Loading jobs...</div>
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        Error loading jobs: {error.message}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Databricks Jobs</h1>
          <p className="mt-2 text-sm text-gray-600">View and manage your Databricks jobs</p>
        </div>
        <div className="text-sm font-medium text-gray-700 bg-gray-100 px-4 py-2 rounded-md">
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
              {jobs?.map((job) => (
                <tr key={job.job_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Database className="h-4 w-4 mr-2 text-primary-600" />
                      <span className="font-medium text-gray-900">{job.job_name}</span>
                    </div>
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
              ))}
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

export default JobsView

