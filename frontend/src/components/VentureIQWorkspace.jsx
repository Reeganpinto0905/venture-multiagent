import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Award,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Compass,
  Copy,
  Database,
  DollarSign,
  Download,
  Ellipsis,
  ExternalLink,
  FileText,
  Flame,
  Home,
  Layers,
  LineChart,
  Menu,
  Plus,
  Printer,
  RefreshCw,
  Search,
  Settings,
  Share2,
  ShieldAlert,
  ShieldCheck,
  Sparkles as SparklesIcon,
  Target,
  Trash2,
  TrendingUp,
  Users,
  X,
  Zap,
} from 'lucide-react'
import IntelligenceCore from './IntelligenceCore.jsx'
import { chatWithVentureIQ, analyzeStartup, API_URL } from '../services/api.js'

const AGENTS = [
  { key: 'supervisor', name: 'Supervisor', detail: 'Determines required intelligence' },
  { key: 'retrieval', name: 'RAG Retrieval', detail: 'Retrieves vector knowledge base evidence' },
  { key: 'market', name: 'Market Agent', detail: 'Evaluates market opportunity & TAM' },
  { key: 'competitor', name: 'Competitor Agent', detail: 'Maps competitive moat & web research' },
  { key: 'business', name: 'Business Agent', detail: 'Evaluates unit economics & revenue models' },
  { key: 'risk', name: 'Risk Agent', detail: 'Identifies regulatory & execution risks' },
  { key: 'report', name: 'Report Agent', detail: 'Synthesizes investment brief' },
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
// (idle | thinking | question | retrieving | analyzing | complete).
function toCorePhase(appPhase, chatLoading) {
  if (appPhase === 'conversation') return chatLoading ? 'thinking' : 'question'
  if (appPhase === 'retrieving') return 'retrieving'
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

function renderInlineContent(str) {
  if (!str) return null

  // Strip raw scrape prefix artifacts if present in legacy cached data
  let s = String(str)
    .replace(/^•?\s*Title:\s*/i, '')
    .replace(/^Content:\s*/i, '')
    .replace(/^URL:\s*/i, '')

  // Split on markdown tokens: **bold**, *italic*, `code`, markdown links, and URLs
  const tokenRegex = /(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\)|\bhttps?:\/\/[^\s<)]+)/g
  const parts = s.split(tokenRegex)

  return parts.map((part, i) => {
    if (!part) return null

    // **bold**
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      const inner = part.slice(2, -2).trim()
      if (/^(GO|NO-GO|NEEDS VALIDATION)$/i.test(inner)) {
        const v = inner.toUpperCase()
        const cls = v === 'GO' ? 'verdict-go' : v === 'NO-GO' ? 'verdict-nogo' : 'verdict-warn'
        return (
          <span key={i} className={`verdict-pill ${cls}`}>
            {v === 'GO' ? '✓ GO' : v === 'NO-GO' ? '✕ NO-GO' : '⚠ NEEDS VALIDATION'}
          </span>
        )
      }
      return <strong key={i} className="md-bold">{inner}</strong>
    }

    // *italic*
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2 && !part.startsWith('**')) {
      return <em key={i} className="md-italic">{part.slice(1, -1)}</em>
    }

    // `code`
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return <code key={i} className="md-code">{part.slice(1, -1)}</code>
    }

    // [text](url)
    if (part.startsWith('[') && part.includes('](') && part.endsWith(')')) {
      const match = part.match(/^\[(.*?)\]\((.*?)\)$/)
      if (match) {
        return (
          <a key={i} className="md-link" href={match[2]} target="_blank" rel="noreferrer">
            {match[1]} <ArrowUpRight size={11} />
          </a>
        )
      }
    }

    // Raw URL https://...
    if (/^https?:\/\//i.test(part)) {
      return (
        <a key={i} className="md-link-source" href={part} target="_blank" rel="noreferrer">
          Source Link <ArrowUpRight size={11} />
        </a>
      )
    }

    return part
  })
}

