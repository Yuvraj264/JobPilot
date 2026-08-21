import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function ApplicationControlManager() {
  const [applications, setApplications] = useState([])
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [selectedApp, setSelectedApp] = useState(null)
  const [validationResult, setValidationResult] = useState(null)
  const [userConfirmed, setUserConfirmed] = useState(false)
  const [approvalNotes, setApprovalNotes] = useState('')
  const [timeline, setTimeline] = useState([])

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
    try {
      const [valRes, timeRes] = await Promise.all([
        fetch(`${API_BASE}/applications/${app.id}/validate`, { method: 'POST' }),
        fetch(`${API_BASE}/applications/${app.id}/timeline`),
      ])
      if (valRes.ok) setValidationResult(await valRes.json())
      if (timeRes.ok) {
        const tData = await timeRes.json()
        setTimeline(tData.timeline || [])
      }
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
        setMessage(`Submission Authorization token #${data.id} issued! Expires: ${data.expires_at}`)
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

  const handleSubmit = async (appId) => {
    try {
      const res = await fetch(`${API_BASE}/applications/${appId}/submit`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setMessage(`SUBMITTED SUCCESS! Submission ID: ${data.submission_id}`)
        loadData()
        const appRes = await fetch(`${API_BASE}/applications/${appId}`)
        if (appRes.ok) handleSelectApp(await appRes.json())
      } else {
        const errData = await res.json()
        setMessage(`Submission failed/blocked: ${errData.detail}`)
      }
    } catch (err) {
      console.error('Failed to submit application:', err)
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Application Approval & Submission Control Layer</h2>

      {message && <div style={{ background: '#e3f2fd', padding: '0.6rem', marginBottom: '1rem', borderRadius: '4px', color: '#0d47a1' }}>{message}</div>}

      {/* Available Packages to Initialize Application */}
      <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid #ddd' }}>
        <h3>Initialize Application from Package</h3>
        {packages.length === 0 ? (
          <p style={{ color: '#666' }}>No application packages available. Create one in Phase 8 component above.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem' }}>
            {packages.map((pkg) => (
              <div key={pkg.id} style={{ background: '#fff', border: '1px solid #ccc', padding: '0.8rem', borderRadius: '6px' }}>
                <div><strong>Package #{pkg.id}</strong> (Job #{pkg.job_id})</div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>Status: {pkg.status}</div>
                <button
                  onClick={() => handleCreateApplication(pkg)}
                  style={{ marginTop: '0.5rem', padding: '0.35rem 0.7rem', background: '#2e7d32', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}
                >
                  Start Application
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Applications List */}
      <h3>Application Control Cards</h3>
      {applications.length === 0 ? (
        <p style={{ color: '#666' }}>No applications initialized yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '1rem', marginBottom: '2rem' }}>
          {applications.map((app) => (
            <div key={app.id} style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', background: app.status === 'SUBMITTED' ? '#e8f5e9' : '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ margin: 0 }}>Application #{app.id} (Job #{app.job_id})</h4>
                <span style={{ background: app.status === 'SUBMITTED' ? '#2e7d32' : app.status === 'APPROVED' ? '#1565c0' : app.status === 'SUBMISSION_AUTHORIZED' ? '#e65100' : '#888', color: '#fff', padding: '4px 10px', borderRadius: '12px', fontWeight: 'bold', fontSize: '0.85rem' }}>
                  {app.status}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem' }}>
                <button
                  onClick={() => handleSelectApp(app)}
                  style={{ padding: '0.4rem 0.8rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  Inspect & Review
                </button>
                {app.status === 'PREPARING' && (
                  <button
                    onClick={() => handleRequestReview(app.id)}
                    style={{ padding: '0.4rem 0.8rem', background: '#e65100', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
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
        <div style={{ border: '2px solid #1565c0', padding: '1.2rem', borderRadius: '8px', background: '#f4f6f9', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Human Review Workspace — Application #{selectedApp.id}</h3>
            <button onClick={() => setSelectedApp(null)} style={{ background: '#888', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px' }}>Close</button>
          </div>

          <p style={{ margin: '0.4rem 0' }}>Current Status: <strong>{selectedApp.status}</strong> | Job ID: #{selectedApp.job_id} | Source: {selectedApp.source}</p>

          {/* Validation Findings */}
          {validationResult && (
            <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '6px', border: '1px solid #ddd', margin: '0.8rem 0' }}>
              <h4>Validation Findings</h4>
              {validationResult.blocking_issues?.length > 0 ? (
                <div style={{ color: '#c62828' }}>
                  <strong>BLOCKING ISSUES ({validationResult.blocking_issues.length}):</strong>
                  <ul>
                    {validationResult.blocking_issues.map((b, idx) => <li key={idx}>{b}</li>)}
                  </ul>
                </div>
              ) : (
                <p style={{ color: '#2e7d32', fontWeight: 'bold' }}>✓ No blocking issues found.</p>
              )}
              {validationResult.warnings?.length > 0 && (
                <div style={{ color: '#ef6c00' }}>
                  <strong>WARNINGS ({validationResult.warnings.length}):</strong>
                  <ul>
                    {validationResult.warnings.map((w, idx) => <li key={idx}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Human Approval Controls */}
          {selectedApp.status === 'READY_FOR_REVIEW' && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '2px solid #2e7d32', margin: '1rem 0' }}>
              <h4>Explicit Human Approval Controls</h4>
              <div style={{ marginBottom: '0.8rem' }}>
                <label style={{ cursor: 'pointer', fontWeight: 'bold', color: '#1565c0' }}>
                  <input
                    type="checkbox"
                    checked={userConfirmed}
                    onChange={(e) => setUserConfirmed(e.target.checked)}
                    style={{ marginRight: '0.5rem' }}
                  />
                  I confirm that I have reviewed all job details, tailored resume content, and screening answers for this application.
                </label>
              </div>

              <div style={{ marginBottom: '0.8rem' }}>
                <input
                  type="text"
                  placeholder="Optional approval notes..."
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  style={{ width: '100%', padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => handleApprove(selectedApp.id)}
                  disabled={!userConfirmed}
                  style={{ padding: '0.5rem 1.2rem', background: userConfirmed ? '#2e7d32' : '#ccc', color: '#fff', border: 'none', borderRadius: '4px', cursor: userConfirmed ? 'pointer' : 'not-allowed', fontWeight: 'bold' }}
                >
                  Approve Application
                </button>
              </div>
            </div>
          )}

          {/* Submission Authorization Controls */}
          {selectedApp.status === 'APPROVED' && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '2px solid #e65100', margin: '1rem 0' }}>
              <h4>Submission Authorization Controls</h4>
              <p>Application is APPROVED. Click below to issue an explicit Submission Authorization Token.</p>
              <button
                onClick={() => handleAuthorize(selectedApp.id)}
                style={{ padding: '0.55rem 1.2rem', background: '#e65100', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                Authorize Submission
              </button>
            </div>
          )}

          {/* Submission Execution Controls */}
          {selectedApp.status === 'SUBMISSION_AUTHORIZED' && (
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '2px solid #1565c0', margin: '1rem 0' }}>
              <h4>Submission Execution Control Center</h4>
              <p>Submission is AUTHORIZED. Ready to submit via local MockSubmissionAdapter.</p>
              <button
                onClick={() => handleSubmit(selectedApp.id)}
                style={{ padding: '0.6rem 1.5rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
              >
                Execute Mock Submission
              </button>
            </div>
          )}

          {/* Event Timeline */}
          <h4>Application Event Timeline</h4>
          <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '6px', border: '1px solid #ddd' }}>
            {timeline.length === 0 ? (
              <p style={{ color: '#666' }}>No timeline events recorded.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                {timeline.map((evt) => (
                  <li key={evt.id} style={{ margin: '0.3rem 0', fontSize: '0.85rem' }}>
                    <strong>{evt.timestamp}</strong> [{evt.actor}]: {evt.description}
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
