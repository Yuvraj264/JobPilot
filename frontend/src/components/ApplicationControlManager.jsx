import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function ApplicationControlManager() {
  const [applications, setApplications] = useState([])
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [selectedApp, setSelectedApp] = useState(null)
  
  // Validation, Timeline & Preview State
  const [validationResult, setValidationResult] = useState(null)
  const [userConfirmed, setUserConfirmed] = useState(false)
  const [approvalNotes, setApprovalNotes] = useState('')
  const [timeline, setTimeline] = useState([])
  const [actionPlan, setActionPlan] = useState([])
  const [browserState, setBrowserState] = useState(null)
  const [interventions, setInterventions] = useState([])
  const [executing, setExecuting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [appRes, pkgRes] = await Promise.all([
        fetch(`${API_BASE}/applications`),
        fetch(`${API_BASE}/application-packages`),
      ])
      if (appRes.ok) setApplications(await appRes.json())
      if (pkgRes.ok) setPackages(await pkgRes.json())
    } catch (err) {
      console.error('Failed to load application control data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateApplication = async (pkg) => {
    try {
      const res = await fetch(`${API_BASE}/applications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: pkg.job_id,
          source_resume_id: pkg.source_resume_id,
          tailored_resume_id: pkg.tailored_resume_id,
          application_package_id: pkg.id,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setMessage(`Application #${data.id} created from Package #${pkg.id}!`)
        loadData()
      }
    } catch (err) {
      console.error('Failed to create application:', err)
    }
  }

  const handleSelectApp = async (app) => {
    setSelectedApp(app)
    setUserConfirmed(false)
    setApprovalNotes('')
    setActionPlan([])
    setBrowserState(null)
    setInterventions([])
    await loadAppDetails(app.id)
  }

  const loadAppDetails = async (appId) => {
    try {
      const [valRes, timeRes, planRes, stateRes, interRes] = await Promise.all([
        fetch(`${API_BASE}/applications/${appId}/validate`, { method: 'POST' }),
        fetch(`${API_BASE}/applications/${appId}/timeline`),
        fetch(`${API_BASE}/applications/${appId}/action-plan`),
        fetch(`${API_BASE}/applications/${appId}/browser-state`),
        fetch(`${API_BASE}/applications/${appId}/interventions`),
      ])
      if (valRes.ok) setValidationResult(await valRes.json())
      if (timeRes.ok) {
        const tData = await timeRes.json()
        setTimeline(tData.timeline || [])
      }
      if (planRes.ok) {
        const pData = await planRes.json()
        setActionPlan(pData.plan || [])
      }
      if (stateRes.ok) setBrowserState(await stateRes.json())
      if (interRes.ok) setInterventions(await interRes.json())
    } catch (err) {
      console.error('Failed to load application details:', err)
    }
  }

  const handleRequestReview = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/review`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setMessage(`Application #${appId} status updated to ${data.status}!`)
        loadData()
        handleSelectApp(data)
      } else {
        const errData = await res.json()
        setMessage(`Review request failed: ${errData.detail}`)
      }
    } catch (err) {
      console.error('Failed to request review:', err)
    }
  }

  const handleApprove = async (appId) => {
    if (!userConfirmed) {
      setMessage('Explicit confirmation required: Please check the confirmation box.')
      return
    }
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_confirmed: true, notes: approvalNotes }),
      })
      if (res.ok) {
        const data = await res.json()
        setMessage(`Application #${appId} explicitly APPROVED by user!`)
        loadData()
        handleSelectApp(data)
      } else {
        const errData = await res.json()
        setMessage(`Approval failed: ${errData.detail}`)
      }
    } catch (err) {
      console.error('Failed to approve application:', err)
    }
  }

  const handleAuthorize = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/authorize-submission`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setMessage(`Submission Authorization token issued!`)
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      } else {
        const errData = await res.json()
        setMessage(`Authorization failed: ${errData.detail}`)
      }
    } catch (err) {
      console.error('Failed to authorize submission:', err)
    }
  }

  // Queue and Execution handlers
  const handlePrepareRun = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/prepare`, { method: 'POST' })
      if (res.ok) {
        setMessage(`Application #${appId} queued for execution successfully!`)
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      }
    } catch (err) {
      setMessage('Failed to enqueue application.')
    }
  }

  const handleExecuteRun = async (appId, isDryRun = false) => {
    setExecuting(true)
    setMessage('')
    const endpoint = isDryRun ? 'dry-run' : 'execute'
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/${endpoint}`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setMessage(isDryRun ? 'Dry run preview completed successfully!' : `Execution submitted successfully! Submission ID: ${data.submission_id || 'N/A'}`)
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      } else {
        const errData = await res.json()
        setMessage(`Execution error: ${errData.detail || 'Paused for user intervention'}`)
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      }
    } catch (err) {
      setMessage('Execution paused or encountered configuration exception.')
    } finally {
      setExecuting(false)
    }
  }

  const handleResumeRun = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/resume`, { method: 'POST' })
      if (res.ok) {
        setMessage('Human intervention resolved. Automation resumed!')
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      }
    } catch (err) {
      setMessage('Failed to resolve intervention.')
    }
  }

  const handleCancelRun = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/cancel`, { method: 'POST' })
      if (res.ok) {
        setMessage('Application run cancelled.')
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      }
    } catch (err) {
      setMessage('Failed to cancel run.')
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
      <h2 style={{ color: '#2c3e50', fontSize: '1.6rem', marginBottom: '1rem' }}>Application Execution & Submission Control</h2>

      {message && (
        <div style={{ background: '#e3f2fd', padding: '0.8rem 1.2rem', marginBottom: '1.5rem', borderRadius: '6px', color: '#0d47a1', borderLeft: '4px solid #1976d2', fontWeight: '500' }}>
          {message}
        </div>
      )}

      {/* Available Packages to Initialize Application */}
      <div style={{ background: '#f5f7fa', padding: '1rem 1.5rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid #dcdfe6' }}>
        <h3 style={{ margin: '0 0 0.8rem 0', fontSize: '1.1rem', color: '#303133' }}>Initialize Application from Package</h3>
        {packages.length === 0 ? (
          <p style={{ color: '#909399', margin: 0 }}>No application packages available. Create one in Phase 8 component above.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem' }}>
            {packages.map((pkg) => (
              <div key={pkg.id} style={{ background: '#fff', border: '1px solid #e4e7ed', padding: '0.8rem 1rem', borderRadius: '6px', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                <strong>Package #{pkg.id}</strong> (Job #{pkg.job_id})
                <div style={{ fontSize: '0.8rem', color: '#909399', marginTop: '0.2rem' }}>Status: {pkg.status}</div>
                <button
                  onClick={() => handleCreateApplication(pkg)}
                  style={{ marginTop: '0.6rem', padding: '0.4rem 0.8rem', background: '#67c23a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600' }}
                >
                  Start Application
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Applications List */}
      <h3 style={{ fontSize: '1.2rem', color: '#2c3e50', marginBottom: '0.8rem' }}>Application Control Cards</h3>
      {applications.length === 0 ? (
        <p style={{ color: '#909399' }}>No applications initialized yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '1rem', marginBottom: '2rem' }}>
          {applications.map((app) => (
            <div key={app.id} style={{ border: '1px solid #e4e7ed', padding: '1.2rem', borderRadius: '8px', background: app.status === 'SUBMITTED' ? '#f0f9eb' : '#fff', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#303133' }}>Application #{app.id} (Job #{app.job_id})</h4>
                <span style={{
                  background: app.status === 'SUBMITTED' ? '#67c23a' : app.status === 'APPROVED' ? '#409eff' : app.status === 'SUBMISSION_AUTHORIZED' ? '#e6a23c' : app.status === 'PAUSED' ? '#e6a23c' : '#909399',
                  color: '#fff',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontWeight: 'bold',
                  fontSize: '0.85rem'
                }}>
                  {app.status}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '0.6rem', marginTop: '1rem' }}>
                <button
                  onClick={() => handleSelectApp(app)}
                  style={{ padding: '0.45rem 0.9rem', background: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' }}
                >
                  Inspect & Review
                </button>
                {app.status === 'PREPARING' && (
                  <button
                    onClick={() => handleRequestReview(app.id)}
                    style={{ padding: '0.45rem 0.9rem', background: '#e6a23c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' }}
                  >
                    Request Human Review
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Interactive Review Workspace */}
      {selectedApp && (
        <div style={{ border: '2px solid #1976d2', padding: '1.5rem', borderRadius: '8px', background: '#f4f8fc', marginBottom: '2rem', boxShadow: '0 4px 12px rgba(25,118,210,0.06)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #dcdfe6', paddingBottom: '0.8rem', marginBottom: '1.2rem' }}>
            <h3 style={{ margin: 0, color: '#1976d2', fontSize: '1.3rem' }}>Human Review Workspace — Application #{selectedApp.id}</h3>
            <button onClick={() => setSelectedApp(null)} style={{ background: '#909399', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: '600' }}>Close</button>
          </div>

          <p style={{ margin: '0.4rem 0', color: '#606266', fontSize: '0.95rem' }}>
            Current Status: <strong style={{ color: '#303133' }}>{selectedApp.status}</strong> | Job ID: #{selectedApp.job_id} | Source Target: <strong>{selectedApp.source}</strong>
          </p>

          {/* Human Intervention Panel */}
          {selectedApp.status === 'PAUSED' && interventions.length > 0 && (
            <div style={{ background: '#fdf6ec', border: '2px solid #e6a23c', borderRadius: '8px', padding: '1.2rem', margin: '1rem 0', color: '#e6a23c' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: '#e6a23c', fontSize: '1.1rem' }}>⚠️ HUMAN INTERVENTION REQUIRED</h4>
              <p style={{ margin: '0 0 1rem 0', color: '#606266' }}>
                <strong>Reason:</strong> {interventions[0].reason || 'Login or CAPTCHA challenge detected.'}
              </p>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button
                  onClick={() => handleResumeRun(selectedApp.id)}
                  style={{ padding: '0.6rem 1.2rem', background: '#67c23a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '700' }}
                >
                  [Resume Automation]
                </button>
                <button
                  onClick={() => handleCancelRun(selectedApp.id)}
                  style={{ padding: '0.6rem 1.2rem', background: '#f56c6c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '700' }}
                >
                  [Stop / Cancel]
                </button>
              </div>
            </div>
          )}

          {/* Validation Findings */}
          {validationResult && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #e4e7ed', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.6rem 0', color: '#303133' }}>Validation Pipeline Findings</h4>
              {validationResult.blocking_issues?.length > 0 ? (
                <div style={{ color: '#f56c6c' }}>
                  <strong>BLOCKING ISSUES ({validationResult.blocking_issues.length}):</strong>
                  <ul style={{ marginTop: '0.4rem', paddingLeft: '1.2rem' }}>
                    {validationResult.blocking_issues.map((b, idx) => <li key={idx}>{b}</li>)}
                  </ul>
                </div>
              ) : (
                <p style={{ color: '#67c23a', fontWeight: 'bold', margin: '0 0 0.5rem 0' }}>✓ No blocking issues found.</p>
              )}
              {validationResult.warnings?.length > 0 && (
                <div style={{ color: '#e6a23c', marginTop: '0.5rem' }}>
                  <strong>WARNINGS ({validationResult.warnings.length}):</strong>
                  <ul style={{ marginTop: '0.4rem', paddingLeft: '1.2rem' }}>
                    {validationResult.warnings.map((w, idx) => <li key={idx}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Action Plan Preview Checklist */}
          {actionPlan.length > 0 && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #e4e7ed', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.6rem 0', color: '#303133' }}>Planned Action Sequence Preview</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {actionPlan.map((act) => (
                  <div key={act.step_number} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#606266' }}>
                    <input type="checkbox" checked readOnly style={{ accentColor: '#1976d2' }} />
                    <span>Step {act.step_number}:</span>
                    <strong style={{ color: '#303133' }}>{act.action}</strong>
                    <span>{act.field_type}</span>
                    <span style={{ color: '#909399', fontSize: '0.8rem' }}>({act.value})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Browser State Preview (Screenshots & Current URL) */}
          {browserState && browserState.current_url && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #e4e7ed', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.6rem 0', color: '#303133' }}>Browser Execution Session State</h4>
              <div style={{ fontSize: '0.85rem', color: '#606266', marginBottom: '0.5rem' }}>
                <div><strong>Current URL:</strong> {browserState.current_url}</div>
                <div><strong>Page Title:</strong> {browserState.page_title}</div>
                <div><strong>State:</strong> {browserState.state}</div>
              </div>
              {browserState.screenshots && browserState.screenshots.length > 0 && (
                <div>
                  <strong style={{ fontSize: '0.85rem', color: '#303133', display: 'block', marginBottom: '0.4rem' }}>Latest Screenshot Log:</strong>
                  <div style={{ fontSize: '0.8rem', color: '#909399', fontStyle: 'italic' }}>
                    Screenshot captured at: {browserState.screenshots[browserState.screenshots.length - 1]}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Human Approval Controls */}
          {selectedApp.status === 'READY_FOR_REVIEW' && (
            <div style={{ background: '#fff', padding: '1.2rem', borderRadius: '6px', border: '2px solid #67c23a', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.8rem 0', color: '#303133' }}>Explicit Human Approval Checks</h4>
              <div style={{ marginBottom: '0.8rem' }}>
                <label style={{ cursor: 'pointer', fontWeight: '600', color: '#1976d2', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    checked={userConfirmed}
                    onChange={(e) => setUserConfirmed(e.target.checked)}
                    style={{ marginTop: '3px' }}
                  />
                  <span>I confirm that I have reviewed all job details, tailored resume content, and screening answers for this application.</span>
                </label>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <input
                  type="text"
                  placeholder="Optional approval notes..."
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #dcdfe6', boxSizing: 'border-box' }}
                />
              </div>

              <button
                onClick={() => handleApprove(selectedApp.id)}
                disabled={!userConfirmed}
                style={{ padding: '0.6rem 1.2rem', background: userConfirmed ? '#67c23a' : '#c0c4cc', color: '#fff', border: 'none', borderRadius: '4px', cursor: userConfirmed ? 'pointer' : 'not-allowed', fontWeight: 'bold' }}
              >
                Approve Application
              </button>
            </div>
          )}

          {/* Submission Authorization Controls */}
          {selectedApp.status === 'APPROVED' && (
            <div style={{ background: '#fff', padding: '1.2rem', borderRadius: '6px', border: '2px solid #e6a23c', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.6rem 0', color: '#303133' }}>Submission Authorization Center</h4>
              <p style={{ margin: '0 0 1rem 0', color: '#606266', fontSize: '0.9rem' }}>
                Application is APPROVED. Click below to issue an explicit Submission Authorization Token.
              </p>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button
                  onClick={() => handleAuthorize(selectedApp.id)}
                  style={{ padding: '0.6rem 1.2rem', background: '#e6a23c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Authorize Submission
                </button>
                <button
                  onClick={() => handlePrepareRun(selectedApp.id)}
                  style={{ padding: '0.6rem 1.2rem', background: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Prepare & Queue
                </button>
              </div>
            </div>
          )}

          {/* Queue & Execution Controls */}
          {selectedApp.status === 'SUBMISSION_AUTHORIZED' && (
            <div style={{ background: '#fff', padding: '1.2rem', borderRadius: '6px', border: '2px solid #1976d2', margin: '1rem 0' }}>
              <h4 style={{ margin: '0 0 0.6rem 0', color: '#303133' }}>Application Execution Control Center</h4>
              <p style={{ margin: '0 0 1rem 0', color: '#606266', fontSize: '0.9rem' }}>
                Application run is AUTHORIZED. Choose execution mode:
              </p>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button
                  onClick={() => handleExecuteRun(selectedApp.id, true)}
                  disabled={executing}
                  style={{ padding: '0.6rem 1.2rem', background: '#e6a23c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  {executing ? 'Simulating...' : 'Run DRY_RUN Preview'}
                </button>
                <button
                  onClick={() => handleExecuteRun(selectedApp.id, false)}
                  disabled={executing}
                  style={{ padding: '0.6rem 1.5rem', background: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  {executing ? 'Automating...' : 'Execute Submission'}
                </button>
              </div>
            </div>
          )}

          {/* Event Timeline */}
          <h4 style={{ color: '#2c3e50', fontSize: '1.1rem', margin: '1.2rem 0 0.6rem 0' }}>Application Event Timeline</h4>
          <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #e4e7ed', maxHeight: '150px', overflowY: 'auto' }}>
            {timeline.length === 0 ? (
              <p style={{ color: '#909399', margin: 0 }}>No timeline events recorded.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#606266', fontSize: '0.85rem', lineHeight: '1.4' }}>
                {timeline.map((evt) => (
                  <li key={evt.id} style={{ margin: '0.3rem 0' }}>
                    <strong>{new Date(evt.timestamp).toLocaleString()}</strong> [{evt.actor}]: {evt.description}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