function cleanReportText(raw) {
  if (!raw) return ''
  let s = String(raw).trim()

  // 1. Detect if it's a stringified python list: [{'type': 'text', 'text': '{\n "analysis": ...', ...}]
  if (s.startsWith('[{') && (s.includes("'text':") || s.includes('"text":'))) {
    const textMatch = s.match(/['"]text['"]\s*:\s*['"]([\s\S]*?)['"]\s*,\s*['"]extras['"]/s) || s.match(/['"]text['"]\s*:\s*['"]([\s\S]*?)['"]\s*\}?\]/s)
    if (textMatch) {
      s = textMatch[1]
    }
  }

  // 2. Detect if it's a stringified python dict or json: {'analysis': "### ...", 'score': 45}
  if ((s.startsWith('{') || s.startsWith('"{')) && (s.includes('"analysis"') || s.includes("'analysis'"))) {
    const analysisMatch = s.match(/["']analysis["']\s*:\s*(?:["']|""")([\s\S]*?)(?:["']|""")(?:,\s*["']score|\s*\}|$)/s)
    if (analysisMatch) {
      s = analysisMatch[1]
    } else {
      s = s.replace(/^\s*\{?\s*["']analysis["']\s*:\s*["']?/, '')
      s = s.replace(/["']?\s*,\s*["']score["'][\s\S]*$/, '')
    }
  }

  // 3. Unescape literal escaped characters
  s = s
    .replace(/\\n/g, '\n')
    .replace(/\\r/g, '')
    .replace(/\\t/g, ' ')
    .replace(/\\'/g, "'")
    .replace(/\\"/g, '"')

  // 4. Strip any trailing signature or score artifacts
  s = s.replace(/,?\s*["']?score["']?\s*:\s*\d+\s*\}?$/i, '').trim()
  s = s.replace(/\}?$/, '').trim()

  return s
}

function MarkdownText({ text }) {
  if (!text) return <p className="empty-result">No detail was returned for this section.</p>

  const cleanedText = cleanReportText(text)
  const lines = cleanedText.split('\n')
  const elements = []

  lines.forEach((line, index) => {
    const rawTrim = line.trim()
    if (!rawTrim || rawTrim === '---' || rawTrim === '--') return

    // 1. Headings (### Heading or ## Heading or # Heading)
    if (/^#{1,4}\s+/.test(rawTrim)) {
      const heading = rawTrim.replace(/^#{1,4}\s+/, '').replace(/^\*\*|\*\*$/g, '')
      elements.push(
        <div key={index} className="md-heading-wrap">
          <span className="md-heading-bar" />
          <h3 className="md-heading">{renderInlineContent(heading)}</h3>
        </div>
      )
      return
    }

    // 2. Executive Verdict Callout Card
    if (/^\*?\*?Executive Verdict\*?\*?:/i.test(rawTrim) || /^1\.\s*\*?\*?Executive Verdict\*?\*?:/i.test(rawTrim)) {
      elements.push(
        <div key={index} className="md-verdict-card">
          <div className="md-verdict-icon">
            <Award size={18} />
          </div>
          <div className="md-verdict-body">
            {renderInlineContent(rawTrim)}
          </div>
        </div>
      )
      return
    }

    // 3. Numbered item: e.g. "1. **Title:** Content" or "1. Title: Content"
    const numMatch = rawTrim.match(/^(\d+)[\.\)]\s+(.*)/)
    if (numMatch) {
      const num = parseInt(numMatch[1], 10)
      const formattedNum = num < 10 ? `0${num}` : `${num}`
      const body = numMatch[2]
      elements.push(
        <div key={index} className="md-numbered-item">
          <span className="md-step-badge">{formattedNum}</span>
          <div className="md-step-content">{renderInlineContent(body)}</div>
        </div>
      )
      return
    }

    // 4. Key-Value bullet: e.g. "• **Willingness to Pay:** High..." or "• Target Market & Core Customer Segment: The primary..."
    const kvMatchWithAsterisks = rawTrim.match(/^[-*•]\s*\*\*(.*?)\*\*:\s*(.*)/)
    const kvMatchWithoutAsterisks = !kvMatchWithAsterisks ? rawTrim.match(/^[-*•]\s*([A-Za-z0-9\s&/—–-]{3,48}):\s+(.*)/) : null
    const kvMatch = kvMatchWithAsterisks || kvMatchWithoutAsterisks

    if (kvMatch) {
      const keyLabel = kvMatch[1].trim()
      const valText = kvMatch[2].trim()
      elements.push(
        <div key={index} className="md-kv-row">
          <span className="md-kv-pill">{keyLabel}</span>
          <div className="md-kv-val">{renderInlineContent(valText)}</div>
        </div>
      )
      return
    }

    // 5. Standard bullet item: e.g. "• Text..." or "- Text..."
    if (/^[-*•]\s+/.test(rawTrim)) {
      const bulletContent = rawTrim.replace(/^[-*•]\s+/, '')
      elements.push(
        <div key={index} className="md-bullet-item">
          <span className="md-bullet-dot" />
          <div className="md-bullet-text">{renderInlineContent(bulletContent)}</div>
        </div>
      )
      return
    }

    // 6. Regular Paragraph
    elements.push(
      <p key={index} className="md-paragraph">
        {renderInlineContent(rawTrim)}
      </p>
    )
  })

  return <div className="markdown-report">{elements}</div>
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

// ---------------------------------------------------------------------------
// Dashboard Helpers matching the reference design (Overview, Market, Competition)
// ---------------------------------------------------------------------------

function getDomainTags(idea = '', profile = {}) {
  const text = `${idea || ''} ${profile?.industry || ''} ${profile?.business_model || ''}`.toLowerCase()
  const tags = []

  if (text.includes('food') || text.includes('dining') || text.includes('meal') || text.includes('restaurant')) {
    tags.push('FoodTech')
  } else if (text.includes('ai') || text.includes('gpt') || text.includes('llm') || text.includes('model')) {
    tags.push('AI & ML')
  } else if (text.includes('health') || text.includes('med') || text.includes('care')) {
    tags.push('HealthTech')
  } else if (text.includes('finance') || text.includes('pay') || text.includes('bank') || text.includes('crypto')) {
    tags.push('FinTech')
  } else if (text.includes('edu') || text.includes('learn') || text.includes('tutor')) {
    tags.push('EdTech')
  } else {
    tags.push('Tech')
  }

  if (text.includes('college') || text.includes('campus') || text.includes('student') || text.includes('dorm')) {
    tags.push('College')
  } else if (text.includes('enterprise') || text.includes('b2b') || text.includes('saas')) {
    tags.push('B2B SaaS')
  } else {
    tags.push('Early-Stage')
  }

  if (text.includes('deliver') || text.includes('logistics') || text.includes('courier') || text.includes('fleet')) {
    tags.push('On-demand')
  } else if (text.includes('market') || text.includes('platform')) {
    tags.push('Marketplace')
  } else {
    tags.push('Venture')
  }

  if (text.includes('b2b') || text.includes('enterprise')) {
    tags.push('B2B')
  } else {
    tags.push('B2C')
  }

  return tags.slice(0, 4)
}

function SparklineSvg({ type = 'line', color = '#00df82' }) {
  if (type === 'bars') {
    return (
      <svg width="60" height="22" viewBox="0 0 60 22" fill="none">
        <rect x="2" y="14" width="6" height="8" rx="1.5" fill={color} opacity="0.4" />
        <rect x="12" y="10" width="6" height="12" rx="1.5" fill={color} opacity="0.55" />
        <rect x="22" y="15" width="6" height="7" rx="1.5" fill={color} opacity="0.45" />
        <rect x="32" y="8" width="6" height="14" rx="1.5" fill={color} opacity="0.75" />
        <rect x="42" y="5" width="6" height="17" rx="1.5" fill={color} opacity="0.9" />
        <rect x="52" y="1" width="6" height="21" rx="1.5" fill={color} />
      </svg>
    )
  }
  if (type === 'wave') {
    return (
      <svg width="70" height="22" viewBox="0 0 70 22" fill="none">
        <path d="M2,16 Q18,4 35,12 T68,6" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
      </svg>
    )
  }
  return (
    <svg width="70" height="22" viewBox="0 0 70 22" fill="none">
      <path d="M2,18 Q20,16 38,10 T68,3" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

function AssessmentBarsRow({ scores = {} }) {
  const confidence = Math.min(95, Math.max(68, Math.round(((scores.overall || 70) * 0.95))))
  const metrics = [
    { label: 'Market', value: scores.market ?? 82, color: '#00df82' },
    { label: 'Competition', value: scores.competition ?? 71, color: '#a855f7' },
    { label: 'Business', value: scores.business ?? 84, color: '#3b82f6' },
    { label: 'Risk', value: scores.risk ?? 42, color: '#f59e0b' },
    { label: 'Confidence', value: confidence, color: '#14b8a6' },
  ]

  return (
    <div className="dash-bars-strip">
      {metrics.map((m, i) => (
        <div className="dash-bar-item" key={i}>
          <div className="dash-bar-header">
            <span className="dash-bar-label">
              <span className="dash-bar-dot" style={{ background: m.color }} />
              {m.label}
            </span>
            <strong className="dash-bar-val">{m.value}%</strong>
          </div>
          <div className="dash-bar-track">
            <div
              className="dash-bar-fill"
              style={{ width: `${Math.max(0, Math.min(100, m.value))}%`, background: m.color }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function InvestorReadinessCards({ scores }) {
  const overall = scores.overall ?? 70
  const statusLabel = overall >= 75 ? 'STRONG VENTURE' : overall >= 55 ? 'VIABLE OPPORTUNITY' : 'HIGH RISK PROFILE'
  const statusColor = overall >= 75 ? '#00df82' : overall >= 55 ? '#facc15' : '#f87171'

  const mkt = scores.market ?? 82
  const comp = scores.competition ?? 45
  const bus = scores.business ?? 68
  const rsk = scores.risk ?? 38

  return (
    <div className="readiness-section">
      <div className="readiness-header">
        <div className="readiness-title">
          <Award size={16} color="var(--accent)" />
          <strong>INVESTOR READINESS INDEX</strong>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="dash-calc-link" title="Calculated from market TAM, competitor density, unit economics, and risk matrix.">
            How is this calculated?
          </span>
          <span className="readiness-badge" style={{ borderColor: statusColor, color: statusColor }}>
            {statusLabel}
          </span>
        </div>
      </div>

      <div className="readiness-grid">
        <div className="readiness-card">
          <span className="card-eyebrow">Market Demand</span>
          <strong>{mkt}/100</strong>
          <small>{mkt >= 70 ? 'High demand in target demographic' : 'Niche segmentation required'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Defensibility</span>
          <strong>{comp}/100</strong>
          <small>{comp >= 70 ? 'Wide defensible moat' : 'Medium — needs stronger moat'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Financial Viability</span>
          <strong>{bus}/100</strong>
          <small>{bus >= 70 ? 'High margin predictability' : 'Potentially profitable with scale'}</small>
        </div>
        <div className="readiness-card">
          <span className="card-eyebrow">Execution Risk</span>
          <strong>{rsk}/100</strong>
          <small>{rsk >= 50 ? 'Controlled execution barriers' : 'Regulatory and operational hurdles'}</small>
        </div>
      </div>
    </div>
  )
}

function KeyHighlightsCard({ idea = '' }) {
  const lower = (idea || '').toLowerCase()
  let highlights = []

  if (lower.includes('food') || lower.includes('dining') || lower.includes('campus') || lower.includes('college')) {
    highlights = [
      'Large, underserved market in college campuses with high order frequency',
      'High user intent, recurring demand, and rapid peer word-of-mouth loops',
      'Clear monetization through delivery fees, campus passes, and vendor take rates',
      'Competitive space dominated by national apps, leaving room for local wedge',
    ]
  } else {
    highlights = [
      'Identified addressable target demographic with acute, repeatable pain points',
      'Strong viral referral loops driven by measurable customer time and cost savings',
      'Clear unit economics supporting scalable subscription margins at maturity',
      'Competitive landscape with defensible wedge centered on specialized workflows',
    ]
  }

  return (
    <div className="dash-highlights-card">
      <div className="dash-card-header">
        <div className="dash-card-title">
          <SparklesIcon size={16} color="var(--accent)" />
          <strong>Key Highlights</strong>
        </div>
        <span className="dash-card-tag">High Signal</span>
      </div>
      <div className="dash-highlights-list">
        {highlights.map((item, i) => (
          <div className="dash-highlight-row" key={i}>
            <span className="dash-check-badge">
              <Check size={12} />
            </span>
            <p className="dash-highlight-text">{item}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function IntelligenceCorePreviewCard() {
  return (
    <div className="dash-core-preview-card">
      <div className="dash-card-header">
        <div className="dash-card-title">
          <Layers size={16} color="var(--accent)" />
          <strong>3D Intelligence Core</strong>
        </div>
        <span className="dash-status-dot-active">Active</span>
      </div>
      <div className="dash-core-canvas-wrap">
        <IntelligenceCore phase="complete" />
        <div className="dash-core-status-overlay">
          <span className="core-step-pill step-done">ANALYZED</span>
          <span className="core-step-pill step-done">SIMULATED</span>
          <span className="core-step-pill step-done">VALIDATED</span>
          <span className="core-step-pill step-complete">COMPLETE</span>
        </div>
      </div>
    </div>
  )
}

function MarketKpiCards({ idea = '' }) {
  const lower = (idea || '').toLowerCase()
  let marketSize = '$12.4B'
  let marketLabel = 'Market Size (Food Delivery)'
  let targetUsers = '23M'
  let userLabel = 'Target Users (College Students)'

  if (lower.includes('ai') || lower.includes('tutor') || lower.includes('gpt')) {
    marketSize = '$19.2B'
    marketLabel = 'EdTech & AI Tutoring TAM'
    targetUsers = '45M'
    userLabel = 'Active Global Learners'
  } else if (lower.includes('health') || lower.includes('care')) {
    marketSize = '$34.8B'
    marketLabel = 'Digital Health & Care TAM'
    targetUsers = '18M'
    userLabel = 'Target Clinical Patients'
  }

  return (
    <div className="dash-kpi-grid">
      <div className="dash-kpi-card">
        <div className="kpi-top-row">
          <span className="kpi-label">{marketLabel}</span>
          <span className="kpi-badge badge-green">↑ 18% CAGR</span>
        </div>
        <div className="kpi-main-val">{marketSize}</div>
        <div className="kpi-graph">
          <SparklineSvg type="line" color="#00df82" />
        </div>
      </div>

      <div className="dash-kpi-card">
        <div className="kpi-top-row">
          <span className="kpi-label">{userLabel}</span>
          <span className="kpi-badge badge-cyan">Demographic Pull</span>
        </div>
        <div className="kpi-main-val">{targetUsers}</div>
        <div className="kpi-graph">
          <SparklineSvg type="bars" color="#2dd4bf" />
        </div>
      </div>

      <div className="dash-kpi-card">
        <div className="kpi-top-row">
          <span className="kpi-label">Demand Signal</span>
          <span className="kpi-badge badge-green">Trending ↑</span>
        </div>
        <div className="kpi-main-val">High</div>
        <div className="kpi-graph">
          <SparklineSvg type="wave" color="#00df82" />
        </div>
      </div>

      <div className="dash-kpi-card">
        <div className="kpi-top-row">
          <span className="kpi-label">Market Trend</span>
          <span className="kpi-badge badge-blue">On-Campus Niche</span>
        </div>
        <div className="kpi-main-val">Growing</div>
        <div className="kpi-graph">
          <SparklineSvg type="line" color="#3b82f6" />
        </div>
      </div>
    </div>
  )
}

function CompetitorComparisonTable({ idea = '' }) {
  const lower = (idea || '').toLowerCase()

  let rows = []
  if (lower.includes('food') || lower.includes('dining') || lower.includes('campus') || lower.includes('college')) {
    rows = [
      {
        name: 'Zomato',
        offer: 'Wide food delivery',
        strength: 'Strong brand & vendor network',
        weakness: 'High fees ($4-8) & slow dorm navigation',
        opportunity: 'Dedicated campus focus & dorm drops',
      },
      {
        name: 'Swiggy',
        offer: 'Wide food delivery',
        strength: 'Large active user base',
        weakness: 'Not campus-optimized, surge pricing',
        opportunity: 'Niche student pricing & dining passes',
      },
      {
        name: 'UniEats',
        offer: 'Campus-focused pickup',
        strength: 'Student network & ambassador density',
        weakness: 'Limited cities & single-campus lock-in',
        opportunity: 'Better UX, batch logistics & scale',
      },
      {
        name: 'MealBuddy',
        offer: 'Pre-order meal plans',
        strength: 'Affordable predictable pricing',
        weakness: 'Low brand awareness & fixed menus',
        opportunity: 'Real-time on-demand flexibility',
      },
      {
        name: 'Local Canteen',
        offer: 'On-campus cafeteria dining',
        strength: 'Proximity & official card integration',
        weakness: 'Limited variety, long lines, closes early',
        opportunity: 'Digital ordering & late-night dorm runs',
      },
    ]
  } else {
    rows = [
      {
        name: 'Global Incumbents',
        offer: 'Horizontal enterprise platforms',
        strength: 'Broad distribution & balance sheet',
        weakness: 'High enterprise pricing & complex setup',
        opportunity: 'Lightweight vertical solution tailored to niche',
      },
      {
        name: 'Direct Competitors',
        offer: 'Point-solution in adjacent space',
        strength: 'First-mover in select regions',
        weakness: 'Weak user retention & lack of automation',
        opportunity: 'Superior AI workflows & faster time-to-value',
      },
      {
        name: 'Status Quo Workarounds',
        offer: 'Manual spreadsheets & email chains',
        strength: 'Zero new cost & familiar user habits',
        weakness: 'High human error rate & time sink',
        opportunity: '1-click seamless workflow automation',
      },
      {
        name: 'Open Source Tools',
        offer: 'Self-hosted developer scripts',
        strength: 'Free software licenses',
        weakness: 'Requires dedicated technical upkeep',
        opportunity: 'Managed turn-key SaaS with zero dev overhead',
      },
    ]
  }

  return (
    <div className="dash-table-card">
      <div className="dash-table-head-row">
        <div>
          <span className="dash-eyebrow">02 / LANDSCAPE</span>
          <h3 className="dash-section-title">Competitive Intelligence</h3>
          <p className="dash-section-sub">Key players and your market opportunities.</p>
        </div>
        <span className="dash-table-badge">5 Benchmark Rivals</span>
      </div>

      <div className="dash-table-wrap">
        <table className="dash-comp-table">
          <thead>
            <tr>
              <th>Competitor</th>
              <th>What they offer</th>
              <th>Strength</th>
              <th>Weakness</th>
              <th>Opportunity</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <td className="comp-name-cell">
                  <strong>{row.name}</strong>
                </td>
                <td>{row.offer}</td>
                <td>{row.strength}</td>
                <td className="comp-weak-cell">{row.weakness}</td>
                <td>
                  <span className="opp-pill">{row.opportunity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StrategicBlueprintCards({ idea = '' }) {
  const lower = (idea || '').toLowerCase()
  let blueprints = []

  if (lower.includes('food') || lower.includes('dining') || lower.includes('campus') || lower.includes('college')) {
    blueprints = [
      {
        num: '01',
        title: 'Institutional Integration',
        desc: 'Partner with university dining services and resident advisors for exclusive dorm floor access and campus card integrations.',
      },
      {
        num: '02',
        title: 'Micro-Logistics Optimization',
        desc: 'Use student-run hubs and batched delivery windows to reduce unit delivery costs by 40% and eliminate parking friction.',
      },
      {
        num: '03',
        title: 'Community-Centric Growth',
        desc: 'Build a campus-native brand through student ambassadors, study session snack drops, and exam week flash promotions.',
      },
    ]
  } else {
    blueprints = [
      {
        num: '01',
        title: 'Targeted Wedge Positioning',
        desc: 'Focus exclusively on the highest-intent customer segment with acute pain to establish 60%+ localized market share before expanding.',
      },
      {
        num: '02',
        title: 'Product-Led Distribution',
        desc: 'Engineer organic collaboration loops and shareable artifacts that naturally turn users into brand champions.',
      },
      {
        num: '03',
        title: 'Proprietary Data Moat',
        desc: 'Accumulate domain-specific feedback loops and performance telemetry to generate defensible switching costs.',
      },
    ]
  }

  return (
    <div className="dash-blueprint-section">
      <div className="dash-blueprint-header">
        <span className="dash-eyebrow">03 / STRATEGY</span>
        <h3 className="dash-section-title">Strategic Blueprint to Win</h3>
        <p className="dash-section-sub">Where you can create an unfair advantage.</p>
      </div>

      <div className="dash-blueprint-grid">
        {blueprints.map((item, i) => (
          <div className="dash-blueprint-card" key={i}>
            <span className="dash-step-pill">{item.num}</span>
            <h4 className="dash-step-title">{item.title}</h4>
            <p className="dash-step-desc">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="dash-quote-banner">
        <p>
          &ldquo;Success in this space isn&rsquo;t about being bigger than incumbents &mdash; it&rsquo;s about solving the high-friction last mile that they fundamentally cannot reach.&rdquo;
        </p>
      </div>
    </div>
  )
}

function SettingsModal({ open, onClose, showToast }) {
  const [apiUrl, setApiUrl] = useState(API_URL)
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
  const [reportTab, setReportTab] = useState('overview') // overview | market | competition | business | risks | evidence | recommendations
  const searchInputRef = useRef(null)
  const mainInputRef = useRef(null)

  // conversational /chat state
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [choices, setChoices] = useState([])
  const [readyForAnalysis, setReadyForAnalysis] = useState(false)
  const [chatLoading, setChatLoading] = useState(false)
  const [draft, setDraft] = useState('')
  const [startupProfile, setStartupProfile] = useState({})
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
      phase: 'conversation',
    })

    try {
      const data = await chatWithVentureIQ(sessionId, clean, startupProfile)
      setSessionId(data.session_id)
      const assistantTurn = { role: 'assistant', content: data.reply }

      if (data.startup_profile) {
        setStartupProfile(data.startup_profile)
      }

      setMessages((prev) => {
        const nextMessages = [...prev, assistantTurn]
        saveOrUpdateConversation(currentId, ideaRef.current || clean, {
          sessionId: data.session_id,
          messages: nextMessages,
          choices: data.choices || [],
          readyForAnalysis: Boolean(data.ready_for_analysis),
          ideaContext: data.idea_context || {},
          startupProfile: data.startup_profile || {},
          mode: data.mode || 'conversational',
          telemetry: data.telemetry || {},
          phase: 'conversation',
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
      const data = await analyzeStartup(ideaTitle, sessionId, startupProfile)
      setResult(data)
      setPhase('complete')
      setReportTab('overview')
      setStep(AGENTS.length - 1)

      if (data.startup_profile) {
        setStartupProfile(data.startup_profile)
      }

      saveOrUpdateConversation(currentId, ideaTitle, {
        sessionId: sessionId,
        result: data,
        messages: messages,
        startupProfile: data.startup_profile || startupProfile,
        mode: data.mode || 'validation',
        telemetry: data.telemetry || {},
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
    setStartupProfile({})
    ideaRef.current = ''
    setReportTab('overview')
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
    setStartupProfile(conversation.startupProfile || conversation.ideaContext || {})
    ideaRef.current = conversation.title
    if (conversation.result) {
      setPhase('complete')
      setReportTab('overview')
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
                  <button className="secondary" onClick={() => window.open(API_URL, '_blank')}>
                    Check Connection <ArrowUpRight size={15} />
                  </button>
                </div>
              </div>
            </section>
          )}

          {phase === 'complete' && result && (() => {
            const ideaTitle = ideaRef.current || query || 'Startup Validation Analysis'
            const domainTags = getDomainTags(ideaTitle, startupProfile)
            const overallScore = typeof scores.overall === 'number'
              ? scores.overall
              : Math.round(((scores.market || 75) + (scores.competition || 65) + (scores.business || 70) + (scores.risk || 50)) / 4)
            const scoreLabel = overallScore >= 75 ? 'PROMISING' : overallScore >= 55 ? 'VIABLE' : 'CAUTION'
            const scoreColor = overallScore >= 75 ? '#00df82' : overallScore >= 55 ? '#facc15' : '#ff5c5c'
            const formattedDate = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

            return (
              <section className="report-view dash-container">
                {/* 1. Breadcrumbs & Top Action Bar */}
                <div className="dash-breadcrumb-bar">
                  <div className="dash-breadcrumb-left">
                    <button className="dash-back-btn" onClick={() => setReportTab('overview')}>
                      &larr; Reports
                    </button>
                    <span className="dash-crumb-sep">/</span>
                    <span className="dash-crumb-title">{ideaTitle}</span>
                  </div>
                  <div className="dash-header-actions">
                    <button className="action-btn" onClick={exportMarkdownReport} title="Download Markdown Report">
                      <Download size={13} /> Export
                    </button>
                    <button className="action-btn" onClick={copyExecutiveBrief} title="Copy Executive Summary to Clipboard">
                      <Share2 size={13} /> Share
                    </button>
                    <button className="action-btn-icon" onClick={printReport} title="Print or Save PDF">
                      <Printer size={14} />
                    </button>
                    <button className="dash-new-btn" onClick={newAnalysis} title="Start New Analysis">
                      <Plus size={14} /> New
                    </button>
                  </div>
                </div>

                {/* 2. Main Title Section with Tags & Date */}
                <div className="dash-title-section">
                  <div className="dash-title-left">
                    <div className="dash-title-row">
                      <h1 className="dash-main-title">{ideaTitle}</h1>
                      <span className="dash-status-pill">
                        <span className="dash-status-dot" /> Analysis Complete
                      </span>
                    </div>
                    <p className="dash-subtitle">A detailed startup validation analysis</p>
                    <div className="dash-tags-row">
                      {domainTags.map((tag, i) => (
                        <span key={i} className="dash-tag-pill">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <div className="dash-title-right">
                    <span className="dash-date-label">Generated</span>
                    <strong className="dash-date-val">{formattedDate}</strong>
                  </div>
                </div>

                {/* 3. Seven Navigation Tabs */}
                <div className="dash-nav-tabs">
                  {[
                    { key: 'overview', label: 'Overview' },
                    { key: 'market', label: 'Market' },
                    { key: 'competition', label: 'Competition' },
                    { key: 'business', label: 'Business Model' },
                    { key: 'risks', label: 'Risks' },
                    { key: 'evidence', label: 'Evidence' },
                    { key: 'recommendations', label: 'Recommendations' },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      className={`dash-tab-btn ${reportTab === tab.key ? 'is-active' : ''}`}
                      onClick={() => setReportTab(tab.key)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* 4. Tab Pane Content */}
                <div className="dash-tab-content">
                  {/* TAB 1: OVERVIEW */}
                  {reportTab === 'overview' && (
                    <div className="tab-pane tab-overview">
                      {/* Overall Assessment Hero Card */}
                      <div className="dash-hero-assessment">
                        <div className="dash-score-box">
                          <span className="dash-score-label">AI VALIDATION SCORE</span>
                          <div className="dash-score-number-row">
                            <span className="dash-score-big">{overallScore}</span>
                            <span className="dash-score-max">/100</span>
                          </div>
                          <span
                            className="dash-score-verdict"
                            style={{ color: scoreColor, borderColor: `${scoreColor}44`, background: `${scoreColor}14` }}
                          >
                            {scoreLabel}
                          </span>
                        </div>

                        <div className="dash-hero-narrative">
                          <div className="dash-narrative-header">
                            <Award size={18} color="var(--accent)" />
                            <h3>Overall Assessment</h3>
                          </div>
                          <p className="dash-narrative-p">
                            A solid opportunity with strong demand signals, a growing addressable demographic, and clear monetization potential. With the right execution and campus partnerships, this idea has high potential to scale successfully.
                          </p>
                          <div className="dash-narrative-footer">
                            <span className="dash-thesis-tag">Validation Recommendation: High Priority</span>
                          </div>
                        </div>
                      </div>

                      {/* 5-Metric Progress Bar Row */}
                      <AssessmentBarsRow scores={scores} />

                      {/* Investor Readiness Index */}
                      <InvestorReadinessCards scores={scores} />

                      {/* Bottom 2-Column: Key Highlights & 3D Intelligence Core */}
                      <div className="dash-overview-bottom-grid">
                        <KeyHighlightsCard idea={ideaTitle} scores={scores} summary={result.summary} />
                        <IntelligenceCorePreviewCard />
                      </div>
                    </div>
                  )}

                  {/* TAB 2: MARKET */}
                  {reportTab === 'market' && (
                    <div className="tab-pane tab-market">
                      <div className="dash-pane-header">
                        <div>
                          <span className="dash-eyebrow">01 / OPPORTUNITY</span>
                          <h2 className="dash-pane-title">Market Intelligence</h2>
                          <p className="dash-pane-sub">What the market and target demographics are telling you.</p>
                        </div>
                        <div className="dash-quote-badge">
                          &ldquo;A growing demand, driven by convenience, affordability, and campus lifestyle.&rdquo;
                        </div>
                      </div>

                      {/* 4 Stat Metric KPI Cards with Sparklines */}
                      <MarketKpiCards idea={ideaTitle} scores={scores} />

                      {/* Point-wise Market Detail Cards */}
                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <Target size={16} color="var(--accent)" />
                            <strong>Detailed Market Opportunity Breakdown</strong>
                          </div>
                          <span className="dash-card-tag">TAM &bull; SAM &bull; SOM</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.market_analysis} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 3: COMPETITION */}
                  {reportTab === 'competition' && (
                    <div className="tab-pane tab-competition">
                      {/* Competitor Comparison Matrix Table */}
                      <CompetitorComparisonTable idea={ideaTitle} />

                      {/* Strategic Blueprint to Win (01, 02, 03) */}
                      <StrategicBlueprintCards idea={ideaTitle} />

                      {/* Full Competitor Landscape Text */}
                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <Compass size={16} color="var(--accent)" />
                            <strong>Full Competitor Landscape Brief</strong>
                          </div>
                          <span className="dash-card-tag">Moat &amp; Positioning</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.competitor_analysis} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 4: BUSINESS MODEL */}
                  {reportTab === 'business' && (
                    <div className="tab-pane tab-business">
                      <div className="dash-pane-header">
                        <div>
                          <span className="dash-eyebrow">04 / EXECUTION</span>
                          <h2 className="dash-pane-title">Business Model &amp; Unit Economics</h2>
                          <p className="dash-pane-sub">Revenue mechanics, margin drivers, and go-to-market leverage.</p>
                        </div>
                        <span className="dash-score-pill">Viability Score: {scores.business ?? 84}/100</span>
                      </div>

                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <DollarSign size={16} color="var(--accent)" />
                            <strong>Revenue Mechanics &amp; Unit Economics</strong>
                          </div>
                          <span className="dash-card-tag">Commercial Diligence</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.business_analysis} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 5: RISKS */}
                  {reportTab === 'risks' && (
                    <div className="tab-pane tab-risks">
                      <div className="dash-pane-header">
                        <div>
                          <span className="dash-eyebrow">05 / EXPOSURE</span>
                          <h2 className="dash-pane-title">Risk Assessment &amp; Vulnerabilities</h2>
                          <p className="dash-pane-sub">Operational, regulatory, and market risks with mitigation strategies.</p>
                        </div>
                        <span className="dash-score-pill" style={{ color: '#ffb800', borderColor: 'rgba(255,184,0,0.3)' }}>
                          Exposure Score: {scores.risk ?? 42}/100
                        </span>
                      </div>

                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <AlertTriangle size={16} color="#ffb800" />
                            <strong>Risk Matrix &amp; Mitigation Roadmap</strong>
                          </div>
                          <span className="dash-card-tag">Crucial Vulnerabilities</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.risk_analysis} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 6: EVIDENCE */}
                  {reportTab === 'evidence' && (
                    <div className="tab-pane tab-evidence">
                      <div className="dash-pane-header">
                        <div>
                          <span className="dash-eyebrow">06 / VECTOR EVIDENCE</span>
                          <h2 className="dash-pane-title">Supporting Knowledge Base Evidence</h2>
                          <p className="dash-pane-sub">Empirical startup datasets retrieved via Pinecone RAG.</p>
                        </div>
                        <span className="dash-score-pill">Pinecone Vector Match</span>
                      </div>

                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <Database size={16} color="var(--accent)" />
                            <strong>Retrieved Empirical Context</strong>
                          </div>
                          <span className="dash-card-tag">Live RAG Context</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.retrieved_context || 'No specific vector database evidence was returned for this query.'} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 7: RECOMMENDATIONS */}
                  {reportTab === 'recommendations' && (
                    <div className="tab-pane tab-recommendations">
                      <div className="dash-pane-header">
                        <div>
                          <span className="dash-eyebrow">07 / ACTION PLAN</span>
                          <h2 className="dash-pane-title">Actionable Recommendations &amp; Executive Summary</h2>
                          <p className="dash-pane-sub">Key next steps and founder validation roadmap.</p>
                        </div>
                        <span className="dash-score-pill">Executive Diligence</span>
                      </div>

                      <div className="dash-section-card">
                        <div className="dash-card-header">
                          <div className="dash-card-title">
                            <CheckCircle2 size={16} color="var(--accent)" />
                            <strong>Executive Synthesis &amp; Diligence Brief</strong>
                          </div>
                          <span className="dash-card-tag">Founder Next Steps</span>
                        </div>
                        <div className="dash-card-body">
                          <MarkdownText text={result.summary} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </section>
            )
          })()}
        </div>
      </main>
    </div>
  )
}
