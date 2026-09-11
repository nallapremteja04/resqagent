import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 widescreen format
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette (Emergency Tech Theme)
    BG_COLOR = RGBColor(11, 19, 43)        # Deep Dark Navy (#0B132B)
    CARD_BG = RGBColor(22, 33, 62)         # Slate Navy (#16213E)
    CARD_BORDER = RGBColor(30, 41, 59)     # Subtle Border (#1E293B)
    CARD_HIGHLIGHT = RGBColor(15, 23, 42)  # Darker Card (#0F172A)
    
    TEXT_MAIN = RGBColor(248, 250, 252)    # Crisp White (#F8FAFC)
    TEXT_MUTED = RGBColor(148, 163, 184)   # Slate Muted (#94A3B8)
    TEXT_DARK = RGBColor(203, 213, 225)    # Light Slate (#CBD5E1)
    
    ACCENT_RED = RGBColor(239, 68, 68)     # Emergency Red (#EF4444)
    ACCENT_ORANGE = RGBColor(249, 115, 22) # Urgent Orange (#F97316)
    ACCENT_BLUE = RGBColor(56, 189, 248)   # Tech Cyan/Blue (#38BDF8)
    ACCENT_GREEN = RGBColor(16, 185, 129)  # Success Green (#10B981)

    blank_layout = prs.slide_layouts[6] # Blank slide layout

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text, slide_num):
        set_slide_background(slide)

        # Top Category Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_right = tf_tag.margin_top = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = category_text.upper()
        p_tag.font.name = "Segoe UI"
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = ACCENT_BLUE

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(10.5), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = "Segoe UI"
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_MAIN

        # Bottom Footer Line & Number
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(30, 41, 59)
        line.line.fill.background()

        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(6), Inches(0.3))
        tf_foot = footer_box.text_frame
        tf_foot.margin_left = tf_foot.margin_top = 0
        p_foot = tf_foot.paragraphs[0]
        p_foot.text = "ResQAgent — Emergency Response & Coordination Platform"
        p_foot.font.name = "Segoe UI"
        p_foot.font.size = Pt(9)
        p_foot.font.color.rgb = TEXT_MUTED

        num_box = slide.shapes.add_textbox(Inches(11.0), Inches(7.12), Inches(1.533), Inches(0.3))
        tf_num = num_box.text_frame
        tf_num.margin_right = tf_num.margin_top = 0
        p_num = tf_num.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.text = f"{slide_num:02d} / 23"
        p_num.font.name = "Segoe UI"
        p_num.font.size = Pt(9)
        p_num.font.color.rgb = TEXT_MUTED

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(1)
        return card

    # =========================================================================
    # SLIDE 1: COVER
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Accent top banner
    top_acc = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.04))
    top_acc.fill.solid()
    top_acc.fill.fore_color.rgb = ACCENT_RED
    top_acc.line.fill.background()

    # Category badge
    c_badge = add_card(s1, 0.8, 1.2, 3.8, 0.4, CARD_HIGHLIGHT, ACCENT_BLUE)
    tf_cb = c_badge.text_frame
    tf_cb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_cb = tf_cb.paragraphs[0]
    p_cb.alignment = PP_ALIGN.CENTER
    p_cb.text = "HACKATHON PROJECT PRESENTATION"
    p_cb.font.name = "Segoe UI"
    p_cb.font.size = Pt(10)
    p_cb.font.bold = True
    p_cb.font.color.rgb = ACCENT_BLUE

    # Title
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.5), Inches(1.2))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = "ResQAgent"
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(44)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_MAIN

    # Subtitle
    st_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.5), Inches(0.6))
    tf_st = st_box.text_frame
    p_st = tf_st.paragraphs[0]
    p_st.text = "Intelligent Emergency Response & Coordination Platform"
    p_st.font.name = "Segoe UI"
    p_st.font.size = Pt(20)
    p_st.font.color.rgb = ACCENT_ORANGE

    # Visual Flow Box (Citizen -> Emergency -> ResQAgent -> Dispatcher -> Responder)
    v_box = add_card(s1, 0.8, 3.7, 11.733, 1.4, CARD_BG, CARD_BORDER)
    flow_steps = ["Citizen SOS", "Emergency Intake", "ResQAgent Triage", "Smart Dispatch", "Field Responder"]
    for i, step in enumerate(flow_steps):
        step_card = add_card(s1, 1.2 + i * 2.3, 4.0, 1.9, 0.8, CARD_HIGHLIGHT, ACCENT_BLUE if i == 2 else CARD_BORDER)
        tf = step_card.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = step
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE if i == 2 else TEXT_MAIN
        
        # Arrow between steps
        if i < len(flow_steps) - 1:
            arr = s1.shapes.add_textbox(Inches(3.15 + i * 2.3), Inches(4.2), Inches(0.35), Inches(0.4))
            p_arr = arr.text_frame.paragraphs[0]
            p_arr.text = "➔"
            p_arr.font.size = Pt(14)
            p_arr.font.color.rgb = ACCENT_RED

    # Metadata Grid
    meta_card = add_card(s1, 0.8, 5.4, 11.733, 1.2, CARD_HIGHLIGHT, CARD_BORDER)
    m_box = s1.shapes.add_textbox(Inches(1.1), Inches(5.55), Inches(11.1), Inches(0.9))
    tf_m = m_box.text_frame
    tf_m.word_wrap = True
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = "Team: ResQAgent Development Team    |    Track: Agentic AI & Autonomous Systems"
    p_m1.font.name = "Segoe UI"
    p_m1.font.size = Pt(12)
    p_m1.font.bold = True
    p_m1.font.color.rgb = TEXT_MAIN

    p_m2 = tf_m.add_paragraph()
    p_m2.text = "GitHub: github.com/nallapremteja04/resqagent    |    Live Deployment: http://localhost:8000"
    p_m2.font.name = "Segoe UI"
    p_m2.font.size = Pt(11)
    p_m2.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: THE PROBLEM
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "During an Emergency, Every Minute Matters", "The Reality of Emergency Response", 2)

    # Workflow BEFORE
    w_top = add_card(s2, 0.8, 1.5, 11.733, 1.1, CARD_HIGHLIGHT, RGBColor(239, 68, 68))
    w_box = s2.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.3), Inches(0.9))
    tf_w = w_box.text_frame
    p_w1 = tf_w.paragraphs[0]
    p_w1.text = "TRADITIONAL 911 DISPATCH WORKFLOW (MANUAL & SEQUENTIAL):"
    p_w1.font.name = "Segoe UI"
    p_w1.font.size = Pt(10)
    p_w1.font.bold = True
    p_w1.font.color.rgb = ACCENT_RED

    p_w2 = tf_w.add_paragraph()
    p_w2.text = "Citizen Call  ➔  Manual Intake  ➔  Operator Verifies  ➔  Radio Voice Search  ➔  Unconfirmed Dispatch  ➔  Delayed Response"
    p_w2.font.name = "Segoe UI"
    p_w2.font.size = Pt(11)
    p_w2.font.bold = True
    p_w2.font.color.rgb = TEXT_MAIN

    # 4 Problem Cards
    probs = [
        ("Incomplete & Panicked Information", "Callers under extreme stress often omit critical medical details or exact addresses, forcing operators to spend 2-4 minutes probing before dispatching.", ACCENT_ORANGE),
        ("Unmonitored Responder Dropouts", "If an assigned ambulance gets stuck in traffic, has radio failure, or declines, traditional systems stay idle until someone notices minutes later.", ACCENT_RED),
        ("Operator Cognitive Overload", "During storms or mass accidents, dispatchers face dozens of simultaneous calls, causing manual triage mistakes and prioritization delays.", ACCENT_ORANGE),
        ("Siloed Communications", "Citizens wait in panic with zero status updates, while receiving trauma centers get no pre-arrival casualty heads-up.", ACCENT_BLUE)
    ]

    for i, (p_title, p_desc, col) in enumerate(probs):
        col_x = 0.8 + i * 2.98
        card = add_card(s2, col_x, 2.8, 2.8, 3.8, CARD_BG, CARD_BORDER)
        
        # Color bar top
        bar = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(col_x + 0.2), Inches(3.0), Inches(2.4), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s2.shapes.add_textbox(Inches(col_x + 0.2), Inches(3.2), Inches(2.4), Inches(3.2))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = f"PROBLEM 0{i+1}"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(9)
        p1.font.bold = True
        p1.font.color.rgb = col
        
        p2 = tf.add_paragraph()
        p2.text = p_title
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(12)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_MAIN
        p2.space_before = Pt(4)
        p2.space_after = Pt(8)

        p3 = tf.add_paragraph()
        p3.text = p_desc
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(10)
        p3.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 3: OUR SOLUTION
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Our Approach: One Coordinated Response Workflow", "The Solution", 3)

    # 4 Pillars Grid
    pillars = [
        ("01. INTAKE", "Collect Emergency Report", "Accepts structured distress forms or raw distress text. Automatically binds caller identity, coordinates, and emergency description into an active incident.", ACCENT_BLUE),
        ("02. TRIAGE", "Understand & Prioritize", "Extracts incident classification (Accident, Fire, Medical, Crime, Rescue) and clinical urgency (P1-Critical to P4-Low) in milliseconds using LLM & fallback logic.", ACCENT_RED),
        ("03. DISPATCH", "Select Best Responder", "Evaluates field units using a proximity and specialization matching formula. Excludes busy/offline responders and picks the optimal unit instantly.", ACCENT_ORANGE),
        ("04. COMMUNICATION", "Coordinate All Stakeholders", "Dispatches simultaneous targeted alerts: push notification to responder, reassuring SMS to caller, radio log to dispatch, and trauma alert to hospital.", ACCENT_GREEN)
    ]

    for i, (p_tag, p_head, p_body, col) in enumerate(pillars):
        col_x = 0.8 + i * 2.98
        c = add_card(s3, col_x, 1.6, 2.8, 4.0, CARD_BG, CARD_BORDER)
        
        # Indicator badge
        ib = add_card(s3, col_x + 0.2, 1.8, 1.2, 0.35, CARD_HIGHLIGHT, col)
        p_ib = ib.text_frame.paragraphs[0]
        p_ib.text = p_tag
        p_ib.alignment = PP_ALIGN.CENTER
        p_ib.font.name = "Segoe UI"
        p_ib.font.size = Pt(9)
        p_ib.font.bold = True
        p_ib.font.color.rgb = col

        tb = s3.shapes.add_textbox(Inches(col_x + 0.2), Inches(2.3), Inches(2.4), Inches(3.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = p_head
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_MAIN
        p1.space_after = Pt(8)

        p2 = tf.add_paragraph()
        p2.text = p_body
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(10)
        p2.font.color.rgb = TEXT_DARK

    # Bottom Banner Statement
    bot_card = add_card(s3, 0.8, 5.8, 11.733, 0.9, CARD_HIGHLIGHT, ACCENT_BLUE)
    tb_b = s3.shapes.add_textbox(Inches(1.0), Inches(5.95), Inches(11.3), Inches(0.6))
    p_b = tb_b.text_frame.paragraphs[0]
    p_b.alignment = PP_ALIGN.CENTER
    p_b.text = "“From reporting an emergency to tracking the response in one coordinated workflow.”"
    p_b.font.name = "Segoe UI"
    p_b.font.size = Pt(13)
    p_b.font.bold = True
    p_b.font.color.rgb = ACCENT_BLUE

    # =========================================================================
    # SLIDE 4: COMPLETE WORKFLOW
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "From SOS to Response: Complete Operational Pipeline", "End-to-End Workflow", 4)

    steps = [
        ("1. Report SOS", "Citizen submits distress call via app or 1-touch SOS button", ACCENT_BLUE),
        ("2. Incident Created", "FastAPI validates & commits new record to database", TEXT_MUTED),
        ("3. AI Triage", "Clinical urgency classified into P1-Critical to P4-Low", ACCENT_RED),
        ("4. Fleet Search", "Available responders ranked by distance & specialty", ACCENT_ORANGE),
        ("5. Unit Dispatched", "Primary unit assigned; notifications sent to all parties", ACCENT_BLUE),
        ("6. 30s SLA Monitor", "Monitors acknowledgment; triggers failover if unaccepted", ACCENT_RED),
        ("7. Mission Active", "Responder updates progress: En Route ➔ On Scene", ACCENT_GREEN),
        ("8. Debrief Report", "System synthesizes AI postmortem & audit timeline", ACCENT_GREEN)
    ]

    for i, (title, desc, col) in enumerate(steps):
        # 2 rows of 4 cards
        row = i // 4
        col_idx = i % 4
        x = 0.8 + col_idx * 2.98
        y = 1.6 + row * 2.6

        c = add_card(s4, x, y, 2.8, 2.3, CARD_BG, CARD_BORDER)

        # Step tag
        num_tag = add_card(s4, x + 0.2, y + 0.2, 0.6, 0.3, CARD_HIGHLIGHT, col)
        p_nt = num_tag.text_frame.paragraphs[0]
        p_nt.text = f"{i+1:02d}"
        p_nt.alignment = PP_ALIGN.CENTER
        p_nt.font.size = Pt(9)
        p_nt.font.bold = True
        p_nt.font.color.rgb = col

        tb = s4.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.6), Inches(2.4), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_MAIN
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 5: MULTI-AGENT / MODULE WORKFLOW
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "How the 6 Specialized Agents Coordinate", "Multi-Agent System Architecture", 5)

    agents = [
        ("EmergencyAnalysisAgent", "PERCEIVE & REASON", "Intake & Clinical Triage: Extracts medical emergency type, severity, and urgency. Determines priority P1-P4.", ACCENT_RED),
        ("ResponderSelectionAgent", "DECIDE", "Fleet Matchmaker: Evaluates field units using distance and medical skill specialization bonus.", ACCENT_ORANGE),
        ("CommunicationAgent", "ACT", "Stakeholder Broadcast: Dispatches tailored notifications to Citizen, Responder, Dispatcher, and Trauma Centers.", ACCENT_BLUE),
        ("MonitoringAgent", "OBSERVE", "SLA Sentinel: Enforces 30-second acknowledgment window. Detects unresponsive units.", ACCENT_RED),
        ("EscalationAgent", "ADAPT", "Self-Healing Failover: Blacklists dropped units, recalculates candidates, and re-routes mission.", ACCENT_ORANGE),
        ("AIIncidentReportAgent", "REPORT", "Debrief Synthesizer: Generates postmortem incident dossier from timeline actions and response metrics.", ACCENT_GREEN)
    ]

    # Center Hub Card
    center_hub = add_card(s5, 4.8, 3.2, 3.733, 1.2, CARD_HIGHLIGHT, ACCENT_BLUE)
    tf_ch = center_hub.text_frame
    tf_ch.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_ch1 = tf_ch.paragraphs[0]
    p_ch1.alignment = PP_ALIGN.CENTER
    p_ch1.text = "AGENT ORCHESTRATOR"
    p_ch1.font.name = "Segoe UI"
    p_ch1.font.size = Pt(13)
    p_ch1.font.bold = True
    p_ch1.font.color.rgb = ACCENT_BLUE
    p_ch2 = tf_ch.add_paragraph()
    p_ch2.alignment = PP_ALIGN.CENTER
    p_ch2.text = "State Machine & Cognitive Trace Logger"
    p_ch2.font.name = "Segoe UI"
    p_ch2.font.size = Pt(9.5)
    p_ch2.font.color.rgb = TEXT_MUTED

    # Surrounding Agent Cards (3 on Left, 3 on Right)
    left_agents = agents[:3]
    right_agents = agents[3:]

    for i, (name, phase, role, col) in enumerate(left_agents):
        y = 1.5 + i * 1.8
        c = add_card(s5, 0.8, y, 3.6, 1.6, CARD_BG, CARD_BORDER)
        tb = s5.shapes.add_textbox(Inches(1.0), Inches(y + 0.1), Inches(3.2), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{name} ({phase})"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = role
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(3)

    for i, (name, phase, role, col) in enumerate(right_agents):
        y = 1.5 + i * 1.8
        c = add_card(s5, 8.9, y, 3.6, 1.6, CARD_BG, CARD_BORDER)
        tb = s5.shapes.add_textbox(Inches(9.1), Inches(y + 0.1), Inches(3.2), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{name} ({phase})"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = role
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 6: TRIAGE
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "How Triage Decides Priority: Clinical Urgency Scoring", "Emergency Analysis Logic", 6)

    # Left: 4 Priority Cards
    priorities = [
        ("P1 - CRITICAL", "Trauma, cardiac arrest, severe bleeding, unconsciousness", "Immediate dispatch (<1 min). Trauma hospital notified.", ACCENT_RED),
        ("P2 - HIGH", "Highway collisions, active flames, major fractures, robbery", "Rapid response (<3 min). Priority dispatch queue.", ACCENT_ORANGE),
        ("P3 - MEDIUM", "Moderate pain, minor burns, localized sprains", "Standard response (<8 min). First available local unit.", ACCENT_BLUE),
        ("P4 - LOW", "Property theft, non-injury disputes, general inquiry", "Routine queue. Scheduled dispatch when units free.", TEXT_MUTED)
    ]

    for i, (p_lvl, criteria, action, col) in enumerate(priorities):
        y = 1.5 + i * 1.3
        c = add_card(s6, 0.8, y, 6.2, 1.15, CARD_BG, CARD_BORDER)
        
        # Color bar
        bar = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(y), Inches(0.15), Inches(1.15))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s6.shapes.add_textbox(Inches(1.1), Inches(y + 0.1), Inches(5.7), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{p_lvl}  —  {criteria}"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = f"Action: {action}"
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(2)

    # Right: Real-world Triage Example Card
    ex_card = add_card(s6, 7.3, 1.5, 5.233, 5.2, CARD_HIGHLIGHT, ACCENT_BLUE)
    tb_ex = s6.shapes.add_textbox(Inches(7.6), Inches(1.8), Inches(4.7), Inches(4.6))
    tf_ex = tb_ex.text_frame
    tf_ex.word_wrap = True

    p_e1 = tf_ex.paragraphs[0]
    p_e1.text = "REAL-WORLD TRIAGE EXECUTION"
    p_e1.font.name = "Segoe UI"
    p_e1.font.size = Pt(12)
    p_e1.font.bold = True
    p_e1.font.color.rgb = ACCENT_BLUE

    p_e2 = tf_ex.add_paragraph()
    p_e2.text = "Incoming Distress Call:\n“Major car crash on highway, smoke rising, passenger trapped and bleeding heavily.”"
    p_e2.font.name = "Segoe UI"
    p_e2.font.size = Pt(10.5)
    p_e2.font.color.rgb = TEXT_MAIN
    p_e2.space_before = Pt(10)
    p_e2.space_after = Pt(12)

    steps_ex = [
        ("1. Classification", "Accident (Extracted from 'car crash', 'collision')"),
        ("2. Severity", "Critical (Triggered by 'trapped', 'bleeding heavily')"),
        ("3. Urgency", "Immediate (Life threat apparent)"),
        ("4. Assigned Priority", "P1-Critical"),
        ("5. Clinical Rationale", "Critical trauma or life-threatening symptoms identified; immediate paramedic extraction required.")
    ]

    for label, val in steps_ex:
        p = tf_ex.add_paragraph()
        p.text = f"• {label}: {val}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 7: DISPATCHER / COMMAND
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Dispatcher: Turning Priority into Optimized Action", "Dispatch Decision Logic", 7)

    # Left: Decision Flow Sequence
    df_card = add_card(s7, 0.8, 1.5, 6.2, 5.2, CARD_BG, CARD_BORDER)
    tb_df = s7.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.6), Inches(4.8))
    tf_df = tb_df.text_frame
    tf_df.word_wrap = True

    p_dft = tf_df.paragraphs[0]
    p_dft.text = "DISPATCH EXECUTION SEQUENCE:"
    p_dft.font.name = "Segoe UI"
    p_dft.font.size = Pt(12)
    p_dft.font.bold = True
    p_dft.font.color.rgb = ACCENT_ORANGE

    df_steps = [
        ("1. Query Candidate Pool", "Filters database for responders with status AVAILABLE"),
        ("2. Apply Incident Blacklist", "Excludes responders who previously timed out or declined this incident"),
        ("3. Determine Optimal Specialization", "Accident ➔ Medical/Rescue | Fire ➔ Fire/Rescue | Crime ➔ Police"),
        ("4. Calculate Suitability Score", "Score = (10 / Distance_km) * Specialization_Bonus (1.5x)"),
        ("5. Rank & Select Winner", "Unit with highest score assigned immediately"),
        ("6. Start 30s SLA Clock", "State set to WAITING_FOR_RESPONSE; timer starts")
    ]

    for st, sd in df_steps:
        p = tf_df.add_paragraph()
        p.text = f"{st}:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(8)
        
        p_sub = tf_df.add_paragraph()
        p_sub.text = sd
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = TEXT_DARK

    # Right: Dispatch Formula & Criteria Side Panel
    crit_card = add_card(s7, 7.3, 1.5, 5.233, 5.2, CARD_HIGHLIGHT, ACCENT_BLUE)
    tb_cr = s7.shapes.add_textbox(Inches(7.6), Inches(1.8), Inches(4.7), Inches(4.6))
    tf_cr = tb_cr.text_frame
    tf_cr.word_wrap = True

    p_c1 = tf_cr.paragraphs[0]
    p_c1.text = "MATHEMATICAL SCORING ENGINE"
    p_c1.font.name = "Segoe UI"
    p_c1.font.size = Pt(12)
    p_c1.font.bold = True
    p_c1.font.color.rgb = ACCENT_BLUE

    p_c2 = tf_cr.add_paragraph()
    p_c2.text = "Implemented in ResponderSelectionAgent.py:"
    p_c2.font.name = "Segoe UI"
    p_c2.font.size = Pt(10)
    p_c2.font.color.rgb = TEXT_MUTED
    p_c2.space_after = Pt(10)

    # Formula Box
    f_box = add_card(s7, 7.5, 2.6, 4.8, 1.1, CARD_BG, ACCENT_BLUE)
    p_fb = f_box.text_frame.paragraphs[0]
    p_fb.alignment = PP_ALIGN.CENTER
    p_fb.text = "Suitability Score = (10 / Distance) × Spec_Bonus\n(Bonus = 1.5x if Specialization matches Emergency Type)"
    p_fb.font.name = "Consolas"
    p_fb.font.size = Pt(10)
    p_fb.font.bold = True
    p_fb.font.color.rgb = ACCENT_BLUE

    tb_cr2 = s7.shapes.add_textbox(Inches(7.6), Inches(3.9), Inches(4.7), Inches(2.6))
    tf_cr2 = tb_cr2.text_frame
    tf_cr2.word_wrap = True
    p_cr2 = tf_cr2.paragraphs[0]
    p_cr2.text = "Example Ranking for Accident (#28):"
    p_cr2.font.name = "Segoe UI"
    p_cr2.font.size = Pt(10.5)
    p_cr2.font.bold = True
    p_cr2.font.color.rgb = TEXT_MAIN

    rankings = [
        "1. Suresh (Medical, 0.8 km) ➔ Score: 18.75 [SELECTED]",
        "2. Ravi (Rescue, 1.5 km) ➔ Score: 10.00 [STANDBY]",
        "3. Priya (General, 1.2 km) ➔ Score: 8.33 [STANDBY]"
    ]
    for r in rankings:
        p = tf_cr2.add_paragraph()
        p.text = f"• {r}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = ACCENT_GREEN if "SELECTED" in r else TEXT_DARK
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 8: REAL-WORLD EXAMPLE
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Example: Medical Emergency & SLA Failover", "End-to-End Walkthrough", 8)

    timeline_events = [
        ("STEP 1: REPORT", "Distress call received: 'Car crash, trapped & bleeding heavily'", "Incident #28 initialized in status NEW", ACCENT_BLUE),
        ("STEP 2: TRIAGE", "EmergencyAnalysisAgent evaluates clinical text", "Classified: P1-Critical | Emergency: Accident", ACCENT_RED),
        ("STEP 3: DISPATCH", "ResponderSelectionAgent scores available fleet", "Assigned Unit: Suresh (Paramedic, 0.8 km away)", ACCENT_ORANGE),
        ("STEP 4: SLA TIMEOUT", "Suresh fails to acknowledge within 30-second window", "MonitoringAgent triggers SLA breach", ACCENT_RED),
        ("STEP 5: FAILOVER", "EscalationAgent blacklists Suresh & searches pool", "Reassigned: Ravi (Rescue Squad, 1.5 km away)", ACCENT_ORANGE),
        ("STEP 6: RESOLUTION", "Ravi accepts call, arrives on scene, assists victim", "Incident marked COMPLETED ➔ RESOLVED", ACCENT_GREEN),
        ("STEP 7: POSTMORTEM", "AIIncidentReportAgent synthesizes debrief dossier", "Report #10 generated with 95/100 score", ACCENT_BLUE)
    ]

    for i, (head, sub, detail, col) in enumerate(timeline_events):
        y = 1.45 + i * 0.77
        c = add_card(s8, 0.8, y, 11.733, 0.68, CARD_BG, CARD_BORDER)

        # Step tag
        stag = add_card(s8, 0.95, y + 0.12, 1.8, 0.44, CARD_HIGHLIGHT, col)
        p_st = stag.text_frame.paragraphs[0]
        p_st.alignment = PP_ALIGN.CENTER
        p_st.text = head
        p_st.font.name = "Segoe UI"
        p_st.font.size = Pt(8.5)
        p_st.font.bold = True
        p_st.font.color.rgb = col

        tb = s8.shapes.add_textbox(Inches(3.0), Inches(y + 0.12), Inches(8.3), Inches(0.44))
        tf = tb.text_frame
        p1 = tf.paragraphs[0]
        p1.text = f"{sub}   ➔   {detail}"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 9: SYSTEM ARCHITECTURE
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "System Architecture: 5 Decoupled Layers", "Technical Design", 9)

    layers = [
        ("LAYER 1: USER ACCESS & CLIENTS", "Citizen Web App (SOS)  |  Responder Field Terminal  |  Dispatcher Command Center  |  Admin Panel", ACCENT_BLUE),
        ("LAYER 2: APPLICATION & FRONTEND", "Vanilla CSS Design System  |  ES6 JavaScript Modules (api.js, app.js)  |  Web Audio API Sound Engine", TEXT_MAIN),
        ("LAYER 3: API & SECURITY GATEWAY", "FastAPI REST Server (8 Routers)  |  bcrypt Password Hashing (12 Rounds)  |  JWT Bearer Authentication", ACCENT_ORANGE),
        ("LAYER 4: AGENT ORCHESTRATION", "Orchestrator  |  Analysis Agent  |  Selection Agent  |  Comm Agent  |  Monitoring Agent  |  Escalation Agent  |  Report Agent", ACCENT_RED),
        ("LAYER 5: DATA & EXTERNAL SERVICES", "SQLAlchemy ORM  |  SQLite Database (resqagent.db)  |  Google Gemini 1.5 Flash REST API  |  Deterministic Fallback Engine", ACCENT_GREEN)
    ]

    for i, (layer_title, layer_desc, col) in enumerate(layers):
        y = 1.5 + i * 1.05
        c = add_card(s9, 0.8, y, 11.733, 0.95, CARD_BG, CARD_BORDER)

        bar = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(y), Inches(0.18), Inches(0.95))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s9.shapes.add_textbox(Inches(1.2), Inches(y + 0.1), Inches(11.1), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = layer_title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = layer_desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 10: DATABASE DESIGN
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Data Behind the Response: 8 Relational Models", "Database Architecture", 10)

    tables = [
        ("User", "Authentication & RBAC", "id, email, password_hash, role (citizen/responder/dispatch/admin), location, is_active"),
        ("Incident", "Distress Records", "id, reporter_name, emergency_type, severity, priority, status, location, description"),
        ("Responder", "Field Fleet", "id, name, role, specialization (Medical/Fire/Rescue/Police), distance, availability"),
        ("Assignment", "Mission Dispatches", "id, incident_id, responder_id, assignment_status (PENDING/ACCEPTED/COMPLETED), attempt_number"),
        ("Notification", "Omnichannel Alerts", "id, incident_id, recipient_type, channel (PUSH/SMS/RADIO/SECURE_NET), message"),
        ("IncidentTimeline", "Event Milestones", "id, incident_id, event_type, actor (Analysis Agent/Orchestrator), description, timestamp"),
        ("AgentAction", "Cognitive Trace Log", "id, incident_id, agent_name, action_type, reasoning, input_data, output_data"),
        ("Report", "Postmortem Synthesis", "id, incident_id, summary, initial_responder, final_responder, escalation_count, full_report_json")
    ]

    for i, (t_name, t_purp, t_fields) in enumerate(tables):
        col_idx = i % 4
        row_idx = i // 4
        x = 0.8 + col_idx * 2.98
        y = 1.5 + row_idx * 2.6

        c = add_card(s10, x, y, 2.8, 2.4, CARD_BG, CARD_BORDER)

        tb = s10.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.15), Inches(2.5), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = f"TABLE: {t_name}"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_BLUE

        p2 = tf.add_paragraph()
        p2.text = t_purp
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.bold = True
        p2.font.color.rgb = ACCENT_ORANGE
        p2.space_before = Pt(2)
        p2.space_after = Pt(6)

        p3 = tf.add_paragraph()
        p3.text = f"Attributes:\n{t_fields}"
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 11: API / BACKEND FLOW
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "How Data Moves Through the System: API Flow", "Backend Data Flow", 11)

    # Left: Sequence Flow Box
    f_card = add_card(s11, 0.8, 1.5, 6.2, 5.2, CARD_BG, CARD_BORDER)
    tb_f = s11.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.6), Inches(4.6))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True

    p_ft = tf_f.paragraphs[0]
    p_ft.text = "REQUEST LIFECYCLE (SOS INTAKE):"
    p_ft.font.name = "Segoe UI"
    p_ft.font.size = Pt(12)
    p_ft.font.bold = True
    p_ft.font.color.rgb = ACCENT_BLUE

    api_steps = [
        ("1. Client Form Submission", "Citizen submits POST /api/incidents/ with description & location"),
        ("2. JWT Authentication & Rate Check", "FastAPI verifies Bearer token & active user session"),
        ("3. Pydantic Model Validation", "Validates incident payload against IncidentCreate schema"),
        ("4. Database Record Creation", "SessionLocal writes incident with initial status NEW"),
        ("5. Agent Orchestrator Trigger", "Synchronously kicks off EmergencyAnalysisAgent triage"),
        ("6. Selection & Notification Loop", "Dispatches to closest responder and writes timeline logs"),
        ("7. JSON Response to Client", "Returns incident object with assigned responder & priority")
    ]

    for st, sd in api_steps:
        p = tf_f.add_paragraph()
        p.text = f"{st}:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(6)
        
        p_sub = tf_f.add_paragraph()
        p_sub.text = sd
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = TEXT_DARK

    # Right: 8 REST Routers Card
    r_card = add_card(s11, 7.3, 1.5, 5.233, 5.2, CARD_HIGHLIGHT, ACCENT_ORANGE)
    tb_r = s11.shapes.add_textbox(Inches(7.6), Inches(1.8), Inches(4.7), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_rt = tf_r.paragraphs[0]
    p_rt.text = "8 REST ROUTERS (FASTAPI BACKEND)"
    p_rt.font.name = "Segoe UI"
    p_rt.font.size = Pt(12)
    p_rt.font.bold = True
    p_rt.font.color.rgb = ACCENT_ORANGE

    routers = [
        ("/api/auth", "Login, register, /me profile, password management"),
        ("/api/admin", "User account provisioning, system stats, role management"),
        ("/api/incidents", "Incident creation, role-isolated filtering, status updates"),
        ("/api/responders", "Fleet roster, availability query, location tracking"),
        ("/api/assignments", "Responder accept/decline, operational progress toggles"),
        ("/api/simulation", "SLA timeout triggers, automated failover testing"),
        ("/api/reports", "AI debrief postmortem generation and export"),
        ("/api/users", "User directory and profile updates")
    ]

    for route, desc in routers:
        p = tf_r.add_paragraph()
        p.text = f"• {route}:"
        p.font.name = "Consolas"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        p.space_before = Pt(4)
        
        p_sub = tf_r.add_paragraph()
        p_sub.text = f"  {desc}"
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(8.5)
        p_sub.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 12: OFFLINE / LOW CONNECTIVITY
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "When Connectivity Is Limited: Dual-Engine Fallback", "Reliability Engineering", 12)

    # Left: Implemented Dual-Engine Fallback
    c_left = add_card(s12, 0.8, 1.5, 5.7, 5.2, CARD_BG, ACCENT_GREEN)
    tb_l = s12.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.1), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p_lt = tf_l.paragraphs[0]
    p_lt.text = "IMPLEMENTED: DUAL-ENGINE TRIAGE"
    p_lt.font.name = "Segoe UI"
    p_lt.font.size = Pt(12)
    p_lt.font.bold = True
    p_lt.font.color.rgb = ACCENT_GREEN

    p_ld = tf_l.add_paragraph()
    p_ld.text = "In mission-critical emergencies, cloud AI API outages cannot be allowed to halt 911 dispatch. ResQAgent implements a two-tier cognitive architecture:"
    p_ld.font.name = "Segoe UI"
    p_ld.font.size = Pt(9.5)
    p_ld.font.color.rgb = TEXT_MAIN
    p_ld.space_before = Pt(6)
    p_ld.space_after = Pt(10)

    points_l = [
        ("Tier 1: Cloud LLM (Gemini 1.5 Flash)", "Used when online for nuanced clinical understanding and semantic priority reasoning."),
        ("Tier 2: Deterministic Fallback Engine", "Instantly triggers if Gemini times out, returns HTTP errors, or if API key is absent."),
        ("Zero Dropped Calls", "Evaluates trauma keywords ('unconscious', 'bleeding', 'trapped') locally in 2ms without internet access."),
        ("Session Token Persistence", "Signed JWT tokens stored in localStorage enable offline interface continuity.")
    ]
    for h, b in points_l:
        p = tf_l.add_paragraph()
        p.text = f"✓ {h}:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        p_sub = tf_l.add_paragraph()
        p_sub.text = f"  {b}"
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(8.5)
        p_sub.font.color.rgb = TEXT_DARK

    # Right: Honest Labeling - Planned Enhancements
    c_right = add_card(s12, 6.8, 1.5, 5.7, 5.2, CARD_HIGHLIGHT, ACCENT_ORANGE)
    tb_r = s12.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.1), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_rt = tf_r.paragraphs[0]
    p_rt.text = "PLANNED: LOW-CONNECTIVITY ENHANCEMENTS"
    p_rt.font.name = "Segoe UI"
    p_rt.font.size = Pt(12)
    p_rt.font.bold = True
    p_rt.font.color.rgb = ACCENT_ORANGE

    p_rd = tf_r.add_paragraph()
    p_rd.text = "To scale beyond prototype stage into extreme catastrophe zones (earthquakes, cellular grid collapse), we have designed the following extensions:"
    p_rd.font.name = "Segoe UI"
    p_rd.font.size = Pt(9.5)
    p_rd.font.color.rgb = TEXT_MAIN
    p_rd.space_before = Pt(6)
    p_rd.space_after = Pt(10)

    points_r = [
        ("IndexedDB Local Outbox Queue (Planned)", "Allows citizens to submit distress reports with zero signal; automatically syncs via background service worker upon reconnection."),
        ("SMS-to-API Gateway (Planned)", "Enables emergency reporting via standard 2G GSM cellular SMS when 4G/5G data networks fail."),
        ("Peer-to-Peer Bluetooth Mesh (Planned)", "Responders relay mission coordinates unit-to-unit when cellular cell towers are down.")
    ]
    for h, b in points_r:
        p = tf_r.add_paragraph()
        p.text = f"➔ {h}:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_ORANGE
        p_sub = tf_r.add_paragraph()
        p_sub.text = f"  {b}"
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(8.5)
        p_sub.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 13: TECHNOLOGY STACK
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Technology Stack: Modular, Modern & Reliable", "Implemented Stack", 13)

    stacks = [
        ("FRONTEND", "Single-Page Application", ["Vanilla HTML5 & Semantic Elements", "Vanilla CSS3 Design System", "Vanilla ES6 JavaScript (No bloat)", "Web Audio API Synthesizer (Sirens/Tones)"], ACCENT_BLUE),
        ("BACKEND API", "High-Performance ASGI", ["Python 3.12 Runtime", "FastAPI Framework", "Uvicorn ASGI Server", "Pydantic V2 Data Validation"], ACCENT_GREEN),
        ("DATABASE & ORM", "Relational Persistence", ["SQLAlchemy 2.0 ORM Engine", "SQLite (Local Development)", "PostgreSQL Compatible Driver (psycopg2)", "Declarative Base Migrations"], ACCENT_ORANGE),
        ("AGENT COGNITION", "AI Triage & Reasoning", ["Google Gemini 1.5 Flash REST API", "Deterministic Clinical Keyword Engine", "Multi-Agent State Machine", "Audit Action Logging"], ACCENT_RED),
        ("SECURITY & AUTH", "Cryptographic RBAC", ["bcrypt (12 Salt Rounds Hashing)", "PyJWT (HS256 Session Tokens)", "Role-Based Route Guards", "Database Query Data Scoping"], ACCENT_BLUE),
        ("TESTING & QUALITY", "Automated Test Suites", ["Auth & RBAC Suite (17 Tests)", "API Integration Suite", "Agent Flow & SLA Escalation Suite", "Zero Mocking of Core Logic"], ACCENT_GREEN)
    ]

    for i, (cat, sub, items, col) in enumerate(stacks):
        col_idx = i % 3
        row_idx = i // 3
        x = 0.8 + col_idx * 3.98
        y = 1.5 + row_idx * 2.6

        c = add_card(s13, x, y, 3.8, 2.4, CARD_BG, CARD_BORDER)

        tb = s13.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.15), Inches(3.5), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = cat
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(6)

        for it in items:
            p = tf.add_paragraph()
            p.text = f"• {it}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(8.5)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(2)

    # =========================================================================
    # SLIDE 14: KEY FEATURES
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "What We Built: Core Implemented Features", "Feature Matrix", 14)

    features = [
        ("One-Touch Citizen SOS", "Quick-preset distress buttons (Accident, Medical, Fire, Crime) and instant GPS location binding.", ACCENT_BLUE),
        ("Autonomous Clinical Triage", "Semantic extraction of severity (Critical/High/Med/Low) and urgency into structured priority P1-P4.", ACCENT_RED),
        ("Proximity & Skill Dispatch", "Mathematical scoring engine that matches responder specialization to emergency type and distance.", ACCENT_ORANGE),
        ("SLA Sentinel Monitoring", "30-second automated acknowledgment timer tracks responder health and flags stalled missions.", ACCENT_RED),
        ("Self-Healing Escalation", "Automatically blacklists dropped responders and assigns the next best unit with citizen reassurance.", ACCENT_ORANGE),
        ("Multi-Party Broadcast", "Simultaneously alerts responders via push, citizens via SMS, dispatch via radio, and hospitals via secure net.", ACCENT_GREEN),
        ("Post-Incident AI Dossier", "Synthesizes comprehensive debrief report, timeline events, and agent performance score (95/100).", ACCENT_BLUE),
        ("Cryptographic RBAC Security", "4 distinct roles (Citizen, Responder, Dispatcher, Admin) with bcrypt hashing and token auth.", ACCENT_GREEN)
    ]

    for i, (title, desc, col) in enumerate(features):
        col_idx = i % 4
        row_idx = i // 4
        x = 0.8 + col_idx * 2.98
        y = 1.5 + row_idx * 2.6

        c = add_card(s14, x, y, 2.8, 2.4, CARD_BG, CARD_BORDER)

        bar = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.2), Inches(y + 0.2), Inches(2.4), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s14.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.35), Inches(2.4), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_MAIN
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 15: ACTUAL APPLICATION
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Application Screens: Real Working Prototype", "User Interface Showcase", 15)

    screenshots = [
        ("screenshot_citizen.png", "Citizen SOS Screen", "One-touch distress button & live incident tracking"),
        ("screenshot_dispatch.png", "Dispatch Command Center", "Active city fleet roster, incident table & SLA simulation"),
        ("screenshot_timeline.png", "AI Cognitive Inspector", "Real-time agent reasoning traces & decision log"),
        ("screenshot_report.png", "AI Incident Report", "Post-incident debrief dossier & performance score")
    ]

    for i, (img_name, label, sub) in enumerate(screenshots):
        col_idx = i % 2
        row_idx = i // 2
        x = 0.8 + col_idx * 5.98
        y = 1.5 + row_idx * 2.65

        # Card container
        c = add_card(s15, x, y, 5.75, 2.5, CARD_BG, CARD_BORDER)

        # Image
        img_path = os.path.join("c:\\Users\\PREMTEJA\\OneDrive\\Desktop\\resqagent", img_name)
        if os.path.exists(img_path):
            s15.shapes.add_picture(img_path, Inches(x + 0.15), Inches(y + 0.15), width=Inches(3.4), height=Inches(2.2))

        # Text Side
        tb = s15.shapes.add_textbox(Inches(x + 3.65), Inches(y + 0.2), Inches(1.95), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_BLUE

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(4)

    # =========================================================================
    # SLIDE 16: USER ROLES
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Who Uses the System: 4 Strict Role Boundaries", "Role-Based Access Control", 16)

    roles = [
        ("CITIZEN", "Route: /citizen", "• Self-registers account\n• Submits one-touch or detailed SOS\n• Receives live arrival ETA & reassurance\n• Strictly isolated: cannot see other citizens", ACCENT_BLUE),
        ("RESPONDER", "Route: /responder", "• Assigned calls push to terminal\n• Acknowledges (Accept / Decline)\n• Updates progress: En Route ➔ Completed\n• Bound strictly to assigned incident ID", ACCENT_GREEN),
        ("DISPATCHER", "Route: /dispatch", "• Full city-wide incident visibility\n• Live responder fleet tracking\n• Manual assignment override controls\n• Interactive SLA timeout simulation trigger", ACCENT_ORANGE),
        ("ADMINISTRATOR", "Route: /admin", "• Provisions Dispatchers & Responders\n• Activates / deactivates system accounts\n• Inspects system audit statistics\n• 1-click demo fleet reset mechanism", ACCENT_RED)
    ]

    for i, (r_name, r_route, r_desc, col) in enumerate(roles):
        col_x = 0.8 + i * 2.98
        c = add_card(s16, col_x, 1.5, 2.8, 5.2, CARD_BG, CARD_BORDER)

        bar = s16.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(col_x + 0.2), Inches(1.7), Inches(2.4), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s16.shapes.add_textbox(Inches(col_x + 0.2), Inches(1.9), Inches(2.4), Inches(4.6))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = r_name
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = r_route
        p2.font.name = "Consolas"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(10)

        p3 = tf.add_paragraph()
        p3.text = r_desc
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 17: CHALLENGES & SOLUTIONS
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    add_header(s17, "What We Had to Solve: Engineering Challenges", "Technical Problem Solving", 17)

    challenges = [
        ("Challenge: Unstructured Distress Descriptions", "Citizens submit frantic, ungrammatical descriptions with mixed symptoms.", "Solution: Gemini 1.5 Flash Prompt + Deterministic Fallback", "Configured structured JSON output schema. Backed by clinical keyword rules that triage critical cases in 2ms if the LLM drops."),
        ("Challenge: Unmonitored Responder Dropouts", "In traditional systems, an unresponsive unit leaves the caller stranded.", "Solution: 30s SLA Countdown + Autonomous EscalationAgent", "Detects SLA breaches automatically, blacklists the unresponsive unit, recalculates the next closest responder, and re-routes the mission."),
        ("Challenge: Suboptimal Unit Dispatching", "Sending general police to cardiac arrest or fire trucks to minor theft.", "Solution: Proximity + Specialization Utility Scoring", "Engine scores candidates by distance weighted with a 1.5x bonus for matching medical/fire/rescue expertise."),
        ("Challenge: Privilege Escalation & Data Leaks", "Unauthorized users accessing dispatch controls or other citizens' data.", "Solution: Cryptographic RBAC & Query-Level Isolation", "Bcrypt 12-round password hashing, HS256 signed JWT tokens, and database query filters verified by 17 automated tests.")
    ]

    for i, (ch_title, ch_desc, sol_title, sol_desc) in enumerate(challenges):
        y = 1.5 + i * 1.3
        c = add_card(s17, 0.8, y, 11.733, 1.15, CARD_BG, CARD_BORDER)

        tb_l = s17.shapes.add_textbox(Inches(1.0), Inches(y + 0.1), Inches(5.4), Inches(0.95))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        p_l1 = tf_l.paragraphs[0]
        p_l1.text = ch_title
        p_l1.font.name = "Segoe UI"
        p_l1.font.size = Pt(10.5)
        p_l1.font.bold = True
        p_l1.font.color.rgb = ACCENT_RED
        p_l2 = tf_l.add_paragraph()
        p_l2.text = ch_desc
        p_l2.font.name = "Segoe UI"
        p_l2.font.size = Pt(9)
        p_l2.font.color.rgb = TEXT_DARK

        tb_r = s17.shapes.add_textbox(Inches(6.6), Inches(y + 0.1), Inches(5.7), Inches(0.95))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        p_r1 = tf_r.paragraphs[0]
        p_r1.text = sol_title
        p_r1.font.name = "Segoe UI"
        p_r1.font.size = Pt(10.5)
        p_r1.font.bold = True
        p_r1.font.color.rgb = ACCENT_GREEN
        p_r2 = tf_r.add_paragraph()
        p_r2.text = sol_desc
        p_r2.font.name = "Segoe UI"
        p_r2.font.size = Pt(9)
        p_r2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 18: WHAT MAKES IT USEFUL
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    add_header(s18, "Why This Matters: Practical Real-World Utility", "Value Proposition", 18)

    utilities = [
        ("FASTER DISPATCH", "Eliminates phone queue delays. Triage occurs in milliseconds instead of 3-5 minutes of manual interrogation.", ACCENT_BLUE),
        ("CLEAR PRIORITY", "Severe life-threats (P1-Critical) are automatically distinguished from non-urgent calls, preventing triage mistakes.", ACCENT_RED),
        ("SMARTER ALLOCATION", "Field responders are matched based on both proximity and specialized skill, sending the right care the first time.", ACCENT_ORANGE),
        ("LIVE VISIBILITY", "Citizens receive automated arrival updates; dispatchers monitor the fleet; receiving hospitals prepare trauma bays early.", ACCENT_GREEN),
        ("FULL AUDITABILITY", "Every agent decision, reassignment, and timeline event is stored in an explainable cognitive log for postmortem review.", ACCENT_BLUE)
    ]

    for i, (title, desc, col) in enumerate(utilities):
        col_x = 0.8 + i * 2.38
        c = add_card(s18, col_x, 1.8, 2.25, 4.8, CARD_BG, CARD_BORDER)

        bar = s18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(col_x + 0.15), Inches(2.0), Inches(1.95), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s18.shapes.add_textbox(Inches(col_x + 0.15), Inches(2.2), Inches(1.95), Inches(4.2))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = f"0{i+1}"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(18)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_MAIN
        p2.space_before = Pt(6)
        p2.space_after = Pt(10)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 19: FUTURE IMPROVEMENTS
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    add_header(s19, "What We Would Build Next: Product Roadmap", "Development Roadmap", 19)

    phases = [
        ("STAGE 1: CURRENT PROTOTYPE (COMPLETED)", [
            "6-Agent Autonomous Cognitive Loop",
            "FastAPI REST Backend with 8 Routers",
            "4-Role Cryptographic RBAC (bcrypt + JWT)",
            "30s SLA Monitoring & Autonomous Escalation",
            "AI Incident Report Postmortem Generator",
            "17 Automated Verification Security Tests"
        ], ACCENT_GREEN),
        ("STAGE 2: NEAR-TERM IMPROVEMENTS (NEXT)", [
            "Native Mobile App (React Native / Flutter)",
            "Live GPS Telemetry with Mapbox / Leaflet",
            "IndexedDB Offline Queue & Background Sync",
            "SMS-to-API Gateway for 2G Emergency Areas",
            "Automated Voice-to-Text Audio Call Ingestion"
        ], ACCENT_BLUE),
        ("STAGE 3: PRODUCTION SCALE (FUTURE)", [
            "Trauma Hospital EHR System Integration",
            "Drone Reconnaissance Automated Dispatch",
            "Multi-City Federated Dispatch Network",
            "Real-time Traffic Routing Engine (Google Maps API)",
            "Automated Resource Inventory Tracking"
        ], ACCENT_ORANGE)
    ]

    for i, (p_title, p_items, col) in enumerate(phases):
        col_x = 0.8 + i * 3.98
        c = add_card(s19, col_x, 1.6, 3.8, 5.0, CARD_BG, CARD_BORDER)

        bar = s19.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(col_x + 0.2), Inches(1.8), Inches(3.4), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col
        bar.line.fill.background()

        tb = s19.shapes.add_textbox(Inches(col_x + 0.2), Inches(1.95), Inches(3.4), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = p_title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.space_after = Pt(10)

        for it in p_items:
            p = tf.add_paragraph()
            p.text = f"• {it}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_MAIN
            p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 20: LIVE DEMO
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    add_header(s20, "Live Demonstration Playbook", "Demonstration Sequence", 20)

    demo_steps = [
        ("01", "Open Application", "Navigate to http://localhost:8000 and view Citizen SOS interface", ACCENT_BLUE),
        ("02", "Report Emergency", "Submit distress call: 'Highway crash, car smoking, driver trapped'", ACCENT_RED),
        ("03", "Observe Triage", "Watch AI categorize as Accident / P1-Critical urgency in real time", ACCENT_ORANGE),
        ("04", "Review Dispatch", "Show Suresh (Paramedic, 0.8 km) assigned by selection algorithm", ACCENT_BLUE),
        ("05", "Simulate SLA Timeout", "Click 'Simulate Suresh Timeout' to trigger 30s deadline breach", ACCENT_RED),
        ("06", "Watch Escalation", "EscalationAgent blacklists Suresh & auto-reassigns Ravi (1.5 km)", ACCENT_ORANGE),
        ("07", "Accept & Complete", "Ravi accepts mission, marks En Route, and completes assistance", ACCENT_GREEN),
        ("08", "Generate Debrief", "Click 'Incident Reports' to view AI-synthesized postmortem dossier", ACCENT_BLUE)
    ]

    for i, (num, title, desc, col) in enumerate(demo_steps):
        row = i // 4
        col_idx = i % 4
        x = 0.8 + col_idx * 2.98
        y = 1.6 + row * 2.6

        c = add_card(s20, x, y, 2.8, 2.3, CARD_BG, CARD_BORDER)

        tag = add_card(s20, x + 0.2, y + 0.2, 0.7, 0.4, CARD_HIGHLIGHT, col)
        p_tg = tag.text_frame.paragraphs[0]
        p_tg.alignment = PP_ALIGN.CENTER
        p_tg.text = num
        p_tg.font.name = "Segoe UI"
        p_tg.font.size = Pt(11)
        p_tg.font.bold = True
        p_tg.font.color.rgb = col

        tb = s20.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.7), Inches(2.4), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_MAIN
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 21: IMPACT
    # =========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    add_header(s21, "Expected Impact: Saving Critical Minutes in Emergency Care", "Social & Operational Impact", 21)

    # Center Circle Graphic
    center_c = s21.shapes.add_shape(MSO_SHAPE.OVAL, Inches(4.9), Inches(2.4), Inches(3.5), Inches(3.5))
    center_c.fill.solid()
    center_c.fill.fore_color.rgb = CARD_HIGHLIGHT
    center_c.line.color.rgb = ACCENT_RED
    center_c.line.width = Pt(2)
    tf_cc = center_c.text_frame
    tf_cc.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_cc1 = tf_cc.paragraphs[0]
    p_cc1.alignment = PP_ALIGN.CENTER
    p_cc1.text = "EMERGENCY\nCOORDINATION"
    p_cc1.font.name = "Segoe UI"
    p_cc1.font.size = Pt(15)
    p_cc1.font.bold = True
    p_cc1.font.color.rgb = TEXT_MAIN

    p_cc2 = tf_cc.add_paragraph()
    p_cc2.alignment = PP_ALIGN.CENTER
    p_cc2.text = "Protecting the Golden Hour"
    p_cc2.font.name = "Segoe UI"
    p_cc2.font.size = Pt(10)
    p_cc2.font.color.rgb = ACCENT_ORANGE

    # 4 Outer Cards
    impacts = [
        ("Faster Coordination", "Replaces manual telephone chasing with autonomous multi-agent handoffs in milliseconds.", 0.8, 1.8, ACCENT_BLUE),
        ("Zero Lost Emergencies", "SLA monitoring ensures no responder dropout goes unnoticed or unhandled.", 0.8, 4.3, ACCENT_RED),
        ("Smarter Care Matching", "Specialization scoring sends trauma paramedics to cardiac calls, not general units.", 8.9, 1.8, ACCENT_ORANGE),
        ("Complete Accountability", "Every action, clinical justification, and reassignment is auditable in code.", 8.9, 4.3, ACCENT_GREEN)
    ]

    for title, desc, x, y, col in impacts:
        c = add_card(s21, x, y, 3.6, 2.1, CARD_BG, CARD_BORDER)
        tb = s21.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.2), Inches(3.2), Inches(1.7))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.space_after = Pt(6)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 22: CONCLUSION
    # =========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    add_header(s22, "From Emergency Report to Coordinated Response", "Conclusion", 22)

    # Workflow Summary Box
    wf_c = add_card(s22, 0.8, 1.7, 11.733, 1.2, CARD_HIGHLIGHT, ACCENT_BLUE)
    p_wf = wf_c.text_frame.paragraphs[0]
    p_wf.alignment = PP_ALIGN.CENTER
    p_wf.text = "REPORT  ➔  UNDERSTAND  ➔  PRIORITIZE  ➔  DISPATCH  ➔  RESPOND  ➔  TRACK  ➔  DEBRIEF"
    p_wf.font.name = "Segoe UI"
    p_wf.font.size = Pt(13)
    p_wf.font.bold = True
    p_wf.font.color.rgb = ACCENT_BLUE

    # Student Conclusion Card
    c_card = add_card(s22, 0.8, 3.2, 11.733, 3.4, CARD_BG, CARD_BORDER)
    tb_c = s22.shapes.add_textbox(Inches(1.2), Inches(3.5), Inches(11.0), Inches(2.8))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True

    p_c1 = tf_c.paragraphs[0]
    p_c1.text = "CONCLUSION & SUMMARY:"
    p_c1.font.name = "Segoe UI"
    p_c1.font.size = Pt(13)
    p_c1.font.bold = True
    p_c1.font.color.rgb = ACCENT_ORANGE
    p_c1.space_after = Pt(8)

    p_c2 = tf_c.add_paragraph()
    p_c2.text = (
        "ResQAgent brings emergency reporting, clinical triage, dispatch optimization, SLA monitoring, and "
        "response tracking into one unified, transparent workflow.\n\n"
        "Rather than relying on a single conversational chatbot, we built an autonomous multi-agent architecture "
        "where each agent handles a dedicated task with mathematical precision, strict state management, and safety guardrails.\n\n"
        "Our focus is simple: make emergency coordination faster, clearer, and more reliable when every second counts."
    )
    p_c2.font.name = "Segoe UI"
    p_c2.font.size = Pt(11)
    p_c2.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 23: THANK YOU
    # =========================================================================
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_background(s23)

    # Accent top
    top_acc = s23.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.04))
    top_acc.fill.solid()
    top_acc.fill.fore_color.rgb = ACCENT_RED
    top_acc.line.fill.background()

    # Big Thank You
    ty_box = s23.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.2))
    tf_ty = ty_box.text_frame
    p_ty = tf_ty.paragraphs[0]
    p_ty.text = "Thank You"
    p_ty.font.name = "Segoe UI"
    p_ty.font.size = Pt(44)
    p_ty.font.bold = True
    p_ty.font.color.rgb = TEXT_MAIN

    # Subtitle
    q_box = s23.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.733), Inches(0.6))
    tf_q = q_box.text_frame
    p_q = tf_q.paragraphs[0]
    p_q.text = "Questions & Discussion"
    p_q.font.name = "Segoe UI"
    p_q.font.size = Pt(22)
    p_q.font.color.rgb = ACCENT_BLUE

    # Summary Info Card
    info_card = add_card(s23, 0.8, 3.8, 11.733, 2.8, CARD_HIGHLIGHT, CARD_BORDER)
    tb_inf = s23.shapes.add_textbox(Inches(1.2), Inches(4.0), Inches(11.0), Inches(2.4))
    tf_inf = tb_inf.text_frame
    tf_inf.word_wrap = True

    p_i1 = tf_inf.paragraphs[0]
    p_i1.text = "ResQAgent — Intelligent Emergency Response & Coordination Platform"
    p_i1.font.name = "Segoe UI"
    p_i1.font.size = Pt(14)
    p_i1.font.bold = True
    p_i1.font.color.rgb = TEXT_MAIN
    p_i1.space_after = Pt(8)

    info_items = [
        ("GitHub Repository", "https://github.com/nallapremteja04/resqagent"),
        ("Live Deployment", "http://localhost:8000 (Running on Uvicorn ASGI Server)"),
        ("API Documentation", "http://localhost:8000/docs (Interactive Swagger UI)"),
        ("Jury Evaluation Dossier", "http://localhost:8000/ResQAgent_Jury_Presentation_Dossier.pdf"),
        ("Student Team", "ResQAgent Development Team")
    ]

    for label, val in info_items:
        p = tf_inf.add_paragraph()
        p.text = f"• {label}:  {val}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(4)

    # Save presentation
    output_path = "ResQAgent_Hackathon_Presentation.pptx"
    prs.save(output_path)
    print(f"[SUCCESS] Presentation generated: {output_path}")

    # Also save to frontend for direct browser download
    frontend_output = os.path.join("frontend", "ResQAgent_Hackathon_Presentation.pptx")
    prs.save(frontend_output)
    print(f"[SUCCESS] Copied to frontend: {frontend_output}")

if __name__ == "__main__":
    create_presentation()
