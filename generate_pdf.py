import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "VentureIQ — Project Summary & Architectural Specification")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)
            
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "CONFIDENTIAL — VentureIQ AI Validation Suite")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        
        self.restoreState()

def build_pdf(filename="VentureIQ_Project_Summary.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0f172a")    # Dark slate
    ACCENT = colors.HexColor("#0d9488")     # Teal accent
    TEXT_DARK = colors.HexColor("#1e293b")  # Body text
    MUTED = colors.HexColor("#475569")      # Subtitles / Secondary
    BG_LIGHT = colors.HexColor("#f8fafc")   # Card background
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=BG_LIGHT,
        borderColor=BORDER_COLOR,
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("VentureIQ — Project Summary & Specification", title_style))
    story.append(Paragraph("AI Multi-Agent Startup Strategy & Validation Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=15))

    # Executive Overview
    story.append(Paragraph("1. Executive Overview", h1_style))
    story.append(Paragraph(
        "<b>VentureIQ</b> is an intelligent, multi-agent startup validation platform designed to analyze, stress-test, and refine startup concepts before founders commit capital or write code. Combining conversational AI discovery with a distributed multi-agent graph architecture (built on LangGraph and Gemini), VentureIQ evaluates market demand, competitive moat, business model viability, and execution risks in seconds.",
        body_style
    ))

    # App Features
    story.append(Spacer(1, 6))
    story.append(Paragraph("2. Application Feature Matrix", h1_style))

    features_data = [
        [
            Paragraph("<b>Feature Area</b>", body_style),
            Paragraph("<b>Capability Specification & Implementation Details</b>", body_style)
        ],
        [
            Paragraph("<b>Conversational Supervisor</b>", body_style),
            Paragraph("Engages in dynamic follow-up questioning to extract target customer details, pricing models, and core value propositions before triggering deep analysis.", body_style)
        ],
        [
            Paragraph("<b>3D Intelligence Core</b>", body_style),
            Paragraph("Interactive Three.js icosahedron core with glowing satellites and state-driven animations (<i>idle, thinking, question, analyzing, complete</i>).", body_style)
        ],
        [
            Paragraph("<b>Multi-Agent Pipeline</b>", body_style),
            Paragraph("Executes 4 specialized analysis agents: <b>Market</b> (TAM/growth), <b>Competitor</b> (moat/landscape), <b>Business</b> (margins/CAC), and <b>Risk</b> (execution/regulatory).", body_style)
        ],
        [
            Paragraph("<b>Investor Readiness Index</b>", body_style),
            Paragraph("Generates quantitative scorecards (0-100) across 4 pillars, classifying ventures into <i>Strong Venture Prospect</i>, <i>Viable Opportunity</i>, or <i>High Risk Profile</i>.", body_style)
        ],
        [
            Paragraph("<b>Session & Local History</b>", body_style),
            Paragraph("Persists analyses locally with relative timestamp grouping (<i>Today, Yesterday, Last 7 Days, Older</i>). Allows instant switching between past briefs.", body_style)
        ],
        [
            Paragraph("<b>Multi-Format Brief Export</b>", body_style),
            Paragraph("Supports <i>Copy Executive Brief</i> to clipboard, Markdown report export (.md download), and print-ready styled PDF view.", body_style)
        ]
    ]

    t_features = Table(features_data, colWidths=[2.0 * inch, 4.9 * inch])
    t_features.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_features)

    # Methodology & Execution Flow
    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Methodology & Execution Flow", h1_style))
    story.append(Paragraph(
        "VentureIQ employs a four-phase state machine workflow combining conversational refinement with deterministic multi-agent graph execution:",
        body_style
    ))

    flow_steps = [
        "<b>Phase 1: Discovery & Prompting</b> — Founder submits initial idea via clean landing input or suggestion chips.",
        "<b>Phase 2: Supervisor Clarification Loop</b> — Lead Supervisor agent inspects context completeness. If crucial parameters are missing, it asks 1-3 targeted questions and offers interactive choice chips.",
        "<b>Phase 3: Multi-Agent Parallel Graph Execution</b> — Once readiness is confirmed, LangGraph orchestrates concurrent execution of Market, Competitor, Business, and Risk analysis agents.",
        "<b>Phase 4: Synthesis & Score Indexing</b> — Executive report generator consolidates individual agent outputs, calculates weighted Investor Readiness scores, and returns structured findings to the UI."
    ]
    for step in flow_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    # Architecture & Technology Stack
    story.append(Spacer(1, 8))
    story.append(Paragraph("4. Technical Architecture", h1_style))

    arch_data = [
        [
            Paragraph("<b>Layer</b>", body_style),
            Paragraph("<b>Technologies & Components</b>", body_style)
        ],
        [
            Paragraph("<b>Frontend UI/UX</b>", body_style),
            Paragraph("React 19, Vite 7, Tailwind CSS 4, Lucide Icons, Framer Motion.<br/><b>3D Engine:</b> Three.js r185, @react-three/fiber, @react-three/drei.", body_style)
        ],
        [
            Paragraph("<b>Backend API</b>", body_style),
            Paragraph("FastAPI (Python 3.10), Uvicorn server, Pydantic data validation.<br/><b>Concurrency:</b> In-flight deduplication locks (`IN_FLIGHT_LOCK`) to prevent race conditions.", body_style)
        ],
        [
            Paragraph("<b>AI Orchestration</b>", body_style),
            Paragraph("LangChain (`langchain-google-genai`), LangGraph state workflows, Google Gemini 2.5/3.6 models with structured JSON parsing.", body_style)
        ],
        [
            Paragraph("<b>Persistence & State</b>", body_style),
            Paragraph("Client-side localStorage history store (`ventureiq_conversations`), in-memory session cache (`SESSIONS` dict) on backend.", body_style)
        ]
    ]

    t_arch = Table(arch_data, colWidths=[2.0 * inch, 4.9 * inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_arch)

    # Architecture Diagram (Textual Representation)
    story.append(Spacer(1, 6))
    story.append(Paragraph("System Communication & Workflow Architecture", h2_style))
    diagram_text = (
        "[ Browser / React 19 Frontend ]\n"
        "        │ (HTTP REST API Requests)\n"
        "        ▼\n"
        "[ FastAPI Backend Server: http://127.0.0.1:8000 ]\n"
        "   ├── POST /chat    ---> Supervisor Agent (Gemini) ---> Context Extraction\n"
        "   └── POST /analyze ---> LangGraph Multi-Agent Execution Engine\n"
        "                              ├── Market Agent (TAM & Growth)\n"
        "                              ├── Competitor Agent (Moat & Positioning)\n"
        "                              ├── Business Agent (Margins & CAC)\n"
        "                              └── Risk Agent (Regulatory & Execution)\n"
        "                                      │\n"
        "                                      ▼\n"
        "                        [ Executive Report & Score Synthesis ]\n"
        "                                      │\n"
        "                                      ▼\n"
        "                        [ Workspace Results Dashboard & Brief Export ]"
    )
    story.append(Paragraph(diagram_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at {os.path.abspath(filename)}")

if __name__ == '__main__':
    build_pdf()
