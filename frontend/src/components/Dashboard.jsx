import React, { useState, useEffect } from 'react'

export default function Dashboard({ userId, onNavigate }) {
  const [overview, setOverview] = useState(null)
  const [orchStatus, setOrchStatus] = useState('IDLE')
  const [loading, setLoading] = useState(true)

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // 1. Load Overview Metrics
      const metricsRes = await fetch('http://localhost:8000/api/analytics/overview', {
        headers: { 'X-User-Id': userId }
      })
      if (metricsRes.ok) {
        setOverview(await metricsRes.ok ? await metricsRes.json() : null)
      }

      // 2. Load Orchestration Status
      const statusRes = await fetch('http://localhost:8000/api/orchestration/status', {
        headers: { 'X-User-Id': userId }
      })
      if (statusRes.ok) {
        const statusData = await statusRes.json()
        setOrchStatus(statusData.status || 'IDLE')
      }
    } catch (err) {
      console.error('Error loading dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(loadDashboardData, 10000)
    return () => clearInterval(interval)
  }, [userId])

  if (loading && !overview) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>Loading Dashboard...</div>
  }

  // Fallback default values
  const stats = overview || {
    discovered: 0,
    matched: 0,
    selected: 0,
    prepared: 0,
    submitted: 0,
    failed: 0,
    awaiting_review: 0,
    recent_activity: []
  }

  // Attention required messages
  const attentionItems = []
  if (stats.awaiting_review > 0) {
    attentionItems.push({
      text: `${stats.awaiting_review} applications are awaiting your review and approval.`,
      actionText: 'Review Queue',
      tab: 'review_queue'
    })
  }
  // Mock login/CAPTCHA warning for demo mode
  if (userId === '99999') {
    attentionItems.push({
      text: 'Action Required: LinkedIn login configuration verification needed.',
      actionText: 'Manage Sources',
      tab: 'sources'
    })
  }

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0f172a', fontSize: '1.75rem' }}>Welcome to JobPilot</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b' }}>Here is what's happening today.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Automation State:</span>
          <span style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '9999px',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            background: orchStatus === 'RUNNING' ? '#ecfdf5' : '#f1f5f9',
            color: orchStatus === 'RUNNING' ? '#059669' : '#475569',
            border: `1px solid ${orchStatus === 'RUNNING' ? '#a7f3d0' : '#cbd5e1'}`
          }}>
            ● {orchStatus}
          </span>
        </div>
      </div>

      {/* Overview Cards */}
      <h3 style={{ color: '#0f172a', marginBottom: '1rem' }}>Today's Overview</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {[
          { label: 'Discovered', val: stats.discovered || 0, color: '#4f46e5' },
          { label: 'High Match', val: stats.matched || 0, color: '#10b981' },
          { label: 'Prepared', val: stats.prepared || 0, color: '#f59e0b' },
          { label: 'Awaiting Review', val: stats.awaiting_review || 0, color: '#ef4444' },
          { label: 'Submitted', val: stats.submitted || 0, color: '#2563eb' },
          { label: 'Failed', val: stats.failed || 0, color: '#dc2626' }
        ].map((item, idx) => (
          <div key={idx} style={{
            background: '#ffffff',
            padding: '1.25rem',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            border: '1px solid #e2e8f0',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '500', marginBottom: '0.5rem' }}>{item.label}</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: item.color }}>{item.val}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Attention Required Block */}
        <div style={{
          background: '#ffffff',
          padding: '1.5rem',
          borderRadius: '16px',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ color: '#ef4444' }}>⚠</span> Attention Required
          </h3>
          {attentionItems.length === 0 ? (
            <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: '8px', color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
              ✓ You are all caught up! No tasks need immediate attention.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {attentionItems.map((item, idx) => (
                <div key={idx} style={{
                  padding: '1rem',
                  background: '#fff8f1',
                  borderRadius: '10px',
                  border: '1px solid #ffedd5',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.9rem',
                  color: '#9a3412'
                }}>
                  <span>{item.text}</span>
                  <button
                    onClick={() => onNavigate(item.tab)}
                    style={{
                      background: '#ea580c',
                      color: '#ffffff',
                      border: 'none',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      fontWeight: '600'
                    }}
                  >
                    {item.actionText}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div style={{
          background: '#ffffff',
          padding: '1.5rem',
          borderRadius: '16px',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#0f172a' }}>Recent Activity</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {stats.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((activity, idx) => (
                <div key={idx} style={{
                  display: 'flex',
                  gap: '0.75rem',
                  fontSize: '0.875rem',
                  borderBottom: '1px solid #f1f5f9',
                  paddingBottom: '0.75rem'
                }}>
                  <div style={{ color: '#4f46e5', fontWeight: 'bold' }}>•</div>
                  <div style={{ color: '#334155' }}>{activity}</div>
                </div>
              ))
            ) : (
              <div style={{ color: '#64748b', fontSize: '0.9rem', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                No recent activity logged. Trigger an automation run to begin.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
