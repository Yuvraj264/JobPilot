import React, { useState, useEffect } from 'react'

export default function SourceManager({ userId }) {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingSource, setEditingSource] = useState(null)
  const [config, setConfig] = useState(null)
  const [message, setMessage] = useState('')

  const loadSources = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/jobs/sources', {
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) setSources(await res.json())
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSources()
  }, [userId])

  const toggleSource = async (sourceName, currentlyEnabled) => {
    const action = currentlyEnabled ? 'disable' : 'enable'
    try {
      const res = await fetch(`http://localhost:8000/api/jobs/sources/${sourceName}/${action}`, {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage(`Source ${sourceName} ${currentlyEnabled ? 'disabled' : 'enabled'} successfully.`)
        loadSources()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleEditConfig = async (sourceName) => {
    setEditingSource(sourceName)
    try {
      const res = await fetch(`http://localhost:8000/api/jobs/sources/${sourceName}/config`, {
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setConfig(await res.json())
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleSaveConfig = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch(`http://localhost:8000/api/jobs/sources/${editingSource}/config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify(config)
      })
      if (res.ok) {
        setMessage(`Configuration for ${editingSource} saved!`)
        setEditingSource(null)
        setConfig(null)
        loadSources()
      }
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) return <div style={{ padding: '2rem', color: '#666' }}>Loading sources...</div>

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <h2>Job Platform Adapters & Sources</h2>
      <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        Configure connected platforms and capability rules for autonomous ingestion and submission execution.
      </p>

      {message && <div style={{ background: '#ecfdf5', color: '#047857', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem' }}>{message}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {sources.map((src) => (
          <div key={src.id} style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>{src.display_name}</h4>
                <span style={{
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '9999px',
                  fontWeight: 'bold',
                  background: src.enabled ? '#ecfdf5' : '#f1f5f9',
                  color: src.enabled ? '#059669' : '#64748b'
                }}>
                  {src.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#64748b', margin: '0.25rem 0' }}>
                Type: <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: '4px' }}>{src.source_type}</code>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#64748b', margin: '0.25rem 0' }}>
                Discovery Capabilities: <span style={{ color: '#4f46e5', fontWeight: '500' }}>SUPPORTED</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#64748b', margin: '0.25rem 0' }}>
                Application Capabilities: <span style={{ color: '#059669', fontWeight: '500' }}>HUMAN_ASSISTED</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem', borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem' }}>
              <button
                onClick={() => toggleSource(src.name, src.enabled)}
                style={{
                  flex: 1,
                  padding: '0.4rem',
                  background: src.enabled ? '#fee2e2' : '#ecfdf5',
                  color: src.enabled ? '#b91c1c' : '#047857',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '0.8rem'
                }}
              >
                {src.enabled ? 'Disable' : 'Enable'}
              </button>
              <button
                onClick={() => handleEditConfig(src.name)}
                style={{
                  padding: '0.4rem 0.75rem',
                  background: '#f1f5f9',
                  color: '#334155',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '500',
                  fontSize: '0.8rem'
                }}
              >
                Configure
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Config Modal */}
      {editingSource && config && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15,23,42,0.3)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#ffffff',
            padding: '2rem',
            borderRadius: '16px',
            maxWidth: '460px',
            width: '100%',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>Configure {editingSource}</h3>
            <form onSubmit={handleSaveConfig} style={{ display: 'grid', gap: '1rem' }}>
              <label>
                <input
                  type="checkbox"
                  checked={config.enabled}
                  onChange={e => setConfig({ ...config, enabled: e.target.checked })}
                /> Enable Source Ingestion & Execution
              </label>

              <label style={{ display: 'block' }}>Max Jobs per run:
                <input
                  type="number"
                  value={config.max_jobs_per_run || 10}
                  onChange={e => setConfig({ ...config, max_jobs_per_run: parseInt(e.target.value) })}
                  style={inputStyle}
                />
              </label>

              <label style={{ display: 'block' }}>Rate limit delay (seconds):
                <input
                  type="number"
                  value={config.rate_limit || 2}
                  onChange={e => setConfig({ ...config, rate_limit: parseInt(e.target.value) })}
                  style={inputStyle}
                />
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setEditingSource(null)} style={cancelBtnStyle}>Cancel</button>
                <button type="submit" style={saveBtnStyle}>Save Config</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  width: '100%',
  padding: '0.45rem',
  borderRadius: '6px',
  border: '1px solid #cbd5e1',
  marginTop: '0.25rem',
  boxSizing: 'border-box'
}

const cancelBtnStyle = {
  padding: '0.5rem 1rem',
  background: '#f1f5f9',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: '600'
}

const saveBtnStyle = {
  padding: '0.5rem 1rem',
  background: '#4f46e5',
  color: '#ffffff',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: '600'
}
