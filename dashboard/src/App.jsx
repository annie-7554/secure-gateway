import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [mockData, setMockData] = useState(null)

  useEffect(() => {
    // Simulate loading data from API
    const data = {
      gates: [
        {
          id: 'gate1',
          name: 'Gate 1: Code Security',
          status: 'pass',
          riskLevel: 'moderate risk',
          findings: 5,
          timestamp: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: 'gate2',
          name: 'Gate 2: Build Security',
          status: 'pass',
          riskLevel: 'low risk',
          findings: 2,
          timestamp: new Date(Date.now() - 7200000).toISOString()
        },
        {
          id: 'gate3',
          name: 'Gate 3: Deployment',
          status: 'pending',
          riskLevel: 'moderate risk',
          findings: 3,
          timestamp: new Date(Date.now() - 10800000).toISOString()
        }
      ],
      recentPRs: [
        {
          id: 'pr-123',
          title: 'feat: Add user authentication',
          author: 'john-dev',
          status: 'advisory-posted',
          findings: 3,
          riskLevel: 'moderate risk'
        },
        {
          id: 'pr-122',
          title: 'fix: Update dependencies',
          author: 'jane-dev',
          status: 'merged',
          findings: 2,
          riskLevel: 'low risk'
        },
        {
          id: 'pr-121',
          title: 'chore: Refactor logging',
          author: 'bob-dev',
          status: 'merged',
          findings: 0,
          riskLevel: 'low risk'
        }
      ],
      overallStats: {
        totalPRsScanned: 347,
        avgRiskLevel: 'moderate risk',
        criticalFindings: 12,
        highFindings: 45,
        mediumFindings: 89,
        lowFindings: 234
      }
    }
    setMockData(data)
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 Security Advisor Dashboard</h1>
          <p>AI-Assisted DevSecOps Pipeline Monitoring</p>
        </div>
      </header>

      <nav className="tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'gates' ? 'active' : ''}`}
          onClick={() => setActiveTab('gates')}
        >
          Security Gates
        </button>
        <button 
          className={`tab ${activeTab === 'prs' ? 'active' : ''}`}
          onClick={() => setActiveTab('prs')}
        >
          Recent PRs
        </button>
      </nav>

      {mockData && (
        <Dashboard 
          data={mockData} 
          activeTab={activeTab}
        />
      )}
    </div>
  )
}

export default App
