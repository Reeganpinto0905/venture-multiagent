import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
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
        if self._pageNumber > 1:
            self.drawString(54, 750, "VentureIQ — Architectural & Viva Documentation")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "CONFIDENTIAL — VentureIQ AI Validation Suite")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()

def build_architecture_pdf():
    filename = "VentureIQ_Architecture_Guide.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0f172a")
    ACCENT = colors.HexColor("#0d9488")
    TEXT_DARK = colors.HexColor("#1e293b")
    BG_LIGHT = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=PRIMARY, spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15, textColor=ACCENT, spaceAfter=12)
    h1_style = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=PRIMARY, spaceBefore=12, spaceAfter=6, keepWithNext=True)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=TEXT_DARK, spaceAfter=5)
    bullet_style = ParagraphStyle('Bullet', parent=body_style, leftIndent=10, spaceAfter=3)

    story = []
    story.append(Paragraph("VentureIQ — System Architecture Specification", title_style))
    story.append(Paragraph("AI-Powered Multi-Agent Startup Due Diligence & Validation Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=12))

    story.append(Paragraph("1. Problem Statement & Solution", h1_style))
    story.append(Paragraph("Early-stage founders face major hurdles: generic LLMs give uncritical answers, manual due diligence is slow, and informal checks lack repeatable rigor. VentureIQ solves this through interactive discovery, Pinecone vector RAG retrieval, parallel LangGraph multi-agent analysis, and an Investor Readiness Index.", body_style))

    story.append(Paragraph("2. Tech Stack Matrix", h1_style))
    stack_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Role in VentureIQ</b>", body_style)],
        [Paragraph("Frontend", body_style), Paragraph("React 19, Vite 7, Tailwind CSS 4", body_style), Paragraph("Responsive SPA workspace & dashboard", body_style)],
        [Paragraph("3D Core", body_style), Paragraph("Three.js r185, @react-three/fiber", body_style), Paragraph("Animated canvas reacting to state machine", body_style)],
        [Paragraph("Backend API", body_style), Paragraph("FastAPI, Uvicorn, Python 3.10", body_style), Paragraph("Async server with deduplication locks", body_style)],
        [Paragraph("Orchestration", body_style), Paragraph("LangGraph, LangChain", body_style), Paragraph("Stateful multi-agent workflow graph", body_style)],
        [Paragraph("LLM Model", body_style), Paragraph("Google Gemini (2.5 / 3.6 Flash)", body_style), Paragraph("Discovery chat & agent analytical reasoning", body_style)],
        [Paragraph("Vector DB (RAG)", body_style), Paragraph("Pinecone (rag-main), text-embedding-004", body_style), Paragraph("768-dim semantic evidence retrieval", body_style)],
        [Paragraph("Web Research", body_style), Paragraph("Tavily Search API", body_style), Paragraph("Real-time live competitor market search", body_style)]
    ]
    t_stack = Table(stack_data, colWidths=[1.4*inch, 2.3*inch, 3.2*inch])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_stack)

    story.append(Paragraph("3. LangGraph Workflow Execution", h1_style))
    flow_steps = [
        "<b>Phase 1: Discovery & Clarification Loop</b> — Lead Supervisor interviews founder, collecting structured context facts.",
        "<b>Phase 2: RAG Retrieval Node</b> — Generates 768-dim vector embedding and fetches top-k (k=5) documents from Pinecone index 'rag-main'.",
        "<b>Phase 3: Parallel Agent Execution</b> — Market (TAM), Competitor (Moat + Tavily search), Business (Economics), and Risk (Regulatory) agents run.",
        "<b>Phase 4: Synthesis & Scoring</b> — Executive Report agent synthesizes overall verdict and calculates 0-100 Investor Readiness scores."
    ]
    for step in flow_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF generated at {os.path.abspath(filename)}")

def build_viva_pdf():
    filename = "VentureIQ_Viva_QA.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0f172a")
    ACCENT = colors.HexColor("#0d9488")
    TEXT_DARK = colors.HexColor("#1e293b")
    BG_LIGHT = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=PRIMARY, spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15, textColor=ACCENT, spaceAfter=12)
    q_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=PRIMARY, spaceBefore=8, spaceAfter=2, keepWithNext=True)
    a_style = ParagraphStyle('Answer', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=TEXT_DARK, spaceAfter=6)

    story = []
    story.append(Paragraph("VentureIQ — Viva Defense Questions & Answers", title_style))
    story.append(Paragraph("Essential Technical & Architectural Q&A Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=12))

    qas = [
        ("Q1: What is VentureIQ?", "VentureIQ is an AI-powered startup due-diligence engine using LangGraph multi-agent workflows and Pinecone vector RAG to validate startup ideas, analyze markets, map competitors, and evaluate business model viability."),
        ("Q2: Why use multiple AI agents instead of a single prompt in ChatGPT?", "A single prompt suffers from context pollution and superficiality. Specialized agents (Market, Competitor, Business, Risk) focus strictly on one domain with dedicated prompts, evidence context, and specialized tools."),
        ("Q3: What is LangGraph and why is it used?", "LangGraph is a stateful orchestration framework that manages complex multi-agent workflows as directed state graphs, enabling state persistence, conditional task routing, and parallel execution."),
        ("Q4: What is RAG and why is it included?", "RAG (Retrieval-Augmented Generation) retrieves relevant external documents from Pinecone before LLM generation, grounding agent analyses on empirical startup benchmark evidence rather than static training memory."),
        ("Q5: What are embeddings and how do they work in VentureIQ?", "Embeddings are dense 768-dim numerical vectors where semantically similar text is close together. VentureIQ uses Google's models/text-embedding-004 to vectorize queries for similarity search against Pinecone."),
        ("Q6: What does Tavily do in your architecture?", "Tavily is a real-time web search API built for AI agents. It searches live competitor pricing and market updates, complementing Pinecone's internal vector knowledge base."),
        ("Q7: What happens if Pinecone or network fails during the demo?", "VentureIQ implements graceful fallbacks. If PINECONE_API_KEY is missing or Pinecone is offline, retrieve_context() logs a warning and sets retrieved_context='' without crashing the pipeline."),
        ("Q8: How are hallucinations reduced?", "By grounding prompts on vector evidence, instructing agents to separate evidence from inference, using heuristic keyword checks, and failing gracefully when evidence is missing.")
    ]

    for q, a in qas:
        story.append(Paragraph(q, q_style))
        story.append(Paragraph(a, a_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Viva Q&A PDF generated at {os.path.abspath(filename)}")

if __name__ == '__main__':
    build_architecture_pdf()
    build_viva_pdf()
