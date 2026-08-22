import React, { useState, useEffect } from 'react'

export default function AnalyticsCenter({ userId }) {
  const [overview, setOverview] = useState(null)
  const [appsData, setAppsData] = useState(null)
  const [matchingData, setMatchingData] = useState(null)
  const [failuresData, setFailuresData] = useState(null)
  const [careerInsights, setCareerInsights] = useState(null)
  const [optimizationSuggestions, setOptimizationSuggestions] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      const [overRes, appRes, matchRes, failRes, careerRes, optRes] = await Promise.all([
        fetch('http://localhost:8000/api/analytics/overview', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/analytics/applications', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/analytics/matching', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/analytics/failures', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/analytics/career-insights', { headers: { 'X-User-Id': userId } }),
        fetch('http://localhost:8000/api/analytics/optimization-suggestions', { headers: { 'X-User-Id': userId } })
      ])

      if (overRes.ok) setOverview(await overRes.json())
      if (appRes.ok) setAppsData(await appRes.json())
      if (matchRes.ok) setMatchingData(await matchRes.json())
      if (failRes.ok) setFailuresData(await failRes.json())
      if (careerRes.ok) setCareerInsights(await careerRes.json())
      if (optRes.ok) setOptimizationSuggestions(await optRes.json())
    } catch (err) {
      console.error('Error loading analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [userId])

  if (loading) return <div style={{ padding: '2rem', color: '#666' }}>Loading Analytics Metrics...</div>

  // Defaults
  const stats = overview || {
    discovered: 0,
    matched: 0,
    selected: 0,
    prepared: 0,
    submitted: 0,
    failed: 0,
    awaiting_review: 0
  }

  const apps = appsData || {
    total: 0,
    submitted: 0,
    failed: 0,
    approved: 0,
    success_rate: 0.0,
    source_distribution: {}
  }

  const matching = matchingData || {
    average_score: 0.0,
    distribution: {}
  }

  const failures = failuresData || {
    total_failures: 0,
    categories: {}
  }

  // Calculate Funnel Conversion Percentages
  const getPercent = (num, den) => {
    if (!den || den === 0) return '0%'
    return `${((num / den) * 100).toFixed(0)}%`
  }

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <h2>Orchestration Funnel & Analytics</h2>
      <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' }}>
        Visualize pipeline funnel conversion rates, matching score spreads, and platform delivery statistics.
      </p>

      {/* Funnel Section */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '1.5rem',
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
        marginBottom: '2rem'
      }}>
        <h3 style={{ margin: '0 0 1.5rem 0', color: '#0f172a' }}>Application Pipeline Funnel</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            { step: 'Discovered', count: stats.discovered, desc: 'Total raw listings ingested' },
            { step: 'Matched', count: stats.matched, desc: 'Eligible matches above score limits', parent: stats.discovered },
            { step: 'Selected', count: stats.selected, desc: 'Qualified listings selected', parent: stats.matched },
            { step: 'Prepared', count: stats.prepared, desc: 'Application packages generated', parent: stats.selected },
            { step: 'Approved', count: stats.approved || stats.prepared - stats.awaiting_review, desc: 'Explicitly approved packages', parent: stats.prepared },
            { step: 'Submitted', count: stats.submitted, desc: 'Successfully delivered applications', parent: stats.approved }
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'grid', gridTemplateColumns: '150px 1fr 100px', alignItems: 'center', gap: '1rem' }}>
              <div style={{ fontWeight: '600', color: '#334155' }}>{item.step}</div>
              <div style={{ background: '#f1f5f9', height: '24px', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
                <div style={{
                  background: '#4f46e5',
                  height: '100%',
                  width: item.parent ? getPercent(item.count, item.parent) : '100%',
                  transition: 'width 0.4s'
                }}></div>
                <span style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '0.75rem',
                  color: '#ffffff',
                  fontWeight: 'bold'
                }}>
                  {item.desc}
                </span>
              </div>
              <div style={{ textAlign: 'right', fontWeight: 'bold', color: '#0f172a' }}>
                {item.count} {item.parent && <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 'normal' }}>({getPercent(item.count, item.parent)})</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid for other Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {/* Source Breakdowns */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>Submissions by Source</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.keys(apps.source_distribution || {}).length === 0 ? (
              <div style={{ color: '#64748b', fontStyle: 'italic', fontSize: '0.9rem' }}>No submissions tracked.</div>
            ) : (
              Object.entries(apps.source_distribution).map(([src, count], idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                  <span style={{ textTransform: 'capitalize', color: '#334155' }}>{src}</span>
                  <span style={{ fontWeight: 'bold', color: '#0f172a' }}>{count}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quality Distribution */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>Match Quality Metrics</h3>
          <div style={{ fontSize: '0.9rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
              <span>Average Match Score:</span>
              <strong style={{ color: '#10b981', fontSize: '1.1rem' }}>{matching.average_score ? matching.average_score.toFixed(1) : '0.0'}%</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
              <span>Submission Success Rate:</span>
              <strong style={{ color: '#2563eb' }}>{apps.success_rate ? apps.success_rate.toFixed(1) : '0.0'}%</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
              <span>Total Submissions Attempted:</span>
              <strong style={{ color: '#0f172a' }}>{apps.total}</strong>
            </div>
          </div>
        </div>

        {/* Failure Categories */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>Run Failures Overview</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.keys(failures.categories || {}).length === 0 ? (
              <div style={{ color: '#64748b', fontStyle: 'italic', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>
                ✓ Zero system failures logged. All runs exited with status code 0.
              </div>
            ) : (
              Object.entries(failures.categories).map(([cat, count], idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem', fontSize: '0.9rem' }}>
                  <span style={{ color: '#ef4444' }}>{cat}</span>
                  <span style={{ fontWeight: 'bold', color: '#0f172a' }}>{count}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Labor Market & Career Insights Section */}
      {careerInsights && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          marginTop: '2rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
            <h3 style={{ margin: 0, color: '#0f172a' }}>💼 JobPilot Labor Market & Career Intelligence</h3>
            <span style={{ fontSize: '0.85rem', color: '#64748b', background: '#f1f5f9', padding: '0.25rem 0.75rem', borderRadius: '12px', fontWeight: '500' }}>
              Sample size: {careerInsights.sample_size} jobs analyzed
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
            <div>
              <h4 style={{ color: '#1e293b', marginBottom: '0.75rem', fontSize: '0.95rem' }}>🔥 Most In-Demand Skills</h4>
              {careerInsights.most_requested_skills?.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: '#64748b' }}>No skills data.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {careerInsights.most_requested_skills.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', borderBottom: '1px dashed #f1f5f9', paddingBottom: '0.25rem' }}>
                      <span style={{ color: '#475569', fontWeight: '500' }}>{item.skill}</span>
                      <span style={{ color: '#0f172a', fontWeight: '600' }}>{item.percentage}% ({item.count})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 style={{ color: '#b91c1c', marginBottom: '0.75rem', fontSize: '0.95rem' }}>⚠️ Your Common Skill Gaps</h4>
              {careerInsights.common_missing_skills?.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: '#16a34a' }}>✓ No skill gaps! Profile aligns perfectly.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {careerInsights.common_missing_skills.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', borderBottom: '1px dashed #f1f5f9', paddingBottom: '0.25rem' }}>
                      <span style={{ color: '#991b1b', fontWeight: '500' }}>{item.skill}</span>
                      <span style={{ color: '#991b1b', fontWeight: '600' }}>{item.percentage}% ({item.count})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 style={{ color: '#2563eb', marginBottom: '0.75rem', fontSize: '0.95rem' }}>🎯 Highest Matching Roles</h4>
              {careerInsights.highest_matching_roles?.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: '#64748b' }}>No role matches yet.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {careerInsights.highest_matching_roles.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', borderBottom: '1px dashed #f1f5f9', paddingBottom: '0.25rem' }}>
                      <span style={{ color: '#3b82f6', fontWeight: '500' }}>{item.role}</span>
                      <span style={{ color: '#0f172a', fontWeight: '600' }}>{item.average_score}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 style={{ color: '#0d9488', marginBottom: '0.75rem', fontSize: '0.95rem' }}>📍 Hot Locations</h4>
              {careerInsights.highest_opportunity_locations?.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: '#64748b' }}>No location data.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {careerInsights.highest_opportunity_locations.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', borderBottom: '1px dashed #f1f5f9', paddingBottom: '0.25rem' }}>
                      <span style={{ color: '#14b8a6', fontWeight: '500' }}>{item.location}</span>
                      <span style={{ color: '#0f172a', fontWeight: '600' }}>{item.count} jobs</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Profile Optimization Engine recommendations */}
      {optimizationSuggestions && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          marginTop: '2rem'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>⚡ Intelligent Optimization Recommendations</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {optimizationSuggestions.map((item, idx) => {
              const isHigh = item.severity === 'HIGH'
              const isMed = item.severity === 'MEDIUM'
              const borderColor = isHigh ? '#f87171' : isMed ? '#60a5fa' : '#cbd5e1'
              const bgColor = isHigh ? '#fef2f2' : isMed ? '#eff6ff' : '#f8fafc'
              const icon = isHigh ? '🚨' : isMed ? '⚡' : 'ℹ️'
              return (
                <div key={idx} style={{
                  borderLeft: `4px solid ${borderColor}`,
                  background: bgColor,
                  padding: '1rem',
                  borderRadius: '0 8px 8px 0',
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'flex-start'
                }}>
                  <span style={{ fontSize: '1.25rem' }}>{icon}</span>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '0.9rem', color: '#1e293b', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      {item.category} ({item.severity} severity)
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#334155', lineHeight: '1.4' }}>
                      {item.suggestion}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

