'use client'

import React, { useState, useEffect } from 'react'
import { Button } from './ui/Button'
import { api } from '@/lib/api'

export const BillingDashboard: React.FC = () => {
  const [creditBalance, setCreditBalance] = useState<any>(null)
  const [billingHistory, setBillingHistory] = useState<any>(null)
  const [usageSummary, setUsageSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showAddCredits, setShowAddCredits] = useState(false)
  const [creditAmount, setCreditAmount] = useState('')
  const [creditDescription, setCreditDescription] = useState('')
  const [historyPage, setHistoryPage] = useState(1)
  const [historyFilter, setHistoryFilter] = useState('')

  useEffect(() => {
    loadBillingData()
  }, [historyPage, historyFilter])

  const loadBillingData = async () => {
    try {
      const [balance, history, summary] = await Promise.all([
        api.getCreditBalance(),
        api.getBillingHistory({
          page: historyPage,
          limit: 10,
          action_type: historyFilter || undefined
        }),
        api.getUsageSummary(30)
      ])
      
      setCreditBalance(balance)
      setBillingHistory(history)
      setUsageSummary(summary)
    } catch (error) {
      console.error('Failed to load billing data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddCredits = async (e: React.FormEvent) => {
    e.preventDefault()
    const amount = parseFloat(creditAmount)
    
    if (isNaN(amount) || amount <= 0) {
      alert('Please enter a valid amount')
      return
    }

    try {
      await api.addCredits(amount, creditDescription)
      setCreditAmount('')
      setCreditDescription('')
      setShowAddCredits(false)
      await loadBillingData()
      alert('Credits added successfully!')
    } catch (error) {
      console.error('Failed to add credits:', error)
      alert('Failed to add credits. Please try again.')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getActionTypeColor = (actionType: string) => {
    switch (actionType) {
      case 'vm_create': return 'bg-blue-100 text-blue-800'
      case 'vm_usage': return 'bg-green-100 text-green-800'
      case 'credit_add': return 'bg-purple-100 text-purple-800'
      case 'credit_deduct': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-6">
                <div className="h-4 bg-gray-700 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-700 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Credit Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Current Balance</h3>
          <p className="text-3xl font-bold text-green-400">
            ${creditBalance?.current_credits?.toFixed(2) || '0.00'}
          </p>
          <div className="mt-4">
            <Button size="sm" onClick={() => setShowAddCredits(true)}>
              Add Credits
            </Button>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Total Spent</h3>
          <p className="text-3xl font-bold text-white">
            ${creditBalance?.total_spent?.toFixed(2) || '0.00'}
          </p>
          <p className="text-sm text-gray-400 mt-2">All time</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Monthly Spending</h3>
          <p className="text-3xl font-bold text-white">
            ${creditBalance?.monthly_spending?.toFixed(2) || '0.00'}
          </p>
          <p className="text-sm text-gray-400 mt-2">This month</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Projected Cost</h3>
          <p className="text-3xl font-bold text-yellow-400">
            ${creditBalance?.projected_monthly_cost?.toFixed(2) || '0.00'}
          </p>
          <p className="text-sm text-gray-400 mt-2">Next month</p>
        </div>
      </div>

      {/* Usage Summary */}
      {usageSummary && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Usage Summary (Last 30 Days)</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {usageSummary.total_vms}
              </div>
              <div className="text-sm text-gray-400">Total VMs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {usageSummary.active_vms}
              </div>
              <div className="text-sm text-gray-400">Active VMs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">
                ${usageSummary.hourly_cost.toFixed(2)}
              </div>
              <div className="text-sm text-gray-400">Current Hourly Cost</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">
                ${usageSummary.projected_monthly_cost.toFixed(2)}
              </div>
              <div className="text-sm text-gray-400">Projected Monthly</div>
            </div>
          </div>
        </div>
      )}

      {/* Billing History */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Billing History</h3>
          <div className="flex space-x-2">
            <select
              value={historyFilter}
              onChange={(e) => setHistoryFilter(e.target.value)}
              className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">All Transactions</option>
              <option value="vm_create">VM Creation</option>
              <option value="vm_usage">VM Usage</option>
              <option value="credit_add">Credit Addition</option>
              <option value="credit_deduct">Credit Deduction</option>
            </select>
          </div>
        </div>

        {billingHistory && billingHistory.items && billingHistory.items.length > 0 ? (
          <div className="space-y-3">
            {billingHistory.items.map((transaction: any, index: number) => (
              <div key={index} className="flex justify-between items-center p-4 bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionTypeColor(transaction.action_type)}`}>
                      {transaction.action_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-white font-medium">
                      {transaction.amount >= 0 ? '+' : ''}${transaction.amount.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-gray-300 mt-1">{transaction.description}</p>
                  <p className="text-gray-400 text-sm">{formatDate(transaction.created_at)}</p>
                </div>
                <div className={`text-lg font-semibold ${
                  transaction.amount >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {transaction.amount >= 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                </div>
              </div>
            ))}

            {/* Pagination */}
            <div className="flex justify-between items-center mt-6">
              <div className="text-sm text-gray-400">
                Showing {((historyPage - 1) * 10) + 1} to {Math.min(historyPage * 10, billingHistory.total)} of {billingHistory.total} transactions
              </div>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setHistoryPage(Math.max(1, historyPage - 1))}
                  disabled={historyPage === 1}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setHistoryPage(historyPage + 1)}
                  disabled={historyPage * 10 >= billingHistory.total}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            No billing history found
          </div>
        )}
      </div>

      {/* Add Credits Modal */}
      {showAddCredits && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add Credits</h3>
            <form onSubmit={handleAddCredits}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={creditAmount}
                  onChange={(e) => setCreditAmount(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  placeholder="25.00"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Description (Optional)</label>
                <input
                  type="text"
                  value={creditDescription}
                  onChange={(e) => setCreditDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  placeholder="Credit card payment"
                />
              </div>
              <div className="flex space-x-3">
                <Button type="submit" className="flex-1">Add Credits</Button>
                <Button type="button" variant="secondary" onClick={() => setShowAddCredits(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Credit Warning */}
      {creditBalance && creditBalance.current_credits < 5 && (
        <div className="bg-yellow-900 border border-yellow-700 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-400">Low Credit Balance</h3>
              <p className="text-sm text-yellow-300 mt-1">
                Your credit balance is low (${creditBalance.current_credits.toFixed(2)}). 
                Consider adding credits to avoid service interruption.
              </p>
            </div>
            <div className="ml-auto">
              <Button size="sm" onClick={() => setShowAddCredits(true)}>
                Add Credits
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}