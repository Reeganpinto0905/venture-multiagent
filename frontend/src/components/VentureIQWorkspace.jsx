import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  ArrowUpRight,
  Award,
  BarChart3,
  Check,
  ChevronDown,
  CircleHelp,
  Copy,
  Database,
  Download,
  Ellipsis,
  FileText,
  Home,
  LineChart,
  Menu,
  Plus,
  Printer,
  RefreshCw,
  Search,
  Settings,
  ShieldAlert,
  Sparkles as SparklesIcon,
  Trash2,
  TrendingUp,
  X,
} from 'lucide-react'
import IntelligenceCore from './IntelligenceCore.jsx'
import { chatWithVentureIQ, analyzeStartup } from '../services/api.js'

const AGENTS = [
  { key: 'supervisor', name: 'Supervisor', detail: 'Determines required intelligence' },
  { key: 'market', name: 'Market', detail: 'Evaluates market opportunity' },
  { key: 'competitor', name: 'Competitor', detail: 'Maps competitive landscape' },
  { key: 'business', name: 'Business', detail: 'Evaluates business viability' },
  { key: 'risk', name: 'Risk', detail: 'Identifies major risks' },
]

const SUGGESTIONS = [
  'Food delivery for college campuses',
  'AI interview preparation platform',
  'Autonomous restaurant delivery robot',
  'Student marketplace',
]

const HISTORY_KEY = 'ventureiq_conversations'

// ---------------------------------------------------------------------------

// Maps our app phases onto the 3D core's animation vocabulary
// (idle | thinking | question | analyzing | complete).
function toCorePhase(appPhase, chatLoading) {
  if (appPhase === 'conversation') return chatLoading ? 'thinking' : 'question'
  if (appPhase === 'analyzing') return 'analyzing'
  if (appPhase === 'complete') return 'complete'
  return 'idle'
}

function Core({ phase, chatLoading = false, pedestal = false }) {
  const corePhase = toCorePhase(phase, chatLoading)
  return (
    <div className="core-wrap" aria-label={`VentureIQ Core ${corePhase}`} role="img">
      <IntelligenceCore phase={corePhase} className="core-canvas" />
      {pedestal && <div className="core-pedestal" />}
      <div className="core-label">
        <span>VENTUREIQ ANALYST</span>
        <strong>
          <i /> ACTIVE
        </strong>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function HistoryGroup({ label, items, activeId, onSelect, onDelete }) {
  if (!items.length) return null
  return (
    <section className="history-group">
      <h3>{label}</h3>
      {items.map((item) => (
        <div key={item.id} className={`history-item ${item.id === activeId ? 'active' : ''}`}>
          <button onClick={() => onSelect(item)}>
            <FileText size={15} />
            <span>{item.title}</span>
            <small>{item.time}</small>
          </button>
          <button className="item-menu" aria-label={`Delete ${item.title}`} onClick={() => onDelete(item.id)}>
            <Trash2 size={13} />
          </button>
        </div>
      ))}
    </section>
  )
}

function relativeDay(ts) {
  if (!ts) return 'today'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return 'today'
  const now = new Date()
  const startOf = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
  const diff = Math.floor((startOf(now) - startOf(d)) / 86400000)
  if (diff <= 0) return 'today'
  if (diff === 1) return 'yesterday'
  if (diff <= 7) return 'last7'
  return 'older'
}

function Sidebar({
  conversations,
  activeId,
  onNew,
  onSelect,
  onDelete,
  open,
  onClose,
  searchInputRef,
  onOpenSettings,
  onOpenHelp,
  onOpenProfile,
}) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return conversations
    return conversations.filter((c) => (c.title || '').toLowerCase().includes(q))
  }, [conversations, search])

  const groups = useMemo(() => {
    const g = { today: [], yesterday: [], last7: [], older: [] }
    for (const c of filtered) {
      const cat = relativeDay(c.timestamp)
      if (g[cat]) g[cat].push(c)
      else g.older.push(c)
    }
    return g
  }, [filtered])

  return (
    <>
      <div className={`sidebar-backdrop ${open ? 'is-open' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'is-open' : ''}`}>
        <div className="brand" onClick={onNew} style={{ cursor: 'pointer' }} title="Return to home page">
          <div className="brand-mark">
            <SparklesIcon size={16} />
          </div>
          <div>
            <strong>VENTUREIQ</strong>
            <span>Startup Intelligence</span>
          </div>
          <button className="mobile-close" onClick={(e) => { e.stopPropagation(); onClose(); }} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>

        <button className="new-analysis" onClick={onNew}>
          <Plus size={17} /> New Analysis
        </button>

        <div className="sidebar-search">
          <Search size={14} />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search conversations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search conversations"
          />
          <span className="search-shortcut">⌘K</span>
        </div>

        <div className="history">
          {conversations.length === 0 ? (
            <div className="history-empty">
              <FileText size={16} />
              <p>No saved analyses yet.</p>
              <small>Run a validation to save reports here.</small>
            </div>
          ) : (
            <>
              <HistoryGroup label="Today" items={groups.today} activeId={activeId} onSelect={onSelect} onDelete={onDelete} />
              <HistoryGroup label="Yesterday" items={groups.yesterday} activeId={activeId} onSelect={onSelect} onDelete={onDelete} />
              <HistoryGroup label="Last 7 days" items={groups.last7} activeId={activeId} onSelect={onSelect} onDelete={onDelete} />
              <HistoryGroup label="Older" items={groups.older} activeId={activeId} onSelect={onSelect} onDelete={onDelete} />
            </>
          )}
        </div>

        <div className="sidebar-bottom">
          <button onClick={onOpenSettings} title="Open System Settings">
            <Settings size={16} /> Settings
          </button>
          <button onClick={onOpenHelp} title="Open Help & Guide">
            <CircleHelp size={16} /> Help
          </button>
          <button className="profile" onClick={onOpenProfile} title="View Founder Profile">
            <span>RP</span>
            <div>
              <strong>Reegan Pinto</strong>
              <small>Pro Plan</small>
            </div>
            <Ellipsis size={16} />
          </button>
        </div>
      </aside>
    </>
  )
}

