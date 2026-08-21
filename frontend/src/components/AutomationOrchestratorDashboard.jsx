import { useState, useEffect } from 'react'

export default function AutomationOrchestratorDashboard() {
  const [orchestratorStatus, setOrchestratorStatus] = useState('IDLE')
  const [runs, setRuns] = useState([])
  const [health, setHealth] = useState(null)
  const [overview, setOverview] = useState(null)
  const [scheduler, setScheduler] = useState({ enabled: false, schedule_type: 'daily', scheduled_hour: 9, scheduled_minute: 0, selected_days: [] })
  const [reviewQueue, setReviewQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/orchestration/status')
      const data = await res.json()
      setOrchestratorStatus(data.status)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchRuns = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/orchestration/runs')
      const data = await res.json()
      setRuns(data.slice(0, 5))
    } catch (e) {
      console.error(e)
    }
  }

  const fetchHealth = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/automation/health')
      const data = await res.json()
      setHealth(data)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchOverview = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/analytics/overview')
      const data = await res.json()
      setOverview(data)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchScheduler = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/scheduler/status')
      const data = await res.json()
      setScheduler(data)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchReviewQueue = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/review/queue')
      const data = await res.json()
      setReviewQueue(data)
    } catch (e) {
      console.error(e)
    }
  }

  const refreshData = () => {
    fetchStatus()
    fetchRuns()
    fetchHealth()
    fetchOverview()
    fetchScheduler()
    fetchReviewQueue()
  }

  useEffect(() => {
    refreshData()
    const timer = setInterval(refreshData, 10000)
    return () => clearInterval(timer)
  }, [])

  const triggerRun = async () => {
    setLoading(true)
    setMsg('Starting orchestration run...')
    try {
      await fetch('http://localhost:8000/api/orchestration/run', { method: 'POST' })
      setMsg('Orchestration run started successfully!')
      setTimeout(() => setMsg(''), 3000)
      refreshData()
    } catch (e) {
      setMsg('Failed to start orchestrator: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const stopRun = async () => {
    setLoading(true)
    setMsg('Stopping orchestration run...')
    try {
      await fetch('http://localhost:8000/api/orchestration/stop', { method: 'POST' })
      setMsg('Orchestration run cancelled.')
      setTimeout(() => setMsg(''), 3000)
      refreshData()
    } catch (e) {
      setMsg('Failed to stop run: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleScheduler = async () => {
    setLoading(true)
    const endpoint = scheduler.enabled ? 'stop' : 'start'
    try {
      await fetch(`http://localhost:8000/api/scheduler/${endpoint}`, { method: 'POST' })
      setMsg(`Scheduler successfully ${scheduler.enabled ? 'disabled' : 'enabled'}!`)
      setTimeout(() => setMsg(''), 3000)
      refreshData()
    } catch (e) {
      setMsg('Failed to update scheduler status: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      marginTop: '2rem',
      padding: '1.5rem',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.2)',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.1)',
      background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
      color: '#fff',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>🤖 Orchestration Control Center</h2>
        <span style={{
          backgroundColor: orchestratorStatus === 'RUNNING' ? '#2ecc71' : '#f39c12',
          padding: '0.4rem 0.8rem',
          borderRadius: '20px',
          fontSize: '0.85rem',
          fontWeight: 700,
          textTransform: 'uppercase'
        }}>{orchestratorStatus}</span>
      </div>

      {msg && <div style={{ marginTop: '1rem', padding: '0.6rem', borderRadius: '6px', background: 'rgba(255,255,255,0.2)', fontSize: '0.9rem' }}>{msg}</div>}

      {/* Control Buttons */}
      <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
        <button
          onClick={triggerRun}
          disabled={loading || orchestratorStatus === 'RUNNING'}
          style={{
            flex: 1, padding: '0.75rem', borderRadius: '8px', border: 'none', fontWeight: 600, fontSize: '0.95rem',
            backgroundColor: '#2ecc71', color: '#fff', cursor: 'pointer', transition: 'all 0.2s',
            opacity: orchestratorStatus === 'RUNNING' ? 0.6 : 1
          }}>
          🚀 Run Pipeline Now (Dry Run Preview)
        </button>
        <button
          onClick={stopRun}
          disabled={loading || orchestratorStatus === 'IDLE'}
          style={{
            flex: 1, padding: '0.75rem', borderRadius: '8px', border: 'none', fontWeight: 600, fontSize: '0.95rem',
            backgroundColor: '#e74c3c', color: '#fff', cursor: 'pointer', transition: 'all 0.2s',
            opacity: orchestratorStatus === 'IDLE' ? 0.6 : 1
          }}>
          🛑 Stop Orchestration
        </button>
      </div>

      {/* Scheduler Dashboard Card */}
      <div style={{
        marginTop: '1.5rem', padding: '1rem', borderRadius: '8px', background: 'rgba(255,255,255,0.1)',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>📅 Background Automation Scheduler</h3>
          <button
            onClick={toggleScheduler}
            style={{
              padding: '0.4rem 0.8rem', borderRadius: '6px', border: 'none', fontWeight: 600,
              backgroundColor: scheduler.enabled ? '#e74c3c' : '#2ecc71', color: '#fff', cursor: 'pointer'
            }}>
            {scheduler.enabled ? 'Disable' : 'Enable'} Scheduler
          </button>
        </div>
        <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', opacity: 0.85 }}>
          <strong>Mode:</strong> {scheduler.schedule_type.toUpperCase()} | <strong>Time:</strong> {String(scheduler.scheduled_hour).padStart(2, '0')}:{String(scheduler.scheduled_minute).padStart(2, '0')}
        </p>
      </div>

      {/* Analytics Conversion Funnel */}
      {overview && (
        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>📊 Application Funnel & Analytics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(255,255,255,0.1)', textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{overview.funnel.discovered}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>Jobs Discovered</div>
            </div>
            <div style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(255,255,255,0.1)', textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{overview.funnel.high_match}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>High Match (≥80)</div>
            </div>
            <div style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(255,255,255,0.1)', textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{overview.funnel.prepared}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>Packages Prepared</div>
            </div>
            <div style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(255,255,255,0.1)', textAlign: 'center' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{overview.funnel.submitted}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>Applications Submitted</div>
            </div>
          </div>
        </div>
      )}

      {/* Attention Required Review Queue */}
      {reviewQueue.length > 0 && (
        <div style={{
          marginTop: '1.5rem', padding: '1rem', borderRadius: '8px', background: '#ffeef0', color: '#d9383a'
        }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600 }}>⚠️ Attention Required review queue ({reviewQueue.length})</h3>
          <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.9rem' }}>
            {reviewQueue.map((item) => (
              <li key={item.id} style={{ marginBottom: '0.3rem' }}>
                Application #{item.id} waiting: status <strong>{item.status}</strong> (URL: {item.application_url})
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Historical Orchestrator runs list */}
      <div style={{ marginTop: '1.5rem' }}>
        <h3 style={{ margin: '0 0 0.8rem 0', fontSize: '1.1rem' }}>📜 Pipeline Execution Logs</h3>
        {runs.length === 0 ? (
          <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>No historical runs found.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {runs.map((run) => (
              <div key={run.id} style={{
                padding: '0.8rem', borderRadius: '6px', background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between',
                fontSize: '0.85rem'
              }}>
                <div>
                  <strong>Run #{run.id}</strong> | Trigger: {run.trigger_type} | Jobs: +{run.jobs_discovered} | Matched: {run.jobs_matched} | Submitted: {run.applications_submitted}
                </div>
                <span style={{
                  color: run.status === 'COMPLETED' ? '#2ecc71' : run.status === 'PARTIAL' ? '#3498db' : '#e74c3c',
                  fontWeight: 'bold'
                }}>{run.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
