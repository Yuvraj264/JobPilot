import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/resumes'

export default function ResumeManager() {
  const [resumes, setResumes] = useState([])
  const [selectedResume, setSelectedResume] = useState(null)
  const [parsedData, setParsedData] = useState(null)
  const [quality, setQuality] = useState(null)
  const [consistency, setConsistency] = useState(null)
  
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadName, setUploadName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const loadResumes = async () => {
    try {
      const res = await fetch(API_BASE)
      if (res.ok) {
        const data = await res.json()
        setResumes(data)
        if (data.length > 0 && !selectedResume) {
          inspectResume(data[0].id)
        }
      }
    } catch (err) {
      console.error('Error loading resumes:', err)
    }
  }

  const inspectResume = async (id) => {
    try {
      const resMeta = await fetch(`${API_BASE}/${id}`)
      if (resMeta.ok) setSelectedResume(await resMeta.json())

      const resParsed = await fetch(`${API_BASE}/${id}/parsed`)
      if (resParsed.ok) setParsedData(await resParsed.json())

      const resQual = await fetch(`${API_BASE}/${id}/quality`)
      if (resQual.ok) setQuality(await resQual.json())

      const resCons = await fetch(`${API_BASE}/${id}/consistency`)
      if (resCons.ok) setConsistency(await resCons.json())
    } catch (err) {
      console.error('Error inspecting resume:', err)
    }
  }

  useEffect(() => {
    loadResumes()
  }, [])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!uploadFile) return

    setUploading(true)
    setMessage('')
    const formData = new FormData()
    formData.append('file', uploadFile)
    if (uploadName) formData.append('name', uploadName)

    try {
      const res = await fetch(API_BASE, {
        method: 'POST',
        body: formData
      })

      if (res.ok) {
        const newResume = await res.json()
        setMessage(`Resume '${newResume.name}' uploaded and processed successfully!`)
        setUploadFile(null)
        setUploadName('')
        loadResumes()
        inspectResume(newResume.id)
      } else {
        const errData = await res.json()
        setMessage(`Upload Error: ${errData.detail || 'Failed to upload file'}`)
      }
    } catch (err) {
      setMessage('Failed to upload file.')
    } finally {
      setUploading(false)
    }
  }

  const handleSetDefault = async (id) => {
    const res = await fetch(`${API_BASE}/${id}/set-default`, { method: 'POST' })
    if (res.ok) {
      setMessage('Default resume updated!')
      loadResumes()
    }
  }

  const handleReprocess = async (id) => {
    setMessage('Reprocessing resume...')
    const res = await fetch(`${API_BASE}/${id}/reprocess`, { method: 'POST' })
    if (res.ok) {
      setMessage('Reprocessing completed!')
      inspectResume(id)
      loadResumes()
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return
    const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
    if (res.ok) {
      setMessage('Resume deleted.')
      setSelectedResume(null)
      setParsedData(null)
      setQuality(null)
      setConsistency(null)
      loadResumes()
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <h2>Resume Management & Intelligence</h2>

      {message && <div style={{ background: '#eef', padding: '0.5rem', marginBottom: '1rem', borderRadius: '4px' }}>{message}</div>}

      {/* Upload Form */}
      <section style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem', borderRadius: '6px' }}>
        <h3>Upload New Resume</h3>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setUploadFile(e.target.files[0])}
            required
          />
          <input
            type="text"
            placeholder="Resume Name (e.g. QA Resume)"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
          />
          <button type="submit" disabled={uploading} style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>
            {uploading ? 'Uploading & Processing...' : 'Upload & Process'}
          </button>
        </form>
        <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.4rem' }}>
          Supported formats: PDF, DOCX (Max 10MB)
        </p>
      </section>

      {/* Resumes List */}
      <section style={{ marginBottom: '1.5rem' }}>
        <h3>Uploaded Resumes ({resumes.length})</h3>
        {resumes.length === 0 ? (
          <p style={{ color: '#777' }}>No resumes uploaded yet.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {resumes.map((r) => (
              <li
                key={r.id}
                style={{
                  border: '1px solid #ccc',
                  padding: '0.8rem',
                  marginBottom: '0.5rem',
                  borderRadius: '6px',
                  background: selectedResume?.id === r.id ? '#f0f7ff' : '#fff',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <strong>{r.name}</strong> ({r.file_type}, {(r.file_size / 1024).toFixed(1)} KB)
                  {r.is_default && <span style={{ marginLeft: '0.5rem', background: '#4caf50', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>DEFAULT</span>}
                  <span style={{ marginLeft: '0.5rem', background: r.processing_status === 'PROCESSED' ? '#e1f5fe' : '#ffe0b2', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>
                    {r.processing_status}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => inspectResume(r.id)}>Inspect</button>
                  {!r.is_default && <button onClick={() => handleSetDefault(r.id)}>Set Default</button>}
                  <a href={`${API_BASE}/${r.id}/download`} target="_blank" rel="noreferrer" style={{ padding: '0.2rem 0.5rem', background: '#eee', borderRadius: '4px', textDecoration: 'none', fontSize: '0.85rem', color: '#333' }}>
                    Download
                  </a>
                  <button onClick={() => handleReprocess(r.id)}>Reprocess</button>
                  <button onClick={() => handleDelete(r.id)} style={{ color: 'red' }}>Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Inspection Details */}
      {selectedResume && (
        <section style={{ border: '1px solid #99c2ff', padding: '1rem', borderRadius: '6px', background: '#fcfdfe' }}>
          <h3>Inspecting: {selectedResume.name}</h3>

          {/* Quality Score */}
          {quality && (
            <div style={{ background: '#fff', padding: '0.8rem', border: '1px solid #ddd', borderRadius: '6px', marginBottom: '1rem' }}>
              <h4>Resume Quality Score: {quality.score}/100</h4>
              {quality.issues?.length > 0 ? (
                <ul>
                  {quality.issues.map((iss, idx) => (
                    <li key={idx} style={{ color: '#d32f2f', fontSize: '0.9rem' }}>{iss}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'green', fontSize: '0.9rem' }}>Excellent! No quality issues detected.</p>
              )}
            </div>
          )}

          {/* Consistency Report */}
          {consistency && (
            <div style={{ background: '#fff', padding: '0.8rem', border: '1px solid #ddd', borderRadius: '6px', marginBottom: '1rem' }}>
              <h4>Profile vs Resume Consistency Check</h4>
              {consistency.issues?.length > 0 ? (
                <ul>
                  {consistency.issues.map((iss, idx) => (
                    <li key={idx} style={{ color: '#e65100', fontSize: '0.9rem' }}>
                      <strong>[{iss.type}]</strong> {iss.message}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'green', fontSize: '0.9rem' }}>Perfect match! Resume matches User Profile.</p>
              )}
            </div>
          )}

          {/* Extracted Structured Sections */}
          {parsedData && (
            <div>
              <h4>Extracted Structured Information</h4>
              <p><strong>Skills Detected:</strong> {parsedData.skills?.map(s => s.name).join(', ') || 'None'}</p>
              <p><strong>Education Entries:</strong> {parsedData.education?.length || 0}</p>
              <p><strong>Experiences Entries:</strong> {parsedData.experiences?.length || 0}</p>
              <p><strong>Projects Entries:</strong> {parsedData.projects?.length || 0}</p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
