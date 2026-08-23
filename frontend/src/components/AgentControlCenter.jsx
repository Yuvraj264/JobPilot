import React, { useState, useEffect } from 'react'

export default function AgentControlCenter({ userId }) {
  const [status, setStatus] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [interventions, setInterventions] = useState([])
  const [mode, setMode] = useState('AUTONOMOUS_WITH_REVIEW')
  
  // Simulator states
  const [simJobId, setSimJobId] = useState('')
  const [simulationResult, setSimulationResult] = useState(null)
  
  // Details dialog / "Why?" modal states
  const [selectedDecision, setSelectedDecision] = useState(null)
  
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/agent/status', { headers: { 'X-User-Id': userId } })
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
        setMode(data.mode)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchDecisions = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/agent/decisions', { headers: { 'X-User-Id': userId } })
      if (res.ok) setDecisions(await res.json())
    } catch (err) {
      console.error(err)
    }
  }

  const fetchInterventions = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/agent/interventions', { headers: { 'X-User-Id': userId } })
      if (res.ok) setInterventions(await res.json())
    } catch (err) {
      console.error(err)
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    await Promise.all([fetchStatus(), fetchDecisions(), fetchInterventions()])
    setLoading(false)
  }

  useEffect(() => {
    refreshAll()
  }, [userId])

  const handleModeChange = async (newMode) => {
    try {
      const res = await fetch('http://localhost:8000/api/agent/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      })
      if (res.ok) {
        setMessage(`Agent mode updated to: ${newMode}`)
        setMode(newMode)
        fetchStatus()
      }
    } catch (err) {
      console.error(err)
      setMessage('Error updating operational mode.')
    }
  }

  const runSimulation = async () => {
    if (!simJobId) {
      setMessage('Provide a Job ID to run simulation planning.')
      return
    }
    setSimulationResult(null)
    try {
      const res = await fetch('http://localhost:8000/api/agent/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify({ job_id: parseInt(simJobId) })
      })
      if (res.ok) {
        setSimulationResult(await res.json())
        setMessage('Simulation planning trace compiled.')
      } else {
        const err = await res.json()
        setMessage(`Simulation failed: ${err.detail || 'check logs'}`)
      }
    } catch (err) {
      console.error(err)
      setMessage('Error triggering simulation.')
    }
  }

  const resolveIntervention = async (eventId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/screening/interventions/${eventId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution_data: {} })
      })
      if (res.ok) {
        setMessage('Intervention resolved successfully.')
        fetchInterventions()
      }
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      
      {/* Safety Banner */}
      <div style={{
        background: '#fffbeb',
        color: '#92400e',
        border: '1px solid #fde68a',
        padding: '0.75rem 1.25rem',
        borderRadius: '8px',
        fontSize: '0.85rem',
        fontWeight: 'bold',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        🛡️ <span>Agent decisions are constrained by your settings, platform capabilities, and safety policies.</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0f172a' }}>🧠 Agent Decision Engine</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b' }}>
            Monitor autonomous execution traces, calibrate modes, and simulate application gates.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Operational Mode:</label>
          <select
            value={mode}
            onChange={(e) => handleModeChange(e.target.value)}
            style={{ padding: '0.45rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', cursor: 'pointer' }}
          >
            <option value="OBSERVE">Observe (Planning only, zero actions)</option>
            <option value="PLAN">Plan (Prepares previews, no submits)</option>
            <option value="ASSIST">Assist (Safe edits, asks user, no auto submits)</option>
            <option value="AUTONOMOUS_WITH_REVIEW">Autonomous with Review (Queues for approval)</option>
          </select>
        </div>
      </div>

      {message && (
        <div style={{
          padding: '1rem',
          background: '#eff6ff',
          color: '#1e40af',
          borderRadius: '8px',
          border: '1px solid #bfdbfe',
          marginBottom: '1.5rem',
          fontWeight: '500'
        }}>
          {message}
        </div>
      )}

      {/* --- GRID LAYOUT --- */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
        
        {/* Main Panel Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Status Overview Card */}
          {status && (
            <div style={{
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '16px',
              padding: '1.5rem',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '1rem'
            }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold', display: 'block', textTransform: 'uppercase' }}>Recent Decision</span>
                <strong style={{ fontSize: '1.2rem', color: '#0f172a' }}>{status.recent_decision}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold', display: 'block', textTransform: 'uppercase' }}>Confidence</span>
                <strong style={{ fontSize: '1.2rem', color: '#0f172a' }}>{Math.round(status.confidence * 100)}%</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold', display: 'block', textTransform: 'uppercase' }}>Permitted Action</span>
                <strong style={{ fontSize: '1.2rem', color: '#4f46e5' }}>{status.selected_action}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold', display: 'block', textTransform: 'uppercase' }}>Blocker Status</span>
                <strong style={{ fontSize: '1.2rem', color: status.blockers?.length > 0 ? '#ef4444' : '#22c55e' }}>
                  {status.blockers?.length > 0 ? 'Blocked' : 'Clear'}
                </strong>
              </div>
            </div>
          )}

          {/* Historical Decisions list */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
          }}>
            <h3 style={{ margin: '0 0 1.25rem 0' }}>Decision History & Diagnostics</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>Time</th>
                  <th style={{ padding: '0.5rem' }}>Decision</th>
                  <th style={{ padding: '0.5rem' }}>Confidence</th>
                  <th style={{ padding: '0.5rem' }}>Proposed Action</th>
                  <th style={{ padding: '0.5rem' }}>Policy Status</th>
                  <th style={{ padding: '0.5rem' }}>Why?</th>
                </tr>
              </thead>
              <tbody>
                {decisions.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: '1rem', color: '#64748b', textAlign: 'center' }}>No historical agent decisions processed yet.</td>
                  </tr>
                ) : (
                  decisions.map((r) => (
                    <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.5rem', color: '#64748b' }}>{new Date(r.created_at).toLocaleTimeString()}</td>
                      <td style={{ padding: '0.5rem', fontWeight: 'bold', color: '#0f172a' }}>{r.decision}</td>
                      <td style={{ padding: '0.5rem' }}>{Math.round(r.confidence * 100)}%</td>
                      <td style={{ padding: '0.5rem', color: '#4f46e5' }}>{r.selected_action}</td>
                      <td style={{ padding: '0.5rem', fontWeight: 'bold', color: r.policy_result === 'ALLOWED' ? '#22c55e' : '#ef4444' }}>{r.policy_result}</td>
                      <td style={{ padding: '0.5rem' }}>
                        <button
                          onClick={() => setSelectedDecision(r)}
                          style={{
                            background: '#f1f5f9',
                            border: '1px solid #cbd5e1',
                            padding: '0.25rem 0.6rem',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: '500'
                          }}
                        >
                          [Why?]
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Interactive Simulator trace panel */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
          }}>
            <h3 style={{ margin: '0 0 0.5rem 0' }}>Interactive Agent Simulator</h3>
            <p style={{ margin: '0 0 1.25rem 0', color: '#64748b', fontSize: '0.85rem' }}>
              Run dry-run simulation traces on target jobs to visualize policy checks and gate resolutions without creating database writes.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <input
                type="number"
                value={simJobId}
                onChange={(e) => setSimJobId(e.target.value)}
                placeholder="Enter Job ID"
                style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', width: '160px' }}
              />
              <button
                onClick={runSimulation}
                style={{
                  background: '#4f46e5',
                  color: '#fff',
                  border: 'none',
                  padding: '0.45rem 1rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                🔬 Simulate Agent
              </button>
            </div>

            {simulationResult && (
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                padding: '1rem',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontFamily: 'monospace'
              }}>
                <strong style={{ color: '#0f172a' }}>Simulation Dry-Run Trace:</strong>
                <p><strong>Decision:</strong> {simulationResult.decision} ({Math.round(simulationResult.confidence * 100)}% confidence)</p>
                <p><strong>Reasoning:</strong> {simulationResult.reasoning?.join(' | ')}</p>
                <p><strong>Safety / Policy checks:</strong></p>
                <ul style={{ margin: '0.5rem 0', paddingLeft: '1.25rem' }}>
                  {Object.entries(simulationResult.policy_checks || {}).map(([action, detail]) => (
                    <li key={action}>
                      <strong>{action}:</strong> <span style={{ color: detail.status === 'ALLOWED' ? '#15803d' : '#b91c1c' }}>{detail.status}</span> ({detail.reason})
                    </li>
                  ))}
                </ul>
                <p><strong>Final Safe Action:</strong> <span style={{ color: '#4f46e5', fontWeight: 'bold' }}>{simulationResult.final_action}</span></p>
              </div>
            )}
          </div>

        </div>

        {/* Sidebar Interventions Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Active human intervention tasks */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
          }}>
            <h3 style={{ margin: '0 0 1.25rem 0' }}>Escalation & Interventions</h3>
            {interventions.length === 0 ? (
              <div style={{ padding: '1rem', color: '#64748b', background: '#f8fafc', borderRadius: '8px', textAlign: 'center', fontSize: '0.85rem' }}>
                All systems healthy. No active interventions pending.
              </div>
            ) : (
              interventions.map((evt) => (
                <div
                  key={evt.id}
                  style={{
                    background: '#fff1f2',
                    border: '1px solid #fecdd3',
                    padding: '0.85rem',
                    borderRadius: '8px',
                    color: '#9f1239',
                    marginBottom: '0.75rem',
                    fontSize: '0.85rem'
                  }}
                >
                  <div style={{ fontWeight: 'bold', display: 'flex', justifyContent: 'space-between' }}>
                    <span>⚠️ {evt.intervention_type}</span>
                    <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.35rem', background: '#ffe4e6', borderRadius: '4px' }}>
                      {evt.priority}
                    </span>
                  </div>
                  <div style={{ marginTop: '0.25rem', marginBottom: '0.5rem' }}>{evt.message}</div>
                  <button
                    onClick={() => resolveIntervention(evt.id)}
                    style={{
                      background: '#9f1239',
                      color: '#fff',
                      border: 'none',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 'bold'
                    }}
                  >
                    Resolve Task
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Audit Metrics Panel */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
            textAlign: 'center'
          }}>
            <h4 style={{ margin: '0 0 0.5rem 0' }}>Decisions Acceptance</h4>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#4f46e5' }}>98.2%</div>
            <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.8rem' }}>
              Proposals validated and permitted through policy gates.
            </p>
          </div>

        </div>

      </div>

      {/* --- Why? Explanation Details Box modal overlay --- */}
      {selectedDecision && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.4)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#ffffff',
            width: '460px',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#0f172a' }}>Decision Breakdown</h3>
            <p><strong>Decision Outcome:</strong> {selectedDecision.decision}</p>
            <p><strong>Permitted Action:</strong> {selectedDecision.selected_action}</p>
            <p><strong>Reasoning Evidence:</strong></p>
            <ul style={{ margin: '0.5rem 0', paddingLeft: '1.25rem' }}>
              {selectedDecision.reasoning?.map((reason, idx) => (
                <li key={idx} style={{ marginBottom: '0.25rem' }}>{reason}</li>
              ))}
            </ul>
            {selectedDecision.blockers?.length > 0 && (
              <div style={{ marginTop: '0.75rem', background: '#ffe4e6', color: '#9f1239', padding: '0.5rem', borderRadius: '6px', fontSize: '0.85rem' }}>
                <strong>Active Blockers:</strong> {selectedDecision.blockers.join(', ')}
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button
                onClick={() => setSelectedDecision(null)}
                style={{
                  background: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  padding: '0.45rem 1rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
