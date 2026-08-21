import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/profile'

export default function ProfileManager() {
  const [profile, setProfile] = useState(null)
  const [summary, setSummary] = useState(null)
  const [completeness, setCompleteness] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  // Form states
  const [basicForm, setBasicForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    current_city: '',
    current_country: '',
    professional_summary: '',
    years_of_experience: 0,
    current_role: '',
    employment_status: ''
  })

  // Sub-item forms
  const [newSkill, setNewSkill] = useState({ name: '', category: 'Programming', proficiency: 'Intermediate', years_of_experience: 1 })
  const [newEdu, setNewEdu] = useState({ institution: '', degree: '', field_of_study: '', start_year: 2020, end_year: 2024 })
  const [newProj, setNewProj] = useState({ name: '', description: '', technologies: '' })
  const [newCert, setNewCert] = useState({ name: '', issuing_organization: '', issue_date: '', expiry_date: '' })

  const loadProfile = async () => {
    setLoading(true)
    try {
      const res = await fetch(API_BASE)
      if (res.ok) {
        const data = await res.json()
        setProfile(data)
        setBasicForm({
          full_name: data.full_name || '',
          email: data.email || '',
          phone: data.phone || '',
          current_city: data.current_city || '',
          current_country: data.current_country || '',
          professional_summary: data.professional_summary || '',
          years_of_experience: data.years_of_experience || 0,
          current_role: data.current_role || '',
          employment_status: data.employment_status || ''
        })
      } else {
        setProfile(null)
      }

      // Load summary & completeness
      const sumRes = await fetch(`${API_BASE}/summary`)
      if (sumRes.ok) setSummary(await sumRes.json())

      const compRes = await fetch(`${API_BASE}/completeness`)
      if (compRes.ok) setCompleteness(await compRes.json())
    } catch (err) {
      console.error('Error loading profile:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  const seedSampleData = async () => {
    try {
      const res = await fetch(`${API_BASE}/seed`, { method: 'POST' })
      if (res.ok) {
        setMessage('Sample profile seeded successfully!')
        loadProfile()
      }
    } catch (err) {
      setMessage('Failed to seed sample profile.')
    }
  }

  const handleSaveBasic = async (e) => {
    e.preventDefault()
    try {
      const method = profile ? 'PUT' : 'POST'
      const res = await fetch(API_BASE, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(basicForm)
      })
      if (res.ok) {
        setMessage('Profile updated successfully!')
        loadProfile()
      } else {
        const error = await res.json()
        setMessage(`Error: ${JSON.stringify(error.detail || error)}`)
      }
    } catch (err) {
      setMessage('Failed to save profile.')
    }
  }

  const handleAddSkill = async (e) => {
    e.preventDefault()
    if (!newSkill.name) return
    const res = await fetch(`${API_BASE}/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSkill)
    })
    if (res.ok) {
      setNewSkill({ name: '', category: 'Programming', proficiency: 'Intermediate', years_of_experience: 1 })
      loadProfile()
    }
  }

  const handleDeleteSkill = async (id) => {
    await fetch(`${API_BASE}/skills/${id}`, { method: 'DELETE' })
    loadProfile()
  }

  const handleAddEdu = async (e) => {
    e.preventDefault()
    if (!newEdu.institution || !newEdu.degree) return
    const res = await fetch(`${API_BASE}/education`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newEdu)
    })
    if (res.ok) {
      setNewEdu({ institution: '', degree: '', field_of_study: '', start_year: 2020, end_year: 2024 })
      loadProfile()
    }
  }

  const handleDeleteEdu = async (id) => {
    await fetch(`${API_BASE}/education/${id}`, { method: 'DELETE' })
    loadProfile()
  }

  const handleAddProj = async (e) => {
    e.preventDefault()
    if (!newProj.name) return
    const payload = {
      ...newProj,
      technologies: newProj.technologies ? newProj.technologies.split(',').map((t) => t.strip ? t.strip() : t.trim()) : []
    }
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      setNewProj({ name: '', description: '', technologies: '' })
      loadProfile()
    }
  }

  const handleDeleteProj = async (id) => {
    await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' })
    loadProfile()
  }

  const handleAddCert = async (e) => {
    e.preventDefault()
    if (!newCert.name || !newCert.issuing_organization) return
    const res = await fetch(`${API_BASE}/certifications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCert)
    })
    if (res.ok) {
      setNewCert({ name: '', issuing_organization: '', issue_date: '', expiry_date: '' })
      loadProfile()
    }
  }

  const handleDeleteCert = async (id) => {
    await fetch(`${API_BASE}/certifications/${id}`, { method: 'DELETE' })
    loadProfile()
  }

  if (loading) return <div>Loading Profile Engine...</div>

  return (
    <div style={{ marginTop: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>User Profile & Preference Engine</h2>
        <button onClick={seedSampleData} style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>
          Seed Dev Sample Profile
        </button>
      </div>

      {message && <div style={{ background: '#eef', padding: '0.5rem', marginBottom: '1rem' }}>{message}</div>}

      {/* Completeness Bar */}
      {completeness && (
        <div style={{ marginBottom: '1.5rem', background: '#f5f5f5', padding: '1rem', borderRadius: '6px' }}>
          <h3>Profile Completeness: {completeness.percentage}%</h3>
          <div style={{ background: '#ddd', height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ background: '#4caf50', width: `${completeness.percentage}%`, height: '100%' }} />
          </div>
          {completeness.missing_sections?.length > 0 && (
            <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
              Missing or incomplete: {completeness.missing_sections.join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Basic & Professional Info Form */}
      <section style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem', borderRadius: '6px' }}>
        <h3>Basic & Professional Information</h3>
        <form onSubmit={handleSaveBasic} style={{ display: 'grid', gap: '0.8rem' }}>
          <div>
            <label>Full Name: </label>
            <input
              type="text"
              value={basicForm.full_name}
              onChange={(e) => setBasicForm({ ...basicForm, full_name: e.target.value })}
              required
            />
          </div>
          <div>
            <label>Email: </label>
            <input
              type="email"
              value={basicForm.email}
              onChange={(e) => setBasicForm({ ...basicForm, email: e.target.value })}
              required
            />
          </div>
          <div>
            <label>Phone: </label>
            <input
              type="text"
              value={basicForm.phone}
              onChange={(e) => setBasicForm({ ...basicForm, phone: e.target.value })}
            />
          </div>
          <div>
            <label>City: </label>
            <input
              type="text"
              value={basicForm.current_city}
              onChange={(e) => setBasicForm({ ...basicForm, current_city: e.target.value })}
            />
          </div>
          <div>
            <label>Country: </label>
            <input
              type="text"
              value={basicForm.current_country}
              onChange={(e) => setBasicForm({ ...basicForm, current_country: e.target.value })}
            />
          </div>
          <div>
            <label>Current Role: </label>
            <input
              type="text"
              value={basicForm.current_role}
              onChange={(e) => setBasicForm({ ...basicForm, current_role: e.target.value })}
            />
          </div>
          <div>
            <label>Years of Experience: </label>
            <input
              type="number"
              step="0.5"
              value={basicForm.years_of_experience}
              onChange={(e) => setBasicForm({ ...basicForm, years_of_experience: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label>Professional Summary: </label>
            <textarea
              rows="3"
              style={{ width: '100%' }}
              value={basicForm.professional_summary}
              onChange={(e) => setBasicForm({ ...basicForm, professional_summary: e.target.value })}
            />
          </div>
          <button type="submit" style={{ padding: '0.5rem', cursor: 'pointer' }}>
            Save Basic Info
          </button>
        </form>
      </section>

      {/* Skills Section */}
      <section style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem', borderRadius: '6px' }}>
        <h3>Skills ({profile?.skills?.length || 0})</h3>
        <ul>
          {profile?.skills?.map((s) => (
            <li key={s.id} style={{ marginBottom: '0.4rem' }}>
              <strong>{s.name}</strong> ({s.category}) - {s.proficiency || 'N/A'} ({s.years_of_experience} yrs)
              <button onClick={() => handleDeleteSkill(s.id)} style={{ marginLeft: '1rem', color: 'red' }}>
                Remove
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={handleAddSkill} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input
            placeholder="Skill Name"
            value={newSkill.name}
            onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
          />
          <input
            placeholder="Category"
            value={newSkill.category}
            onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}
          />
          <button type="submit">Add Skill</button>
        </form>
      </section>

      {/* Education Section */}
      <section style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem', borderRadius: '6px' }}>
        <h3>Education ({profile?.education?.length || 0})</h3>
        <ul>
          {profile?.education?.map((e) => (
            <li key={e.id} style={{ marginBottom: '0.4rem' }}>
              <strong>{e.degree}</strong> in {e.field_of_study} at {e.institution} ({e.start_year} - {e.end_year})
              <button onClick={() => handleDeleteEdu(e.id)} style={{ marginLeft: '1rem', color: 'red' }}>
                Remove
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={handleAddEdu} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input
            placeholder="Institution"
            value={newEdu.institution}
            onChange={(e) => setNewEdu({ ...newEdu, institution: e.target.value })}
          />
          <input
            placeholder="Degree"
            value={newEdu.degree}
            onChange={(e) => setNewEdu({ ...newEdu, degree: e.target.value })}
          />
          <input
            placeholder="Field of Study"
            value={newEdu.field_of_study}
            onChange={(e) => setNewEdu({ ...newEdu, field_of_study: e.target.value })}
          />
          <button type="submit">Add Education</button>
        </form>
      </section>

      {/* Projects Section */}
      <section style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem', borderRadius: '6px' }}>
        <h3>Projects ({profile?.projects?.length || 0})</h3>
        <ul>
          {profile?.projects?.map((p) => (
            <li key={p.id} style={{ marginBottom: '0.4rem' }}>
              <strong>{p.name}</strong> - {p.description} [{p.technologies?.join(', ')}]
              <button onClick={() => handleDeleteProj(p.id)} style={{ marginLeft: '1rem', color: 'red' }}>
                Remove
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={handleAddProj} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input
            placeholder="Project Name"
            value={newProj.name}
            onChange={(e) => setNewProj({ ...newProj, name: e.target.value })}
          />
          <input
            placeholder="Description"
            value={newProj.description}
            onChange={(e) => setNewProj({ ...newProj, description: e.target.value })}
          />
          <input
            placeholder="Technologies (comma separated)"
            value={newProj.technologies}
            onChange={(e) => setNewProj({ ...newProj, technologies: e.target.value })}
          />
          <button type="submit">Add Project</button>
        </form>
      </section>

      {/* Profile Summary JSON Preview */}
      {summary && (
        <section style={{ background: '#fafafa', padding: '1rem', borderRadius: '6px', border: '1px solid #ccc' }}>
          <h3>Profile Summary JSON (AI Matching View)</h3>
          <pre style={{ background: '#eee', padding: '0.8rem', borderRadius: '4px', overflowX: 'auto' }}>
            {JSON.stringify(summary, null, 2)}
          </pre>
        </section>
      )}
    </div>
  )
}
