import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/jobs'

export default function JobDiscoveryManager() {
  const [activeTab, setActiveTab] = useState('jobs') // 'jobs' | 'sources' | 'stats'
  const [jobs, setJobs] = useState([])
  const [sources, setSources] = useState([])
  const [stats, setStats] = useState(null)
  const [runs, setRuns] = useState([])
  
  const [searchQuery, setSearchQuery] = useState('')
  const [filterWorkplace, setFilterWorkplace] = useState('')
  const [filterSource, setFilterSource] = useState('')
  const [selectedJob, setSelectedJob] = useState(null)
  
  const [discovering, setDiscovering] = useState(false)
  const [message, setMessage] = useState('')
  
  // Configuration State
  const [selectedConfigName, setSelectedConfigName] = useState(null)
  const [configData, setConfigData] = useState(null)
  const [savingConfig, setSavingConfig] = useState(false)

  const loadJobs = async () => {
    try {
      let url = `${API_BASE}`
      if (searchQuery) {
        url = `${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`
      }
      const res = await fetch(url)
      if (res.ok) {
        let data = await res.json()
        if (filterWorkplace) {
          data = data.filter(j => j.workplace_type === filterWorkplace)
        }
        if (filterSource) {
          data = data.filter(j => j.source_id === parseInt(filterSource))
        }
        setJobs(data)
      }
    } catch (err) {
      console.error('Error loading jobs:', err)
    }
  }

  const loadSources = async () => {
    try {
      const res = await fetch(`${API_BASE}/sources`)
      if (res.ok) setSources(await res.json())
    } catch (err) {
      console.error('Error loading sources:', err)
    }
  }

  const loadStats = async () => {
    try {
      const resStats = await fetch(`${API_BASE}/stats`)
      if (resStats.ok) setStats(await resStats.json())

      const resRuns = await fetch(`${API_BASE}/discovery-runs`)
      if (resRuns.ok) setRuns(await resRuns.json())
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  useEffect(() => {
    loadJobs()
    loadSources()
    loadStats()
  }, [searchQuery, filterWorkplace, filterSource])

  const handleRunDiscovery = async (sourceName = null) => {
    setDiscovering(true)
    setMessage('')
    try {
      const url = sourceName ? `${API_BASE}/discover/${sourceName}` : `${API_BASE}/discover`
      const res = await fetch(url, { method: 'POST' })
      if (res.ok) {
        const summary = await res.json()
        const count = summary.jobs_created || summary[0]?.jobs_created || 0
        setMessage(`Discovery completed! Ingested ${count} new job listings.`)
        loadJobs()
        loadSources()
        loadStats()
      } else {
        const errData = await res.json()
        setMessage(`Discovery error: ${errData.detail || 'Failed to run discovery'}`)
      }
    } catch (err) {
      setMessage('Failed to execute job discovery.')
    } finally {
      setDiscovering(false)
    }
  }

  const toggleSource = async (sourceName, currentlyEnabled) => {
    const action = currentlyEnabled ? 'disable' : 'enable'
    const res = await fetch(`${API_BASE}/sources/${sourceName}/${action}`, { method: 'POST' })
    if (res.ok) {
      loadSources()
    }
  }

  const inspectJob = async (id) => {
    const res = await fetch(`${API_BASE}/${id}`)
    if (res.ok) setSelectedJob(await res.json())
  }

  // Load Source Configuration Panel
  const handleConfigureSource = async (sourceName) => {
    setSelectedConfigName(sourceName)
    try {
      const res = await fetch(`${API_BASE}/sources/${sourceName}/config`)
      if (res.ok) {
        setConfigData(await res.json())
      }
    } catch (err) {
      console.error('Error loading source configuration:', err)
    }
  }

  // Save Source Configuration
  const handleSaveConfig = async (e) => {
    e.preventDefault()
    setSavingConfig(true)
    try {
      const res = await fetch(`${API_BASE}/sources/${selectedConfigName}/config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: configData.enabled,
          discovery_enabled: configData.discovery_enabled,
          application_enabled: configData.application_enabled,
          max_jobs_per_run: parseInt(configData.max_jobs_per_run),
          max_pages_per_run: parseInt(configData.max_pages_per_run),
          rate_limit: parseFloat(configData.rate_limit),
          configuration: configData.configuration
        })
      })
      if (res.ok) {
        setMessage(`Configuration for ${selectedConfigName} updated successfully!`)
        setSelectedConfigName(null)
        setConfigData(null)
        loadSources()
      } else {
        const errData = await res.json()
        setMessage(`Config error: ${errData.detail || 'Failed to save config'}`)
      }
    } catch (err) {
      setMessage('Failed to update source configuration.')
    } finally {
      setSavingConfig(false)
    }
  }

  const getHealthColor = (health) => {
    switch (health?.toLowerCase()) {
      case 'healthy':
      case 'available':
        return '#2e7d32' // Green
      case 'rate_limited':
        return '#f57c00' // Orange
      case 'authentication_required':
        return '#0288d1' // Blue
      case 'blocked':
      case 'error':
        return '#d32f2f' // Red
      default:
        return '#757575' // Gray
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
      <h2 style={{ color: '#2c3e50', fontSize: '1.6rem', marginBottom: '1rem' }}>Job Source Architecture & Discovery Catalog</h2>

      {message && (
        <div style={{ background: '#e8f5e9', padding: '0.8rem 1.2rem', marginBottom: '1rem', borderRadius: '6px', color: '#2e7d32', borderLeft: '4px solid #2e7d32', fontWeight: '500' }}>
          {message}
        </div>
      )}

      {/* Discovery Trigger Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%)', padding: '1rem 1.5rem', borderRadius: '8px', border: '1px solid #dcdfe6' }}>
        <div>
          <strong style={{ color: '#2c3e50' }}>Discovery Engine</strong> — Dynamic multi-source crawling with strict rate limits.
        </div>
        <div style={{ display: 'flex', gap: '0.8rem' }}>
          <button
            onClick={() => handleRunDiscovery()}
            disabled={discovering}
            style={{ padding: '0.6rem 1.2rem', background: '#1976d2', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', transition: 'all 0.2s' }}
          >
            {discovering ? 'Ingesting Jobs...' : 'Run All Enabled Sources'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #dcdfe6', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('jobs')}
          style={{ padding: '0.8rem 1.2rem', border: 'none', borderBottom: activeTab === 'jobs' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'jobs' ? '700' : '500', color: activeTab === 'jobs' ? '#1976d2' : '#606266', fontSize: '0.95rem' }}
        >
          Discovered Jobs ({jobs.length})
        </button>
        <button
          onClick={() => setActiveTab('sources')}
          style={{ padding: '0.8rem 1.2rem', border: 'none', borderBottom: activeTab === 'sources' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'sources' ? '700' : '500', color: activeTab === 'sources' ? '#1976d2' : '#606266', fontSize: '0.95rem' }}
        >
          Job Sources ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          style={{ padding: '0.8rem 1.2rem', border: 'none', borderBottom: activeTab === 'stats' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'stats' ? '700' : '500', color: activeTab === 'stats' ? '#1976d2' : '#606266', fontSize: '0.95rem' }}
        >
          Stats & Runs
        </button>
      </div>

      {/* Tab 1: Jobs View */}
      {activeTab === 'jobs' && (
        <div>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.2rem' }}>
            <input
              type="text"
              placeholder="Search title, company, description keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ flex: 1, padding: '0.7rem 1rem', borderRadius: '6px', border: '1px solid #dcdfe6', fontSize: '0.9rem' }}
            />
            <select value={filterWorkplace} onChange={(e) => setFilterWorkplace(e.target.value)} style={{ padding: '0.7rem 1rem', borderRadius: '6px', border: '1px solid #dcdfe6', background: '#fff', fontSize: '0.9rem' }}>
              <option value="">All Workplace Arrangements</option>
              <option value="REMOTE">Remote</option>
              <option value="HYBRID">Hybrid</option>
              <option value="ONSITE">Onsite</option>
            </select>
            <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)} style={{ padding: '0.7rem 1rem', borderRadius: '6px', border: '1px solid #dcdfe6', background: '#fff', fontSize: '0.9rem' }}>
              <option value="">All Sources</option>
              {sources.map(s => (
                <option key={s.id} value={s.id}>{s.display_name}</option>
              ))}
            </select>
          </div>

          {jobs.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#909399', border: '1px dashed #dcdfe6', borderRadius: '8px', background: '#fafafa' }}>
              <h3>No job listings match your search</h3>
              <p>Click 'Run All Enabled Sources' to fetch jobs from active platforms.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {jobs.map((j) => (
                <div
                  key={j.id}
                  style={{
                    border: '1px solid #e4e7ed',
                    padding: '1rem 1.2rem',
                    borderRadius: '8px',
                    background: '#fff',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                    transition: 'transform 0.15s, box-shadow 0.15s'
                  }}
                >
                  <div>
                    <h3 style={{ margin: '0 0 0.3rem 0', fontSize: '1.1rem', color: '#303133' }}>{j.title}</h3>
                    <span style={{ fontSize: '0.9rem', color: '#1976d2', fontWeight: '600' }}>{j.company_name}</span>
                    <div style={{ fontSize: '0.85rem', color: '#606266', marginTop: '0.3rem', display: 'flex', gap: '1rem' }}>
                      <span>📍 {j.normalized_location || j.location || 'Remote'}</span>
                      <span>💼 {j.employment_type}</span>
                      <span>🏠 {j.workplace_type}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      background: j.status === 'DUPLICATE' ? '#fde2e2' : j.status === 'POTENTIAL_DUPLICATE' ? '#faecd8' : '#f0f9eb',
                      color: j.status === 'DUPLICATE' ? '#f56c6c' : j.status === 'POTENTIAL_DUPLICATE' ? '#e6a23c' : '#67c23a',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>
                      {j.status}
                    </span>
                    <button
                      onClick={() => inspectJob(j.id)}
                      style={{ padding: '0.5rem 1rem', border: '1px solid #dcdfe6', background: '#fff', color: '#606266', borderRadius: '4px', cursor: 'pointer', fontWeight: '500' }}
                    >
                      Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Sources View */}
      {activeTab === 'sources' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #e4e7ed', borderRadius: '8px', overflow: 'hidden' }}>
            <thead>
              <tr style={{ background: '#f5f7fa', textAlign: 'left', borderBottom: '2px solid #e4e7ed' }}>
                <th style={{ padding: '0.8rem 1rem', color: '#909399', fontWeight: '600', fontSize: '0.85rem' }}>Platform Name</th>
                <th style={{ padding: '0.8rem 1rem', color: '#909399', fontWeight: '600', fontSize: '0.85rem' }}>Access Mode</th>
                <th style={{ padding: '0.8rem 1rem', color: '#909399', fontWeight: '600', fontSize: '0.85rem' }}>Status</th>
                <th style={{ padding: '0.8rem 1rem', color: '#909399', fontWeight: '600', fontSize: '0.85rem' }}>Capabilities</th>
                <th style={{ padding: '0.8rem 1rem', color: '#909399', fontWeight: '600', fontSize: '0.85rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #e4e7ed' }}>
                  <td style={{ padding: '1rem' }}>
                    <strong style={{ fontSize: '1rem', color: '#303133' }}>{s.display_name}</strong>
                    <div style={{ fontSize: '0.85rem', color: '#909399', marginTop: '0.2rem' }}>{s.name}</div>
                  </td>
                  <td style={{ padding: '1rem', fontSize: '0.9rem', color: '#606266' }}>{s.source_type}</td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ height: '10px', width: '10px', borderRadius: '50%', background: s.enabled ? '#67c23a' : '#c0c4cc', display: 'inline-block' }}></span>
                      <span style={{ fontSize: '0.9rem', fontWeight: '500', color: s.enabled ? '#303133' : '#909399' }}>
                        {s.enabled ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      {s.name === 'company_careers' && <span style={{ background: '#ecf5ff', color: '#409eff', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>DISCOVERY</span>}
                      {s.name === 'mock' && <span style={{ background: '#ecf5ff', color: '#409eff', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>DISCOVERY</span>}
                      {s.name === 'linkedin' && <span style={{ background: '#fdf6ec', color: '#e6a23c', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>HUMAN_ASSISTED</span>}
                      <span style={{ background: '#f4f4f5', color: '#909399', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>{s.source_type}</span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.6rem' }}>
                      {s.enabled && (s.name === 'company_careers' || s.name === 'mock') ? (
                        <button
                          onClick={() => handleRunDiscovery(s.name)}
                          disabled={discovering}
                          style={{ padding: '0.4rem 0.8rem', background: '#67c23a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}
                        >
                          Run
                        </button>
                      ) : null}
                      <button
                        onClick={() => handleConfigureSource(s.name)}
                        style={{ padding: '0.4rem 0.8rem', border: '1px solid #dcdfe6', background: '#fff', color: '#606266', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}
                      >
                        Configure
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Configuration Panel */}
          {selectedConfigName && configData && (
            <div style={{ border: '1px solid #409eff', borderRadius: '8px', background: '#fbfdff', padding: '1.5rem', boxShadow: '0 4px 12px rgba(64,158,255,0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem' }}>
                <h3 style={{ margin: 0, color: '#303133' }}>Configure Setup: {selectedConfigName.toUpperCase()}</h3>
                <button
                  onClick={() => { setSelectedConfigName(null); setConfigData(null); }}
                  style={{ background: 'none', border: 'none', color: '#909399', cursor: 'pointer', fontSize: '1.1rem' }}
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={configData.enabled}
                      onChange={(e) => setConfigData({ ...configData, enabled: e.target.checked })}
                    />
                    <strong>Enable Source</strong>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={configData.discovery_enabled}
                      onChange={(e) => setConfigData({ ...configData, discovery_enabled: e.target.checked })}
                    />
                    <strong>Enable Job Discovery</strong>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', opacity: 0.7 }}>
                    <input
                      type="checkbox"
                      disabled
                      checked={configData.application_enabled}
                      onChange={(e) => setConfigData({ ...configData, application_enabled: e.target.checked })}
                    />
                    <strong>Enable Automation (Blocked)</strong>
                  </label>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.2rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: '#606266' }}>Max Jobs per Run</label>
                    <input
                      type="number"
                      value={configData.max_jobs_per_run}
                      onChange={(e) => setConfigData({ ...configData, max_jobs_per_run: e.target.value })}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #dcdfe6' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: '#606266' }}>Max Pages per Run</label>
                    <input
                      type="number"
                      value={configData.max_pages_per_run}
                      onChange={(e) => setConfigData({ ...configData, max_pages_per_run: e.target.value })}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #dcdfe6' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: '#606266' }}>Delay Between Requests (s)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={configData.rate_limit}
                      onChange={(e) => setConfigData({ ...configData, rate_limit: e.target.value })}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #dcdfe6' }}
                    />
                  </div>
                </div>

                {selectedConfigName === 'company_careers' && (
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: '#606266' }}>
                      Company Selector Setup Configuration (JSON)
                    </label>
                    <textarea
                      rows={12}
                      value={JSON.stringify(configData.configuration, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value)
                          setConfigData({ ...configData, configuration: parsed })
                        } catch (err) {
                          // Allow editing invalid JSON without instantly crashing
                        }
                      }}
                      style={{ width: '100%', fontFamily: 'monospace', padding: '0.6rem', borderRadius: '4px', border: '1px solid #dcdfe6' }}
                    />
                  </div>
                )}

                <div style={{ display: 'flex', gap: '0.8rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => { setSelectedConfigName(null); setConfigData(null); }}
                    style={{ padding: '0.6rem 1.2rem', borderRadius: '4px', border: '1px solid #dcdfe6', background: '#fff', color: '#606266', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingConfig}
                    style={{ padding: '0.6rem 1.2rem', borderRadius: '4px', background: '#1976d2', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: '600' }}
                  >
                    {savingConfig ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Stats & Discovery Runs */}
      {activeTab === 'stats' && (
        <div>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ background: '#e3f2fd', padding: '1rem 1.5rem', borderRadius: '8px', borderLeft: '5px solid #1976d2' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#606266', fontSize: '0.9rem', textTransform: 'uppercase' }}>Total Catalog Jobs</h4>
                <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#2c3e50' }}>{stats.total_jobs}</div>
                <div style={{ fontSize: '0.85rem', color: '#606266', marginTop: '0.3rem' }}>Active listings: {stats.active_jobs}</div>
              </div>
              <div style={{ background: '#faecd8', padding: '1rem 1.5rem', borderRadius: '8px', borderLeft: '5px solid #e6a23c' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#606266', fontSize: '0.9rem', textTransform: 'uppercase' }}>Deduplication Status</h4>
                <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#2c3e50' }}>{stats.potential_duplicates}</div>
                <div style={{ fontSize: '0.85rem', color: '#606266', marginTop: '0.3rem' }}>Potential cross-source duplicates: {stats.potential_duplicates}</div>
              </div>
              <div style={{ background: '#f0f9eb', padding: '1rem 1.5rem', borderRadius: '8px', borderLeft: '5px solid #67c23a' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#606266', fontSize: '0.9rem', textTransform: 'uppercase' }}>Discovery Health</h4>
                <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#2c3e50' }}>{stats.enabled_sources} / {stats.total_sources}</div>
                <div style={{ fontSize: '0.85rem', color: '#606266', marginTop: '0.3rem' }}>Discovered today: {stats.jobs_discovered_today}</div>
              </div>
            </div>
          )}

          <h4 style={{ color: '#2c3e50', fontSize: '1.1rem', marginBottom: '0.8rem' }}>Discovery Run History & Audit Logs</h4>
          <div style={{ border: '1px solid #e4e7ed', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f5f7fa', textAlign: 'left', borderBottom: '1px solid #e4e7ed' }}>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Run ID</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Started At</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Status</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Jobs Found</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Created</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Duplicates</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Pages</th>
                  <th style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: '#909399' }}>Requests</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #e4e7ed', fontSize: '0.9rem' }}>
                    <td style={{ padding: '0.8rem 1rem', fontWeight: '600' }}>#{r.id}</td>
                    <td style={{ padding: '0.8rem 1rem', color: '#606266' }}>{new Date(r.started_at).toLocaleString()}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        background: r.status === 'COMPLETED' ? '#f0f9eb' : r.status === 'RUNNING' ? '#ecf5ff' : '#fde2e2',
                        color: r.status === 'COMPLETED' ? '#67c23a' : r.status === 'RUNNING' ? '#409eff' : '#f56c6c'
                      }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.8rem 1rem' }}>{r.jobs_discovered}</td>
                    <td style={{ padding: '0.8rem 1rem', color: '#67c23a', fontWeight: '600' }}>{r.jobs_created}</td>
                    <td style={{ padding: '0.8rem 1rem', color: '#e6a23c' }}>{r.duplicates}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>{r.pages_visited || 1}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>{r.requests_made || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedJob && (
        <div style={{ border: '2px solid #1976d2', padding: '1.5rem', borderRadius: '8px', background: '#f4f8fc', marginTop: '1.5rem', boxShadow: '0 4px 12px rgba(25,118,210,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #dcdfe6', paddingBottom: '0.8rem', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.3rem', color: '#2c3e50' }}>{selectedJob.title}</h3>
              <span style={{ fontSize: '1rem', color: '#1976d2', fontWeight: '600', display: 'block', marginTop: '0.2rem' }}>{selectedJob.company_name}</span>
            </div>
            <button
              onClick={() => setSelectedJob(null)}
              style={{ padding: '0.4rem 0.8rem', border: '1px solid #dcdfe6', background: '#fff', borderRadius: '4px', cursor: 'pointer' }}
            >
              Close
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1.2rem', fontSize: '0.9rem', color: '#606266' }}>
            <p style={{ margin: 0 }}><strong>Location:</strong> {selectedJob.normalized_location || selectedJob.location || 'Remote'}</p>
            <p style={{ margin: 0 }}><strong>Workplace Arrangement:</strong> {selectedJob.workplace_type}</p>
            <p style={{ margin: 0 }}><strong>Employment Type:</strong> {selectedJob.employment_type}</p>
            <p style={{ margin: 0 }}><strong>Salary Bounds:</strong> {selectedJob.salary_min ? `$${selectedJob.salary_min.toLocaleString()} - $${selectedJob.salary_max?.toLocaleString()} ${selectedJob.salary_currency}` : 'Unspecified'}</p>
            <p style={{ margin: 0 }}><strong>URL Verification Status:</strong> <span style={{ fontWeight: '600', color: selectedJob.url_status === 'REACHABLE' ? 'green' : 'orange' }}>{selectedJob.url_status || 'UNKNOWN'}</span></p>
          </div>
          {selectedJob.job_url && (
            <p style={{ fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
              <strong>Direct Job Posting Link:</strong>{' '}
              <a href={selectedJob.job_url} target="_blank" rel="noreferrer" style={{ color: '#1976d2', textDecoration: 'none' }}>
                {selectedJob.job_url}
              </a>
            </p>
          )}
          <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #e4e7ed', maxHeight: '200px', overflowY: 'auto' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#303133', fontSize: '0.95rem' }}>Detailed Job Description:</strong>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#606266', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>{selectedJob.description}</p>
          </div>
        </div>
      )}
    </div>
  )
}
