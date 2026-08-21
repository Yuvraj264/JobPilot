import { useState, useEffect } from 'react'
import ProfileManager from './components/ProfileManager'
import ResumeManager from './components/ResumeManager'
import JobDiscoveryManager from './components/JobDiscoveryManager'
import MatchDashboardManager from './components/MatchDashboardManager'
import AutomationMonitorManager from './components/AutomationMonitorManager'

function App() {
  const [status, setStatus] = useState('checking...')
  const [dbStatus, setDbStatus] = useState('unknown')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => {
        setStatus(data.status || 'online')
        setDbStatus(data.database?.status || 'unknown')
      })
      .catch((err) => {
        console.error('Failed to reach backend health endpoint:', err)
        setStatus('unreachable (backend offline)')
      })
  }, [])

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: '950px', margin: '0 auto' }}>
      <h1>JobPilot</h1>
      <p style={{ fontSize: '1.1rem', color: '#555' }}>
        Phase 6: Mock Application Environment & Application Agent Foundation
      </p>
      <div style={{ marginTop: '1rem', padding: '0.8rem', border: '1px solid #ccc', borderRadius: '8px', background: '#f9f9f9' }}>
        <p style={{ margin: '0.2rem 0' }}><strong>Backend status:</strong> {status}</p>
        <p style={{ margin: '0.2rem 0' }}><strong>Database status:</strong> {dbStatus}</p>
      </div>

      <ProfileManager />
      <ResumeManager />
      <JobDiscoveryManager />
      <MatchDashboardManager />
      <AutomationMonitorManager />
    </div>
  )
}

export default App
