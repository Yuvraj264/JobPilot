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
  const [selectedJob, setSelectedJob] = useState(null)
  
  const [discovering, setDiscovering] = useState(false)
  const [message, setMessage] = useState('')

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
  }, [searchQuery, filterWorkplace])

  const handleRunDiscovery = async (sourceName = null) => {
    setDiscovering(true)
    setMessage('')
    try {
      const url = sourceName ? `${API_BASE}/discover/${sourceName}` : `${API_BASE}/discover`
      const res = await fetch(url, { method: 'POST' })
      if (res.ok) {
        const summary = await res.json()
        setMessage(`Discovery completed! Created ${summary.jobs_created || summary[0]?.jobs_created || 0} new job records.`)
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

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Job Source Architecture & Discovery Catalog</h2>

      {message && <div style={{ background: '#e8f5e9', padding: '0.5rem', marginBottom: '1rem', borderRadius: '4px', color: '#2e7d32' }}>{message}</div>}

      {/* Discovery Trigger Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', background: '#f5f5f5', padding: '0.8rem', borderRadius: '6px' }}>
        <div>
          <strong>Discovery Engine</strong> — Adheres to platform compliance boundaries.
        </div>
        <button
          onClick={() => handleRunDiscovery()}
          disabled={discovering}
          style={{ padding: '0.5rem 1rem', background: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {discovering ? 'Running Mock Discovery...' : 'Run Mock Discovery'}
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #ccc', marginBottom: '1rem' }}>
        <button
          onClick={() => setActiveTab('jobs')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'jobs' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'jobs' ? 'bold' : 'normal' }}
        >
          Discovered Jobs ({jobs.length})
        </button>
        <button
          onClick={() => setActiveTab('sources')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'sources' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'sources' ? 'bold' : 'normal' }}
        >
          Job Sources ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'stats' ? '3px solid #1976d2' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'stats' ? 'bold' : 'normal' }}
        >
          Stats & Runs
        </button>
      </div>

      {/* Tab 1: Jobs View */}
      {activeTab === 'jobs' && (
        <div>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Search by title, company, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ flex: 1, padding: '0.5rem' }}
            />
            <select value={filterWorkplace} onChange={(e) => setFilterWorkplace(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="">All Workplace Types</option>
              <option value="REMOTE">Remote</option>
              <option value="HYBRID">Hybrid</option>
              <option value="ONSITE">Onsite</option>
            </select>
          </div>

          {jobs.length === 0 ? (
            <p style={{ color: '#777' }}>No jobs found. Click 'Run Mock Discovery' above to ingest synthetic jobs.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {jobs.map((j) => (
                <li
                  key={j.id}
                  style={{
                    border: '1px solid #ddd',
                    padding: '0.8rem',
                    marginBottom: '0.5rem',
                    borderRadius: '6px',
                    background: '#fff',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <strong style={{ fontSize: '1.05rem' }}>{j.title}</strong> — {j.company_name}
                    <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.2rem' }}>
                      📍 {j.normalized_location || j.location || 'Location Not Specified'} | 💼 {j.employment_type} | 🏠 {j.workplace_type}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', background: j.status === 'DUPLICATE' ? '#ffebee' : j.status === 'POTENTIAL_DUPLICATE' ? '#fff3e0' : '#e8f5e9', padding: '3px 6px', borderRadius: '4px' }}>
                      {j.status}
                    </span>
                    <button onClick={() => inspectJob(j.id)}>Details</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Tab 2: Sources View */}
      {activeTab === 'sources' && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f5f5f5', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd' }}>Source Name</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd' }}>Type</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd' }}>State</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id}>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>
                    <strong>{s.display_name}</strong> ({s.name})
                  </td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>{s.source_type}</td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>
                    {s.enabled ? (
                      <span style={{ color: 'green', fontWeight: 'bold' }}>Enabled</span>
                    ) : (
                      <span style={{ color: '#888' }}>Disabled (Placeholder)</span>
                    )}
                  </td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>
                    {s.name === 'mock' ? (
                      <button onClick={() => handleRunDiscovery(s.name)}>Run Discovery</button>
                    ) : (
                      <button onClick={() => toggleSource(s.name, s.enabled)}>
                        {s.enabled ? 'Disable' : 'Enable'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Stats & Discovery Runs */}
      {activeTab === 'stats' && (
        <div>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ background: '#e3f2fd', padding: '1rem', borderRadius: '6px' }}>
                <h3>Total Jobs: {stats.total_jobs}</h3>
                <p>Active Jobs: {stats.active_jobs}</p>
              </div>
              <div style={{ background: '#fff3e0', padding: '1rem', borderRadius: '6px' }}>
                <h3>Duplicates: {stats.duplicate_jobs}</h3>
                <p>Potential Matches: {stats.potential_duplicates}</p>
              </div>
              <div style={{ background: '#e8f5e9', padding: '1rem', borderRadius: '6px' }}>
                <h3>Enabled Sources: {stats.enabled_sources} / {stats.total_sources}</h3>
                <p>Discovered Today: {stats.jobs_discovered_today}</p>
              </div>
            </div>
          )}

          <h4>Recent Discovery Runs</h4>
          <ul>
            {runs.map((r) => (
              <li key={r.id} style={{ marginBottom: '0.4rem', fontSize: '0.9rem' }}>
                <strong>Run #{r.id}</strong> — Status: {r.status} | Discovered: {r.jobs_discovered} | Created: {r.jobs_created} | Duplicates: {r.duplicates}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detail Modal */}
      {selectedJob && (
        <div style={{ border: '1px solid #1976d2', padding: '1rem', borderRadius: '6px', background: '#f0f7ff', marginTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h3>{selectedJob.title} — {selectedJob.company_name}</h3>
            <button onClick={() => setSelectedJob(null)}>Close</button>
          </div>
          <p><strong>Location:</strong> {selectedJob.normalized_location || selectedJob.location}</p>
          <p><strong>Workplace:</strong> {selectedJob.workplace_type} | <strong>Employment:</strong> {selectedJob.employment_type}</p>
          <p><strong>Salary Range:</strong> ${selectedJob.salary_min || 0} - ${selectedJob.salary_max || 0} {selectedJob.salary_currency}</p>
          {selectedJob.job_url && <p><strong>Job URL:</strong> <a href={selectedJob.job_url} target="_blank" rel="noreferrer">{selectedJob.job_url}</a></p>}
          <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '4px', marginTop: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
            <strong>Description:</strong>
            <p>{selectedJob.description}</p>
          </div>
        </div>
      )}
    </div>
  )
}
