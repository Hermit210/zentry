'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { 
  ArrowLeft, 
  Book, 
  Code, 
  Terminal, 
  Server, 
  Database,
  Shield,
  Zap,
  Copy,
  ExternalLink
} from 'lucide-react'
import Link from 'next/link'

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState('getting-started')
  const [copiedCode, setCopiedCode] = useState('')

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(id)
    setTimeout(() => setCopiedCode(''), 2000)
  }

  const sections = [
    { id: 'getting-started', title: 'Getting Started', icon: <Zap className="w-4 h-4" /> },
    { id: 'authentication', title: 'Authentication', icon: <Shield className="w-4 h-4" /> },
    { id: 'api-reference', title: 'API Reference', icon: <Code className="w-4 h-4" /> },
    { id: 'cli-tools', title: 'CLI Tools', icon: <Terminal className="w-4 h-4" /> },
    { id: 'vm-management', title: 'VM Management', icon: <Server className="w-4 h-4" /> },
    { id: 'storage', title: 'Storage', icon: <Database className="w-4 h-4" /> },
  ]

  const CodeBlock = ({ code, language, id }: { code: string; language: string; id: string }) => (
    <div className="relative bg-gray-900 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-gray-400 uppercase">{language}</span>
        <button
          onClick={() => copyToClipboard(code, id)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {copiedCode === id ? (
            <span className="text-green-400 text-xs">Copied!</span>
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>
      </div>
      <pre className="text-sm text-gray-300 overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  )

  const renderContent = () => {
    switch (activeSection) {
      case 'getting-started':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">Getting Started</h1>
            <p className="text-gray-400 mb-8">
              Welcome to Zentry Cloud! This guide will help you get up and running in minutes.
            </p>

            <h2 className="text-2xl font-semibold mb-4">Quick Start</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">1. Create an Account</h3>
                <p className="text-gray-400 mb-4">
                  Sign up for a free account and get $50 in credits to start building.
                </p>
                <Link href="/">
                  <Button>Create Account</Button>
                </Link>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">2. Install the CLI</h3>
                <p className="text-gray-400 mb-4">
                  Install the Zentry CLI to manage your infrastructure from the command line.
                </p>
                <CodeBlock
                  id="install-cli"
                  language="bash"
                  code={`# Install via npm
npm install -g @zentry/cli

# Or via curl
curl -sSL https://cli.zentry.cloud/install.sh | bash`}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">3. Deploy Your First VM</h3>
                <p className="text-gray-400 mb-4">
                  Launch a virtual machine in seconds with our simple API.
                </p>
                <CodeBlock
                  id="first-vm"
                  language="bash"
                  code={`# Login to your account
zentry auth login

# Create a new project
zentry projects create "My First Project"

# Launch a VM
zentry vms create \\
  --name "web-server" \\
  --type "small" \\
  --image "ubuntu-22.04"`}
                />
              </div>
            </div>

            <div className="bg-primary-600/10 border border-primary-600/20 rounded-lg p-6 mt-8">
              <h3 className="text-lg font-semibold mb-2 flex items-center">
                <Book className="w-5 h-5 mr-2" />
                Next Steps
              </h3>
              <ul className="space-y-2 text-gray-300">
                <li>• Learn about <button onClick={() => setActiveSection('authentication')} className="text-primary-400 hover:underline">Authentication</button></li>
                <li>• Explore the <button onClick={() => setActiveSection('api-reference')} className="text-primary-400 hover:underline">API Reference</button></li>
                <li>• Set up <button onClick={() => setActiveSection('vm-management')} className="text-primary-400 hover:underline">VM Management</button></li>
              </ul>
            </div>
          </div>
        )

      case 'authentication':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">Authentication</h1>
            <p className="text-gray-400 mb-8">
              Zentry uses JWT tokens for API authentication. Here's how to get started.
            </p>

            <h2 className="text-2xl font-semibold mb-4">API Authentication</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Login</h3>
                <p className="text-gray-400 mb-4">
                  Authenticate with your email and password to get an access token.
                </p>
                <CodeBlock
                  id="auth-login"
                  language="curl"
                  code={`curl -X POST "https://api.zentry.cloud/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "your@email.com",
    "password": "your-password"
  }'`}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Using the Token</h3>
                <p className="text-gray-400 mb-4">
                  Include the JWT token in the Authorization header for all API requests.
                </p>
                <CodeBlock
                  id="auth-header"
                  language="curl"
                  code={`curl -X GET "https://api.zentry.cloud/vms" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"`}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">JavaScript Example</h3>
                <CodeBlock
                  id="js-auth"
                  language="javascript"
                  code={`// Login and store token
const response = await fetch('https://api.zentry.cloud/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'your@email.com',
    password: 'your-password'
  })
});

const { access_token } = await response.json();
localStorage.setItem('zentry_token', access_token);

// Use token for API calls
const vmsResponse = await fetch('https://api.zentry.cloud/vms', {
  headers: {
    'Authorization': \`Bearer \${access_token}\`
  }
});`}
                />
              </div>
            </div>
          </div>
        )

      case 'api-reference':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">API Reference</h1>
            <p className="text-gray-400 mb-8">
              Complete reference for the Zentry Cloud REST API.
            </p>

            <div className="bg-gray-900 rounded-lg p-6 mb-8">
              <h3 className="text-lg font-semibold mb-2">Base URL</h3>
              <code className="text-primary-400">https://api.zentry.cloud</code>
            </div>

            <h2 className="text-2xl font-semibold mb-4">Endpoints</h2>

            <div className="space-y-8">
              {/* Authentication */}
              <div>
                <h3 className="text-xl font-semibold mb-4 text-primary-400">Authentication</h3>
                <div className="space-y-4">
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">POST</span>
                      <code>/auth/signup</code>
                    </div>
                    <p className="text-gray-400 text-sm">Create a new user account</p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">POST</span>
                      <code>/auth/login</code>
                    </div>
                    <p className="text-gray-400 text-sm">Authenticate user and get access token</p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">GET</span>
                      <code>/auth/me</code>
                    </div>
                    <p className="text-gray-400 text-sm">Get current user information</p>
                  </div>
                </div>
              </div>

              {/* Projects */}
              <div>
                <h3 className="text-xl font-semibold mb-4 text-primary-400">Projects</h3>
                <div className="space-y-4">
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">GET</span>
                      <code>/projects</code>
                    </div>
                    <p className="text-gray-400 text-sm">List all projects</p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">POST</span>
                      <code>/projects</code>
                    </div>
                    <p className="text-gray-400 text-sm">Create a new project</p>
                  </div>
                </div>
              </div>

              {/* VMs */}
              <div>
                <h3 className="text-xl font-semibold mb-4 text-primary-400">Virtual Machines</h3>
                <div className="space-y-4">
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">GET</span>
                      <code>/vms</code>
                    </div>
                    <p className="text-gray-400 text-sm">List all virtual machines</p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">POST</span>
                      <code>/vms</code>
                    </div>
                    <p className="text-gray-400 text-sm">Create a new virtual machine</p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-red-600 text-white px-2 py-1 rounded text-xs">DELETE</span>
                      <code>/vms/{'{id}'}</code>
                    </div>
                    <p className="text-gray-400 text-sm">Delete a virtual machine</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 p-6 bg-primary-600/10 border border-primary-600/20 rounded-lg">
              <h3 className="text-lg font-semibold mb-2 flex items-center">
                <ExternalLink className="w-5 h-5 mr-2" />
                Interactive API Explorer
              </h3>
              <p className="text-gray-400 mb-4">
                Try out the API endpoints with our interactive documentation.
              </p>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                <Button>Open API Docs</Button>
              </a>
            </div>
          </div>
        )

      case 'cli-tools':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">CLI Tools</h1>
            <p className="text-gray-400 mb-8">
              The Zentry CLI provides a powerful command-line interface for managing your cloud infrastructure.
            </p>

            <h2 className="text-2xl font-semibold mb-4">Installation</h2>
            <CodeBlock
              id="cli-install"
              language="bash"
              code={`# Install via npm (recommended)
npm install -g @zentry/cli

# Install via curl
curl -sSL https://cli.zentry.cloud/install.sh | bash

# Verify installation
zentry --version`}
            />

            <h2 className="text-2xl font-semibold mb-4 mt-8">Authentication</h2>
            <CodeBlock
              id="cli-auth"
              language="bash"
              code={`# Login to your account
zentry auth login

# Check authentication status
zentry auth status

# Logout
zentry auth logout`}
            />

            <h2 className="text-2xl font-semibold mb-4 mt-8">Common Commands</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Project Management</h3>
                <CodeBlock
                  id="cli-projects"
                  language="bash"
                  code={`# List projects
zentry projects list

# Create a project
zentry projects create "My Project" --description "Project description"

# Delete a project
zentry projects delete <project-id>`}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">VM Management</h3>
                <CodeBlock
                  id="cli-vms"
                  language="bash"
                  code={`# List VMs
zentry vms list

# Create a VM
zentry vms create \\
  --name "web-server" \\
  --type "small" \\
  --image "ubuntu-22.04" \\
  --project-id <project-id>

# Start a VM
zentry vms start <vm-id>

# Stop a VM
zentry vms stop <vm-id>

# Delete a VM
zentry vms delete <vm-id>`}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">SSH Access</h3>
                <CodeBlock
                  id="cli-ssh"
                  language="bash"
                  code={`# SSH into a VM
zentry ssh <vm-id>

# SSH with custom user
zentry ssh <vm-id> --user ubuntu

# Copy files to VM
zentry scp local-file.txt <vm-id>:/remote/path/`}
                />
              </div>
            </div>
          </div>
        )

      case 'vm-management':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">VM Management</h1>
            <p className="text-gray-400 mb-8">
              Learn how to create, manage, and scale virtual machines on Zentry Cloud.
            </p>

            <h2 className="text-2xl font-semibold mb-4">Instance Types</h2>
            <div className="overflow-x-auto mb-8">
              <table className="w-full bg-gray-900 rounded-lg">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-4 px-4">Type</th>
                    <th className="text-left py-4 px-4">vCPU</th>
                    <th className="text-left py-4 px-4">Memory</th>
                    <th className="text-left py-4 px-4">Storage</th>
                    <th className="text-left py-4 px-4">Use Case</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-800">
                    <td className="py-4 px-4 font-semibold">Small</td>
                    <td className="py-4 px-4">1</td>
                    <td className="py-4 px-4">1GB</td>
                    <td className="py-4 px-4">25GB</td>
                    <td className="py-4 px-4 text-gray-400">Development, testing</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-4 px-4 font-semibold">Medium</td>
                    <td className="py-4 px-4">2</td>
                    <td className="py-4 px-4">4GB</td>
                    <td className="py-4 px-4">80GB</td>
                    <td className="py-4 px-4 text-gray-400">Web applications</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-4 px-4 font-semibold">Large</td>
                    <td className="py-4 px-4">4</td>
                    <td className="py-4 px-4">8GB</td>
                    <td className="py-4 px-4">160GB</td>
                    <td className="py-4 px-4 text-gray-400">Production workloads</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-4 font-semibold">XLarge</td>
                    <td className="py-4 px-4">8</td>
                    <td className="py-4 px-4">16GB</td>
                    <td className="py-4 px-4">320GB</td>
                    <td className="py-4 px-4 text-gray-400">High-performance apps</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h2 className="text-2xl font-semibold mb-4">Creating a VM</h2>
            <CodeBlock
              id="create-vm-api"
              language="curl"
              code={`curl -X POST "https://api.zentry.cloud/vms" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "my-web-server",
    "instance_type": "medium",
    "image": "ubuntu-22.04",
    "project_id": "project-uuid"
  }'`}
            />

            <h2 className="text-2xl font-semibold mb-4 mt-8">Available Images</h2>
            <div className="grid md:grid-cols-2 gap-4 mb-8">
              <div className="bg-gray-900 rounded-lg p-4">
                <h3 className="font-semibold mb-2">Ubuntu</h3>
                <ul className="text-gray-400 space-y-1">
                  <li>• ubuntu-22.04 (LTS)</li>
                  <li>• ubuntu-20.04 (LTS)</li>
                </ul>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <h3 className="font-semibold mb-2">CentOS</h3>
                <ul className="text-gray-400 space-y-1">
                  <li>• centos-8</li>
                  <li>• centos-7</li>
                </ul>
              </div>
            </div>

            <h2 className="text-2xl font-semibold mb-4">VM Lifecycle</h2>
            <div className="space-y-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <h3 className="font-semibold mb-2">States</h3>
                <ul className="text-gray-400 space-y-1">
                  <li>• <span className="text-yellow-400">Creating</span> - VM is being provisioned</li>
                  <li>• <span className="text-green-400">Running</span> - VM is active and accessible</li>
                  <li>• <span className="text-gray-400">Stopped</span> - VM is stopped but can be restarted</li>
                  <li>• <span className="text-red-400">Terminated</span> - VM is permanently deleted</li>
                </ul>
              </div>
            </div>
          </div>
        )

      case 'storage':
        return (
          <div>
            <h1 className="text-4xl font-bold mb-6">Storage</h1>
            <p className="text-gray-400 mb-8">
              Zentry provides S3-compatible object storage and persistent block storage for your applications.
            </p>

            <h2 className="text-2xl font-semibold mb-4">Object Storage</h2>
            <p className="text-gray-400 mb-4">
              S3-compatible object storage for files, backups, and static assets.
            </p>

            <CodeBlock
              id="s3-example"
              language="javascript"
              code={`// Using AWS SDK
import AWS from 'aws-sdk';

const s3 = new AWS.S3({
  endpoint: 'https://storage.zentry.cloud',
  accessKeyId: 'your-access-key',
  secretAccessKey: 'your-secret-key',
  s3ForcePathStyle: true
});

// Upload a file
const uploadParams = {
  Bucket: 'my-bucket',
  Key: 'my-file.txt',
  Body: 'Hello, Zentry!'
};

s3.upload(uploadParams, (err, data) => {
  if (err) console.error(err);
  else console.log('Upload successful:', data.Location);
});`}
            />

            <h2 className="text-2xl font-semibold mb-4 mt-8">Block Storage</h2>
            <p className="text-gray-400 mb-4">
              Persistent block storage that can be attached to your VMs.
            </p>

            <CodeBlock
              id="block-storage"
              language="bash"
              code={`# Create a volume
zentry volumes create --name "my-volume" --size 100GB

# Attach to VM
zentry volumes attach <volume-id> <vm-id>

# Mount in VM
sudo mkdir /mnt/data
sudo mount /dev/sdb /mnt/data`}
            />

            <h2 className="text-2xl font-semibold mb-4 mt-8">Backup & Snapshots</h2>
            <CodeBlock
              id="snapshots"
              language="bash"
              code={`# Create a snapshot
zentry snapshots create <vm-id> --name "backup-$(date +%Y%m%d)"

# List snapshots
zentry snapshots list

# Restore from snapshot
zentry vms create-from-snapshot <snapshot-id>`}
            />
          </div>
        )

      default:
        return <div>Section not found</div>
    }
  }

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
            <Link href="/pricing">
              <Button variant="secondary" size="sm">View Pricing</Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="pt-24 flex">
        {/* Sidebar */}
        <div className="w-64 fixed h-full bg-gray-900 border-r border-gray-800 p-6">
          <h2 className="text-lg font-semibold mb-6">Documentation</h2>
          <nav className="space-y-2">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full text-left px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                {section.icon}
                <span>{section.title}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="ml-64 flex-1 p-8">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-4xl"
          >
            {renderContent()}
          </motion.div>
        </div>
      </div>
    </div>
  )
}