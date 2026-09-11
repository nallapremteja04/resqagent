import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "ResQAgent: Autonomous Agentic AI Emergency Response System")
            self.drawRightString(612 - 54, 750, "Jury Presentation & Defense Dossier")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "CONFIDENTIAL — EVALUATION DOSSIER (100 MARKS TOTAL)")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 612 - 54, 46)

        self.restoreState()

def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=44,
        rightMargin=44,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#dc2626'), # Emergency Red
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e3a8a'), # Deep Navy
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155'),
        leftIndent=12,
        spaceAfter=3
    )
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=4,
        spaceAfter=6
    )
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("ResQAgent — Project Presentation & Jury Defense", title_style))
    story.append(Paragraph("AUTONOMOUS AGENTIC AI EMERGENCY RESPONSE & COORDINATION SYSTEM", subtitle_style))
    
    meta_data = [
        [
            Paragraph("<b>Target Score:</b> 100 / 100 Marks", body_style),
            Paragraph("<b>Architecture:</b> 6-Agent Autonomous Cognitive Loop", body_style),
            Paragraph("<b>Status:</b> Live & Operational on Port 8000", body_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[170, 200, 154])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Executive Summary Card
    exec_summary = (
        "<b>Executive Pitch for Jury:</b> ResQAgent is an autonomous emergency response coordination platform powered by "
        "an end-to-end Agentic AI cognitive cycle (PERCEIVE ➔ REASON ➔ DECIDE ➔ ACT ➔ OBSERVE ➔ ADAPT ➔ REPORT). "
        "It eliminates 911 dispatch latency by clinically triaging distress messages, optimizing field responder dispatch "
        "via multi-factor proximity/specialization scoring, monitoring 30-second SLA acknowledgment timeouts, and autonomously "
        "re-routing missions with zero human bottleneck. Backed by 17 automated tests, production RBAC, and Gemini 1.5 Flash."
    )
    t_exec = Table([[Paragraph(exec_summary, callout_style)]], colWidths=[524])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('LINELEFT', (0,0), (-1,-1), 3.5, colors.HexColor('#2563eb')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#bfdbfe')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 12))

    # Scorecard Table
    story.append(Paragraph("1. AGENTIC AI EVALUATION SCORECARD (100 MARKS)", h1_style))
    scorecard_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Marks</b>", body_style), Paragraph("<b>Focus Area</b>", body_style), Paragraph("<b>ResQAgent Compliance & Implementation</b>", body_style)],
        [Paragraph("1. Problem Understanding & Identification", body_style), Paragraph("<b>10</b>", body_style), Paragraph("Clearly identify real problem, users & needs", body_style), Paragraph("Golden Hour dispatch latency; 4 distinct personas (Citizen, Responder, Dispatch, Admin)", body_style)],
        [Paragraph("2. Innovation, Creativity & Use-Case", body_style), Paragraph("<b>10</b>", body_style), Paragraph("Original & meaningful solution", body_style), Paragraph("Self-healing dispatch loop; autonomous SLA timeout recovery; explainable cognitive actions", body_style)],
        [Paragraph("3. Agent Architecture, Workflow & Reasoning", body_style), Paragraph("<b>20</b>", body_style), Paragraph("Task breakdown, reasoning & workflows", body_style), Paragraph("6 specialized agents; state machine: PERCEIVE ➔ REASON ➔ DECIDE ➔ ACT ➔ OBSERVE ➔ ADAPT", body_style)],
        [Paragraph("4. AI Implementation & Technical Stack", body_style), Paragraph("<b>20</b>", body_style), Paragraph("LLMs, prompting, tool calling, APIs", body_style), Paragraph("Gemini 1.5 Flash REST API; structured JSON schema; deterministic cognitive fallback engine", body_style)],
        [Paragraph("5. Functionality, Performance & Reliability", body_style), Paragraph("<b>15</b>", body_style), Paragraph("Reliable real-world execution", body_style), Paragraph("17-test security suite; bcrypt 12-round hashing; JWT tokens; database-level privacy isolation", body_style)],
        [Paragraph("6. GitHub, Code Quality & Deployment", body_style), Paragraph("<b>5</b>", body_style), Paragraph("Clean code, README & deployment", body_style), Paragraph("Decoupled architecture; comprehensive README; 1-click startup on http://127.0.0.1:8000", body_style)],
        [Paragraph("7. Profile Building (LinkedIn & Instagram)", body_style), Paragraph("<b>5</b>", body_style), Paragraph("Professional public showcase", body_style), Paragraph("Viral technical showcase post, architectural diagrams, and carousel copy provided", body_style)],
        [Paragraph("8. Presentation & Live Demonstration", body_style), Paragraph("<b>15</b>", body_style), Paragraph("Explain & demonstrate working app", body_style), Paragraph("4-minute live demo script showing SOS intake, automated dispatch, SLA breach & report", body_style)],
        [Paragraph("<b>TOTAL</b>", body_style), Paragraph("<b>100</b>", body_style), Paragraph("<b>Comprehensive Project Coverage</b>", body_style), Paragraph("<b>Fully Operational & Validated Across All Criteria</b>", body_style)]
    ]
    t_score = Table(scorecard_data, colWidths=[120, 42, 142, 220])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_score)
    story.append(Spacer(1, 14))

    # Metric 1
    story.append(Paragraph("METRIC 1: PROBLEM UNDERSTANDING & IDENTIFICATION (10 MARKS)", h1_style))
    story.append(Paragraph("<b>The Real-World Emergency Crisis:</b> In trauma medicine, survival drops exponentially after the 'Golden Hour' (the first 60 minutes post-incident). Traditional 911 CAD systems suffer from three acute bottlenecks:", body_style))
    story.append(Paragraph("• <b>Dispatcher Overload & Fatigue:</b> In mass-casualty events, operators face severe cognitive overload, leading to delayed categorization.", bullet_style))
    story.append(Paragraph("• <b>Unmonitored SLA Dropouts:</b> If a responder is delayed, has radio failure, or declines, traditional systems stay idle until someone notices 5–10 minutes later.", bullet_style))
    story.append(Paragraph("• <b>Fragmented Communications:</b> Callers are left in the dark without arrival updates, and trauma hospitals receive zero pre-arrival casualty heads-up.", bullet_style))
    story.append(Paragraph("<b>4 Distinct Real-World Stakeholder Personas Addressed:</b>", h2_style))
    story.append(Paragraph("1. <b>Citizen / Caller:</b> One-touch distress SOS submission, live arrival tracking, privacy protection, and reassuring automated SMS updates.", bullet_style))
    story.append(Paragraph("2. <b>Field Responder (EMT/Fire/Police):</b> Mobile alerts with exact clinical priority (P1-P4), patient conditions, and 1-click status transitions.", bullet_style))
    story.append(Paragraph("3. <b>Central Dispatcher:</b> Full operational oversight across all live incidents, responder fleet map, and transparent agent reasoning traces.", bullet_style))
    story.append(Paragraph("4. <b>System Administrator:</b> Role-based access provisioning, security audits, simulation triggers, and user lifecycle governance.", bullet_style))
    story.append(Spacer(1, 10))

    # Metric 2
    story.append(Paragraph("METRIC 2: INNOVATION, CREATIVITY & USE-CASE RELEVANCE (10 MARKS)", h1_style))
    story.append(Paragraph("<b>Why ResQAgent is an Original, Breakthrough Solution:</b>", body_style))
    story.append(Paragraph("• <b>Not a Chatbot — An Autonomous Actuator:</b> Most hackathon submissions wrap LLMs into text chat interfaces. ResQAgent is an autonomous decision and actuation engine that changes database states, reserves units, tracks timers, and sends multi-party alerts.", bullet_style))
    story.append(Paragraph("• <b>Self-Healing Dynamic Escalation:</b> If an assigned unit fails to respond within 30 seconds, the agent autonomously blacklists that responder, re-engages the selection algorithm, and re-routes the next best unit with zero human intervention.", bullet_style))
    story.append(Paragraph("• <b>Full Cognitive Transparency:</b> Every decision made by any agent is persisted in an auditable <i>AgentAction</i> log detailing agent name, action type, raw input, clinical/mathematical reasoning, and output.", bullet_style))
    story.append(Spacer(1, 10))

    # Metric 3
    story.append(Paragraph("METRIC 3: AGENT ARCHITECTURE, WORKFLOW & REASONING DESIGN (20 MARKS)", h1_style))
    story.append(Paragraph("ResQAgent separates concerns into <b>6 specialized autonomous agents</b> coordinating within a strict state machine:", body_style))
    
    agent_arch_data = [
        [Paragraph("<b>Agent Name</b>", body_style), Paragraph("<b>Cognitive Phase</b>", body_style), Paragraph("<b>Core Responsibility & Operational Logic</b>", body_style)],
        [Paragraph("<b>1. EmergencyAnalysisAgent</b>", body_style), Paragraph("PERCEIVE & REASON", body_style), Paragraph("Parses unstructured text; classifies type (Accident, Fire, Medical, Crime, Rescue), severity (Critical, High, Med, Low), and priority (P1–P4).", body_style)],
        [Paragraph("<b>2. ResponderSelectionAgent</b>", body_style), Paragraph("DECIDE", body_style), Paragraph("Evaluates available fleet using mathematical utility score: <code>Score = (10 / Dist) * Spec_Bonus(1.5x)</code>. Matches units to emergency type.", body_style)],
        [Paragraph("<b>3. CommunicationAgent</b>", body_style), Paragraph("ACT", body_style), Paragraph("Omnichannel multi-stakeholder alert dispatch: App push to Responder, SMS reassurance to Citizen, Radio log to Dispatch, Secure Alert to Hospital.", body_style)],
        [Paragraph("<b>4. MonitoringAgent</b>", body_style), Paragraph("OBSERVE", body_style), Paragraph("Enforces strict 30-second acknowledgment SLA window. Tracks mission progression and flags timeouts.", body_style)],
        [Paragraph("<b>5. EscalationAgent</b>", body_style), Paragraph("ADAPT", body_style), Paragraph("Self-healing loop: Blacklists dropped unit, searches candidate pool excluding failed units, assigns new responder. Safeguard: Max 3 attempts.", body_style)],
        [Paragraph("<b>6. AIIncidentReportAgent</b>", body_style), Paragraph("REPORT", body_style), Paragraph("Synthesizes post-incident debrief dossier from timeline logs, response times, and escalations. Scores agentic performance.", body_style)]
    ]
    t_agents = Table(agent_arch_data, colWidths=[130, 94, 300])
    t_agents.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_agents)
    story.append(Spacer(1, 10))

    # Metric 4
    story.append(Paragraph("METRIC 4: AI IMPLEMENTATION & TECHNICAL STACK (20 MARKS)", h1_style))
    story.append(Paragraph("• <b>LLM Integration:</b> Powered by Google Gemini 1.5 Flash via REST API (<code>backend/agents/llm_service.py</code>) using strict system prompts and JSON mime type enforcement.", bullet_style))
    story.append(Paragraph("• <b>Mission-Critical Dual-Engine Architecture:</b> If internet connectivity is interrupted or LLM API rate limits are hit, the system triggers an automatic <b>Deterministic Cognitive Fallback Engine</b> (<code>backend/agents/analysis_agent.py</code> lines 47-98). Distress calls are never lost or hung.", bullet_style))
    story.append(Paragraph("• <b>RESTful Tool Calling & Micro-APIs:</b> 8 modular FastAPI controllers handling Authentication, Administration, Incidents, Responders, Assignments, Simulation, Users, and Reports.", bullet_style))
    story.append(Spacer(1, 10))

    # Metric 5
    story.append(Paragraph("METRIC 5: FUNCTIONALITY, PERFORMANCE & RELIABILITY (15 MARKS)", h1_style))
    story.append(Paragraph("• <b>Cryptographic RBAC Security:</b> Passwords hashed with <code>bcrypt</code> (12 salt rounds). Plaintext passwords never stored. Authenticated via signed HS256 JWT tokens.", bullet_style))
    story.append(Paragraph("• <b>Data Isolation:</b> Citizens cannot view incidents from other citizens. Responders can only access missions assigned to them. Administrative endpoints reject unauthorized roles with HTTP 403.", bullet_style))
    story.append(Paragraph("• <b>3 Automated Verification Suites:</b>", h2_style))
    story.append(Paragraph("1. <code>backend/test_auth_suite.py</code>: 17 comprehensive security and RBAC test scenarios.", code_style))
    story.append(Paragraph("2. <code>backend/test_api_suite.py</code>: End-to-end REST endpoint testing across all routers.", code_style))
    story.append(Paragraph("3. <code>backend/test_agent_flow.py</code>: Full autonomous cognitive loop & SLA escalation verification.", code_style))
    story.append(Spacer(1, 10))

    # Metric 6
    story.append(Paragraph("METRIC 6: GITHUB, CODE QUALITY & DEPLOYMENT (5 MARKS)", h1_style))
    story.append(Paragraph("• Clean modular repository separating backend agents, models, API routes, and pure vanilla reactive frontend.", bullet_style))
    story.append(Paragraph("• Fully documented setup in <code>README.md</code> with clear role descriptions, API specifications, and test commands.", bullet_style))
    story.append(Paragraph("• Live server runs with single command: <code>.\\venv\\Scripts\\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000</code>", bullet_style))
    story.append(Spacer(1, 10))

    # Metric 7
    story.append(Paragraph("METRIC 7: LINKEDIN & INSTAGRAM PROFILE BUILDING (5 MARKS)", h1_style))
    story.append(Paragraph("<b>LinkedIn Post Template (Ready to Publish):</b>", h2_style))
    li_text = (
        "🚨 Can Agentic AI save lives during the 'Golden Hour' of emergency response?<br/>"
        "Thrilled to introduce ResQAgent — an autonomous Agentic AI Emergency Coordination platform. "
        "Unlike basic chatbots, ResQAgent executes a 6-stage cognitive loop (Perceive ➔ Reason ➔ Decide ➔ Act ➔ Observe ➔ Adapt ➔ Report). "
        "It eliminates 911 dispatch latency, scores responders by proximity & medical specialization, and self-heals by re-routing "
        "assignments when SLA timeouts occur. Built with Python, FastAPI, Gemini 1.5 Flash & 17 automated security tests! #AgenticAI #Python #FastAPI #AI"
    )
    t_li = Table([[Paragraph(li_text, callout_style)]], colWidths=[524])
    t_li.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_li)
    story.append(Spacer(1, 10))

    # Metric 8
    story.append(Paragraph("METRIC 8: PRESENTATION & LIVE DEMONSTRATION PLAYBOOK (15 MARKS)", h1_style))
    story.append(Paragraph("<b>Step-by-Step 4-Minute Live Demo Script:</b>", h2_style))
    story.append(Paragraph("1. <b>Minute 0:00 - 1:00 (Citizen SOS Intake):</b> Open <code>http://localhost:8000</code>, enter accident distress call ('Severe crash, car smoking, driver trapped & bleeding'). Show status transitioning from ANALYZING to ANALYZED with P1-Critical clinical priority.", bullet_style))
    story.append(Paragraph("2. <b>Minute 1:00 - 2:00 (Automated Selection & Multi-Alerts):</b> Show SelectionAgent assigning unit Suresh (0.8km away). Show CommunicationAgent sending push to responder, SMS to citizen, and trauma advisory to hospital.", bullet_style))
    story.append(Paragraph("3. <b>Minute 2:00 - 3:00 (The WOW Factor: SLA Escalation):</b> Click 'Simulate SLA Timeout'. Watch MonitoringAgent detect timeout, EscalationAgent blacklist Suresh, and reassign unit Ravi (1.5km) with citizen reassurance.", bullet_style))
    story.append(Paragraph("4. <b>Minute 3:00 - 4:00 (Resolution & AI Debrief):</b> Mark mission Completed. Click 'Generate AI Incident Report'. Show executive debrief dossier and 95/100 performance score.", bullet_style))
    story.append(Spacer(1, 10))

    # Q&A Defense
    story.append(Paragraph("JURY Q&A DEFENSE CHEAT SHEET", h1_style))
    qa_data = [
        [Paragraph("<b>Jury Question</b>", body_style), Paragraph("<b>Winning High-Impact Answer</b>", body_style)],
        [Paragraph("Why multi-agent instead of one prompt?", body_style), Paragraph("Emergency dispatch requires deterministic mathematical scoring (distance, availability) and strict SLA timing, which monolithic LLM prompts cannot reliably guarantee. Our multi-agent separation ensures speed, precision, and zero hallucinations.", body_style)],
        [Paragraph("What if Gemini API goes down?", body_style), Paragraph("ResQAgent features a built-in Deterministic Cognitive Fallback Engine. If the LLM API fails or times out, rule-based clinical keyword extraction takes over in milliseconds without dropping the call.", body_style)],
        [Paragraph("How do you prevent infinite loops?", body_style), Paragraph("EscalationAgent has a hardcoded safeguard: <code>MAX_ESCALATION_ATTEMPTS = 3</code>. If 3 automated reassignment attempts fail, the incident immediately escalates to human central dispatch (<code>ESCALATED_TO_DISPATCH</code>).", body_style)],
        [Paragraph("How is citizen privacy protected?", body_style), Paragraph("Full RBAC with bcrypt 12-round password hashing and JWT tokens. Database queries are scoped so citizens can only view their own records. Non-admin access to admin routes returns HTTP 403.", body_style)]
    ]
    t_qa = Table(qa_data, colWidths=[160, 364])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_qa)

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF Generated at: {filename}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "ResQAgent_Jury_Presentation_Dossier.pdf"
    build_pdf(target)
