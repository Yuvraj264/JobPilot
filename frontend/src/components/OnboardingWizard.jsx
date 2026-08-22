import React, { useState, useEffect } from 'react'

export default function OnboardingWizard({ userId, onComplete }) {
  const [step, setStep] = useState(1)
  const [basic, setBasic] = useState({
    full_name: '',
    email: '',
    phone: '',
    current_city: '',
    current_country: '',
    professional_summary: '',
    years_of_experience: 1.0,
    current_role: '',
    employment_status: 'Open to Opportunities'
  })
  
  const [skills, setSkills] = useState([])
  const [newSkill, setNewSkill] = useState({ name: '', category: 'Programming', proficiency: 'Intermediate', years_of_experience: 1.0 })
  
  const [education, setEducation] = useState([])
  const [newEdu, setNewEdu] = useState({ institution: '', degree: '', field_of_study: '', start_year: 2020, end_year: 2024 })
  
  const [projects, setProjects] = useState([])
  const [newProj, setNewProj] = useState({ name: '', description: '', technologies: '' })

  const [jobPref, setJobPref] = useState({
    target_roles: '',
    preferred_locations: '',
    min_expected_salary: 80000,
    salary_currency: 'USD',
    work_arrangements: ['remote', 'hybrid']
  })

  const [completeness, setCompleteness] = useState(0)
  const [msg, setMsg] = useState('')

  const calculateCompleteness = () => {
    let score = 0
    if (basic.full_name && basic.email) score += 20
    if (basic.professional_summary) score += 15
    if (education.length > 0) score += 15
    if (skills.length > 0) score += 15
    if (projects.length > 0) score += 15
    if (jobPref.target_roles) score += 20
    setCompleteness(score)
  }

  useEffect(() => {
    calculateCompleteness()
  }, [basic, skills, education, projects, jobPref])

  const handleNext = () => {
    if (step < 7) {
      setStep(step + 1)
    } else {
      handleSaveAll()
    }
  }

  const handleBack = () => {
    if (step > 1) setStep(step - 1)
  }

  const handleAddSkill = () => {
    if (!newSkill.name.trim()) return
    setSkills([...skills, newSkill])
    setNewSkill({ name: '', category: 'Programming', proficiency: 'Intermediate', years_of_experience: 1.0 })
  }

  const handleAddEdu = () => {
    if (!newEdu.institution.trim()) return
    setEducation([...education, newEdu])
    setNewEdu({ institution: '', degree: '', field_of_study: '', start_year: 2020, end_year: 2024 })
  }

  const handleAddProj = () => {
    if (!newProj.name.trim()) return
    setProjects([...projects, newProj])
    setNewProj({ name: '', description: '', technologies: '' })
  }

  const handleSaveAll = async () => {
    try {
      // 1. Save Profile basic info
      const profileRes = await fetch('http://localhost:8000/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify(basic)
      })

      if (!profileRes.ok) {
        setMsg('Error saving profile details.')
        return
      }

      // 2. Save Education
      for (const eduItem of education) {
        await fetch('http://localhost:8000/api/profile/education', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
          body: JSON.stringify(eduItem)
        })
      }

      // 3. Save Skills
      for (const skillItem of skills) {
        await fetch('http://localhost:8000/api/profile/skills', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
          body: JSON.stringify(skillItem)
        })
      }

      // 4. Save Projects
      for (const projItem of projects) {
        const cleanedProj = {
          ...projItem,
          technologies: projItem.technologies.split(',').map(t => t.trim())
        }
        await fetch('http://localhost:8000/api/profile/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
          body: JSON.stringify(cleanedProj)
        })
      }

      // 5. Save Job Preferences
      const cleanPref = {
        target_roles: jobPref.target_roles.split(',').map(r => r.trim()),
        preferred_locations: jobPref.preferred_locations.split(',').map(l => l.trim()),
        work_arrangements: jobPref.work_arrangements,
        employment_types: ['full-time'],
        min_expected_salary: parseFloat(jobPref.min_expected_salary),
        salary_currency: jobPref.salary_currency
      }
      await fetch('http://localhost:8000/api/profile/preferences/job', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
        body: JSON.stringify(cleanPref)
      })

      setMsg('Profile Seeding Complete! Enjoy JobPilot.')
      setTimeout(onComplete, 1500)
    } catch (err) {
      console.error(err)
      setMsg('Exception occurred during save.')
    }
  }

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div>
            <h3>Step 1: Personal Details</h3>
            <div style={{ display: 'grid', gap: '0.8rem' }}>
              <label>Full Name:
                <input type="text" value={basic.full_name} onChange={e => setBasic({ ...basic, full_name: e.target.value })} style={inputStyle} required />
              </label>
              <label>Email:
                <input type="email" value={basic.email} onChange={e => setBasic({ ...basic, email: e.target.value })} style={inputStyle} required />
              </label>
              <label>Phone:
                <input type="text" value={basic.phone} onChange={e => setBasic({ ...basic, phone: e.target.value })} style={inputStyle} />
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <label>City:
                  <input type="text" value={basic.current_city} onChange={e => setBasic({ ...basic, current_city: e.target.value })} style={inputStyle} />
                </label>
                <label>Country:
                  <input type="text" value={basic.current_country} onChange={e => setBasic({ ...basic, current_country: e.target.value })} style={inputStyle} />
                </label>
              </div>
            </div>
          </div>
        )
      case 2:
        return (
          <div>
            <h3>Step 2: Education</h3>
            <div style={{ display: 'grid', gap: '0.5rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <input type="text" placeholder="Institution" value={newEdu.institution} onChange={e => setNewEdu({ ...newEdu, institution: e.target.value })} style={inputStyle} />
              <input type="text" placeholder="Degree (e.g. BS)" value={newEdu.degree} onChange={e => setNewEdu({ ...newEdu, degree: e.target.value })} style={inputStyle} />
              <input type="text" placeholder="Field of Study" value={newEdu.field_of_study} onChange={e => setNewEdu({ ...newEdu, field_of_study: e.target.value })} style={inputStyle} />
              <button onClick={handleAddEdu} style={secBtnStyle}>Add Record</button>
            </div>
            <div>
              {education.map((edu, idx) => (
                <div key={idx} style={badgeStyle}>🎓 {edu.degree} at {edu.institution}</div>
              ))}
            </div>
          </div>
        )
      case 3:
        return (
          <div>
            <h3>Step 3: Professional Skills</h3>
            <div style={{ display: 'grid', gap: '0.5rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <input type="text" placeholder="Skill Name (e.g., Python)" value={newSkill.name} onChange={e => setNewSkill({ ...newSkill, name: e.target.value })} style={inputStyle} />
              <select value={newSkill.category} onChange={e => setNewSkill({ ...newSkill, category: e.target.value })} style={inputStyle}>
                <option value="Programming">Programming</option>
                <option value="Testing">Testing</option>
                <option value="Database">Database</option>
                <option value="DevOps">DevOps</option>
              </select>
              <button onClick={handleAddSkill} style={secBtnStyle}>Add Skill</button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {skills.map((s, idx) => (
                <span key={idx} style={skillBadgeStyle}>{s.name} ({s.proficiency})</span>
              ))}
            </div>
          </div>
        )
      case 4:
        return (
          <div>
            <h3>Step 4: Experience / Projects</h3>
            <div style={{ display: 'grid', gap: '0.8rem', marginBottom: '1rem' }}>
              <label>Years of experience:
                <input type="number" value={basic.years_of_experience} onChange={e => setBasic({ ...basic, years_of_experience: parseFloat(e.target.value) })} style={inputStyle} />
              </label>
              <label>Professional Summary:
                <textarea value={basic.professional_summary} onChange={e => setBasic({ ...basic, professional_summary: e.target.value })} rows="3" style={inputStyle} />
              </label>
            </div>
            <div style={{ display: 'grid', gap: '0.5rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
              <h4>Add Projects</h4>
              <input type="text" placeholder="Project Name" value={newProj.name} onChange={e => setNewProj({ ...newProj, name: e.target.value })} style={inputStyle} />
              <textarea placeholder="Description" value={newProj.description} onChange={e => setNewProj({ ...newProj, description: e.target.value })} style={inputStyle} />
              <input type="text" placeholder="Tech keywords (comma separated)" value={newProj.technologies} onChange={e => setNewProj({ ...newProj, technologies: e.target.value })} style={inputStyle} />
              <button onClick={handleAddProj} style={secBtnStyle}>Add Project</button>
            </div>
            <div style={{ marginTop: '0.5rem' }}>
              {projects.map((p, idx) => (
                <div key={idx} style={badgeStyle}>💻 {p.name} ({p.technologies})</div>
              ))}
            </div>
          </div>
        )
      case 5:
        return (
          <div>
            <h3>Step 5: Resume Center</h3>
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
              You will be able to upload and parse your Master Resume PDF inside the <strong>Resume Center</strong> tab once onboarding is complete.
            </p>
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '1rem', borderRadius: '8px', color: '#15803d', fontSize: '0.85rem' }}>
              ✓ Integration with ResumeIntelligence parser is configured.
            </div>
          </div>
        )
      case 6:
        return (
          <div>
            <h3>Step 6: Job Preferences</h3>
            <div style={{ display: 'grid', gap: '0.8rem' }}>
              <label>Target Roles (comma separated):
                <input type="text" placeholder="e.g. QA Engineer, SDET" value={jobPref.target_roles} onChange={e => setJobPref({ ...jobPref, target_roles: e.target.value })} style={inputStyle} />
              </label>
              <label>Preferred Locations (comma separated):
                <input type="text" placeholder="e.g. Seattle, Remote" value={jobPref.preferred_locations} onChange={e => setJobPref({ ...jobPref, preferred_locations: e.target.value })} style={inputStyle} />
              </label>
              <label>Expected Salary:
                <input type="number" value={jobPref.min_expected_salary} onChange={e => setJobPref({ ...jobPref, min_expected_salary: parseInt(e.target.value) })} style={inputStyle} />
              </label>
            </div>
          </div>
        )
      case 7:
        return (
          <div>
            <h3>Step 7: Automation & Safety Mode</h3>
            <p style={{ fontSize: '0.9rem', color: '#475569' }}>
              JobPilot launches in **Safe Mode** by default.
            </p>
            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#475569', lineHeight: '1.5' }}>
              <li><strong>Dry-Run Mode:</strong> ON (Simulates application adapter workflow without hitting sub-endpoints)</li>
              <li><strong>Human Approval:</strong> REQUIRED (JobPilot will never submit applications without explicit user approval)</li>
              <li><strong>Scheduler Loop:</strong> DISABLED by default.</li>
            </ul>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div style={{
      maxWidth: '560px',
      margin: '4rem auto',
      background: '#ffffff',
      padding: '2.5rem',
      borderRadius: '16px',
      boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
      border: '1px solid #e2e8f0',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <h2 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>Welcome to JobPilot</h2>
      <p style={{ margin: '0 0 1.5rem 0', color: '#64748b', fontSize: '0.9rem' }}>Let's configure your profile details.</p>

      {/* Progress Bar */}
      <div style={{ background: '#e2e8f0', height: '6px', borderRadius: '3px', marginBottom: '1.5rem', overflow: 'hidden' }}>
        <div style={{ background: '#4f46e5', height: '100%', width: `${(step / 7) * 100}%`, transition: 'width 0.3s' }}></div>
      </div>

      <div style={{ fontSize: '0.8rem', color: '#4f46e5', fontWeight: 'bold', marginBottom: '1rem' }}>
        STEP {step} OF 7 ({completeness}% Profile Completeness Calculated)
      </div>

      {msg && <div style={{ background: '#ecfdf5', color: '#047857', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem' }}>{msg}</div>}

      <div style={{ minHeight: '260px' }}>
        {renderStep()}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem', borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem' }}>
        <button onClick={handleBack} disabled={step === 1} style={{
          padding: '0.5rem 1.25rem',
          background: '#f1f5f9',
          color: step === 1 ? '#94a3b8' : '#334155',
          border: 'none',
          borderRadius: '8px',
          cursor: step === 1 ? 'not-allowed' : 'pointer',
          fontWeight: '600'
        }}>Back</button>

        <button onClick={handleNext} style={{
          padding: '0.5rem 1.5rem',
          background: '#4f46e5',
          color: '#ffffff',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: '600'
        }}>
          {step === 7 ? 'Finish Onboarding' : 'Next'}
        </button>
      </div>
    </div>
  )
}

const inputStyle = {
  width: '100%',
  padding: '0.55rem',
  borderRadius: '6px',
  border: '1px solid #cbd5e1',
  marginTop: '0.25rem',
  fontSize: '0.9rem',
  boxSizing: 'border-box'
}

const badgeStyle = {
  background: '#f1f5f9',
  padding: '0.4rem 0.75rem',
  borderRadius: '6px',
  fontSize: '0.85rem',
  color: '#334155',
  marginBottom: '0.4rem'
}

const skillBadgeStyle = {
  background: '#e0e7ff',
  color: '#4338ca',
  padding: '0.35rem 0.65rem',
  borderRadius: '9999px',
  fontSize: '0.8rem',
  fontWeight: '600'
}

const secBtnStyle = {
  padding: '0.45rem',
  background: '#0f172a',
  color: '#ffffff',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: '500',
  fontSize: '0.85rem'
}
