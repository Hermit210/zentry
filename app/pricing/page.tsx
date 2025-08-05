'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { PricingCalculator } from '@/components/PricingCalculator'
import { Check, X, ArrowLeft, Zap, Shield, Globe, Calculator } from 'lucide-react'
import Link from 'next/link'

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [showCalculator, setShowCalculator] = useState(false)

  const plans = [
    {
      name: 'Starter',
      description: 'Perfect for small projects and testing',
      price: { monthly: 5, yearly: 50 },
      features: [
        '1 vCPU, 1GB RAM',
        '25GB SSD Storage',
        '1TB Bandwidth',
        'Basic Support',
        '99.9% Uptime SLA',
        'Community Forums'
      ],
      limitations: [
        'Limited to 3 VMs',
        'No priority support',
        'Basic monitoring'
      ],
      popular: false,
      color: 'gray'
    },
    {
      name: 'Pro',
      description: 'Best for growing businesses and teams',
      price: { monthly: 25, yearly: 250 },
      features: [
        '4 vCPU, 8GB RAM',
        '160GB SSD Storage',
        '4TB Bandwidth',
        'Priority Support',
        '99.95% Uptime SLA',
        'Advanced Monitoring',
        'Load Balancing',
        'Auto Scaling',
        'Backup & Recovery'
      ],
      limitations: [
        'Limited to 50 VMs'
      ],
      popular: true,
      color: 'primary'
    },
    {
      name: 'Enterprise',
      description: 'For large organizations with custom needs',
      price: { monthly: 'Custom', yearly: 'Custom' },
      features: [
        'Custom Resources',
        'Unlimited VMs',
        'Dedicated Support Team',
        '99.99% Uptime SLA',
        'White-label Options',
        'Custom Integrations',
        'Advanced Security',
        'Compliance Support',
        'On-premise Options'
      ],
      limitations: [],
      popular: false,
      color: 'purple'
    }
  ]

  const vmPricing = [
    { type: 'Small', cpu: '1 vCPU', ram: '1GB', storage: '25GB', price: 0.05 },
    { type: 'Medium', cpu: '2 vCPU', ram: '4GB', storage: '80GB', price: 0.10 },
    { type: 'Large', cpu: '4 vCPU', ram: '8GB', storage: '160GB', price: 0.20 },
    { type: 'XLarge', cpu: '8 vCPU', ram: '16GB', storage: '320GB', price: 0.40 }
  ]

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="flex items-center space-x-2">
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Home</span>
            </Link>
            <div className="text-2xl font-bold glow-text">ZENTRY</div>
            <Link href="/docs">
              <Button variant="secondary" size="sm">View Docs</Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-12 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl md:text-6xl font-bold mb-6 glow-text">
              Simple, Transparent Pricing
            </h1>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
              Pay only for what you use. No hidden fees, no surprises. Scale up or down anytime.
            </p>

            {/* Billing Toggle */}
            <div className="flex flex-col items-center space-y-4 mb-8">
              <div className="flex items-center space-x-4">
                <span className={billingCycle === 'monthly' ? 'text-white' : 'text-gray-400'}>Monthly</span>
                <button
                  onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                  className="relative w-14 h-7 bg-gray-700 rounded-full p-1 transition-colors duration-200"
                >
                  <div className={`w-5 h-5 bg-primary-500 rounded-full transition-transform duration-200 ${
                    billingCycle === 'yearly' ? 'translate-x-7' : 'translate-x-0'
                  }`} />
                </button>
                <span className={billingCycle === 'yearly' ? 'text-white' : 'text-gray-400'}>
                  Yearly <span className="text-green-400 text-sm">(Save 17%)</span>
                </span>
              </div>
              
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => setShowCalculator(true)}
                className="flex items-center space-x-2"
              >
                <Calculator className="w-4 h-4" />
                <span>Pricing Calculator</span>
              </Button>
            </div>
          </motion.div>

          {/* Pricing Plans */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative bg-gray-900 rounded-xl p-8 border ${
                  plan.popular ? 'border-primary-600' : 'border-gray-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary-600 text-white text-sm px-4 py-1 rounded-full">
                    Most Popular
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-gray-400 mb-4">{plan.description}</p>
                  <div className="text-4xl font-bold mb-2">
                    {typeof plan.price[billingCycle] === 'number' ? (
                      <>
                        ${plan.price[billingCycle]}
                        <span className="text-lg text-gray-400">/{billingCycle === 'monthly' ? 'mo' : 'yr'}</span>
                      </>
                    ) : (
                      plan.price[billingCycle]
                    )}
                  </div>
                </div>

                <div className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <div key={i} className="flex items-center space-x-3">
                      <Check className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{feature}</span>
                    </div>
                  ))}
                  {plan.limitations.map((limitation, i) => (
                    <div key={i} className="flex items-center space-x-3">
                      <X className="w-5 h-5 text-red-400 flex-shrink-0" />
                      <span className="text-gray-500">{limitation}</span>
                    </div>
                  ))}
                </div>

                <Button 
                  className={`w-full ${plan.popular ? '' : 'variant-secondary'}`}
                  variant={plan.popular ? 'primary' : 'secondary'}
                >
                  {plan.name === 'Enterprise' ? 'Contact Sales' : 'Get Started'}
                </Button>
              </motion.div>
            ))}
          </div>

          {/* VM Pricing Table */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900 rounded-xl p-8 mb-16"
          >
            <h2 className="text-3xl font-bold mb-6 text-center">VM Instance Pricing</h2>
            <p className="text-gray-400 text-center mb-8">Hourly rates for virtual machines</p>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-4 px-4">Instance Type</th>
                    <th className="text-left py-4 px-4">vCPU</th>
                    <th className="text-left py-4 px-4">Memory</th>
                    <th className="text-left py-4 px-4">Storage</th>
                    <th className="text-left py-4 px-4">Price/Hour</th>
                  </tr>
                </thead>
                <tbody>
                  {vmPricing.map((vm, index) => (
                    <tr key={vm.type} className="border-b border-gray-800">
                      <td className="py-4 px-4 font-semibold">{vm.type}</td>
                      <td className="py-4 px-4 text-gray-300">{vm.cpu}</td>
                      <td className="py-4 px-4 text-gray-300">{vm.ram}</td>
                      <td className="py-4 px-4 text-gray-300">{vm.storage}</td>
                      <td className="py-4 px-4 text-primary-400 font-semibold">${vm.price}/hr</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Features Comparison */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900 rounded-xl p-8 mb-16"
          >
            <h2 className="text-3xl font-bold mb-8 text-center">What's Included</h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-8 h-8 text-primary-500" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
                <p className="text-gray-400">Deploy infrastructure in seconds, not minutes</p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-primary-500" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
                <p className="text-gray-400">Bank-grade security with compliance support</p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Globe className="w-8 h-8 text-primary-500" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Global Network</h3>
                <p className="text-gray-400">Edge locations worldwide for low latency</p>
              </div>
            </div>
          </motion.div>

          {/* FAQ */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold mb-8">Frequently Asked Questions</h2>
            
            <div className="grid md:grid-cols-2 gap-8 text-left">
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">How is billing calculated?</h3>
                <p className="text-gray-400">You're billed hourly for active resources. No charges when VMs are stopped.</p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">Can I change plans anytime?</h3>
                <p className="text-gray-400">Yes, upgrade or downgrade your plan at any time with no penalties.</p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">Is there a free trial?</h3>
                <p className="text-gray-400">New users get $50 in free credits to test our platform.</p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">What about data transfer?</h3>
                <p className="text-gray-400">Generous bandwidth allowances included. Additional transfer at $0.09/GB.</p>
              </div>
            </div>

            <div className="mt-12">
              <Link href="/">
                <Button size="lg">Start Your Free Trial</Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Pricing Calculator Modal */}
      <PricingCalculator 
        isOpen={showCalculator} 
        onClose={() => setShowCalculator(false)} 
      />
    </div>
  )
}