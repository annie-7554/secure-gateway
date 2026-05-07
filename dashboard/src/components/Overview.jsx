import React from 'react'

function Overview({ data }) {
  const { overallStats, gates } = data

  const getRiskColor = (riskLevel) => {
    if (riskLevel.includes('high')) return 'risk-high'
    if (riskLevel.includes('moderate')) return 'risk-moderate'
    return 'risk-low'
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>Dashboard Overview</h2>

      <div className="grid">
        <div className="card stat-card">
          <div className="stat-label">PRs Scanned</div>
          <div className="stat-value">{overallStats.totalPRsScanned}</div>
          <div className="stat-label">Total this month</div>
        </div>

        <div className="card stat-card">
          <div className="stat-label">Current Risk Level</div>
          <div className={`stat-value ${getRiskColor(overallStats.avgRiskLevel)}`}>
            {overallStats.avgRiskLevel}
          </div>
          <div className="stat-label">Pipeline average</div>
        </div>

        <div className="card stat-card">
          <div className="stat-label">Critical Issues</div>
          <div style={{ color: '#ef4444' }} className="stat-value">
            {overallStats.criticalFindings}
          </div>
          <div className="stat-label">Needs immediate attention</div>
        </div>
      </div>

      <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Severity Breakdown</h3>
      <div className="grid">
        <div className="card">
          <div className="stat-label">High Severity</div>
          <div style={{ color: '#f97316', fontSize: '2rem', fontWeight: 'bold', margin: '0.5rem 0' }}>
            {overallStats.highFindings}
          </div>
        </div>

        <div className="card">
          <div className="stat-label">Medium Severity</div>
          <div style={{ color: '#eab308', fontSize: '2rem', fontWeight: 'bold', margin: '0.5rem 0' }}>
            {overallStats.mediumFindings}
          </div>
        </div>

        <div className="card">
          <div className="stat-label">Low Severity</div>
          <div style={{ color: '#22c55e', fontSize: '2rem', fontWeight: 'bold', margin: '0.5rem 0' }}>
            {overallStats.lowFindings}
          </div>
        </div>
      </div>

      <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Security Gates Status</h3>
      <div>
        {gates.map(gate => (
          <div key={gate.id} className="gate-card">
            <div className="gate-info">
              <h3>{gate.name}</h3>
              <div className="gate-status">
                <span>Last check: {new Date(gate.timestamp).toLocaleString()}</span>
                <span>•</span>
                <span className={`risk-${gate.riskLevel.split(' ')[0]}`}>
                  {gate.riskLevel}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div>
                <span className={`status-badge status-${gate.status}`}>
                  {gate.status.toUpperCase()}
                </span>
              </div>
              <div style={{ color: '#94a3b8', minWidth: '100px', textAlign: 'right' }}>
                {gate.findings} finding{gate.findings !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Overview
