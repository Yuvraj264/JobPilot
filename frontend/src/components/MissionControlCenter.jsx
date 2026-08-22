import React, { useState, useEffect } from 'react'

export default function MissionControlCenter({ userId }) {
  const [missions, setMissions] = useState([])
  const [selectedMission, setSelectedMission] = useState(null)
  const [runs, setRuns] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [health, setHealth] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [wizardStep, setWizardStep] = useState(0) // 0 = list, 1 = wizard step 1, 2 = step 2, 3 = step 3, 4 = preview
  
  // Wizard creation states
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [targetRoles, setTargetRoles] = useState('')
  const [targetLocations, setTargetLocations] = useState('')
  const [workModes, setWorkModes] = useState(['REMOTE'])
  const [minMatch, setMinMatch] = useState(80)
  const [skills, setSkills] = useState('')
  const [excludedCompanies, setExcludedCompanies] = useState('')
  const [maxAppsDay, setMaxAppsDay] = useState(5)
  const [strategy, setStrategy] = useState('HUMAN_REVIEW')
  const [goalType, setGoalType] = useState('APPLICATION_COUNT')
  const [goalTarget, setGoalTarget] = useState(20)

  // Preset templates
  const presets = [
    { name: 'QA Automation', roles: 'QA Automation, SDET', locations: 'Bangalore, Remote', skills: 'Selenium, Playwright, Python', desc: 'Auto campaign for QA automation' },
    { name: 'SDET Search', roles: 'SDET, Software Development Engineer in Test', locations: 'Bangalore, Remote', skills: 'Java, Selenium, TestNG', desc: 'Focuses on SDET engineering' },
    { name: 'Backend Developer', roles: 'Backend Developer, Software Engineer', locations: 'Remote', skills: 'Python, Django, FastAPI, PostgreSQL', desc: 'FastAPI / python developer targets' }
  ]

  const applyPreset = (preset) => {
    setName(preset.name)
    setDesc(preset.desc)
    setTargetRoles(preset.roles)
    setTargetLocations(preset.locations)
    setSkills(preset.skills)
    setMessage(`Applied preset template for: ${preset.name}`)
  }

  const fetchMissions = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/missions', { headers: { 'X-User-Id': userId } })
      if (res.ok) setMissions(await res.json())
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchMissionDetails = async (id) => {
    try {
      const [mRes, runsRes, anaRes, healthRes, sugRes] = await Promise.all([
        fetch(`http://localhost:8000/api/missions/${id}`, { headers: { 'X-User-Id': userId } }),
        fetch(`http://localhost:8000/api/missions/${id}/runs`, { headers: { 'X-User-Id': userId } }),
        fetch(`http://localhost:8000/api/missions/${id}/analytics`, { headers: { 'X-User-Id': userId } }),
        fetch(`http://localhost:8000/api/missions/${id}/health`, { headers: { 'X-User-Id': userId } }),
        fetch(`http://localhost:8000/api/missions/${id}/suggestions`, { headers: { 'X-User-Id': userId } })
      ])
      if (mRes.ok) setSelectedMission(await mRes.json())
      if (runsRes.ok) setRuns(await runsRes.json())
      if (anaRes.ok) setAnalytics(await anaRes.json())
      if (healthRes.ok) setHealth(await healthRes.json())
      if (sugRes.ok) setSuggestions(await sugRes.json())
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchMissions()
  }, [userId])

  const handleCreateMission = async (status = 'DRAFT') => {
    const payload = {
      name,
      description: desc,
      objective: {
        target_roles: targetRoles.split(',').map(s => s.trim()).filter(Boolean),
        target_locations: targetLocations.split(',').map(s => s.trim()).filter(Boolean),
        target_work_modes: workModes,
        preferred_skills: skills.split(',').map(s => s.trim()).filter(Boolean),
        excluded_companies: excludedCompanies.split(',').map(s => s.trim()).filter(Boolean),
        minimum_match_score: minMatch
      },
      source_configuration: { all_enabled_sources: true, selected_sources: [] },
      limits: { max_applications_per_day: maxAppsDay, max_applications_per_run: 3 },
      scheduler_preset: { schedule_type: 'daily', scheduled_hour: 9, scheduled_minute: 0 },
      application_strategy: strategy,
      application_budget: { daily: maxAppsDay, weekly: maxAppsDay * 5 },
      goal_configuration: { goal_type: goalType, target_value: goalTarget, current_progress: 0 }
    }

    try {
      const res = await fetch('http://localhost:8000/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        const data = await res.json()
        setMessage('Mission created successfully!')
        
        if (status === 'ACTIVE') {
          // Auto activate
          await fetch(`http://localhost:8000/api/missions/${data.id}/activate`, {
            method: 'POST',
            headers: { 'X-User-Id': userId }
          })
        }
        
        setWizardStep(0)
        fetchMissions()
      } else {
        const err = await res.json()
        setMessage(`Failed to create mission: ${err.detail || 'check parameters'}`)
      }
    } catch (err) {
      console.error(err)
      setMessage('Error creating search mission.')
    }
  }

  const handleAction = async (action, id) => {
    try {
      const res = await fetch(`http://localhost:8000/api/missions/${id}/${action}`, {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage(`Mission action '${action}' triggered successfully!`)
        fetchMissions()
        if (selectedMission && selectedMission.id === id) {
          fetchMissionDetails(id)
        }
      } else {
        const err = await res.json()
        setMessage(`Action failed: ${err.detail?.message || err.detail || 'error'}`)
      }
    } catch (err) {
      console.error(err)
      setMessage('Error executing action.')
    }
  }

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0f172a' }}>🎯 Persistent Job Search Missions</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b' }}>
            Set persistent job targets, schedule run frequencies, and track application conversion campaign progress.
          </p>
        </div>
        {wizardStep === 0 && (
          <button
            onClick={() => setWizardStep(1)}
            style={{
              background: '#4f46e5',
              color: '#fff',
              border: 'none',
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            ➕ Create New Mission
          </button>
        )}
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

      {/* --- WIZARD FORM --- */}
      {wizardStep > 0 && (
        <div style={{
          background: '#fff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          marginBottom: '2rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Create Job Mission Wizard</h3>
            <span style={{ fontWeight: 'bold', color: '#4f46e5' }}>Step {wizardStep} of 4</span>
          </div>

          {/* Quick presets templates */}
          {wizardStep === 1 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#64748b', marginBottom: '0.5rem' }}>Or Start from Template Preset:</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {presets.map((p, idx) => (
                  <button key={idx} onClick={() => applyPreset(p)} style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '0.35rem 0.75rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}>
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 1: Basic objective */}
          {wizardStep === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Mission Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Bangalore QA Automation Campaign" style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Target Job Titles (comma separated)</label>
                <input type="text" value={targetRoles} onChange={(e) => setTargetRoles(e.target.value)} placeholder="e.g. QA Automation, SDET" style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Locations</label>
                  <input type="text" value={targetLocations} onChange={(e) => setTargetLocations(e.target.value)} placeholder="e.g. Bangalore, Remote" style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Min Match Score (%)</label>
                  <input type="number" value={minMatch} onChange={(e) => setMinMatch(parseInt(e.target.value))} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Preferred skills */}
          {wizardStep === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Preferred Skills (comma separated)</label>
                <input type="text" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="e.g. Selenium, Python, API Testing" style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Excluded Companies (comma separated)</label>
                <input type="text" value={excludedCompanies} onChange={(e) => setExcludedCompanies(e.target.value)} placeholder="e.g. SpamCorp, BadInc" style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
              </div>
            </div>
          )}

          {/* Step 3: limits and strategy */}
          {wizardStep === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Max Applications Per Day</label>
                  <input type="number" value={maxAppsDay} onChange={(e) => setMaxAppsDay(parseInt(e.target.value))} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Application Strategy</label>
                  <select value={strategy} onChange={(e) => setStrategy(e.target.value)} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                    <option value="PREPARE_ONLY">Prepare Only (do not submit)</option>
                    <option value="HUMAN_REVIEW">Human Review (require review queue authorization)</option>
                    <option value="SUPPORTED_AUTOMATIC">Supported Automatic (auto approve)</option>
                  </select>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Goal Type</label>
                  <select value={goalType} onChange={(e) => setGoalType(e.target.value)} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                    <option value="APPLICATION_COUNT">Target Application Count</option>
                    <option value="JOB_DISCOVERY">Target Discovery Count</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.4rem' }}>Goal Target Number</label>
                  <input type="number" value={goalTarget} onChange={(e) => setGoalTarget(parseInt(e.target.value))} style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Preview */}
          {wizardStep === 4 && (
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
              <h4>Mission Configuration Preview</h4>
              <p><strong>Name:</strong> {name}</p>
              <p><strong>Target:</strong> {targetRoles} ({targetLocations})</p>
              <p><strong>Min Match Score:</strong> {minMatch}%</p>
              <p><strong>Strategy:</strong> {strategy}</p>
              <p><strong>Daily Limit:</strong> Up to {maxAppsDay} applications/day</p>
              <p><strong>Goal:</strong> Reach {goalTarget} applications</p>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
            <button onClick={() => setWizardStep(wizardStep - 1)} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', fontWeight: 'bold' }}>
              Back
            </button>
            {wizardStep < 4 ? (
              <button onClick={() => setWizardStep(wizardStep + 1)} style={{ background: '#4f46e5', color: '#fff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
                Next Step
              </button>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleCreateMission('DRAFT')} style={{ background: '#e2e8f0', color: '#334155', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Save Draft</button>
                <button onClick={() => handleCreateMission('ACTIVE')} style={{ background: '#22c55e', color: '#fff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Activate Mission</button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- DASHBOARD VIEW --- */}
      {wizardStep === 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem' }}>
          
          {/* Sidebar Missions List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3>Campaign Goals List</h3>
            {missions.length === 0 ? (
              <div style={{ padding: '1rem', color: '#64748b', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                No search missions configured yet. Create a draft to begin.
              </div>
            ) : (
              missions.map((m) => (
                <div
                  key={m.id}
                  onClick={() => fetchMissionDetails(m.id)}
                  style={{
                    background: selectedMission?.id === m.id ? '#eff6ff' : '#ffffff',
                    border: `1px solid ${selectedMission?.id === m.id ? '#bfdbfe' : '#e2e8f0'}`,
                    padding: '1rem',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <strong style={{ color: '#0f172a' }}>{m.name}</strong>
                    <span style={{
                      padding: '0.2rem 0.5rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      background: m.status === 'ACTIVE' ? '#dcfce7' : '#f1f5f9',
                      color: m.status === 'ACTIVE' ? '#15803d' : '#475569'
                    }}>
                      {m.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    Progress: {m.goal_progress || 0}%
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Details Content Panel */}
          <div>
            {selectedMission ? (
              <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '16px',
                padding: '2rem',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #f1f5f9', paddingBottom: '1.25rem', marginBottom: '1.5rem' }}>
                  <div>
                    <h2 style={{ margin: 0, color: '#0f172a' }}>{selectedMission.name}</h2>
                    <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Strategy: {selectedMission.application_strategy} | Config Version: V{selectedMission.configuration_version}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={() => handleAction('run', selectedMission.id)} style={{ background: '#4f46e5', color: '#fff', border: 'none', padding: '0.45rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Run Now</button>
                    {selectedMission.status === 'ACTIVE' ? (
                      <button onClick={() => handleAction('pause', selectedMission.id)} style={{ background: '#ea580c', color: '#fff', border: 'none', padding: '0.45rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Pause</button>
                    ) : (
                      <button onClick={() => handleAction('resume', selectedMission.id)} style={{ background: '#22c55e', color: '#fff', border: 'none', padding: '0.45rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Resume</button>
                    )}
                    <button onClick={() => handleAction('cancel', selectedMission.id)} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '0.45rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Cancel</button>
                  </div>
                </div>

                {/* Health & Suggestion Cards */}
                {selectedMission.health !== 'HEALTHY' && (
                  <div style={{ background: '#fffbeb', border: '1px solid #fef3c7', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', color: '#92400e' }}>
                    <strong>⚠️ Diagnostic Warning: {selectedMission.health}</strong>
                    <div style={{ fontSize: '0.9rem', marginTop: '0.25rem' }}>{selectedMission.diagnostics?.reason}</div>
                    {suggestions.map((sug, idx) => (
                      <div key={idx} style={{ marginTop: '0.5rem', background: '#fff', border: '1px solid #fde68a', padding: '0.5rem', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem' }}>{sug.message}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Analytical Funnel Grid */}
                {analytics && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Application Campaign Funnel</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.5rem', textAlign: 'center' }}>
                      {[
                        { label: 'Discovered', val: analytics.funnel?.DISCOVERED || 0 },
                        { label: 'Eligible', val: analytics.funnel?.ELIGIBLE || 0 },
                        { label: 'Selected', val: analytics.funnel?.SELECTED || 0 },
                        { label: 'Prepared', val: analytics.funnel?.PREPARED || 0 },
                        { label: 'Submitted', val: analytics.funnel?.SUBMITTED || 0 }
                      ].map((stage, idx) => (
                        <div key={idx} style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold', marginBottom: '0.25rem' }}>{stage.label}</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#0f172a' }}>{stage.val}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Run History List */}
                <div>
                  <h3 style={{ marginBottom: '1rem' }}>Recent Execution runs</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                        <th style={{ padding: '0.5rem' }}>Run ID</th>
                        <th style={{ padding: '0.5rem' }}>Status</th>
                        <th style={{ padding: '0.5rem' }}>Discovered</th>
                        <th style={{ padding: '0.5rem' }}>Selected</th>
                        <th style={{ padding: '0.5rem' }}>Prepared</th>
                        <th style={{ padding: '0.5rem' }}>Failed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.length === 0 ? (
                        <tr>
                          <td colSpan="6" style={{ padding: '1rem', color: '#64748b', textAlign: 'center' }}>No execution runs recorded yet. Click 'Run Now' to execute.</td>
                        </tr>
                      ) : (
                        runs.map((r) => (
                          <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '0.5rem' }}>#{r.id}</td>
                            <td style={{ padding: '0.5rem', fontWeight: 'bold', color: r.status === 'COMPLETED' ? '#22c55e' : '#f59e0b' }}>{r.status}</td>
                            <td style={{ padding: '0.5rem' }}>{r.jobs_discovered}</td>
                            <td style={{ padding: '0.5rem' }}>{r.jobs_selected}</td>
                            <td style={{ padding: '0.5rem' }}>{r.prepared}</td>
                            <td style={{ padding: '0.5rem' }}>{r.failed}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

              </div>
            ) : (
              <div style={{ padding: '3rem', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '16px', textAlign: 'center', color: '#64748b' }}>
                Select a mission campaign from the list or create a new objective wizard above to check detailed diagnostic results.
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  )
}