// ---------------------------------------------------------------------------

function StartupInput({ value, setValue, onSubmit, disabled, inputRef }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
      e.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="input-shell">
      <textarea
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe your startup idea..."
        aria-label="Describe your startup idea"
        rows={3}
        disabled={disabled}
      />
      <div className="input-footer">
        <span>
          <Search size={14} /> Press Enter to analyze
        </span>
        <button onClick={onSubmit} disabled={!value.trim() || disabled}>
          Analyze Idea <ArrowUpRight size={16} />
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Conversation phase — new, not in the visual reference. The reference
// jumped straight from the landing textarea to analysis; this reinserts
// the clarifying-questions step your backend's /chat endpoint drives.

function ConversationView({ messages, choices, loading, readyForAnalysis, draft, setDraft, onSend, onStartAnalysis }) {
  const containerRef = useRef(null)
  const inputRef = useRef(null)
  const autoScrollRef = useRef(true)
  const [showScrollBottom, setShowScrollBottom] = useState(false)

  const scrollToBottom = (behavior = 'smooth') => {
    autoScrollRef.current = true
    setShowScrollBottom(false)
    const scrollElem = containerRef.current?.closest('.workspace-scroll')
    if (scrollElem) {
      scrollElem.scrollTo({
        top: scrollElem.scrollHeight,
        behavior,
      })
    }
  }

  useEffect(() => {
    const scrollElem = containerRef.current?.closest('.workspace-scroll')
    if (!scrollElem) return

    const handleScroll = () => {
      const distanceToBottom = scrollElem.scrollHeight - scrollElem.scrollTop - scrollElem.clientHeight
      const isAtBottom = distanceToBottom <= 80

      autoScrollRef.current = isAtBottom
      setShowScrollBottom(!isAtBottom)
    }

    scrollElem.addEventListener('scroll', handleScroll, { passive: true })
    return () => scrollElem.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (autoScrollRef.current) {
      scrollToBottom(messages.length <= 2 ? 'auto' : 'smooth')
    }
  }, [messages, choices, loading])

  // Return focus to main text input after assistant finishes generating response
  useEffect(() => {
    if (!loading && !readyForAnalysis) {
      const isCoarse = window.matchMedia('(pointer: coarse)').matches
      if (!isCoarse) {
        const timer = setTimeout(() => {
          inputRef.current?.focus({ preventScroll: true })
        }, 60)
        return () => clearTimeout(timer)
      }
    }
  }, [loading, readyForAnalysis])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
      e.preventDefault()
      const text = draft.trim()
      if (text) {
        setDraft('')
        onSend(text)
      }
    }
  }

  return (
    <section className="conversation-view" ref={containerRef}>
      <Core phase="conversation" chatLoading={loading} />

      {messages.map((m, i) => (
        <div key={i} className={`conv-turn ${m.role}`}>
          <div className="conv-bubble">{m.content}</div>
        </div>
      ))}

      {loading && (
        <div className="conv-typing">
          <i /> <i /> <i /> VentureIQ is evaluating...
        </div>
      )}

      {!loading && choices.length > 0 && !readyForAnalysis && (
        <div className="conv-chips">
          {choices.map((c) => (
            <button
              key={c}
              onClick={() => {
                onSend(c)
                inputRef.current?.focus({ preventScroll: true })
              }}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {readyForAnalysis && (
        <div className="conv-ready">
          <div>
            <strong>VentureIQ Intelligence Ready</strong>
            <p>VentureIQ has collected sufficient context to validate this idea.</p>
          </div>
          <button onClick={onStartAnalysis}>
            START VALIDATION <ArrowUpRight size={15} />
          </button>
        </div>
      )}

      {showScrollBottom && (
        <button
          className="scroll-to-bottom-btn"
          onClick={() => scrollToBottom('smooth')}
          aria-label="Scroll to bottom"
          title="Scroll to latest messages"
        >
          <ChevronDown size={18} />
        </button>
      )}

      {!readyForAnalysis && (
        <div className="conv-input">
          <div className="input-shell">
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell VentureIQ more about your idea..."
              aria-label="Tell VentureIQ more about your idea"
              rows={1}
              disabled={loading}
            />
            <div className="input-footer">
              <span>
                <Search size={14} /> Press Enter to send
              </span>
              <button
                onClick={() => {
                  const text = draft.trim()
                  if (!text) return
                  setDraft('')
                  onSend(text)
                }}
                disabled={!draft.trim() || loading}
              >
                Send <ArrowUpRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------

function Pipeline({ activeIndex, complete }) {
  return (
    <div className="pipeline">
      {AGENTS.map((agent, index) => {
        const state = complete || index < activeIndex ? 'complete' : index === activeIndex ? 'running' : 'queued'
        return (
          <div className="pipeline-step" key={agent.key}>
            <div className={`agent-node ${state}`}>
              <span>
                {state === 'complete' ? (
                  <Check size={15} />
                ) : state === 'running' ? (
                  <Activity size={15} />
                ) : (
                  <span className="node-number">0{index + 1}</span>
                )}
              </span>
            </div>
            <div>
              <strong>{agent.name}</strong>
              <small>{agent.detail}</small>
              <em>{state}</em>
            </div>
            {index < AGENTS.length - 1 && <div className={`pipeline-line ${state === 'complete' ? 'complete' : ''}`} />}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------

function MarkdownText({ text }) {
  if (!text) return <p className="empty-result">No detail was returned for this section.</p>
  const lines = String(text).split('\n').filter(Boolean)
  return (
    <div className="markdown">
      {lines.map((line, index) => {
        const clean = line.replace(/^#{1,4}\s*/, '').replace(/^[-*]\s*/, '')
        const bullet = /^[-*]\s/.test(line)
        return bullet ? (
          <p key={index} className="bullet">
            <span />
            {clean}
          </p>
        ) : (
          <p key={index}>{clean}</p>
        )
      })}
    </div>
  )
}

function ResultSection({ title, eyebrow, text, defaultOpen = true }) {
  return (
    <details className="result-section" open={defaultOpen}>
      <summary>
        <div>
          <span>{eyebrow}</span>
          <h2>{title}</h2>
        </div>
        <ChevronDown size={18} />
      </summary>
      <div className="result-content">
        <MarkdownText text={text} />
      </div>
    </details>
  )
}

function AssessmentBar({ label, value }) {
  const v = typeof value === 'number' ? value : 0
  return (
    <div className="assessment-bar">
      <span>{label}</span>
      <div className="assessment-bar-track">
        <div className="assessment-bar-fill" style={{ width: `${Math.max(0, Math.min(100, v))}%` }} />
      </div>
      <strong>{v}</strong>
    </div>
  )
}

// ---------------------------------------------------------------------------

function InvestorReadinessCards({ scores }) {
  const overall = scores.overall ?? 70
  const statusLabel = overall >= 75 ? 'STRONG VENTURE PROSPECT' : overall >= 55 ? 'VIABLE OPPORTUNITY' : 'HIGH RISK PROFILE'
  const statusColor = overall >= 75 ? '#8ce6c0' : overall >= 55 ? '#facc15' : '#f87171'

  return (
    <div className="readiness-section">
      <div className="readiness-header">
        <div className="readiness-title">
          <Award size={16} color="var(--accent)" />
          <strong>INVESTOR READINESS INDEX</strong>
        </div>
        <span className="readiness-badge" style={{ borderColor: statusColor, color: statusColor }}>
          {statusLabel}
        </span>
      </div>

      <div className="readiness-grid">
        <div className="readiness-card">
          <span className="card-eyebrow">Market Demand</span>
          <strong>{scores.market ?? 0}/100</strong>
          <small>{(scores.market ?? 0) >= 70 ? 'High TAM & Growth Pull' : 'Target Niche Required'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Defensibility</span>
          <strong>{scores.competition ?? 0}/100</strong>
          <small>{(scores.competition ?? 0) >= 70 ? 'Differentiated Moat' : 'Crowded Competitor Space'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Financial Scalability</span>
          <strong>{scores.business ?? 0}/100</strong>
          <small>{(scores.business ?? 0) >= 70 ? 'Scalable Margins' : 'High CAC / Capital Intensive'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Risk Protection</span>
          <strong>{scores.risk ?? 0}/100</strong>
          <small>{(scores.risk ?? 0) >= 70 ? 'Manageable Exposure' : 'Regulatory / Execution Risk'}</small>
        </div>
      </div>
    </div>
  )
}

function SettingsModal({ open, onClose, showToast }) {
  const [apiUrl, setApiUrl] = useState('http://127.0.0.1:8000')
  const [autoScroll, setAutoScroll] = useState(true)

  if (!open) return null

  const handleSave = () => {
    showToast('Settings saved successfully!')
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><Settings size={18} color="var(--accent)" /> System Settings</h2>
          <button className="modal-close-btn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: '#c0c8c4' }}>Backend API Base URL</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              style={{ width: '100%', padding: '9px 12px', background: '#0d1112', border: '1px solid var(--border)', borderRadius: 6, color: '#fff', outline: 'none' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
            <span>Automatic Chat Scrolling</span>
            <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} style={{ cursor: 'pointer', accentColor: 'var(--accent)' }} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="action-btn" onClick={onClose}>Cancel</button>
          <button className="new-report" onClick={handleSave}>Save Settings</button>
        </div>
      </div>
    </div>
  )
}

function HelpModal({ open, onClose }) {
  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><CircleHelp size={18} color="var(--accent)" /> VentureIQ Help & Guide</h2>
          <button className="modal-close-btn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <p><strong>1. Discovery Conversation:</strong> Describe any startup concept. The Lead Analyst asks 1–3 sharp follow-up questions to clarify target customer, pain point, and business model.</p>
          <p><strong>2. Validation Pipeline:</strong> Once ready, click <code>START VALIDATION</code> to run 4 specialized agents (Market, Competitor, Business, Risk).</p>
          <p><strong>3. Export Briefs:</strong> Click Copy Brief, Export MD, or Print PDF to share your validation report.</p>
          <p><strong>Keyboard Shortcuts:</strong><br /><code>⌘K / Ctrl+K</code> : Focus search<br /><code>Enter</code> : Submit idea / send message<br /><code>Esc</code> : Close modal / drawer</p>
        </div>
        <div className="modal-footer">
          <button className="new-report" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  )
}

function ProfileModal({ open, onClose }) {
  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><SparklesIcon size={18} color="var(--accent)" /> Founder Profile</h2>
          <button className="modal-close-btn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#172d24', border: '1px solid #2b453b', color: 'var(--accent)', display: 'grid', placeItems: 'center', fontWeight: 700, fontSize: 16 }}>RP</div>
            <div>
              <strong style={{ fontSize: 16, color: '#fff', display: 'block' }}>Reegan Pinto</strong>
              <span style={{ fontSize: 12, color: 'var(--accent)' }}>Pro Founder Plan • Active</span>
            </div>
          </div>
          <div style={{ background: '#0d1112', border: '1px solid var(--border)', borderRadius: 8, padding: 12, display: 'grid', gap: 6, fontSize: 13 }}>
            <div><strong>Email:</strong> reegan@ventureiq.ai</div>
            <div><strong>Analyses Run:</strong> 14 reports completed</div>
            <div><strong>Permissions:</strong> Full Multi-Agent Pipeline & Unlimited Exports</div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="new-report" onClick={onClose}>Close Profile</button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

export default function VentureIQWorkspace() {
  const [query, setQuery] = useState('')
  const [phase, setPhase] = useState('idle') // idle | conversation | analyzing | complete | error
  const [step, setStep] = useState(0)
  const [result, setResult] = useState()
  const [error, setError] = useState('')
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [activeModal, setActiveModal] = useState(null) // null | 'settings' | 'help' | 'profile'
  const searchInputRef = useRef(null)
  const mainInputRef = useRef(null)

  // conversational /chat state
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [choices, setChoices] = useState([])
  const [readyForAnalysis, setReadyForAnalysis] = useState(false)
  const [chatLoading, setChatLoading] = useState(false)
  const [draft, setDraft] = useState('')
  const ideaRef = useRef('')
  const sendingRef = useRef(false)
  const analyzingRef = useRef(false)

  const showToast = (msg) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(''), 2500)
  }

  // Auto focus main startup input whenever entering idle phase
  useEffect(() => {
    if (phase === 'idle') {
      const timer = setTimeout(() => {
        mainInputRef.current?.focus()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [phase])

  // Keyboard shortcuts (Ctrl+K or Cmd+K for search, Esc to close sidebar)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        searchInputRef.current?.focus()
      } else if (e.key === 'Escape') {
        if (mobileOpen) setMobileOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileOpen])

  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      if (saved) setConversations(JSON.parse(saved))
    } catch {
      // malformed local history is safely ignored
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(conversations))
  }, [conversations])

  useEffect(() => {
    if (phase !== 'analyzing') return
    const timer = window.setInterval(() => {
      setStep((current) => Math.min(current + 1, AGENTS.length - 1))
    }, 1500)
    return () => window.clearInterval(timer)
  }, [phase])

  const saveOrUpdateConversation = (id, title, updatedData) => {
    setConversations((prev) => {
      const existingIdx = prev.findIndex((item) => item.id === id)
      const entry = {
        id,
        title: (title || 'Untitled Idea').trim().slice(0, 34),
        time: 'just now',
        timestamp: Date.now(),
        ...(prev[existingIdx] || {}),
        ...updatedData,
      }
      if (existingIdx >= 0) {
        const next = [...prev]
        next[existingIdx] = entry
        return next
      }
      return [entry, ...prev].slice(0, 30)
    })
  }

  const sendMessage = async (text) => {
    const clean = (text || '').trim()
    if (!clean || chatLoading || sendingRef.current) return
    sendingRef.current = true
    if (!ideaRef.current) ideaRef.current = clean

    const currentId = activeId || crypto.randomUUID()
    if (!activeId) setActiveId(currentId)

    const userTurn = { role: 'user', content: clean }
    const initialMessages = [...messages, userTurn]
    setMessages(initialMessages)
    setChoices([])
    setChatLoading(true)
    setPhase('conversation')

    // Preserve conversation in sidebar history immediately
    saveOrUpdateConversation(currentId, ideaRef.current || clean, {
      sessionId: sessionId || currentId,
      messages: initialMessages,
      choices: [],
      readyForAnalysis: false,
      ideaContext: {},
    })

    try {
      const data = await chatWithVentureIQ(sessionId, clean)
      setSessionId(data.session_id)
      const assistantTurn = { role: 'assistant', content: data.reply }

      setMessages((prev) => {
        const nextMessages = [...prev, assistantTurn]
        saveOrUpdateConversation(currentId, ideaRef.current || clean, {
          sessionId: data.session_id,
          messages: nextMessages,
          choices: data.choices || [],
          readyForAnalysis: Boolean(data.ready_for_analysis),
          ideaContext: data.idea_context || {},
        })
        return nextMessages
      })

      setChoices(data.choices || [])
      setReadyForAnalysis(Boolean(data.ready_for_analysis))
    } catch (err) {
      setPhase('error')
      setError(err instanceof Error ? err.message : "VentureIQ couldn't reach the backend.")
    } finally {
      setChatLoading(false)
      sendingRef.current = false
    }
  }

  const startFromLanding = () => {
    const text = query.trim()
    if (!text) return
    setQuery('')
    sendMessage(text)
  }

  const startAnalysis = async () => {
    if (phase === 'analyzing' || analyzingRef.current) return
    analyzingRef.current = true
    setPhase('analyzing')
    setStep(0)
    setError('')
    setResult(undefined)

    const currentId = activeId || crypto.randomUUID()
    if (!activeId) setActiveId(currentId)
    const ideaTitle = ideaRef.current || query || 'Startup Analysis'

    try {
      const data = await analyzeStartup(ideaTitle, sessionId)
      setResult(data)
      setPhase('complete')
      setStep(AGENTS.length - 1)

      saveOrUpdateConversation(currentId, ideaTitle, {
        sessionId: sessionId,
        result: data,
        messages: messages,
        phase: 'complete',
      })
    } catch (err) {
      setPhase('error')
      setError(err instanceof Error ? err.message : 'Unable to complete the analysis.')
    } finally {
      analyzingRef.current = false
    }
  }

  const newAnalysis = () => {
    sendingRef.current = false
    analyzingRef.current = false
    setChatLoading(false)
    setQuery('')
    setResult(undefined)
    setError('')
    setPhase('idle')
    setStep(0)
    setActiveId(undefined)
    setMobileOpen(false)
    setSessionId(null)
    setMessages([])
    setChoices([])
    setReadyForAnalysis(false)
    setDraft('')
    ideaRef.current = ''
    setTimeout(() => {
      mainInputRef.current?.focus()
    }, 50)
  }

  const copyExecutiveBrief = async () => {
    if (!result) return
    const text = `VENTUREIQ EXECUTIVE BRIEF: ${ideaRef.current || query}
Overall Score: ${scores.overall || 'N/A'}/100
Market: ${scores.market || 0}/100 | Competition: ${scores.competition || 0}/100 | Business: ${scores.business || 0}/100 | Risk: ${scores.risk || 0}/100

EXECUTIVE SUMMARY:
${result.summary || 'N/A'}

MARKET INTELLIGENCE:
${result.market_analysis || 'N/A'}

COMPETITOR LANDSCAPE:
${result.competitor_analysis || 'N/A'}

BUSINESS VIABILITY:
${result.business_analysis || 'N/A'}

RISK ASSESSMENT:
${result.risk_analysis || 'N/A'}`

    try {
      await navigator.clipboard.writeText(text)
      showToast('Brief copied to clipboard!')
    } catch {
      showToast('Unable to copy automatically.')
    }
  }

  const exportMarkdownReport = () => {
    if (!result) return
    const mdContent = `# VentureIQ Startup Intelligence Report
**Startup Idea**: ${ideaRef.current || query}  
**Date**: ${new Date().toLocaleDateString()}  
**Overall Validation Score**: ${scores.overall || 'N/A'}/100  

---

## 1. Executive Summary
${result.summary || 'N/A'}

## 2. Score Breakdown
- **Market Opportunity**: ${scores.market || 0}/100
- **Competitive Positioning**: ${scores.competition || 0}/100
- **Business Model Viability**: ${scores.business || 0}/100
- **Risk Mitigation Score**: ${scores.risk || 0}/100

## 3. Market Intelligence
${result.market_analysis || 'N/A'}

## 4. Competitor Landscape
${result.competitor_analysis || 'N/A'}

## 5. Business Viability & Unit Economics
${result.business_analysis || 'N/A'}

## 6. Risk Assessment
${result.risk_analysis || 'N/A'}

---
*Generated by VentureIQ AI Multi-Agent Validation Pipeline*
`
    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `VentureIQ_Report_${(ideaRef.current || 'startup').slice(0, 15).replace(/\s+/g, '_')}.md`
    link.click()
    URL.revokeObjectURL(url)
    showToast('Markdown report downloaded!')
  }

  const printReport = () => {
    window.print()
  }

  const selectConversation = (conversation) => {
    setActiveId(conversation.id)
    setSessionId(conversation.sessionId || conversation.id)
    setQuery(conversation.title)
    setResult(conversation.result)
    setMessages(conversation.messages || [])
    setChoices(conversation.choices || [])
    setReadyForAnalysis(Boolean(conversation.readyForAnalysis))
    ideaRef.current = conversation.title
    if (conversation.result) {
      setPhase('complete')
    } else if (conversation.messages && conversation.messages.length > 0) {
      setPhase('conversation')
    } else {
      setPhase('idle')
    }
    setMobileOpen(false)
  }

  const deleteConversation = (id) => setConversations((current) => current.filter((item) => item.id !== id))

  const scores = result?.scores || {}
  const crumbLabel =
    phase === 'complete' ? 'Validation Report' : phase === 'conversation' ? 'Conversation' : phase === 'analyzing' ? 'Analyzing' : phase === 'error' ? 'Error' : 'New Analysis'

  return (
    <div className="app-shell">
      {toastMessage && <div className="toast-notification">{toastMessage}</div>}

      <SettingsModal open={activeModal === 'settings'} onClose={() => setActiveModal(null)} showToast={showToast} />
      <HelpModal open={activeModal === 'help'} onClose={() => setActiveModal(null)} />
      <ProfileModal open={activeModal === 'profile'} onClose={() => setActiveModal(null)} />

      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onNew={newAnalysis}
        onSelect={selectConversation}
        onDelete={deleteConversation}
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        searchInputRef={searchInputRef}
        onOpenSettings={() => setActiveModal('settings')}
        onOpenHelp={() => setActiveModal('help')}
        onOpenProfile={() => setActiveModal('profile')}
      />

      <main className="workspace">
        <header className="topbar">
          <button className="menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu size={19} />
          </button>
          <div className="crumb">
            <Home size={14} />
            <span>/</span>
            <strong>{crumbLabel}</strong>
          </div>
          <div className="topbar-meta">
            <span className="status-dot" /> Validation Suite Active <span className="topbar-divider" /> v1.0
            <button aria-label="More options">
              <Ellipsis size={18} />
            </button>
          </div>
        </header>

        <div className="workspace-scroll">
          {phase === 'idle' && (
            <section className="hero-grid">
              <div className="hero-left">
                <div className="landing-copy">
                  <span className="eyebrow">
                    <i /> Startup Strategy & Validation
                  </span>
                  <h1>
                    Validate your startup
                    <br />
                    before you <em>build.</em>
                  </h1>
                  <p>
                    Get instant, data-backed feedback on your startup idea — test real market demand,
                    map competitors, and spot hidden execution risks before launching.
                  </p>
                </div>

                <div className="landing-input">
                  <StartupInput value={query} setValue={setQuery} onSubmit={startFromLanding} inputRef={mainInputRef} />
                  <div className="suggestions">
                    <span>Try an example</span>
                    {SUGGESTIONS.map((item) => (
                      <button key={item} onClick={() => { setQuery(''); sendMessage(item); }}>
                        {item}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="hero-features">
                  <div className="hero-feature">
                    <span>
                      <LineChart size={15} />
                    </span>
                    Market Intelligence
                  </div>
                  <div className="hero-feature">
                    <span>
                      <BarChart3 size={15} />
                    </span>
                    Competitor Analysis
                  </div>
                  <div className="hero-feature">
                    <span>
                      <TrendingUp size={15} />
                    </span>
                    Business Validation
                  </div>
                  <div className="hero-feature">
                    <span>
                      <SparklesIcon size={15} />
                    </span>
                    Actionable Insights
                  </div>
                </div>
              </div>

              <div className="hero-right">
                <Core phase="idle" pedestal />
                <div className="stat-badge stat-badge-1">
                  <Activity size={14} /> Analyzing opportunities
                </div>
                <div className="stat-badge stat-badge-2">
                  <Database size={14} /> Competitive intelligence
                </div>
                <div className="stat-badge stat-badge-3">
                  <BarChart3 size={14} /> Global market data
                </div>
                <div className="stat-badge stat-badge-4">
                  <TrendingUp size={14} /> Business validation
                </div>
              </div>
            </section>
          )}

          {phase === 'conversation' && (
            <ConversationView
              messages={messages}
              choices={choices}
              loading={chatLoading}
              readyForAnalysis={readyForAnalysis}
              draft={draft}
              setDraft={setDraft}
              onSend={sendMessage}
              onStartAnalysis={startAnalysis}
            />
          )}

          {phase === 'analyzing' && (
            <section className="analysis-view">
              <div className="analysis-header">
                <span className="eyebrow">
                  <i /> Analysis in progress
                </span>
                <h1>
                  VentureIQ is <em>thinking.</em>
                </h1>
                <p>Evaluating your startup opportunity across the intelligence pipeline.</p>
              </div>
              <Core phase="analyzing" pedestal />
              <div className="query-chip">
                <span>Analyzing</span>
                <strong>{ideaRef.current}</strong>
              </div>
              <Pipeline activeIndex={step} />
            </section>
          )}

          {phase === 'error' && (
            <section className="error-view">
              <Core phase="error" />
              <div className="error-card">
                <span className="error-icon">
                  <RefreshCw size={18} />
                </span>
                <span className="eyebrow">Analysis interrupted</span>
                <h1>Backend connection lost</h1>
                <p>{error || "VentureIQ couldn't reach the analysis engine."}</p>
                <div className="error-actions">
                  <button onClick={sessionId ? startAnalysis : () => sendMessage(ideaRef.current)}>
                    <RefreshCw size={15} /> Retry
                  </button>
                  <button className="secondary" onClick={() => window.open('http://127.0.0.1:8000', '_blank')}>
                    Check Connection <ArrowUpRight size={15} />
                  </button>
                </div>
              </div>
            </section>
          )}

          {phase === 'complete' && result && (
            <section className="report-view">
              <div className="report-head">
                <div>
                  <span className="eyebrow success">
                    <Check size={13} /> Validation complete
                  </span>
                  <h1>
                    Intelligence <em>brief.</em>
                  </h1>
                  <p className="report-idea">{ideaRef.current || query}</p>
                </div>
                <div className="report-actions">
                  <button className="action-btn" onClick={copyExecutiveBrief} title="Copy Executive Summary to Clipboard">
                    <Copy size={14} /> Copy Brief
                  </button>
                  <button className="action-btn" onClick={exportMarkdownReport} title="Download Markdown Report">
                    <Download size={14} /> Export MD
                  </button>
                  <button className="action-btn" onClick={printReport} title="Print or Save PDF">
                    <Printer size={14} /> Print PDF
                  </button>
                  <button className="new-report" onClick={newAnalysis}>
                    <Plus size={15} /> New analysis
                  </button>
                </div>
              </div>

              <div className="assessment">
                <div>
                  <span className="eyebrow">Overall assessment</span>
                  <h2>{result.summary ? 'A considered opportunity, ready for scrutiny.' : 'Analysis received.'}</h2>
                </div>

                {typeof scores.overall === 'number' && (
                  <div className="score-ring" style={{ '--pct': scores.overall }}>
                    <div className="score-ring-inner">
                      <strong>{scores.overall}</strong>
                      <span>Score</span>
                    </div>
                  </div>
                )}

                <div className="assessment-bars">
                  <AssessmentBar label="Market" value={scores.market} />
                  <AssessmentBar label="Competition" value={scores.competition} />
                  <AssessmentBar label="Business" value={scores.business} />
                  <AssessmentBar label="Risk" value={scores.risk} />
                </div>
              </div>

              <InvestorReadinessCards scores={scores} />

              <div className="report-grid">
                <div>
                  <ResultSection title="Market Intelligence" eyebrow="01 / Opportunity" text={result.market_analysis} />
                  <ResultSection title="Competitor Intelligence" eyebrow="02 / Landscape" text={result.competitor_analysis} />
                  <ResultSection title="Risk Assessment" eyebrow="03 / Exposure" text={result.risk_analysis} />
                </div>
                <div>
                  <ResultSection title="Business Viability" eyebrow="04 / Execution" text={result.business_analysis} />
                  <ResultSection title="Executive Summary" eyebrow="05 / Takeaway" text={result.summary} />
                  <ResultSection
                    title="Tasks Run"
                    eyebrow="06 / Pipeline"
                    text={Array.isArray(result.tasks) ? result.tasks.map(String).join('\n') : result.tasks}
                    defaultOpen={false}
                  />
                </div>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
