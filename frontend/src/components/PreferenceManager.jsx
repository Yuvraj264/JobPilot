import React, { useState, useEffect } from 'react'

export default function PreferenceManager({ userId }) {
  const [preferences, setPreferences] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  
  // Explicit item adding states
  const [newRole, setNewRole] = useState('')
  const [newSkill, setNewSkill] = useState('')
  const [newLocation, setNewLocation] = useState('')
  const [newCompany, setNewCompany] = useState('')

  const fetchPrefsAndSuggestions = async () => {
    setLoading(true)
    try {
      const [prefRes, sugRes] = await Promise.all([
        fetch('http://localhost:8000/api/personalization/preferences', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/personalization/preferences/suggestions', { headers: { 'X-User-Id': userId } })
      ])
      if (prefRes.ok) setPreferences(await prefRes.json())
      if (sugRes.ok) setSuggestions(await sugRes.json())
    } catch (err) {
      console.error('Failed to load preferences:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPrefsAndSuggestions()
  }, [userId])

  const handleUpdatePreference = async (updatedFields) => {
    try {
      const res = await fetch('http://localhost:8000/api/personalization/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({ ...preferences, ...updatedFields })
      })
      if (res.ok) {
        setMessage('Preferences updated successfully!')
        fetchPrefsAndSuggestions()
      } else {
        setMessage('Failed to update preferences.')
      }
    } catch (err) {
      console.error(err)
      setMessage('Error updating preferences.')
    }
  }

  const handleAddExplicit = (category, value) => {
    if (!value) return
    const key = `preferred_${category}`
    const currentList = preferences[key] || []
    const updatedList = [...currentList, { value, source: 'USER_EXPLICIT', strength: 1.0, confidence: 1.0 }]
    handleUpdatePreference({ [key]: updatedList })
    
    // Clear state
    if (category === 'roles') setNewRole('')
    if (category === 'skills') setNewSkill('')
    if (category === 'locations') setNewLocation('')
    if (category === 'companies') setNewCompany('')
  }

  const handleRemoveExplicit = (category, valueToRemove) => {
    const key = `preferred_${category}`
    const currentList = preferences[key] || []
    const updatedList = currentList.filter(item => item.value !== valueToRemove)
    handleUpdatePreference({ [key]: updatedList })
  }

  const handleAcceptSuggestion = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/api/personalization/preferences/suggestions/${id}/accept`, {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage('Suggestion applied successfully!')
        fetchPrefsAndSuggestions()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleDismissSuggestion = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/api/personalization/preferences/suggestions/${id}/dismiss`, {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage('Suggestion dismissed.')
        fetchPrefsAndSuggestions()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleRollback = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/personalization/rollback', {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage('Successfully rolled back to the previous configuration version!')
        fetchPrefsAndSuggestions()
      } else {
        setMessage('No previous preference configuration exists to rollback.')
      }
    } catch (err) {
      console.error(err)
      setMessage('Error performing rollback.')
    }
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to permanently clear all personalization history, metrics, and preferences? This cannot be undone.')) {
      return
    }
    try {
      const res = await fetch('http://localhost:8000/api/personalization/history/clear', {
        method: 'DELETE',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        setMessage('All personalization data has been cleared successfully.')
        fetchPrefsAndSuggestions()
      }
    } catch (err) {
      console.error(err)
      setMessage('Error clearing history.')
    }
  }

  if (loading) return <div style={{ padding: '2rem', color: '#666' }}>Loading preference profile...</div>
  if (!preferences) return <div style={{ padding: '2rem', color: '#666' }}>No preference profile found.</div>

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <h2>My Preference Engine Dashboard</h2>
      <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' }}>
        Control explicit preferences, customize answer writing styles, and accept smart optimization recommendations safely.
      </p>

      {message && (
        <div style={{
          padding: '1rem',
          background: '#eff6ff',
          color: '#1e40af',
          borderRadius: '8px',
          border: '1px solid #bfdbfe',
          marginBottom: '1.5rem',
          fontWeight: '500',
          fontSize: '0.9rem'
        }}>
          {message}
        </div>
      )}

      {/* Toggle & Writing Style Preferences */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '1.5rem',
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
        marginBottom: '2rem'
      }}>
        <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>⚙️ Personalization Controls</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 'bold', color: '#334155', marginBottom: '0.5rem' }}>
              Enable Smart Personalization Match Adjustment
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="checkbox"
                checked={preferences.enabled}
                onChange={(e) => handleUpdatePreference({ enabled: e.target.checked })}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.9rem', color: '#475569' }}>
                {preferences.enabled ? 'Personalization ON (adjusts matching based on behavior/feedback)' : 'Personalization OFF'}
              </span>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 'bold', color: '#334155', marginBottom: '0.5rem' }}>
              AI Answer Generation Tone & Style
            </label>
            <select
              value={preferences.answer_style}
              onChange={(e) => handleUpdatePreference({ answer_style: e.target.value })}
              style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', width: '100%' }}
            >
              <option value="Concise">Concise (shorter, direct response)</option>
              <option value="Professional">Professional (traditional business style)</option>
              <option value="Conversational">Conversational (friendly, engaging tone)</option>
              <option value="Technical">Technical (focuses on engineering specifics)</option>
              <option value="Achievement-focused">Achievement-focused (highlights metrics/actions)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Suggested & Inferred Preferences */}
      {suggestions.length > 0 && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '16px',
          padding: '1.5rem',
          marginBottom: '2rem'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#991b1b' }}>🚨 Pending Optimization Suggestions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {suggestions.map((sug) => (
              <div key={sug.id} style={{
                background: '#ffffff',
                border: '1px solid #fee2e2',
                borderRadius: '8px',
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <div>
                  <div style={{ fontWeight: 'bold', color: '#7f1d1d', fontSize: '0.9rem' }}>{sug.suggestion}</div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>Evidence: {sug.evidence}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => handleAcceptSuggestion(sug.id)} style={{ background: '#16a34a', color: '#fff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>Accept</button>
                  <button onClick={() => handleDismissSuggestion(sug.id)} style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>Dismiss</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explicit Preference Lists Manager */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Roles */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', color: '#0f172a' }}>Preferred Target Roles</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="e.g. QA Automation"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              style={{ flex: 1, padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '4px' }}
            />
            <button onClick={() => handleAddExplicit('roles', newRole)} style={{ background: '#4f46e5', color: '#fff', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Add</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {preferences.preferred_roles?.map((r, idx) => (
              <span key={idx} style={{ background: '#f1f5f9', color: '#334155', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                {r.value}
                <button onClick={() => handleRemoveExplicit('roles', r.value)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#ef4444', fontWeight: 'bold' }}>×</button>
              </span>
            ))}
          </div>
        </div>

        {/* Skills */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', color: '#0f172a' }}>Preferred Technologies</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="e.g. Selenium"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              style={{ flex: 1, padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '4px' }}
            />
            <button onClick={() => handleAddExplicit('skills', newSkill)} style={{ background: '#4f46e5', color: '#fff', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Add</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {preferences.preferred_skills?.map((s, idx) => (
              <span key={idx} style={{ background: '#f1f5f9', color: '#334155', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                {s.value}
                <button onClick={() => handleRemoveExplicit('skills', s.value)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#ef4444', fontWeight: 'bold' }}>×</button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Configuration Rollback & Deletion Options */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #cbd5e1',
        borderRadius: '16px',
        padding: '1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <h4 style={{ margin: '0 0 0.25rem 0', color: '#0f172a' }}>Preference Versioning & Privacy Control</h4>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Current Config Version: V{preferences.version}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={handleRollback} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '0.5rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}>
            Undo Last Config Change
          </button>
          <button onClick={handleClearHistory} style={{ background: '#94a3b8', color: '#fff', border: 'none', padding: '0.5rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}>
            Clear History & Reset
          </button>
        </div>
      </div>
    </div>
  )
}
