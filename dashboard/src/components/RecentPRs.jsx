import React from 'react'

function RecentPRs({ prs }) {
  const getRiskColor = (riskLevel) => {
    if (riskLevel.includes('high')) return 'risk-high'
    if (riskLevel.includes('moderate')) return 'risk-moderate'
    return 'risk-low'
  }

  const getStatusColor = (status) => {
    if (status === 'merged') return 'status-pass'
    if (status === 'advisory-posted') return 'status-pending'
    return 'status-fail'
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>Recent Pull Requests</h2>

      <div>
        {prs.map(pr => (
          <div key={pr.id} className="pr-row">
            <div className="pr-info">
              <h4>{pr.title}</h4>
              <div className="pr-meta">
                by {pr.author} • ID: {pr.id}
              </div>
            </div>
            <div className="pr-stats">
              <span className={`finding-badge ${getRiskColor(pr.riskLevel)}`}>
                {pr.riskLevel}
              </span>
              <span className="finding-badge">
                {pr.findings} finding{pr.findings !== 1 ? 's' : ''}
              </span>
              <span className={`status-badge ${getStatusColor(pr.status)}`}>
                {pr.status === 'merged' ? 'MERGED' : pr.status === 'advisory-posted' ? 'ADVISORY' : 'BLOCKED'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Sample PR with detailed comment */}
      <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#1e293b', borderRadius: '8px', border: '1px solid #334155' }}>
        <h3 style={{ marginBottom: '1rem' }}>Sample PR Advisory Comment</h3>
        <div style={{ 
          padding: '1rem', 
          background: '#0f172a', 
          borderRadius: '4px', 
          borderLeft: '4px solid #0ea5e9',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          lineHeight: '1.6',
          color: '#cbd5e1'
        }}>
          <div style={{ marginBottom: '0.5rem' }}><strong>🤖 Security Advisory</strong></div>
          <div style={{ marginBottom: '0.5rem' }}></div>
          <div><strong>Risk Assessment:</strong> moderate risk</div>
          <div><strong>Gate Status:</strong> FAIL</div>
          <div style={{ marginBottom: '0.5rem' }}></div>
          <div><strong>Summary:</strong> Found 1 high, 2 medium severity findings.</div>
          <div style={{ marginBottom: '0.5rem' }}></div>
          <div><strong>Key Findings:</strong></div>
          <div>  • [HIGH] SQL injection vulnerability in database.py:42</div>
          <div>  • [MEDIUM] Hardcoded secret in config.py:15</div>
          <div>  • [MEDIUM] Weak cryptography (MD5) in auth.py:78</div>
          <div style={{ marginBottom: '0.5rem' }}></div>
          <div><strong>Recommended Action:</strong> fix before deployment</div>
          <div style={{ marginBottom: '0.5rem' }}></div>
          <div><strong>Fix Steps:</strong></div>
          <div>  1. Use parameterized queries to prevent SQL injection</div>
          <div>  2. Move secrets to environment variables</div>
          <div>  3. Use SHA256 or bcrypt for password hashing</div>
          <div style={{ marginTop: '0.5rem', color: '#94a3b8', fontSize: '0.85rem' }}>
            <em>This is an advisory assessment. Security gates make the final decision.</em>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RecentPRs
