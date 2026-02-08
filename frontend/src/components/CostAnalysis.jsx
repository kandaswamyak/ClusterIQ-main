import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchCostBreakdown, fetchPricingTiers } from '../services/api'
import { TrendingDown, DollarSign, AlertTriangle, Zap, BarChart3 } from 'lucide-react'

function CostAnalysis() {
  const { data: costData, isLoading: costLoading } = useQuery({
    queryKey: ['cost-breakdown'],
    queryFn: fetchCostBreakdown,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: pricingData } = useQuery({
    queryKey: ['pricing-tiers'],
    queryFn: fetchPricingTiers,
  })

  const breakdown = costData?.breakdown

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-2">
        <div>
          <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">Cost Analysis</h1>
          <p className="mt-3 text-base text-gray-600 font-medium">Monitor and optimize your Databricks spending</p>
        </div>
      </div>

      {costLoading ? (
        <div className="text-center py-12 text-gray-500">Loading cost analysis...</div>
      ) : breakdown ? (
        <>
          {/* Main Cost Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="metric-card" style={{ background: 'linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%)', border: '1px solid #ef4444' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-red-200 mb-2 uppercase tracking-wide">Total Cost (Hourly)</p>
                  <p className="text-4xl font-extrabold text-white">${breakdown.total_cost.toFixed(2)}</p>
                  <p className="text-sm text-red-200 mt-3">Based on current resources</p>
                </div>
                <DollarSign className="h-14 w-14 text-red-300" />
              </div>
            </div>

            <div className="metric-card" style={{ background: 'linear-gradient(135deg, #9a3412 0%, #f97316 100%)', border: '1px solid #fb923c' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-orange-200 mb-2 uppercase tracking-wide">Estimated Monthly</p>
                  <p className="text-4xl font-extrabold text-white">${breakdown.estimated_monthly.toFixed(2)}</p>
                  <p className="text-sm text-orange-200 mt-3">~${(breakdown.estimated_monthly / 20).toFixed(2)}/day</p>
                </div>
                <BarChart3 className="h-14 w-14 text-orange-300" />
              </div>
            </div>

            <div className="metric-card" style={{ background: 'linear-gradient(135deg, #581c87 0%, #a855f7 100%)', border: '1px solid #c084fc' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-purple-200 mb-2 uppercase tracking-wide">Estimated Annual</p>
                  <p className="text-4xl font-extrabold text-white">${breakdown.estimated_annual.toFixed(2)}</p>
                  <p className="text-sm text-purple-200 mt-3">Projected yearly spend</p>
                </div>
                <TrendingDown className="h-14 w-14 text-purple-300" />
              </div>
            </div>
          </div>

          {/* Cost by Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Zap className="h-5 w-5 mr-2 text-yellow-600" />
                Cost by Resource Type
              </h2>
              <div className="space-y-3">
                {Object.entries(breakdown.by_type).map(([type, cost]) => (
                  <div key={type} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span className="font-medium text-gray-700 capitalize">{type.replace(/_/g, ' ')}</span>
                    <span className="text-lg font-bold text-gray-900">${cost.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <DollarSign className="h-5 w-5 mr-2 text-green-600" />
                Cost by Tier
              </h2>
              <div className="space-y-3">
                {Object.entries(breakdown.by_tier).map(([tier, cost]) => (
                  <div key={tier} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span className="font-medium text-gray-700 capitalize">{tier.replace(/_/g, ' ')}</span>
                    <span className="text-lg font-bold text-gray-900">${cost.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

                    {/* High Cost Resources */}
          {breakdown.high_cost_resources.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-red-50 border-b border-red-200 p-4">
                <h2 className="text-lg font-semibold text-red-900 flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  Top High Cost Drivers ({breakdown.high_cost_resources.length})
                </h2>
              </div>
              <div className="divide-y divide-gray-200">
                {breakdown.high_cost_resources.map((resource, idx) => (
                  <div key={idx} className="p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{resource.name}</p>
                        <p className="text-xs text-gray-500 mt-1 capitalize">{resource.type}</p>
                      </div>
                      <p className="text-2xl font-bold text-red-600">${resource.cost.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Optimization Opportunities */}
          {breakdown.optimization_opportunities.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-green-50 border-b border-green-200 p-4">
                <h2 className="text-lg font-semibold text-green-900 flex items-center">
                  <TrendingDown className="h-5 w-5 mr-2" />
                  Cost Optimization Opportunities
                </h2>
              </div>
              <div className="divide-y divide-gray-200">
                {breakdown.optimization_opportunities.map((opp, idx) => (
                  <div key={idx} className="p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{opp.recommendation}</p>
                        <p className="text-sm text-gray-600 mt-1">Resource: {opp.resource}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-500">Potential Savings</p>
                        <p className="text-2xl font-bold text-green-600">${opp.potential_savings.toFixed(2)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pricing Tiers Reference */}
          {pricingData && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Pricing Reference</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(pricingData.description).map(([tier, description]) => (
                  <div key={tier} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {tier.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-bold text-gray-900">{description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Total Resources</p>
              <p className="text-2xl font-bold text-blue-600">{(costData.cluster_count + costData.job_count) || 0}</p>
              <p className="text-xs text-gray-500 mt-1">{costData.cluster_count} clusters, {costData.job_count} jobs</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Cost/Resource</p>
              <p className="text-2xl font-bold text-green-600">${((breakdown.total_cost / (costData.cluster_count + costData.job_count)) || 0).toFixed(2)}</p>
              <p className="text-xs text-gray-500 mt-1">Average per hour</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Idle Resources</p>
              <p className="text-2xl font-bold text-orange-600">{breakdown.idle_resources.length}</p>
              <p className="text-xs text-gray-500 mt-1">Consuming costs</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Savings Potential</p>
              <p className="text-2xl font-bold text-purple-600">
                ${breakdown.optimization_opportunities.reduce((sum, o) => sum + o.potential_savings, 0).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">If optimized</p>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-gray-500">No cost data available</div>
      )}
    </div>
  )
}

export default CostAnalysis
