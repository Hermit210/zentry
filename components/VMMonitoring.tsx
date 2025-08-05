'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface VMMonitoringProps {
  vmId: string
  vmName: string
}

export const VMMonitoring: React.FC<VMMonitoringProps> = ({ vmId, vmName }) => {
  const [metrics, setMetrics] = useState<any>(null)
  const [history, setHistory] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState(24)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 10000) // Update every 10 seconds
    return () => clearInterval(interval)
  }, [vmId, timeRange])

  const loadMetrics = async () => {
    try {
      const [currentMetrics, metricsHistory] = await Promise.all([
        api.getVMMetrics(vmId),
        api.getVMMetricsHistory(vmId, timeRange)
      ])
      setMetrics(currentMetrics)
      setHistory(metricsHistory)
    } catch (error) {
      console.error('Failed to load VM metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  const getUsageColor = (usage: number) => {
    if (usage >= 80) return 'text-red-400'
    if (usage >= 60) return 'text-yellow-400'
    return 'text-green-400'
  }

  const getUsageBarColor = (usage: number) => {
    if (usage >= 80) return 'bg-red-500'
    if (usage >= 60) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-700 rounded"></div>
            <div className="h-3 bg-gray-700 rounded w-5/6"></div>
            <div className="h-3 bg-gray-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <p className="text-gray-400">No metrics available for this VM</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Current Metrics */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Real-time Metrics - {vmName}</h3>
          <div className="flex space-x-2">
            {[6, 12, 24, 48].map((hours) => (
              <button
                key={hours}
                onClick={() => setTimeRange(hours)}
                className={`px-3 py-1 rounded text-sm ${
                  timeRange === hours
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {hours}h
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* CPU Usage */}
          <div className="text-center">
            <div className="mb-2">
              <div className="text-2xl font-bold">
                <span className={getUsageColor(metrics.cpu_usage)}>
                  {metrics.cpu_usage.toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-gray-400">CPU Usage</div>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getUsageBarColor(metrics.cpu_usage)}`}
                style={{ width: `${Math.min(metrics.cpu_usage, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Memory Usage */}
          <div className="text-center">
            <div className="mb-2">
              <div className="text-2xl font-bold">
                <span className={getUsageColor(metrics.memory_usage)}>
                  {metrics.memory_usage.toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-gray-400">Memory Usage</div>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getUsageBarColor(metrics.memory_usage)}`}
                style={{ width: `${Math.min(metrics.memory_usage, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Disk Usage */}
          <div className="text-center">
            <div className="mb-2">
              <div className="text-2xl font-bold">
                <span className={getUsageColor(metrics.disk_usage)}>
                  {metrics.disk_usage.toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-gray-400">Disk Usage</div>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getUsageBarColor(metrics.disk_usage)}`}
                style={{ width: `${Math.min(metrics.disk_usage, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Network I/O */}
          <div className="text-center">
            <div className="mb-2">
              <div className="text-lg font-bold text-blue-400">
                ↓ {(metrics.network_in / 1024).toFixed(1)} KB/s
              </div>
              <div className="text-lg font-bold text-green-400">
                ↑ {(metrics.network_out / 1024).toFixed(1)} KB/s
              </div>
              <div className="text-sm text-gray-400">Network I/O</div>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-gray-700">
          <div className="text-center">
            <div className="text-lg font-semibold text-white">
              {metrics.uptime_hours.toFixed(1)}h
            </div>
            <div className="text-sm text-gray-400">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-white">
              ${metrics.cost_per_hour.toFixed(3)}/hr
            </div>
            <div className="text-sm text-gray-400">Hourly Rate</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-white">
              ${metrics.total_cost.toFixed(2)}
            </div>
            <div className="text-sm text-gray-400">Total Cost</div>
          </div>
        </div>
      </div>

      {/* Historical Data */}
      {history && history.metrics && history.metrics.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            Historical Data ({timeRange}h)
          </h3>
          
          {/* Averages */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-blue-400">
                {history.averages.cpu_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Avg CPU</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-green-400">
                {history.averages.memory_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Avg Memory</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-yellow-400">
                {history.averages.disk_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Avg Disk</div>
            </div>
          </div>

          {/* Peak Usage */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-red-400">
                {history.peaks.cpu_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Peak CPU</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-red-400">
                {history.peaks.memory_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Peak Memory</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-xl font-bold text-red-400">
                {(history.peaks.network_in / 1024).toFixed(1)} KB/s
              </div>
              <div className="text-sm text-gray-400">Peak Network In</div>
            </div>
          </div>

          {/* Data Points Info */}
          <div className="mt-4 text-center text-sm text-gray-400">
            {history.data_points} data points collected over {timeRange} hours
          </div>
        </div>
      )}
    </div>
  )
}