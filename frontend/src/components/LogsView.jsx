import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchLogs, fetchLogsStats, fetchLogsByLevel, clearLogs } from '../services/api'
import { RefreshCw, Trash2, Download, AlertCircle, Info, AlertTriangle } from 'lucide-react'

function LogsView() {
  const [selectedLevel, setSelectedLevel] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [limit, setLimit] = useState(100)
  const queryClient = useQueryClient()

  const { data: logs, isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['logs', selectedLevel, limit],
    queryFn: () => fetchLogs(selectedLevel, limit),
    refetchInterval: autoRefresh ? 5000 : false, // Refresh every 5 seconds if enabled
    enabled: true
  })

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['logs-stats'],
    queryFn: fetchLogsStats,
    refetchInterval: autoRefresh ? 5000 : false,
  })

  const { data: levelData, isLoading: levelLoading } = useQuery({
    queryKey: ['logs-levels'],
    queryFn: fetchLogsByLevel,
    refetchInterval: autoRefresh ? 5000 : false,
  })

  const handleClearLogs = async () => {
    if (!window.confirm('Are you sure you want to clear all logs? This action cannot be undone.')) {
      return
    }
    try {
      await clearLogs()
      queryClient.invalidateQueries({ queryKey: ['logs'] })
      queryClient.invalidateQueries({ queryKey: ['logs-stats'] })
      queryClient.invalidateQueries({ queryKey: ['logs-levels'] })
    } catch (error) {
      console.error('Error clearing logs:', error)
    }
  }

  const handleExport = (format) => {
    if (!logs?.logs || logs.logs.length === 0) {
      alert('No logs to export')
      return
    }

    const data = JSON.stringify(logs.logs, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${new Date().toISOString()}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getLevelIcon = (level) => {
    switch (level) {
      case 'ERROR':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'INFO':
        return <Info className="h-4 w-4 text-blue-500" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-600 bg-red-50'
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50'
      case 'INFO':
        return 'text-blue-600 bg-blue-50'
      case 'DEBUG':
        return 'text-gray-600 bg-gray-50'
      case 'CRITICAL':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Application Logs</h1>
          <p className="mt-2 text-sm text-gray-600">Monitor and analyze application logs in real-time</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => refetchLogs()}
            className="dxc-button-secondary flex items-center"
            title="Refresh logs"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => handleExport('json')}
            className="dxc-button-secondary flex items-center"
            title="Export logs as JSON"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
          <button
            onClick={handleClearLogs}
            className="dxc-button-danger flex items-center"
            title="Clear all logs"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Auto Refresh
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-600">Enable (5s interval)</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Level
            </label>
            <select
              value={selectedLevel || ''}
              onChange={(e) => setSelectedLevel(e.target.value || null)}
              className="rounded border-gray-300 border px-3 py-2"
            >
              <option value="">All Levels</option>
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Limit
            </label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(Math.max(1, parseInt(e.target.value) || 100))}
              min="1"
              max="1000"
              className="rounded border-gray-300 border px-3 py-2 w-20"
            />
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {!statsLoading && stats?.stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total Logs</p>
            <p className="text-2xl font-bold text-gray-900">{stats.stats.total_logs}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Capacity Usage</p>
            <p className="text-2xl font-bold text-blue-600">{stats.stats.capacity_usage}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Oldest Log</p>
            <p className="text-xs text-gray-500 break-words">
              {stats.stats.oldest_log_timestamp
                ? new Date(stats.stats.oldest_log_timestamp).toLocaleString()
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Latest Log</p>
            <p className="text-xs text-gray-500 break-words">
              {stats.stats.newest_log_timestamp
                ? new Date(stats.stats.newest_log_timestamp).toLocaleString()
                : 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Log Level Summary */}
      {!levelLoading && levelData?.data && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Logs by Level</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(levelData.data).map(([level, count]) => (
              <div
                key={level}
                className={`p-3 rounded-lg text-center cursor-pointer hover:opacity-80 transition-opacity ${getLevelColor(level)}`}
                onClick={() => setSelectedLevel(level)}
              >
                <p className="text-sm font-semibold">{level}</p>
                <p className="text-2xl font-bold">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Logs ({logs?.count || 0})
          </h2>
        </div>

        {logsLoading ? (
          <div className="p-8 text-center text-gray-500">Loading logs...</div>
        ) : logs?.logs && logs.logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Timestamp</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Level</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Logger</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Message</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Function</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.logs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-600 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${getLevelColor(log.level)}`}>
                        {getLevelIcon(log.level)}
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600 font-mono">
                      {log.logger.split('.').slice(-1)[0]}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-700 max-w-md truncate">
                      {log.message}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600 font-mono whitespace-nowrap">
                      {log.function}:{log.line_number}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">No logs found</div>
        )}
      </div>

      {/* Exception Details (if any) */}
      {logs?.logs?.some(log => log.exception) && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Exception Details</h2>
          <div className="space-y-4">
            {logs.logs
              .filter(log => log.exception)
              .map((log, idx) => (
                <div key={idx} className="bg-red-50 border border-red-200 rounded p-3">
                  <p className="text-xs font-mono text-red-600 whitespace-pre-wrap">
                    {log.exception}
                  </p>
                  <p className="text-xs text-gray-600 mt-2">
                    {new Date(log.timestamp).toLocaleString()} | {log.logger}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LogsView
