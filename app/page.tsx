'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { FeatureCard } from '@/components/FeatureCard'
import { AuthForm } from '@/components/AuthForm'
import { Dashboard } from '@/components/Dashboard'
import { api, type User } from '@/lib/api'
import Link from 'next/link'
import { 
  Server, 
  Database, 
  Lock, 
  BarChart3,
  Code,
  Globe,
  Activity,
  Cloud,
  TrendingUp
} from 'lucide-react'

export default function LandingPage() {
  const [user, setUser] = useState<User | null>(null)
  const [showAuth, setShowAuth] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = api.getStoredUser()
    if (storedUser && api.isAuthenticated()) {
      setUser(storedUser)
    }
    setLoading(false)
  }, [])

  const handleAuthSuccess = (userData: User) => {
    setUser(userData)
    setShowAuth(false)
  }

  const handleLogout = () => {
    api.logout()
    setUser(null)
    setShowAuth(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  // Show dashboard if user is logged in
  if (user) {
    return <Dashboard user={user} onLogout={handleLogout} />
  }

  // Show auth form if requested
  if (showAuth) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />
  }

  // Show landing page
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Cloud className="w-5 h-5 text-white" />
              </div>
              <div className="text-2xl font-bold glow-text">ZENTRY</div>
            </div>
            <div className="hidden md:flex space-x-8">
              <a href="#features" className="nav-link">Features</a>
              <Link href="/pricing" className="nav-link">Pricing</Link>
              <Link href="/docs" className="nav-link">Docs</Link>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="secondary" size="sm" onClick={() => setShowAuth(true)}>Login</Button>
              <Button size="sm" onClick={() => setShowAuth(true)}>Get Started</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section with Dashboard Preview */}
      <section className="pt-24 pb-12 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="stat-card"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Total Deployed</span>
                <Button variant="secondary" size="sm" className="text-xs py-1 px-2" onClick={() => setShowAuth(true)}>Deploy</Button>
              </div>
              <div className="text-2xl font-bold text-white">$0.00</div>
              <div className="text-xs text-gray-500 mt-1">Infrastructure</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="stat-card"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Total Compute</span>
                <Button variant="secondary" size="sm" className="text-xs py-1 px-2" onClick={() => setShowAuth(true)}>Scale</Button>
              </div>
              <div className="text-2xl font-bold text-white">$0.00</div>
              <div className="text-xs text-primary-500 mt-1">+0.00%</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="stat-card"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Available Resources</span>
                <Button variant="secondary" size="sm" className="text-xs py-1 px-2" onClick={() => setShowAuth(true)}>Provision</Button>
              </div>
              <div className="text-2xl font-bold text-white">$0.00</div>
              <div className="text-xs text-gray-500 mt-1">Ready to deploy</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="stat-card"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Health Factor</span>
              </div>
              <div className="text-2xl font-bold text-white">0%</div>
              <div className="text-xs text-gray-500 mt-1">System status</div>
            </motion.div>
          </div>

          {/* Main Hero Content */}
          <div className="text-center mb-12">
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-4xl md:text-6xl font-bold mb-6"
            >
              Launch your infrastructure in{' '}
              <span className="glow-text">seconds</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-xl text-gray-400 max-w-3xl mx-auto mb-8"
            >
              Developer-first cloud platform for building fast, scaling smarter, 
              and paying only for what you use — without surprises.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="flex flex-col sm:flex-row justify-center gap-4"
            >
              <Button size="lg" onClick={() => setShowAuth(true)}>Get Early Access</Button>
              <Button variant="secondary" size="lg" onClick={() => setShowAuth(true)}>View Dashboard</Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Dashboard Preview Section */}
      <section className="py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* My Infrastructure */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="dashboard-card"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">My Infrastructure</h3>
                <div className="text-sm text-gray-400">
                  Total Balance: <span className="text-white font-semibold">$0.00</span>
                </div>
              </div>
              <div className="text-sm text-gray-400 mb-4">
                Max Deployment: <span className="text-white">$0.00</span>
              </div>
              
              {/* Empty state with icon */}
              <div className="flex items-center justify-center h-48 border-2 border-dashed border-gray-700 rounded-lg">
                <div className="text-center">
                  <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Server className="w-8 h-8 text-primary-500" />
                  </div>
                  <p className="text-gray-400 mb-2">No infrastructure deployed yet</p>
                  <Button size="sm" onClick={() => setShowAuth(true)}>Deploy Your First VM</Button>
                </div>
              </div>
            </motion.div>

            {/* Active Deployments */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="dashboard-card"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">Active Deployments</h3>
                <div className="flex space-x-2">
                  <div className="text-xs bg-gray-800 px-2 py-1 rounded">Compute</div>
                  <div className="text-xs bg-gray-800 px-2 py-1 rounded">Storage</div>
                  <div className="text-xs bg-gray-800 px-2 py-1 rounded">Network</div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg border border-gray-700">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-white">Production API</span>
                  </div>
                  <div className="text-sm text-gray-400">Running</div>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg border border-gray-700">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span className="text-white">Staging Environment</span>
                  </div>
                  <div className="text-sm text-gray-400">Deploying</div>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg border border-gray-700">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                    <span className="text-white">Development DB</span>
                  </div>
                  <div className="text-sm text-gray-400">Stopped</div>
                </div>
              </div>
              
              {/* Empty state with icon */}
              <div className="flex items-center justify-center h-24 border-2 border-dashed border-gray-700 rounded-lg mt-4">
                <div className="text-center">
                  <div className="w-12 h-12 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-2">
                    <Activity className="w-6 h-6 text-primary-500" />
                  </div>
                  <p className="text-gray-400 text-sm">Ready to scale</p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Core Features Grid */}
      <section id="features" className="py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            className="text-3xl font-bold text-center mb-12 glow-text"
          >
            Everything you need to build
          </motion.h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Server className="w-8 h-8 text-primary-500" />}
              title="Compute"
              description="Launch VMs or containers with full root access in seconds. Scale up or down instantly."
            />
            <FeatureCard
              icon={<Database className="w-8 h-8 text-primary-500" />}
              title="Object Storage"
              description="S3-compatible, high-availability storage with simple APIs and global CDN."
            />
            <FeatureCard
              icon={<Lock className="w-8 h-8 text-primary-500" />}
              title="Identity & Access"
              description="Built-in project roles, teams, and secure OAuth2 SSO integration."
            />
            <FeatureCard
              icon={<BarChart3 className="w-8 h-8 text-primary-500" />}
              title="Usage-Based Billing"
              description="Pay only for what you actually use. No overprovisioning required."
            />
            <FeatureCard
              icon={<Globe className="w-8 h-8 text-primary-500" />}
              title="Global Network"
              description="Low-latency edge locations worldwide with automatic failover."
            />
            <FeatureCard
              icon={<Code className="w-8 h-8 text-primary-500" />}
              title="Developer Tools"
              description="Full CLI, REST APIs, Terraform support, and GitHub Actions integration."
            />
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-12 px-4 text-center">
        <div className="max-w-4xl mx-auto">
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            className="text-3xl font-bold mb-6 glow-text"
          >
            Ready to build without the cloud bloat?
          </motion.h2>
          <p className="text-xl mb-8 text-gray-400">
            Join early access and get $50 in free credits. No credit card required.
          </p>
          <Button size="lg" className="mb-4" onClick={() => setShowAuth(true)}>Get Early Access</Button>
          <p className="text-sm text-gray-500">
            Join 500+ developers already building on Zentry
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black py-12 px-4 border-t border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Cloud className="w-5 h-5 text-white" />
                </div>
                <div className="text-2xl font-bold glow-text">ZENTRY</div>
              </div>
              <p className="text-gray-400">Developer-first cloud platform</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-white">Product</h4>
              <div className="space-y-2 text-gray-400">
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Compute</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Storage</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Networking</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Pricing</div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-white">Developers</h4>
              <div className="space-y-2 text-gray-400">
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Documentation</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">API Reference</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">CLI Tools</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">GitHub</div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-white">Company</h4>
              <div className="space-y-2 text-gray-400">
                <div className="hover:text-primary-500 cursor-pointer transition-colors">About</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Blog</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Careers</div>
                <div className="hover:text-primary-500 cursor-pointer transition-colors">Contact</div>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
            <p>&copy; 2024 Zentry Cloud. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}