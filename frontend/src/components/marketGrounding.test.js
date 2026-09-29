import test from 'node:test'
import assert from 'node:assert/strict'
import {
  filterUnsupportedMarketNumbers,
  getGroundedMarketMetrics,
  cleanReportText,
} from './marketGrounding.js'

test('1. Market Data Grounding: unsupported market numbers cannot reach Market Intelligence cards or analysis', () => {
  const evidence = 'India food delivery market size: USD 19.99B by 2034; CAGR: 10.05%.'
  const metrics = getGroundedMarketMetrics(evidence)
  const visibleAnalysis = filterUnsupportedMarketNumbers(
    'Market size: $12.4B.\nCAGR: 18%.\nTarget users: 23M.',
    evidence,
  )

  // Grounded numbers from retrieved source are extracted
  assert.equal(metrics.size, 'USD 19.99B')
  assert.equal(metrics.cagr, '10.05%')

  // Ungrounded / invented claims are blocked
  assert.equal(visibleAnalysis, [
    'UNKNOWN / Insufficient Evidence',
    'UNKNOWN / Insufficient Evidence',
    'UNKNOWN / Insufficient Evidence',
  ].join('\n'))
})

test('1. Market Data Grounding: ungrounded evidence defaults to UNKNOWN / Insufficient Evidence', () => {
  const emptyMetrics = getGroundedMarketMetrics('')
  assert.equal(emptyMetrics.size, 'UNKNOWN / Insufficient Evidence')
  assert.equal(emptyMetrics.cagr, 'UNKNOWN / Insufficient Evidence')
  assert.equal(emptyMetrics.targetUsers, 'UNKNOWN / Insufficient Evidence')
})

test('2. Internal Metadata Hiding: hides raw OKF IDs, PDFs, page numbers, flags, and paths while preserving content', () => {
  const rawContext = `[OKF Primary Empirical Evidence | OKF v0.2]:

• [OKF Evidence #1 | Airbnb (Marketplace) | [MACHINE-CONFIRMED | CURRENT]]
  Source Provenance: startup_playbook.pdf (p.14 | Section 3)
  • Connected Concepts: implements_model -> two-sided-marketplace, competes_with -> vrbo
  Airbnb solved the chicken-and-egg problem by targeting high-demand events like the DNC in Denver, photographing listings manually, and cross-posting to Craigslist.

• [OKF Evidence #2 | Zomato (Food Delivery) | [MACHINE-CONFIRMED | CURRENT]]
  Source Provenance: india_startup_failures.pdf (p.88)
  • Connected Concepts: implements_model -> delivery_fleet
  Outcome: Market Leader. Zomato scaled restaurant listings before launching food delivery.`

  const cleaned = cleanReportText(rawContext)

  // Internal metadata hidden
  assert.equal(cleaned.includes('OKF Evidence #'), false, 'Should hide raw OKF Evidence IDs')
  assert.equal(cleaned.includes('.pdf'), false, 'Should hide PDF filenames')
  assert.equal(cleaned.includes('(p.14'), false, 'Should hide page provenance')
  assert.equal(cleaned.includes('Source Provenance:'), false, 'Should hide Source Provenance text')
  assert.equal(cleaned.includes('MACHINE-CONFIRMED'), false, 'Should hide internal verification flags')
  assert.equal(cleaned.includes('Connected Concepts:'), false, 'Should hide Connected Concepts text')
  assert.equal(cleaned.includes('implements_model ->'), false, 'Should hide internal entity graph relations')
  assert.equal(cleaned.includes('OKF Primary Empirical Evidence'), false, 'Should hide raw schema headers')

  // User-facing content preserved
  assert.equal(cleaned.includes('Airbnb (Marketplace)'), true, 'Should preserve company name and category')
  assert.equal(cleaned.includes('Zomato (Food Delivery)'), true, 'Should preserve company name and category')
  assert.equal(cleaned.includes('Outcome: Market Leader'), true, 'Should preserve business outcome')
  assert.equal(cleaned.includes('Airbnb solved the chicken-and-egg problem'), true, 'Should preserve empirical evidence content')
  assert.equal(cleaned.includes('Zomato scaled restaurant listings'), true, 'Should preserve empirical evidence content')
})

test('3. Markdown Display: headings with asterisks render without literal asterisks', () => {
  const headings = [
    '### 5. **Critical Risk Audit & Lethal Failure Modes**',
    '### 6. **Evidence Gaps & Unknowns**',
    '### 7. **48-Hour Validation Action Plan**',
    '5. **Critical Risks & Failure Modes**',
  ]

  for (const h of headings) {
    let cleanHeading = h.replace(/^#{1,4}\s+/, '').replace(/\*\*/g, '').trim()
    assert.equal(cleanHeading.includes('**'), false, `Heading should not contain **: ${cleanHeading}`)
  }
})
