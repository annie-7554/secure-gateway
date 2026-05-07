import React from 'react'
import Overview from './Overview'
import SecurityGates from './SecurityGates'
import RecentPRs from './RecentPRs'
import './Dashboard.css'

function Dashboard({ data, activeTab }) {
  return (
    <div className="content">
      {activeTab === 'overview' && <Overview data={data} />}
      {activeTab === 'gates' && <SecurityGates gates={data.gates} />}
      {activeTab === 'prs' && <RecentPRs prs={data.recentPRs} />}
    </div>
  )
}

export default Dashboard
