import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/automation'

export default function AutomationMonitorManager() {
  const [runs, setRuns] = useState([])
  const [activeRun, setActiveRun] = useState(null)
  const [actionLogs, setActionLogs] = useState([])
  const [screenshots, setScreenshots] = useState([])
  
  const [starting, setStarting] = useState(false)
  const [message, setMessage] = useState('')

  const loadRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/runs`)
      if (res.ok) {
        const data = await res.json()
        setRuns(data)
        if (data.length > 0 && !activeRun) {
          inspectRun(data[0].id)
        }
      }
    } catch (err) {
      console.error('Error loading automation runs:', err)
    }
  }

  const inspectRun = async (runId) => {
    try {
      const resRun = await fetch(`${API_BASE}/runs/${runId}`)
      if (resRun.ok) setActiveRun(await resRun.json())

      const resLogs = await fetch(`${API_BASE}/runs/${runId}/actions`)
      if (resLogs.ok) setActionLogs(await resLogs.json())

      const resShots = await fetch(`${API_BASE}/runs/${runId}/screenshots`)
      if (resShots.ok) {
        const shotData = await resShots.json()
        setScreenshots(shotData.screenshots || [])
      }
    } catch (err) {
      console.error('Error inspecting run:', err)
    }
  }

  useEffect(() => {
    loadRuns()
  }, [])

  const handleStartAutomation = async () => {
    setStarting(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: 101 }),
      })
      if (res.ok) {
        const runRes = await res.json()
        setMessage(`Automation run #${runRes.id} initiated! State: ${runRes.state}`)
        loadRuns()
        inspectRun(runRes.id)
      } else {
        const errData = await res.json()
        setMessage(`Automation error: ${errData.detail || 'Failed to start automation'}`)
      }
    } catch (err) {
      setMessage('Failed to execute browser automation.')
    } finally {
      setStarting(false)
    }
  }

  const handleResumeRun = async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/runs/${runId}/resume`, { method: 'POST' })
      if (res.ok) {
        setMessage(`Run #${runId} resumed successfully!`)
        inspectRun(runId)
        loadRuns()
      }
    } catch (err) {
      console.error('Failed to resume run:', err)
    }
  }

  const getStateBadgeColor = (state, humanRequired) => {
    if (humanRequired || state === 'PAUSED') return { bg: '#fff3e0', text: '#ef6c00', border: '#ffe0b2' }
    if (state === 'READY_FOR_REVIEW' || state === 'COMPLETED') return { bg: '#e8f5e9', text: '#2e7d32', border: '#a5d6a7' }
    if (state === 'FAILED') return { bg: '#ffebee', text: '#c62828', border: '#ef9a9a' }
    return { bg: '#e3f2fd', text: '#1565c0', border: '#90caf9' }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Application Automation Agent</h2>

      {message && <div style={{ background: '#e8f5e9', padding: '0.6rem', marginBottom: '1rem', borderRadius: '4px', color: '#2e7d32' }}>{message}</div>}

      {/* Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', background: '#f8f9fa', padding: '0.8rem', borderRadius: '6px' }}>
        <div>
          <strong>Playwright Browser Automation Agent</strong> — Controlled local testbed execution (`/mock/apply/*`).
        </div>
        <button
          onClick={handleStartAutomation}
          disabled={starting}
          style={{ padding: '0.5rem 1.2rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {starting ? 'Running Browser Agent...' : 'Start Mock Automation Run'}
        </button>
      </div>

      {/* Active Run Overview */}
      {activeRun && (
        <div style={{ background: '#fff', border: '1px solid #ddd', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0 }}>
              Run #{activeRun.id} <span style={{ fontWeight: 'normal', fontSize: '0.9rem', color: '#666' }}>({activeRun.current_url || 'N/A'})</span>
            </h3>
            {(() => {
              const badge = getStateBadgeColor(activeRun.state, activeRun.human_intervention_required)
              return (
                <span style={{ fontSize: '0.85rem', fontWeight: 'bold', background: badge.bg, color: badge.text, border: `1px solid ${badge.border}`, padding: '4px 10px', borderRadius: '12px' }}>
                  {activeRun.state}
                </span>
              )
            })()}
          </div>

          {/* Human Intervention Banner */}
          {activeRun.human_intervention_required && (
            <div style={{ marginTop: '1rem', background: '#fff3e0', border: '1px solid #ffe0b2', padding: '0.8rem', borderRadius: '6px', color: '#e65100' }}>
              <strong>⚠ Human Intervention Required:</strong> {activeRun.pause_reason || 'Agent paused before action.'}
              <div style={{ marginTop: '0.5rem' }}>
                <button onClick={() => handleResumeRun(activeRun.id)} style={{ padding: '0.4rem 0.8rem', background: '#e65100', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '0.5rem' }}>
                  Resume Run
                </button>
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem', background: '#f9f9f9', padding: '0.8rem', borderRadius: '6px' }}>
            <div>Attempted: <strong>{activeRun.actions_attempted}</strong></div>
            <div>Completed: <strong style={{ color: 'green' }}>{activeRun.actions_completed}</strong></div>
            <div>Failed / Paused: <strong style={{ color: 'red' }}>{activeRun.actions_failed}</strong></div>
          </div>

          {/* Step Timeline & Action Audit Logs */}
          <h4 style={{ marginTop: '1.2rem' }}>Action Audit Timeline</h4>
          {actionLogs.length === 0 ? (
            <p style={{ color: '#777' }}>No action logs recorded for this run.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
              <thead>
                <tr style={{ background: '#f5f5f5', textAlign: 'left', fontSize: '0.85rem' }}>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>#</th>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>Action</th>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>Field Type</th>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>Selector</th>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>Result</th>
                  <th style={{ padding: '0.4rem', border: '1px solid #ddd' }}>Conf</th>
                </tr>
              </thead>
              <tbody>
                {actionLogs.map((log) => (
                  <tr key={log.id} style={{ fontSize: '0.85rem' }}>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd' }}>{log.id}</td>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd' }}><strong>{log.action_type}</strong></td>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd' }}>{log.field_type || 'N/A'}</td>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd', fontFamily: 'monospace' }}>{log.target_selector || '-'}</td>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd' }}>
                      <span style={{ color: log.result === 'SUCCESS' ? 'green' : log.result === 'PAUSED' ? 'orange' : 'red', fontWeight: 'bold' }}>
                        {log.result}
                      </span>
                    </td>
                    <td style={{ padding: '0.4rem', border: '1px solid #ddd' }}>{(log.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Screenshot Gallery Metadata */}
          {screenshots.length > 0 && (
            <div style={{ marginTop: '1.2rem' }}>
              <h4>Captured Step Screenshots ({screenshots.length})</h4>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {screenshots.map((s, idx) => (
                  <li key={idx} style={{ fontSize: '0.8rem', color: '#555', fontFamily: 'monospace' }}>
                    📷 {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Historical Runs List */}
      <h4>Automation Run History</h4>
      {runs.length === 0 ? (
        <p style={{ color: '#777' }}>No historical runs.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {runs.map((r) => (
            <li
              key={r.id}
              onClick={() => inspectRun(r.id)}
              style={{
                border: '1px solid #eee',
                padding: '0.6rem',
                marginBottom: '0.4rem',
                borderRadius: '4px',
                cursor: 'pointer',
                background: activeRun?.id === r.id ? '#e3f2fd' : '#fff',
                display: 'flex',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <strong>Run #{r.id}</strong> — State: <code>{r.state}</code>
              </div>
              <span style={{ fontSize: '0.8rem', color: '#666' }}>
                Completed: {r.actions_completed} | Failed: {r.actions_failed}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
