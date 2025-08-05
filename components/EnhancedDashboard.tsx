'use client'

import React, { useState, useEffect } from 'react'
import { Button } from './ui/Button'
import { api, type User, type Project, type VM } from '@/lib/api'

interface DashboardProps {
  user: User
  onLogout: () => void
}

export const EnhancedDashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [projects, setProjects] = useState<Project[]>([])
  const [vms, setVMs] = useState<VM[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [showCreateVM, setShowCreateVM] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')
  const [newVMName, setNewVMName] = useState('')
  const [newVMType, setNewVMType] = useState('small')
  const [newVMImage, setNewVMImage] = useState('ubuntu-22.04')
  const [selectedProject, setSelectedProject] = useState('')
  const [vmMetrics, setVMMetrics] = useState<Record<string, any>>({})
  const [creditBalance, setCreditBalance] = useState<any>(null)
  const [monitoringData, setMonitoringData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'vms' | 'projects' | 'billing' | 'monitoring'>('overview')

  useEffect(() => {
    loadData()
    // Set up auto-refresh for metrics
    const interval = setInterval(loadData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [projectsData, vmsData, creditData, dashboardData] = await Promise.all([
        api.getProjects(),
        api.getVMs(),
        api.getCreditBalance().catch(() => null),
        api.getMonitoringDashboard().catch(() => null)
      ])
      setProjects(projectsData)
      setVMs(vmsData)
      setCreditBalance(creditData)
      setMonitoringData(dashboardData)
      
      // Load metrics for each VM
      const metricsPromises = vmsData.map(async (vm) => {
        try {
          const metrics = await api.getVMMetrics(vm.id.toString())
          return { [vm.id]: metrics }
        } catch {
          return { [vm.id]: null }
        }
      })
      
      const metricsResults = await Promise.all(metricsPromises)
      const metricsMap = metricsResults.reduce((acc, curr) => ({ ...acc, ...curr }), {})
      setVMMetrics(metricsMap)
      
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const newProject = await api.createProject(newProjectName, newProjectDesc)
      setProjects([newProject, ...projects])
      setNewProjectName('')
      setNewProjectDesc('')
      setShowCreateProject(false)
    } catch (error) {
      console.error('Failed to create project:', error)
      alert('Failed to create project. Please try again.')
    }
  }

  const handleCreateVM = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProject) {
      alert('Please select a project for the VM')
      return
    }
    
    try {
      const newVM = await api.createVM({
        name: newVMName,
        instance_type: newVMType,
        image: newVMImage,
        project_id: selectedProject
      })
      setVMs([newVM, ...vms])
      setNewVMName('')
      setNewVMType('small')
      setNewVMImage('ubuntu-22.04')
      setSelectedProject('')
      setShowCreateVM(false)
      await loadData() // Refresh data to update credits
    } catch (error) {
      console.error('Failed to create VM:', error)
      alert('Failed to create VM. Please check your credits and try again.')
    }
  }

  const handleVMAction = async (vmId: string, action: 'start' | 'stop' | 'restart' | 'delete') => {
    try {
      let result
      switch (action) {
        case 'start':
          result = await api.startVM(vmId)
          break
        case 'stop':
          result = await api.stopVM(vmId)
          break
        case 'restart':
          result = await api.restartVM(vmId)
          break
        case 'delete':
          if (!confirm('Are you sure you want to delete this VM? This action cannot be undone.')) {
            return
          }
          result = await api.deleteVM(vmId)
          break
      }
      
      if (result.success) {
        await loadData() // Refresh data
        alert(result.message)
      }
    } catch (error) {
      console.error(`Failed to ${action} VM:`, error)
      alert(`Failed to ${action} VM. Please try again.`)
    }
  }

  const getVMStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'text-green-600 bg-green-100'
      case 'stopped': return 'text-yellow-600 bg-yellow-100'
      case 'creating': return 'text-blue-600 bg-blue-100'
      case 'terminated': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getVMStatusDot = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'bg-green-500'
      case 'stopped': return 'bg-yellow-500'
      case 'creating': return 'bg-blue-500'
      case 'terminated': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Zentry Cloud Dashboard</h1>
            <p className="text-gray-300">Welcome back, {user.name}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-gray-400">Credits</p>
              <p className="text-lg font-semibold text-green-400">
                ${creditBalance?.current_credits?.toFixed(2) || user.credits.toFixed(2)}
              </p>
            </div>
            <Button variant="secondary" onClick={onLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700 px-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'vms', label: 'Virtual Machines' },
            { id: 'projects', label: 'Projects' },
            { id: 'billing', label: 'Billing' },
            { id: 'monitoring', label: 'Monitoring' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Total VMs</h3>
                <p className="text-2xl font-bold text-white">{vms.length}</p>
                <p className="text-sm text-green-400">
                  {vms.filter(vm => vm.status === 'running').length} running
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Projects</h3>
                <p className="text-2xl font-bold text-white">{projects.length}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Monthly Spending</h3>
                <p className="text-2xl font-bold text-white">
                  ${creditBalance?.monthly_spending?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Projected Cost</h3>
                <p className="text-2xl font-bold text-white">
                  ${creditBalance?.projected_monthly_cost?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>

            {/* Recent VMs */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Recent Virtual Machines</h3>
                <Button onClick={() => setActiveTab('vms')}>View All</Button>
              </div>
              <div className="space-y-3">
                {vms.slice(0, 5).map((vm) => (
                  <div key={vm.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${getVMStatusDot(vm.status)}`}></div>
                      <div>
                        <p className="font-medium">{vm.name}</p>
                        <p className="text-sm text-gray-400">{vm.instance_type} • {vm.image}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getVMStatusColor(vm.status)}`}>
                        {vm.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* VMs Tab */}
        {activeTab === 'vms' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Virtual Machines</h2>
              <Button onClick={() => setShowCreateVM(true)}>Create VM</Button>
            </div>

            <div className="grid gap-6">
              {vms.map((vm) => (
                <div key={vm.id} className="bg-gray-800 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">{vm.name}</h3>
                      <p className="text-gray-400">{vm.instance_type} • {vm.image}</p>
                      <p className="text-sm text-gray-500">IP: {vm.ip_address}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getVMStatusColor(vm.status)}`}>
                        {vm.status}
                      </span>
                    </div>
                  </div>

                  {/* VM Metrics */}
                  {vmMetrics[vm.id] && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <p className="text-sm text-gray-400">CPU</p>
                        <p className="text-lg font-semibold">{vmMetrics[vm.id].cpu_usage?.toFixed(1)}%</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-400">Memory</p>
                        <p className="text-lg font-semibold">{vmMetrics[vm.id].memory_usage?.toFixed(1)}%</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-400">Uptime</p>
                        <p className="text-lg font-semibold">{vmMetrics[vm.id].uptime_hours?.toFixed(1)}h</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-400">Cost</p>
                        <p className="text-lg font-semibold">${vmMetrics[vm.id].total_cost?.toFixed(2)}</p>
                      </div>
                    </div>
                  )}

                  {/* VM Actions */}
                  <div className="flex space-x-2">
                    {vm.status === 'stopped' && (
                      <Button size="sm" onClick={() => handleVMAction(vm.id.toString(), 'start')}>
                        Start
                      </Button>
                    )}
                    {vm.status === 'running' && (
                      <>
                        <Button size="sm" variant="secondary" onClick={() => handleVMAction(vm.id.toString(), 'stop')}>
                          Stop
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => handleVMAction(vm.id.toString(), 'restart')}>
                          Restart
                        </Button>
                      </>
                    )}
                    {vm.status !== 'terminated' && (
                      <Button size="sm" variant="secondary" onClick={() => handleVMAction(vm.id.toString(), 'delete')}>
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Projects</h2>
              <Button onClick={() => setShowCreateProject(true)}>Create Project</Button>
            </div>

            <div className="grid gap-6">
              {projects.map((project) => (
                <div key={project.id} className="bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-2">{project.name}</h3>
                  <p className="text-gray-400 mb-4">{project.description}</p>
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-gray-500">
                      {vms.filter(vm => vm.id === project.id).length} VMs
                    </p>
                    <p className="text-sm text-gray-500">
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Billing Tab */}
        {activeTab === 'billing' && creditBalance && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Billing & Credits</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Current Balance</h3>
                <p className="text-3xl font-bold text-green-400">
                  ${creditBalance.current_credits.toFixed(2)}
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Total Spent</h3>
                <p className="text-3xl font-bold text-white">
                  ${creditBalance.total_spent.toFixed(2)}
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Monthly Spending</h3>
                <p className="text-3xl font-bold text-white">
                  ${creditBalance.monthly_spending.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Usage Projection</h3>
              <p className="text-gray-400 mb-2">
                Projected monthly cost: <span className="text-white font-semibold">
                  ${creditBalance.projected_monthly_cost.toFixed(2)}
                </span>
              </p>
              <p className="text-sm text-gray-500">
                Based on current VM usage patterns
              </p>
            </div>
          </div>
        )}

        {/* Monitoring Tab */}
        {activeTab === 'monitoring' && monitoringData && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">System Monitoring</h2>
            
            {/* System Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Total VMs</h3>
                <p className="text-2xl font-bold text-white">{monitoringData.overview.total_vms}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Running VMs</h3>
                <p className="text-2xl font-bold text-green-400">{monitoringData.overview.running_vms}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Hourly Cost</h3>
                <p className="text-2xl font-bold text-white">${monitoringData.overview.hourly_cost.toFixed(2)}</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Avg CPU</h3>
                <p className="text-2xl font-bold text-white">
                  {monitoringData.resource_utilization.avg_cpu.toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Alerts */}
            {monitoringData.alerts && monitoringData.alerts.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Active Alerts</h3>
                <div className="space-y-3">
                  {monitoringData.alerts.map((alert: any, index: number) => (
                    <div key={index} className={`p-3 rounded-lg ${
                      alert.severity === 'critical' ? 'bg-red-900 border border-red-700' :
                      alert.severity === 'warning' ? 'bg-yellow-900 border border-yellow-700' :
                      'bg-blue-900 border border-blue-700'
                    }`}>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-sm text-gray-400">{alert.type}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Project</h3>
            <form onSubmit={handleCreateProject}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Project Name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  rows={3}
                />
              </div>
              <div className="flex space-x-3">
                <Button type="submit" className="flex-1">Create Project</Button>
                <Button type="button" variant="secondary" onClick={() => setShowCreateProject(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create VM Modal */}
      {showCreateVM && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New VM</h3>
            <form onSubmit={handleCreateVM}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">VM Name</label>
                <input
                  type="text"
                  value={newVMName}
                  onChange={(e) => setNewVMName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Project</label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  required
                >
                  <option value="">Select a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id.toString()}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Instance Type</label>
                <select
                  value={newVMType}
                  onChange={(e) => setNewVMType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                >
                  <option value="small">Small ($0.05/hr)</option>
                  <option value="medium">Medium ($0.10/hr)</option>
                  <option value="large">Large ($0.20/hr)</option>
                  <option value="xlarge">XLarge ($0.40/hr)</option>
                </select>
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">OS Image</label>
                <select
                  value={newVMImage}
                  onChange={(e) => setNewVMImage(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                >
                  <option value="ubuntu-22.04">Ubuntu 22.04 LTS</option>
                  <option value="ubuntu-20.04">Ubuntu 20.04 LTS</option>
                  <option value="centos-8">CentOS 8</option>
                  <option value="debian-11">Debian 11</option>
                  <option value="fedora-38">Fedora 38</option>
                </select>
              </div>
              <div className="flex space-x-3">
                <Button type="submit" className="flex-1">Create VM</Button>
                <Button type="button" variant="secondary" onClick={() => setShowCreateVM(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}