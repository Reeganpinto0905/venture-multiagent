const UNKNOWN = 'UNKNOWN / Insufficient Evidence'

export const marketClaimPattern = /(?:(?:USD|\$)\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[BMKT]|billion|million|thousand|trillion)?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|[BMKT]\b|billion\b|million\b|thousand\b|trillion\b))/gi

export function normalizedNumber(value) {
  return value
    .replace(/USD|[$,%\s]/gi, '')
    .replace(/\b(billion|B)\b/i, 'B')
    .replace(/\b(million|M)\b/i, 'M')
    .replace(/\b(thousand|K)\b/i, 'K')
    .toLowerCase()
}

export function getGroundedMarketMetrics(evidence = '') {
  const text = String(evidence || '')
  const sentences = text.split(/(?:\r?\n|(?<=[.!?])\s+)/)

  const sizeSentence = sentences.find((s) => /(?:market|tam|sam|som|worth|valuation|industry)\b/i.test(s) && /(?:USD|\$)/i.test(s)) || ''
  const cagrSentence = sentences.find((s) => /(?:cagr|annual growth|growth rate)\b/i.test(s) && /%/.test(s)) || ''
  const userSentence = sentences.find((s) => /(?:user|student|customer|learner|patient|demographic|subscriber|audience)s?\b/i.test(s) && /\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[BMK]\b|billion\b|million\b|thousand\b)/i.test(s)) || ''

  const size = sizeSentence.match(/(?:USD\s*)?\$?\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:B\b|billion\b|M\b|million\b|T\b|trillion\b)/i)?.[0]
  const cagr = cagrSentence.match(/\d+(?:\.\d+)?\s*%/i)?.[0]
  const targetUsers = userSentence.match(/\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[BMK]\b|billion\b|million\b|thousand\b)\s*(?:users?|students?|customers?|learners?|patients?|people)?/i)?.[0]

  return {
    size: size ? size.trim() : UNKNOWN,
    sizeSource: size ? sizeSentence.trim() : '',
    cagr: cagr ? cagr.trim() : UNKNOWN,
    cagrSource: cagr ? cagrSentence.trim() : '',
    targetUsers: targetUsers ? targetUsers.trim() : UNKNOWN,
    targetUsersSource: targetUsers ? userSentence.trim() : '',
  }
}

export function filterUnsupportedMarketNumbers(analysis = '', evidence = '') {
  const sourceNumbers = new Set((String(evidence || '').match(marketClaimPattern) || []).map(normalizedNumber))

  return String(analysis || '').split(/\r?\n/).map((line) => {
    const claimText = line.replace(/^\s*(?:[-*•]\s*)?\d+[.)]\s*/, '')
    const claims = claimText.match(marketClaimPattern) || []
    if (claims.length === 0) return line

    const hasUnsupported = claims.some((claim) => !sourceNumbers.has(normalizedNumber(claim)))
    if (!hasUnsupported) return line

    const prefixMatch = line.match(/^(\s*(?:[-*•]\s*)?(?:\*\*[^*]+\*\*:|[A-Za-z0-9\s&/—–-]+:\s*))/)
    if (prefixMatch && line.includes('**')) {
      return `${prefixMatch[1]} ${UNKNOWN}`
    }
    return UNKNOWN
  }).join('\n')
}

export function cleanReportText(raw) {
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

  // 4. Line-by-line sanitization of internal OKF and retrieval metadata
  const lines = s.split('\n')
  const filtered = []

  for (let line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      filtered.push('')
      continue
    }

    // Hide schema / retriever headers
    if (/^\[(?:OKF Primary Empirical Evidence|Live Web Evidence)[^\]]*\]:?$/i.test(trimmed)) {
      continue
    }

    // Hide Source Provenance lines
    if (/^\s*(?:[-*•]\s*)?Source Provenance\s*:/i.test(trimmed) || /^\s*Source:\s*.*\.pdf\b/i.test(trimmed) || /^\s*Page(?:\s+Number)?\s*[:#]/i.test(trimmed)) {
      continue
    }

    // Hide Connected Concepts and internal entity relationship lines
    if (/^\s*(?:[-*•]\s*)?Connected Concepts\s*:/i.test(trimmed) || /^\s*(?:[-*•]\s*)?[a-z_]+(?:_[a-z]+)*\s*->\s*[\w-]+/i.test(trimmed)) {
      continue
    }

    // Transform OKF evidence header to preserve company name and category without raw OKF IDs or verification flags:
    // e.g. "• [OKF Evidence #1 | Airbnb (Marketplace) | [MACHINE-CONFIRMED | CURRENT]]" -> "• **Airbnb (Marketplace)**"
    let cleanedLine = line.replace(/^\s*[-*•]?\s*\[\s*OKF Evidence #\d+\s*\|\s*(.*?)(?:\s*\|\s*\[[^\]]+\]|\s*\|\s*[^\]]+)?\s*\]/gi, (_match, title) => {
      const cleanTitle = title.replace(/\[\s*(?:MACHINE-CONFIRMED|HUMAN-REVIEWED|UNVERIFIED)[^\]]*\]/gi, '').trim()
      return `• **${cleanTitle}**`
    })

    // Hide inline internal tags while preserving user-facing content
    cleanedLine = cleanedLine
      .replace(/\[\s*(?:MACHINE-CONFIRMED|HUMAN-REVIEWED|UNVERIFIED)\s*\|\s*(?:CURRENT|HISTORICAL|DRAFT|ARCHIVED)\s*\]/gi, '')
      .replace(/\[OKF Evidence #\d+\s*\|?/gi, '')
      .replace(/\b[\w.-]+\.pdf\b/gi, '')
      .replace(/\b(?:p\.|page)\s*\d+(?:\s*[-–]\s*\d+)?\b/gi, '')
      .replace(/\b[a-z_]+_model\s*->\s*[\w-]+/gi, '')
      .replace(/\bbackend[_ -]?(?:id|path)\b/gi, '')

    const testEmpty = cleanedLine.trim()
    if (!testEmpty || testEmpty === '•' || testEmpty === '• ****' || testEmpty === '• **' || testEmpty === '-' || testEmpty === '*') {
      continue
    }

    filtered.push(cleanedLine)
  }

  s = filtered.join('\n')

  // 5. Strip any trailing signature or score artifacts
  s = s.replace(/,?\s*["']?score["']?\s*:\s*\d+\s*\}?$/i, '').trim()
  s = s.replace(/\}?$/, '').trim()

  return s
}

