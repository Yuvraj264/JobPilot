import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/matching'

export default function MatchDashboardManager() {
  const [activeTab, setActiveTab] = useState('dashboard') // 'dashboard' | 'matches' | 'config'
  const [stats, setStats] = useState(null)
  const [matches, setMatches] = useState([])
  const [runs, setRuns] = useState([])
  const [config, setConfig] = useState(null)
  
  const [filterRecommendation, setFilterRecommendation] = useState('')
  const [filterMinScore, setFilterMinScore] = useState('')
  const [selectedMatch, setSelectedMatch] = useState(null)
  
  const [matching, setMatching] = useState(false)
  const [message, setMessage] = useState('')

  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`)
      if (res.ok) setStats(await res.json())

      const resRuns = await fetch(`${API_BASE}/runs`)
      if (resRuns.ok) setRuns(await resRuns.json())
    } catch (err) {
      console.error('Error loading matching stats:', err)
    }
  }

  const loadMatches = async () => {
    try {
      let url = `${API_BASE}/jobs?limit=100`
      if (filterRecommendation) url += `&recommendation=${filterRecommendation}`
      if (filterMinScore) url += `&min_score=${filterMinScore}`
      const res = await fetch(url)
      if (res.ok) setMatches(await res.json())
    } catch (err) {
      console.error('Error loading job matches:', err)
    }
  }

  const loadConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/config`)
      if (res.ok) setConfig(await res.json())
    } catch (err) {
      console.error('Error loading matching config:', err)
    }
  }

  useEffect(() => {
    loadStats()
    loadMatches()
    loadConfig()
  }, [filterRecommendation, filterMinScore])

  const handleRunBatchMatching = async () => {
    setMatching(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/run`, { method: 'POST' })
      if (res.ok) {
        const runRes = await res.json()
        setMessage(`Batch matching run completed! Evaluated ${runRes.jobs_evaluated} jobs (${runRes.apply_count} APPLY, ${runRes.review_count} REVIEW, ${runRes.skip_count} SKIP).`)
        loadStats()
        loadMatches()
      } else {
        const errData = await res.json()
        setMessage(`Matching error: ${errData.detail || 'Failed to run matching'}`)
      }
    } catch (err) {
      setMessage('Failed to execute batch matching run.')
    } finally {
      setMatching(false)
    }
  }

  const getScoreBadgeColor = (score, recommendation) => {
    if (recommendation === 'APPLY' || score >= 85) return { bg: '#e8f5e9', text: '#2e7d32', border: '#a5d6a7' }
    if (recommendation === 'REVIEW' || score >= 70) return { bg: '#fff3e0', text: '#ef6c00', border: '#ffe0b2' }
    return { bg: '#ffebee', text: '#c62828', border: '#ef9a9a' }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Job Matching & Selection Engine</h2>

      {message && <div style={{ background: '#e8f5e9', padding: '0.6rem', marginBottom: '1rem', borderRadius: '4px', color: '#2e7d32' }}>{message}</div>}

      {/* Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', background: '#f8f9fa', padding: '0.8rem', borderRadius: '6px' }}>
        <div>
          <strong>AI Selection Engine</strong> — Computes hard eligibility, weighted match scores & transparent explanations.
        </div>
        <button
          onClick={handleRunBatchMatching}
          disabled={matching}
          style={{ padding: '0.5rem 1.2rem', background: '#2e7d32', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {matching ? 'Evaluating Active Jobs...' : 'Run Batch Matching'}
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #ccc', marginBottom: '1rem' }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'dashboard' ? '3px solid #2e7d32' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'dashboard' ? 'bold' : 'normal' }}
        >
          Dashboard Metrics
        </button>
        <button
          onClick={() => setActiveTab('matches')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'matches' ? '3px solid #2e7d32' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'matches' ? 'bold' : 'normal' }}
        >
          Match Results ({matches.length})
        </button>
        <button
          onClick={() => setActiveTab('config')}
          style={{ padding: '0.5rem 1rem', border: 'none', borderBottom: activeTab === 'config' ? '3px solid #2e7d32' : 'none', background: 'none', cursor: 'pointer', fontWeight: activeTab === 'config' ? 'bold' : 'normal' }}
        >
          Scoring Config
        </button>
      </div>

      {/* Tab 1: Dashboard View */}
      {activeTab === 'dashboard' && stats && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#e3f2fd', padding: '1rem', borderRadius: '6px', textAlign: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.8rem', color: '#1565c0' }}>{stats.jobs_evaluated}</h3>
              <p style={{ margin: '0.2rem 0', color: '#555' }}>Jobs Evaluated</p>
              <small style={{ color: '#777' }}>Eligible: {stats.eligible}</small>
            </div>
            <div style={{ background: '#e8f5e9', padding: '1rem', borderRadius: '6px', textAlign: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.8rem', color: '#2e7d32' }}>{stats.apply}</h3>
              <p style={{ margin: '0.2rem 0', color: '#555' }}>Recommended APPLY</p>
              <small style={{ color: '#777' }}>Review: {stats.review} | Skip: {stats.skip}</small>
            </div>
            <div style={{ background: '#f3e5f5', padding: '1rem', borderRadius: '6px', textAlign: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.8rem', color: '#7b1fa2' }}>{stats.average_score}%</h3>
              <p style={{ margin: '0.2rem 0', color: '#555' }}>Average Match Score</p>
            </div>
          </div>

          <h4>Recent Batch Runs</h4>
          {runs.length === 0 ? (
            <p style={{ color: '#777' }}>No matching runs recorded yet. Click 'Run Batch Matching' above to evaluate jobs.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {runs.map((r) => (
                <li key={r.id} style={{ borderBottom: '1px solid #eee', padding: '0.5rem 0', fontSize: '0.9rem' }}>
                  <strong>Run #{r.id}</strong> — Status: {r.status} | Evaluated: {r.jobs_evaluated} | APPLY: {r.apply_count} | REVIEW: {r.review_count} | SKIP: {r.skip_count}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Tab 2: Match Results View */}
      {activeTab === 'matches' && (
        <div>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <select
              value={filterRecommendation}
              onChange={(e) => setFilterRecommendation(e.target.value)}
              style={{ padding: '0.5rem', flex: 1 }}
            >
              <option value="">All Recommendations</option>
              <option value="APPLY">APPLY (High Suitability)</option>
              <option value="REVIEW">REVIEW (Moderate Suitability)</option>
              <option value="SKIP">SKIP (Low / Hard Failure)</option>
            </select>

            <select
              value={filterMinScore}
              onChange={(e) => setFilterMinScore(e.target.value)}
              style={{ padding: '0.5rem', flex: 1 }}
            >
              <option value="">All Match Scores</option>
              <option value="85">Score &ge; 85%</option>
              <option value="70">Score &ge; 70%</option>
              <option value="50">Score &ge; 50%</option>
            </select>
          </div>

          {matches.length === 0 ? (
            <p style={{ color: '#777' }}>No match records found. Click 'Run Batch Matching' to evaluate active catalog jobs.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {matches.map((m) => {
                const badge = getScoreBadgeColor(m.overall_score, m.recommendation)
                return (
                  <li
                    key={m.id}
                    style={{
                      border: `1px solid ${badge.border}`,
                      padding: '1rem',
                      marginBottom: '0.8rem',
                      borderRadius: '8px',
                      background: '#fff',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h3 style={{ margin: '0 0 0.3rem 0', fontSize: '1.1rem' }}>
                          {m.job?.title} <span style={{ fontWeight: 'normal', color: '#666' }}>at {m.job?.company_name}</span>
                        </h3>
                        <div style={{ fontSize: '0.85rem', color: '#555', marginBottom: '0.4rem' }}>
                          📍 {m.job?.normalized_location || m.job?.location || 'Location Unspecified'} | 💼 {m.job?.employment_type} | 🏠 {m.job?.workplace_type}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: badge.text }}>
                          {m.overall_score}%
                        </span>
                        <div style={{ marginTop: '0.2rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 'bold', background: badge.bg, color: badge.text, padding: '2px 8px', borderRadius: '12px' }}>
                            {m.recommendation}
                          </span>
                        </div>
                      </div>
                    </div>

                    {m.strengths && m.strengths.length > 0 && (
                      <div style={{ fontSize: '0.85rem', color: '#2e7d32', marginTop: '0.4rem' }}>
                        ✓ {m.strengths[0]}
                      </div>
                    )}
                    {m.concerns && m.concerns.length > 0 && (
                      <div style={{ fontSize: '0.85rem', color: '#c62828', marginTop: '0.2rem' }}>
                        ⚠ {m.concerns[0]}
                      </div>
                    )}

                    <div style={{ marginTop: '0.8rem', textAlign: 'right' }}>
                      <button onClick={() => setSelectedMatch(m)} style={{ padding: '0.4rem 0.8rem', cursor: 'pointer' }}>
                        View Detailed Explanation
                      </button>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}

      {/* Tab 3: Config View */}
      {activeTab === 'config' && config && (
        <div style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '6px' }}>
          <h4>Active Scoring Component Weights</h4>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>Skills Weight: <strong>{(config.weight_skills * 100).toFixed(0)}%</strong></li>
            <li>Role Similarity Weight: <strong>{(config.weight_role * 100).toFixed(0)}%</strong></li>
            <li>Experience Bounds Weight: <strong>{(config.weight_experience * 100).toFixed(0)}%</strong></li>
            <li>Location Weight: <strong>{(config.weight_location * 100).toFixed(0)}%</strong></li>
            <li>Workplace Type Weight: <strong>{(config.weight_workplace * 100).toFixed(0)}%</strong></li>
            <li>Employment Type Weight: <strong>{(config.weight_employment * 100).toFixed(0)}%</strong></li>
            <li>Education Weight: <strong>{(config.weight_education * 100).toFixed(0)}%</strong></li>
            <li>Semantic Similarity Weight: <strong>{(config.weight_semantic * 100).toFixed(0)}%</strong></li>
          </ul>

          <h4 style={{ marginTop: '1rem' }}>Recommendation Thresholds</h4>
          <p>APPLY Threshold: <strong>&ge; {config.threshold_apply}%</strong></p>
          <p>REVIEW Threshold: <strong>&ge; {config.threshold_review}%</strong></p>
        </div>
      )}

      {/* Detail Modal */}
      {selectedMatch && (
        <div style={{ border: '2px solid #2e7d32', padding: '1.2rem', borderRadius: '8px', background: '#f0fdf4', marginTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Match Explanation: {selectedMatch.job?.title}</h3>
            <button onClick={() => setSelectedMatch(null)}>Close</button>
          </div>

          <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '6px', marginTop: '0.5rem', border: '1px solid #ddd' }}>
            <p style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold' }}>Summary: {selectedMatch.explanation?.summary}</p>
            
            <h4>Component Breakdown Score</h4>
            {Object.entries(selectedMatch.component_scores || {}).map(([key, val]) => (
              <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: '0.3rem' }}>
                <span style={{ width: '120px', fontSize: '0.85rem', textTransform: 'capitalize' }}>{key}:</span>
                <div style={{ flex: 1, background: '#eee', height: '10px', borderRadius: '5px', overflow: 'hidden', marginRight: '0.5rem' }}>
                  <div style={{ width: `${val}%`, background: val >= 80 ? '#2e7d32' : val >= 60 ? '#ef6c00' : '#c62828', height: '100%' }}></div>
                </div>
                <span style={{ fontSize: '0.85rem', fontWeight: 'bold', width: '45px' }}>{val}%</span>
              </div>
            ))}

            {selectedMatch.hard_failures && selectedMatch.hard_failures.length > 0 && (
              <div style={{ marginTop: '0.8rem', background: '#ffebee', padding: '0.5rem', borderRadius: '4px', color: '#c62828' }}>
                <strong>Hard Failures:</strong>
                <ul style={{ margin: '0.3rem 0 0 1.2rem', padding: 0 }}>
                  {selectedMatch.hard_failures.map((hf, i) => <li key={i}>{hf}</li>)}
                </ul>
              </div>
            )}

            <h4 style={{ marginTop: '0.8rem', color: '#2e7d32' }}>Key Strengths</h4>
            <ul>
              {(selectedMatch.strengths || []).map((s, i) => <li key={i}>{s}</li>)}
            </ul>

            <h4 style={{ marginTop: '0.5rem', color: '#c62828' }}>Potential Concerns</h4>
            <ul>
              {(selectedMatch.concerns || []).map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
