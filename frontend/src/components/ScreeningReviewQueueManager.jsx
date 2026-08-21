import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function ScreeningReviewQueueManager() {
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editText, setEditText] = useState('')
  const [message, setMessage] = useState('')

  const loadReviewQueue = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/questions/review`)
      if (res.ok) {
        setQuestions(await res.json())
      }
    } catch (err) {
      console.error('Failed to load screening review queue:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReviewQueue()
  }, [])

  const handleApprove = async (qId, customText = null) => {
    try {
      const res = await fetch(`${API_BASE}/questions/${qId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer_text: customText, save_to_memory: true }),
      })
      if (res.ok) {
        setMessage(`Question #${qId} approved and saved to AnswerMemory!`)
        setEditingId(null)
        loadReviewQueue()
      }
    } catch (err) {
      console.error('Failed to approve question answer:', err)
    }
  }

  const handleReject = async (qId) => {
    try {
      const res = await fetch(`${API_BASE}/questions/${qId}/reject`, { method: 'POST' })
      if (res.ok) {
        setMessage(`Question #${qId} answer rejected.`)
        loadReviewQueue()
      }
    } catch (err) {
      console.error('Failed to reject question answer:', err)
    }
  }

  return (
    <div style={{ marginTop: '2rem', borderTop: '2px solid #eee', paddingTop: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Screening Question Review Queue</h2>
        <button
          onClick={loadReviewQueue}
          disabled={loading}
          style={{ padding: '0.4rem 0.9rem', background: '#455a64', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {loading ? 'Refreshing...' : 'Refresh Queue'}
        </button>
      </div>

      {message && <div style={{ background: '#e8f5e9', padding: '0.6rem', marginBottom: '1rem', borderRadius: '4px', color: '#2e7d32' }}>{message}</div>}

      {questions.length === 0 ? (
        <div style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '6px', color: '#666' }}>
          ✓ No screening questions currently require human review. All answers are validated or auto-filled.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {questions.map((q) => {
            const ans = q.answer || {}
            const isEditing = editingId === q.id

            return (
              <div key={q.id} style={{ border: '1px solid #ddd', padding: '1rem', borderRadius: '8px', background: '#fff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 'bold', background: '#e3f2fd', color: '#1565c0', padding: '3px 8px', borderRadius: '10px' }}>
                    {q.question_type}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: ans.answer_status === 'INSUFFICIENT_INFORMATION' ? '#c62828' : '#ef6c00', fontWeight: 'bold' }}>
                    Status: {ans.answer_status || 'NEEDS_REVIEW'} (Conf: {(q.classification_confidence * 100).toFixed(0)}%)
                  </span>
                </div>

                <h4 style={{ margin: '0.3rem 0', color: '#222' }}>{q.question_text}</h4>
                <p style={{ fontSize: '0.85rem', color: '#666', margin: '0.2rem 0' }}>
                  Source: <code>{q.answer_source}</code> {q.max_length ? `| Max Length: ${q.max_length} chars` : ''}
                </p>

                {ans.validation_result?.reason && (
                  <div style={{ fontSize: '0.85rem', color: '#c62828', background: '#ffebee', padding: '0.4rem', borderRadius: '4px', margin: '0.5rem 0' }}>
                    ⚠ {ans.validation_result.reason}
                  </div>
                )}

                {/* Proposed Answer Preview or Edit Box */}
                <div style={{ marginTop: '0.8rem', background: '#f8f9fa', padding: '0.8rem', borderRadius: '6px', border: '1px solid #eee' }}>
                  <strong>Proposed Answer:</strong>
                  {isEditing ? (
                    <div style={{ marginTop: '0.5rem' }}>
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        rows="3"
                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
                      />
                      <div style={{ marginTop: '0.4rem' }}>
                        <button
                          onClick={() => handleApprove(q.id, editText)}
                          style={{ padding: '0.4rem 0.8rem', background: '#2e7d32', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '0.5rem' }}
                        >
                          Save & Approve
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          style={{ padding: '0.4rem 0.8rem', background: '#888', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p style={{ margin: '0.4rem 0 0 0', fontStyle: ans.answer_text ? 'normal' : 'italic', color: ans.answer_text ? '#333' : '#888' }}>
                      {ans.answer_text || '[No answer text — candidate profile facts missing for this question]'}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                {!isEditing && (
                  <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.5rem' }}>
                    {ans.answer_text && (
                      <button
                        onClick={() => handleApprove(q.id)}
                        style={{ padding: '0.4rem 0.9rem', background: '#2e7d32', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                      >
                        Approve Answer
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setEditingId(q.id)
                        setEditText(ans.answer_text || '')
                      }}
                      style={{ padding: '0.4rem 0.9rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      {ans.answer_text ? 'Edit & Approve' : 'Provide Manual Answer'}
                    </button>
                    <button
                      onClick={() => handleReject(q.id)}
                      style={{ padding: '0.4rem 0.9rem', background: '#c62828', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      Reject Answer
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
