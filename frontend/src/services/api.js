import axios from 'axios'

// Use Vite proxy in development, or direct URL in production
// In dev mode, use empty string so requests go through Vite proxy
// In production, use full backend URL
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '' : 'http://localhost:8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for analyze endpoint
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error.message)
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      error.message = 'Cannot connect to backend server. Make sure the backend is running on http://localhost:8000'
    }
    return Promise.reject(error)
  }
)

export const fetchJobs = async () => {
  const response = await api.get('/api/jobs')
  return response.data
}

export const fetchJobRuns = async (jobId) => {
  const response = await api.get(`/api/jobs/${jobId}/runs`)
  return response.data
}

export const fetchClusters = async () => {
  const response = await api.get('/api/clusters')
  return response.data
}

export const fetchClusterMetrics = async (clusterId) => {
  const response = await api.get(`/api/clusters/${clusterId}/metrics`)
  return response.data
}

export const analyzeJobsAndClusters = async () => {
  const response = await api.post('/api/analyze')
  return response.data
}

export const fetchRecommendations = async () => {
  const response = await api.get('/api/recommendations')
  return response.data
}

export const fetchRecommendationsRealtime = async () => {
  try {
    const response = await api.get('/api/recommendations/real-time')
    return response.data
  } catch (error) {
    // If real-time endpoint fails, try the regular recommendations endpoint
    if (error.response?.status === 404) {
      const response = await api.get('/api/recommendations')
      return {
        ...response.data,
        real_time: false
      }
    }
    throw error
  }
}

export const fetchStats = async () => {
  const response = await api.get('/api/stats')
  return response.data
}

export const fetchSQLWarehouses = async () => {
  const response = await api.get('/api/sql-warehouses')
  return response.data
}

export const fetchPools = async () => {
  const response = await api.get('/api/pools')
  return response.data
}

export const fetchVectorSearch = async () => {
  const response = await api.get('/api/vector-search')
  return response.data
}

export const fetchPolicies = async () => {
  const response = await api.get('/api/policies')
  return response.data
}

export const fetchApps = async () => {
  const response = await api.get('/api/apps')
  return response.data
}

export const fetchLakebase = async () => {
  const response = await api.get('/api/lakebase')
  return response.data
}

export const fetchAllCompute = async () => {
  const response = await api.get('/api/compute')
  return response.data
}

export const fetchMLJobs = async () => {
  const response = await api.get('/api/ml-jobs')
  return response.data
}

export const fetchMLflowExperiments = async () => {
  const response = await api.get('/api/mlflow-experiments')
  return response.data
}

export const fetchMLflowModels = async () => {
  const response = await api.get('/api/mlflow-models')
  return response.data
}

export const fetchModelServing = async () => {
  const response = await api.get('/api/model-serving')
  return response.data
}

export const fetchFeatureStore = async () => {
  const response = await api.get('/api/feature-store')
  return response.data
}

export const fetchSummaryMetrics = async () => {
  const response = await api.get('/api/summary')
  return response.data
}

export const analyzeDeltaTables = async (payload) => {
  const response = await api.post('/api/analyze-delta', payload)
  return response.data
}

export const fetchApprovals = async (status) => {
  const response = await api.get('/api/approvals', {
    params: status ? { status } : undefined
  })
  return response.data
}

export const approveRecommendation = async (recId) => {
  const response = await api.post(`/api/approvals/${recId}/approve`)
  return response.data
}

export const rejectRecommendation = async (recId) => {
  const response = await api.post(`/api/approvals/${recId}/reject`)
  return response.data
}

export const applyRecommendation = async (recId) => {
  const response = await api.post(`/api/approvals/${recId}/apply`)
  return response.data
}

export const fetchLogs = async (level = null, limit = 100, logger = null) => {
  const params = new URLSearchParams()
  if (level) params.append('level', level)
  if (logger) params.append('logger', logger)
  params.append('limit', limit)
  
  const response = await api.get('/api/logs', { params })
  return response.data
}

export const fetchLogsStats = async () => {
  const response = await api.get('/api/logs/stats')
  return response.data
}

export const fetchLogsByLevel = async () => {
  const response = await api.get('/api/logs/levels')
  return response.data
}

export const exportLogs = async (format = 'json') => {
  const response = await api.get('/api/logs/export', {
    params: { format }
  })
  return response.data
}

export const clearLogs = async () => {
  const response = await api.post('/api/logs/clear')
  return response.data
}

export const fetchPricingTiers = async () => {
  const response = await api.get('/api/cost/pricing')
  return response.data
}

export const fetchClusterCost = async (clusterId, hours = 100) => {
  const response = await api.get(`/api/cost/cluster/${clusterId}`, {
    params: { hours }
  })
  return response.data
}

export const fetchJobCost = async (jobId, runs = 4, runtime = 0.5) => {
  const response = await api.get(`/api/cost/job/${jobId}`, {
    params: { runs, runtime }
  })
  return response.data
}

export const fetchCostBreakdown = async () => {
  const response = await api.get('/api/cost/breakdown')
  return response.data
}

export const fetchCostRecommendations = async (clusterId) => {
  const response = await api.get(`/api/cost/recommendations/${clusterId}`)
  return response.data
}

export const startCluster = async (clusterId) => {
  try {
    const url = `/api/clusters/${String(clusterId)}/start`
    console.log(`Starting cluster request to: ${url}`)
    const response = await api.post(url)
    return response.data
  } catch (error) {
    console.error(`Error in startCluster for ID ${clusterId}:`, error)
    if (error.response?.status === 404) {
      error.message = `Cluster endpoint not found. URL attempted: /api/clusters/${clusterId}/start`
    }
    throw error
  }
}

export const terminateCluster = async (clusterId) => {
  try {
    const url = `/api/clusters/${String(clusterId)}/terminate`
    console.log(`Terminating cluster request to: ${url}`)
    const response = await api.post(url)
    return response.data
  } catch (error) {
    console.error(`Error in terminateCluster for ID ${clusterId}:`, error)
    if (error.response?.status === 404) {
      error.message = `Cluster endpoint not found. URL attempted: /api/clusters/${clusterId}/terminate`
    }
    throw error
  }
}

// Self-Healing API
export const getSelfHealingConfig = async () => {
  const response = await api.get('/api/self-healing/config')
  return response.data
}

export const updateSelfHealingConfig = async (config) => {
  const response = await api.post('/api/self-healing/config', config)
  return response.data
}

export const getHealthStatus = async () => {
  const response = await api.get('/api/self-healing/health')
  return response.data
}

export const runSelfHealing = async () => {
  const response = await api.post('/api/self-healing/run')
  return response.data
}

export const getHealingHistory = async (limit = 50) => {
  const response = await api.get(`/api/self-healing/history?limit=${limit}`)
  return response.data
}

export const getSelfHealingStats = async () => {
  const response = await api.get('/api/self-healing/stats')
  return response.data
}

export default api

