'use client'

import React, { useState, useEffect } from 'react'
import { Button } from './ui/Button'
import { api, type User, type Project, type VM } from '@/lib/api'

interface DashboardProps {
  user: User
  onLogout: () => void
}

export const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
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

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [projectsData, vmsData, creditData, dashboardData] = await Promise.all([
        api.getProjects().catch(() => []),
        api.getVMs().catch(() => []),
        api.getCreditBalance().catch(() => null),
        api.getMonitoringDashboard().catch(() => null)
      ])
      
      // Ensure vmsData is an array
      const safeVmsData = Array.isArray(vmsData) ? vmsData : []
      
      setProjects(Array.isArray(projectsData) ? projectsData : [])
      setVMs(safeVmsData)
      setCreditBalance(creditData)
      setMonitoringData(dashboardData)
      
      // Load metrics for each VM only if we have VMs
      if (safeVmsData.length > 0) {
        try {
          const metricsPromises = safeVmsData.map(async (vm) => {
            try {
              const metrics = await api.getVMMetrics(vm.id.toString())
              return { [vm.id]: metrics }
            } catch {
              return { [vm.id]: null }
            }
          })
          
          const metricsResults = await Promise.all(metricsPromises)
          const metricsMap: Record<string, any> = {}
          metricsResults.forEach(result => {
            Object.assign(metricsMap, result)
          })
          setVMMetrics(metricsMap)
        } catch (error) {
          console.error('Failed to load VM metrics:', error)
        }
      }
      
    } catch (error) {
      console.error('Failed to load data:', error)
      // Set empty arrays as fallback
      setProjects([])
      setVMs([])
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

  const handleDeleteVM = async (vmId: string | number) => {
    if (!confirm('Are you sure you want to delete this VM? This action cannot be undone.')) {
      return
    }
    try {
      await api.deleteVM(vmId.toString())
      setVMs(vms.filter(vm => vm.id !== vmId))
    } catch (error) {
      console.error('Failed to delete VM:', error)
      alert('Failed to delete VM. Please try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'text-green-400'
      case 'stopped': return 'text-gray-400'
      case 'creating': return 'text-yellow-400'
      case 'terminated': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusDot = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'bg-green-500'
      case 'stopped': return 'bg-gray-500'
      case 'creating': return 'bg-yellow-500'
      case 'terminated': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Welcome back, {user.name}!</h1>
          <p className="text-gray-300">Manage your cloud infrastructure</p>
        </div>
        <Button variant="secondary" onClick={onLogout}>
          Logout
        </Button>
      </div>

      {/* Credits */}
      <div className="bg-gray-800 rounded-xl p-6 mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold mb-2">Available Credits</h2>
            <p className="text-3xl font-bold text-green-400">${user.credits.toFixed(2)}</p>
            <p className="text-sm text-gray-400 mt-1">
              {user.credits < 5 ? 'Low balance - consider adding credits' : 'Sufficient balance'}
            </p>
          </div>
          <div className="space-y-2">
            <Button variant="secondary" size="sm">Add Credits</Button>
            <div className="text-xs text-gray-400 text-center">
              VM costs: $0.05-0.40/hr
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-4">Projects</h3>
          <p className="text-gray-300 mb-4">You have {projects.length} projects</p>
          <Button onClick={() => setShowCreateProject(true)}>
            Create Project
          </Button>
        </div>

        <div className="bg-gray-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-4">Virtual Machines</h3>
          <p className="text-gray-300 mb-4">You have {vms.length} VMs</p>
          <Button onClick={() => setShowCreateVM(true)}>
            Launch VM
          </Button>
        </div>
      </div>

      {/* Projects List */}
      <div className="bg-gray-800 rounded-xl p-6 mb-8">
        <h3 className="text-xl font-semibold mb-4">Your Projects</h3>
        {projects.length === 0 ? (
          <p className="text-gray-400">No projects yet. Create your first project!</p>
        ) : (
          <div className="space-y-3">
            {projects.map((project) => (
              <div key={project.id} className="bg-gray-700 rounded-lg p-4">
                <h4 className="font-semibold">{project.name}</h4>
                <p className="text-gray-300 text-sm">{project.description}</p>
                <p className="text-gray-400 text-xs mt-2">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* VMs List */}
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-4">Your Virtual Machines</h3>
        {vms.length === 0 ? (
          <p className="text-gray-400">No VMs yet. Launch your first VM!</p>
        ) : (
          <div className="space-y-3">
            {vms.map((vm) => (
              <div key={vm.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold">{vm.name}</h4>
                      <div className={`w-2 h-2 rounded-full ${getStatusDot(vm.status)}`}></div>
                    </div>
                    <p className="text-gray-300 text-sm">
                      {vm.instance_type} • {vm.image}
                    </p>
                    <p className="text-gray-400 text-xs">
                      IP: {vm.ip_address} • Created: {new Date(vm.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(vm.status)}`}>
                    {vm.status.toUpperCase()}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  {vm.status === 'running' && (
                    <Button variant="secondary" size="sm" className="text-xs">
                      SSH Connect
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleDeleteVM(vm.id)}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Create New Project</h3>
            <form onSubmit={handleCreateProject}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
                  rows={3}
                />
              </div>
              <div className="flex gap-3">
                <button type="submit" className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200">
                  Create
                </button>
                <button
                  type="button"
                  className="border-primary-600 hover:bg-primary-600 hover:text-white text-primary-600 bg-transparent font-semibold py-3 px-6 rounded-lg transition-all duration-200"
                  onClick={() => setShowCreateProject(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create VM Modal */}
      {showCreateVM && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Launch New VM</h3>
            <form onSubmit={handleCreateVM}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  VM Name
                </label>
                <input
                  type="text"
                  value={newVMName}
                  onChange={(e) => setNewVMName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Instance Type
                </label>
                <select
                  value={newVMType}
                  onChange={(e) => setNewVMType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
                >
                  <option value="small">Small (1 vCPU, 1GB RAM)</option>
                  <option value="medium">Medium (2 vCPU, 4GB RAM)</option>
                  <option value="large">Large (4 vCPU, 8GB RAM)</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Image
                </label>
                <select
                  value={newVMImage}
                  onChange={(e) => setNewVMImage(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
                >
                  <option value="ubuntu-22.04">Ubuntu 22.04</option>
                  <option value="ubuntu-20.04">Ubuntu 20.04</option>
                  <option value="centos-8">CentOS 8</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button type="submit" className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200">
                  Launch
                </button>
                <button
                  type="button"
                  className="border-primary-600 hover:bg-primary-600 hover:text-white text-primary-600 bg-transparent font-semibold py-3 px-6 rounded-lg transition-all duration-200"
                  onClick={() => setShowCreateVM(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}