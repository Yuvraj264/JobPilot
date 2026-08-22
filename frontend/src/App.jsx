import { useState, useEffect } from 'react'
import ProfileManager from './components/ProfileManager'
import ResumeManager from './components/ResumeManager'
import JobDiscoveryManager from './components/JobDiscoveryManager'
import MatchDashboardManager from './components/MatchDashboardManager'
import AutomationMonitorManager from './components/AutomationMonitorManager'
import ScreeningReviewQueueManager from './components/ScreeningReviewQueueManager'
import TailoredResumeManager from './components/TailoredResumeManager'
import ApplicationControlManager from './components/ApplicationControlManager'
import AutomationOrchestratorDashboard from './components/AutomationOrchestratorDashboard'
import SourceManager from './components/SourceManager'
import AnalyticsCenter from './components/AnalyticsCenter'
import Dashboard from './components/Dashboard'
import OnboardingWizard from './components/OnboardingWizard'
import PreferenceManager from './components/PreferenceManager'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '1')
  const [profileComplete, setProfileComplete] = useState(true)
  const [loading, setLoading] = useState(true)
  const [showTour, setShowTour] = useState(false)
  const [tourStep, setTourStep] = useState(1)
  const [bannerMsg, setBannerMsg] = useState('')

  const checkProfileStatus = async (uid) => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/profile', {
        headers: { 'X-User-Id': uid }
      })
      if (res.ok) {
        setProfileComplete(true)
      } else {
        setProfileComplete(false)
      }
    } catch (err) {
      console.error(err)
      setProfileComplete(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkProfileStatus(userId)
  }, [userId])

  const toggleDemoMode = async () => {
    if (userId !== '99999') {
      // Enable Demo Mode: switch to user 99999 and reset
      setLoading(true)
      try {
        const res = await fetch('http://localhost:8000/api/demo/reset', { method: 'POST' })
        if (res.ok) {
          localStorage.setItem('userId', '99999')
          setUserId('99999')
          setBannerMsg('Demo mode activated with synthetic software candidate data.')
          setActiveTab('dashboard')
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    } else {
      // Disable Demo Mode: switch to user 1
      localStorage.setItem('userId', '1')
      setUserId('1')
      setBannerMsg('Demo mode deactivated. Returned to production workspace.')
      setActiveTab('dashboard')
    }
  }

  const handleResetDemo = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/demo/reset', { method: 'POST' })
      if (res.ok) {
        setBannerMsg('Demo environment reset successfully.')
        checkProfileStatus(userId)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleStartTour = () => {
    setTourStep(1)
    setShowTour(true)
  }

  const handleTourNext = () => {
    const tabsSequence = ['dashboard', 'jobs', 'resume', 'review_queue', 'automation', 'analytics']
    if (tourStep < 6) {
      setActiveTab(tabsSequence[tourStep])
      setTourStep(tourStep + 1)
    } else {
      setShowTour(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#f8fafc' }}>
        <h3 style={{ fontFamily: 'sans-serif', color: '#64748b' }}>Initializing JobPilot Workspace...</h3>
      </div>
    )
  }

  if (!profileComplete && userId !== '99999') {
    return <OnboardingWizard userId={userId} onComplete={() => checkProfileStatus(userId)} />
  }

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, sans-serif', background: '#f8fafc', overflow: 'hidden' }}>
      
      {/* Sidebar Navigation */}
      <div style={{
        width: '240px',
        background: '#0f172a',
        color: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '1.5rem 1rem',
        boxSizing: 'border-box'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem', paddingLeft: '0.5rem' }}>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>🚀 JobPilot</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'jobs', label: 'Jobs', icon: '💼' },
              { id: 'applications', label: 'Applications', icon: '📝' },
              { id: 'review_queue', label: 'Review Queue', icon: '📥' },
              { id: 'resume', label: 'Resume Center', icon: '📄' },
              { id: 'profile', label: 'Profile Manager', icon: '👤' },
              { id: 'sources', label: 'Job Sources', icon: '🔌' },
              { id: 'automation', label: 'Automation Loop', icon: '⚙️' },
              { id: 'analytics', label: 'Analytics', icon: '📈' },
              { id: 'preferences', label: 'Preferences', icon: '🛠️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  width: '100%',
                  background: activeTab === tab.id ? '#1e293b' : 'transparent',
                  color: activeTab === tab.id ? '#38bdf8' : '#94a3b8',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  transition: 'all 0.2s'
                }}
              >
                <span>{tab.icon}</span> {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderTop: '1px solid #1e293b', paddingTop: '1rem' }}>
          <button
            onClick={handleStartTour}
            style={{
              padding: '0.5rem',
              background: '#1e293b',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 'bold'
            }}
          >
            🗺️ Start Product Tour
          </button>
          <button
            onClick={toggleDemoMode}
            style={{
              padding: '0.5rem',
              background: userId === '99999' ? '#dc2626' : '#22c55e',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 'bold'
            }}
          >
            {userId === '99999' ? '🚫 Exit Demo Mode' : '🎮 Enter Demo Mode'}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Demo Mode persistent Banner */}
        {userId === '99999' && (
          <div style={{
            background: '#fef3c7',
            borderBottom: '1px solid #fde68a',
            padding: '0.75rem 1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.85rem',
            color: '#92400e',
            fontWeight: '600',
            boxSizing: 'border-box'
          }}>
            <span>
              ⚠️ <strong>DEMO MODE ACTIVE</strong> — Viewing isolated synthetic sandbox data. Real job portals will not be connected.
            </span>
            <button
              onClick={handleResetDemo}
              style={{
                background: '#d97706',
                color: '#ffffff',
                border: 'none',
                padding: '0.3rem 0.75rem',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 'bold'
              }}
            >
              🔄 Reset Demo Data
            </button>
          </div>
        )}

        {/* Banner Alert Message */}
        {bannerMsg && (
          <div style={{
            background: '#e0f2fe',
            padding: '0.6rem 1.5rem',
            fontSize: '0.85rem',
            color: '#0369a1',
            fontWeight: '600',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>{bannerMsg}</span>
            <button onClick={() => setBannerMsg('')} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontWeight: 'bold', color: '#0369a1' }}>×</button>
          </div>
        )}

        {/* Tab view rendering */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'dashboard' && <Dashboard userId={userId} onNavigate={setActiveTab} />}
          {activeTab === 'jobs' && (
            <div style={{ padding: '1rem' }}>
              <MatchDashboardManager />
              <JobDiscoveryManager />
            </div>
          )}
          {activeTab === 'applications' && (
            <div style={{ padding: '1rem' }}>
              <ApplicationControlManager />
            </div>
          )}
          {activeTab === 'review_queue' && (
            <div style={{ padding: '1rem' }}>
              <ScreeningReviewQueueManager />
            </div>
          )}
          {activeTab === 'resume' && (
            <div style={{ padding: '1rem' }}>
              <ResumeManager />
              <TailoredResumeManager />
            </div>
          )}
          {activeTab === 'profile' && (
            <div style={{ padding: '1rem' }}>
              <ProfileManager />
            </div>
          )}
          {activeTab === 'sources' && <SourceManager userId={userId} />}
          {activeTab === 'automation' && (
            <div style={{ padding: '1rem' }}>
              <AutomationOrchestratorDashboard />
              <AutomationMonitorManager />
            </div>
          )}
          {activeTab === 'analytics' && <AnalyticsCenter userId={userId} />}
          {activeTab === 'preferences' && <PreferenceManager userId={userId} />}
        </div>
      </div>

      {/* Product Tour Modal Overlay */}
      {showTour && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15,23,42,0.4)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 2000
        }}>
          <div style={{
            background: '#ffffff',
            padding: '2rem',
            borderRadius: '16px',
            maxWidth: '420px',
            width: '100%',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
            fontFamily: 'sans-serif'
          }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>JobPilot Product Tour</h3>
            <div style={{ fontSize: '0.8rem', color: '#4f46e5', fontWeight: 'bold', marginBottom: '1rem' }}>
              STEP {tourStep} OF 6
            </div>
            
            <p style={{ color: '#475569', fontSize: '0.95rem', lineHeight: '1.5', minHeight: '80px' }}>
              {tourStep === 1 && 'Welcome to the Dashboard! Get a real-time summary of today\'s job discovery ingestion count, tailored resume outputs, and automatic platform delivery counters.'}
              {tourStep === 2 && 'Under the Jobs tab, search and filter through matched listings. Inspect match explanation scorecards highlighting strengths and concern checkmarks.'}
              {tourStep === 3 && 'In the Resume Center, manage master resumes and view version histories of tailored resumes generated by the tailoring parser.'}
              {tourStep === 4 && 'The Review Queue enables you to edit, confirm, or provide answers for screening questions that the model has flagged as needing review.'}
              {tourStep === 5 && 'The Automation Loop page is where you configure execution modes, set daily limits, and schedule runs.'}
              {tourStep === 6 && 'Finally, Analytics compiles metrics for funnel conversions, success rates, and category failures.'}
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem', borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
              <button onClick={() => setShowTour(false)} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', fontWeight: 'bold' }}>Skip</button>
              <button
                onClick={handleTourNext}
                style={{
                  background: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.5rem 1.25rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                {tourStep === 6 ? 'Finish Tour' : 'Next Step'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
