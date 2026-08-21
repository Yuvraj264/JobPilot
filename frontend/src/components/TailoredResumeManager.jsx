import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function TailoredResumeManager() {
  const [tailoredResumes, setTailoredResumes] = useState([])
  const [packages, setPackages] = useState([])
  const [jobs, setJobs] = useState([])
  const [resumes, setResumes] = useState([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedTailored, setSelectedTailored] = useState(null)
  const [message, setMessage] = useState('')

  const loadData = async () => {
    setLoading(true)
    try {
      const [trRes, pkgRes, jobRes, resRes] = await Promise.all([
        fetch(`${API_BASE}/tailored-resumes`),
        fetch(`${API_BASE}/application-packages`),
        fetch(`${API_BASE}/jobs`),
        fetch(`${API_BASE}/resumes`),
      ])
      if (trRes.ok) setTailoredResumes(await trRes.json())
      if (pkgRes.ok) setPackages(await pkgRes.json())
      if (jobRes.ok) setJobs(await jobRes.json())
      if (resRes.ok) setResumes(await resRes.json())
    } catch (err) {
      console.error('Failed to load tailoring data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleGenerateTailoredResume = async () => {
    if (!selectedJobId || !selectedResumeId) {
      setMessage('Please select both a Job and a Master Resume.')
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/resumes/${selectedResumeId}/tailor/${selectedJobId}`, {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setMessage(`Tailored Resume #${data.id} successfully generated! Match relevance score: ${data.relevance_score}%`)
        loadData()
      } else {
        const errData = await res.json()
        setMessage(`Tailoring failed: ${errData.detail || 'Truthfulness check failed.'}`)
      }
    } catch (err) {
      console.error('Error generating tailored resume:', err)
      setMessage('Error connecting to tailoring service.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePackage = async (jobId, sourceResId, tailoredResId) => {
    try {
      const res = await fetch(`${API_BASE}/application-packages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          source_resume_id: sourceResId,
          tailored_resume_id: tailoredResId,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setMessage(`ApplicationPackage #${data.id} created! Status: ${data.status}`)
        loadData()
      }
    } catch (err) {
      console.error('Failed to create package:', err)
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Job-Specific Resume Tailoring & Application Packages</h2>

      {message && <div style={{ background: '#e3f2fd', padding: '0.6rem', marginBottom: '1rem', borderRadius: '4px', color: '#0d47a1' }}>{message}</div>}

      {/* Generator Controls */}
      <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid #ddd' }}>
        <h3>Generate Job-Specific Tailored Resume</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.3rem' }}>Select Target Job:</label>
            <select value={selectedJobId} onChange={(e) => setSelectedJobId(e.target.value)} style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}>
              <option value="">-- Choose Job --</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>{j.title} @ {j.company_name}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.3rem' }}>Select Source Resume:</label>
            <select value={selectedResumeId} onChange={(e) => setSelectedResumeId(e.target.value)} style={{ width: '100%', padding: '0.5rem', borderRadius: '4px' }}>
              <option value="">-- Choose Master Resume --</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>{r.original_filename} (ID #{r.id})</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleGenerateTailoredResume}
            disabled={loading}
            style={{ padding: '0.55rem 1.2rem', background: '#2e7d32', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {loading ? 'Tailoring...' : 'Generate Tailored Resume'}
          </button>
        </div>
      </div>

      {/* Tailored Resumes List */}
      <h3>Generated Tailored Resumes</h3>
      {tailoredResumes.length === 0 ? (
        <p style={{ color: '#666' }}>No tailored resumes generated yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '1rem', marginBottom: '2rem' }}>
          {tailoredResumes.map((tr) => (
            <div key={tr.id} style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', background: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ margin: 0 }}>{tr.title}</h4>
                <span style={{ background: '#e8f5e9', color: '#2e7d32', padding: '3px 8px', borderRadius: '10px', fontWeight: 'bold', fontSize: '0.85rem' }}>
                  Relevance Coverage: {tr.relevance_score}%
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#666', margin: '0.4rem 0' }}>
                Status: <strong>{tr.status}</strong> | PDF: <code>{tr.pdf_file_path}</code> | DOCX: <code>{tr.docx_file_path}</code>
              </p>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem' }}>
                <button
                  onClick={() => setSelectedTailored(tr)}
                  style={{ padding: '0.4rem 0.8rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  View Preview & Diff
                </button>
                <button
                  onClick={() => handleCreatePackage(tr.job_id, tr.source_resume_id, tr.id)}
                  style={{ padding: '0.4rem 0.8rem', background: '#e65100', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  Create Application Package
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal / Container */}
      {selectedTailored && (
        <div style={{ border: '2px solid #1565c0', padding: '1rem', borderRadius: '8px', background: '#f4f6f9', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Preview & Change Diff: {selectedTailored.title}</h3>
            <button onClick={() => setSelectedTailored(null)} style={{ background: '#888', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px' }}>Close</button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #ddd' }}>
              <h4>Structured Resume Preview</h4>
              <p><strong>Summary:</strong> {selectedTailored.structured_content?.summary}</p>
              <p><strong>Prioritized Skills:</strong> {selectedTailored.structured_content?.skills?.map((s) => s.name).join(', ')}</p>
              <p><strong>Top Projects:</strong></p>
              <ul>
                {selectedTailored.structured_content?.projects?.map((p, idx) => (
                  <li key={idx}><strong>{p.name}</strong> (Relevance: {p.relevance_score}%) — {p.technologies}</li>
                ))}
              </ul>
            </div>

            <div style={{ background: '#fff', padding: '1rem', borderRadius: '6px', border: '1px solid #ddd' }}>
              <h4>Transparent Change Report</h4>
              <ul>
                {selectedTailored.change_report?.changes?.map((c, idx) => (
                  <li key={idx}><strong>{c.section}:</strong> {c.description}</li>
                ))}
              </ul>
              <h4>Keyword Analysis</h4>
              <p><strong>Matched ({selectedTailored.keyword_analysis?.matched_count}):</strong> {selectedTailored.keyword_analysis?.matched_keywords?.map((k) => k.keyword).join(', ')}</p>
              <p><strong>Unsupported/Missing ({selectedTailored.keyword_analysis?.unsupported_count}):</strong> {selectedTailored.keyword_analysis?.unsupported_keywords?.map((k) => k.keyword).join(', ')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Application Packages List */}
      <h3>Application Packages</h3>
      {packages.length === 0 ? (
        <p style={{ color: '#666' }}>No application packages created yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {packages.map((pkg) => (
            <div key={pkg.id} style={{ border: '1px solid #ddd', padding: '1rem', borderRadius: '8px', background: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ margin: 0 }}>Package #{pkg.id} for Job #{pkg.job_id}</h4>
                <span style={{ background: pkg.status === 'READY_FOR_REVIEW' ? '#e8f5e9' : '#fff3e0', color: pkg.status === 'READY_FOR_REVIEW' ? '#2e7d32' : '#e65100', padding: '4px 10px', borderRadius: '12px', fontWeight: 'bold' }}>
                  {pkg.status}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#666', margin: '0.4rem 0' }}>
                Tailored Resume ID: <strong>{pkg.tailored_resume_id || 'None'}</strong> | Source Resume ID: <strong>{pkg.source_resume_id || 'None'}</strong>
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
