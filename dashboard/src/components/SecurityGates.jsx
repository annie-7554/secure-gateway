import React from 'react'

function SecurityGates({ gates }) {
  const getRiskColor = (riskLevel) => {
    if (riskLevel.includes('high')) return 'risk-high'
    if (riskLevel.includes('moderate')) return 'risk-moderate'
    return 'risk-low'
  }

  const getStatusColor = (status) => {
    if (status === 'pass') return 'status-pass'
    if (status === 'fail') return 'status-fail'
    return 'status-pending'
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>Security Gates Details</h2>

      {gates.map(gate => (
        <div key={gate.id} style={{ marginBottom: '1.5rem' }}>
          <div className="gate-card">
            <div className="gate-info">
              <h3>{gate.name}</h3>
              <div className="gate-status">
                <span>Last check: {new Date(gate.timestamp).toLocaleString()}</span>
                <span>•</span>
                <span className={getRiskColor(gate.riskLevel)}>
                  {gate.riskLevel}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span className={`status-badge ${getStatusColor(gate.status)}`}>
                {gate.status.toUpperCase()}
              </span>
              <div style={{ color: '#94a3b8', minWidth: '100px', textAlign: 'right' }}>
                {gate.findings} finding{gate.findings !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          {/* Sample findings */}
          <div style={{ marginLeft: '1.5rem', marginTop: '1rem' }}>
            <h4 style={{ color: '#cbd5e1', marginBottom: '0.75rem' }}>Top Findings:</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {gate.id === 'gate1' && (
                <>
                  <div style={{ padding: '0.75rem', background: '#1e293b', borderRadius: '4px', borderLeft: '3px solid #ef4444' }}>
                    <strong style={{ color: '#ef4444' }}>SQL Injection Risk</strong>
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem' }}>User input in SQL query - use parameterized queries</p>
                  </div>
                  <div style={{ padding: '0.75rem', background: '#1e293b', borderRadius: '4px', borderLeft: '3px solid #f97316' }}>
                    <strong style={{ color: '#f97316' }}>Weak Cryptography</strong>
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem' }}>MD5 is cryptographically broken - use SHA256</p>
                  </div>
                </>
              )}
              {gate.id === 'gate2' && (
                <>
                  <div style={{ padding: '0.75rem', background: '#1e293b', borderRadius: '4px', borderLeft: '3px solid #f97316' }}>
                    <strong style={{ color: '#f97316' }}>OS Package Vulnerability</strong>
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem' }}>Critical CVE in base image - rebuild from latest</p>
                  </div>
                </>
              )}
              {gate.id === 'gate3' && (
                <>
                  <div style={{ padding: '0.75rem', background: '#1e293b', borderRadius: '4px', borderLeft: '3px solid #f97316' }}>
                    <strong style={{ color: '#f97316' }}>RBAC Configuration</strong>
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem' }}>Service account has elevated permissions</p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SecurityGates
