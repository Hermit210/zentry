'use client'

import React, { useState } from 'react'
import { Button } from './ui/Button'
import { Calculator, X } from 'lucide-react'

interface PricingCalculatorProps {
  isOpen: boolean
  onClose: () => void
}

export const PricingCalculator: React.FC<PricingCalculatorProps> = ({ isOpen, onClose }) => {
  const [vmCount, setVmCount] = useState(1)
  const [vmType, setVmType] = useState('small')
  const [hoursPerDay, setHoursPerDay] = useState(8)
  const [daysPerMonth, setDaysPerMonth] = useState(22)

  const vmPricing = {
    small: 0.05,
    medium: 0.10,
    large: 0.20,
    xlarge: 0.40
  }

  const vmSpecs = {
    small: '1 vCPU, 1GB RAM',
    medium: '2 vCPU, 4GB RAM', 
    large: '4 vCPU, 8GB RAM',
    xlarge: '8 vCPU, 16GB RAM'
  }

  const hourlyRate = vmPricing[vmType as keyof typeof vmPricing]
  const dailyCost = hourlyRate * vmCount * hoursPerDay
  const monthlyCost = dailyCost * daysPerMonth
  const yearlyCost = monthlyCost * 12

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold flex items-center">
            <Calculator className="w-5 h-5 mr-2" />
            Pricing Calculator
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              VM Type
            </label>
            <select
              value={vmType}
              onChange={(e) => setVmType(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
            >
              <option value="small">Small - {vmSpecs.small}</option>
              <option value="medium">Medium - {vmSpecs.medium}</option>
              <option value="large">Large - {vmSpecs.large}</option>
              <option value="xlarge">XLarge - {vmSpecs.xlarge}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Number of VMs: {vmCount}
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={vmCount}
              onChange={(e) => setVmCount(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Hours per day: {hoursPerDay}
            </label>
            <input
              type="range"
              min="1"
              max="24"
              value={hoursPerDay}
              onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Days per month: {daysPerMonth}
            </label>
            <input
              type="range"
              min="1"
              max="31"
              value={daysPerMonth}
              onChange={(e) => setDaysPerMonth(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-900 rounded-lg">
          <h4 className="font-semibold mb-3">Estimated Costs</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Hourly:</span>
              <span className="font-semibold">${(hourlyRate * vmCount).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Daily:</span>
              <span className="font-semibold">${dailyCost.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Monthly:</span>
              <span className="font-semibold text-primary-400">${monthlyCost.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Yearly:</span>
              <span className="font-semibold">${yearlyCost.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="mt-6 text-xs text-gray-400">
          * Estimates based on selected usage. Actual costs may vary based on actual usage and additional services.
        </div>

        <div className="mt-6">
          <Button onClick={onClose} className="w-full">
            Close Calculator
          </Button>
        </div>
      </div>
    </div>
  )
}