"""
FinShield AI — Manager Presentation Generator  (v2 — Document-Detail Edition)
Generates a dark-themed, Morph-transition PowerPoint deck.
Run:  python scripts/generate_ppt.py
Out:  FinShield_AI_Presentation.pptx  (project root)
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree
import os

# ── Palette ────────────────────────────────────────────────────────────────────
BG      = RGBColor(0x0A, 0x0A, 0x0F)
CARD    = RGBColor(0x11, 0x11, 0x18)
BORDER  = RGBColor(0x1E, 0x1E, 0x2E)
MUTED   = RGBColor(0x2A, 0x2A, 0x3A)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GRAY    = RGBColor(0x94, 0xA3, 0xB8)
DGRAY   = RGBColor(0x4B, 0x55, 0x63)
GREEN   = RGBColor(0x00, 0xFF, 0x87)
BLUE    = RGBColor(0x3B, 0x82, 0xF6)
PURPLE  = RGBColor(0x8B, 0x5C, 0xF6)
RED     = RGBColor(0xEF, 0x44, 0x44)
YELLOW  = RGBColor(0xF5, 0x9E, 0x0B)
TEAL    = RGBColor(0x06, 0xB6, 0xD4)
PINK    = RGBColor(0xEC, 0x48, 0x99)

W = Inches(13.33)
H = Inches(7.5)

# ── Core helpers ───────────────────────────────────────────────────────────────

def prs_new():
    p = Presentation()
    p.slide_width  = W
    p.slide_height = H
    return p

def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def bg(slide, c=BG):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = c

def rect(slide, l, t, w, h, fill=None, line=None, lw=0.75, name="r", radius=False):
    shp = slide.shapes.add_shape(
        5 if radius else 1,
        Inches(l), Inches(t), Inches(w), Inches(h))
    shp.name = name
    if radius: shp.adjustments[0] = 0.5
    sf = shp.fill
    if fill: sf.solid(); sf.fore_color.rgb = fill
    else: sf.background()
    lf = shp.line
    if line: lf.color.rgb = line; lf.width = Pt(lw)
    else: lf.fill.background()
    return shp

def txt(slide, text, l, t, w, h, sz=14, bold=False, col=WHITE,
        align=PP_ALIGN.LEFT, italic=False, name="t", wrap=True, spacing=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame; tf.word_wrap = wrap
    p = tf.paragraphs[0]; p.alignment = align
    if spacing:
        from pptx.util import Pt as PT
        p.space_after = PT(spacing)
    r = p.add_run(); r.text = text
    r.font.size = Pt(sz); r.font.bold = bold
    r.font.italic = italic; r.font.color.rgb = col
    return tb

def pill(slide, text, l, t, w, h, bg_c=BLUE, fg=WHITE, sz=11, name="p"):
    shp = rect(slide, l, t, w, h, fill=bg_c, name=name, radius=True)
    shp.adjustments[0] = 0.5
    tf = shp.text_frame; tf.word_wrap = False
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(sz); r.font.bold = True; r.font.color.rgb = fg
    return shp

def line(slide, l, t, w, col=GREEN, th=1.0):
    s = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Pt(th))
    s.fill.solid(); s.fill.fore_color.rgb = col
    s.line.fill.background()

def morph(slide):
    xml = (
        '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
        ' xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"'
        ' spd="med" advClick="1">'
        '<p14:morph xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"'
        ' option="byObject"/></p:transition>'
    )
    el = etree.fromstring(xml)
    sld = slide._element
    for ch in list(sld):
        if ch.tag.endswith("}transition"): sld.remove(ch)
    sld.append(el)

def section_header(slide, num, label, title, accent, sub=None):
    pill(slide, f"{num} / {label}", 0.5, 0.32, 1.9, 0.33,
         bg_c=MUTED, fg=accent, sz=11, name=f"pill_{num}")
    txt(slide, title, 0.5, 0.78, 11, 0.8, sz=38, bold=True, col=WHITE, name=f"hdr_{num}")
    line(slide, 0.5, 1.65, 3.2, col=accent)
    if sub:
        txt(slide, sub, 0.5, 1.72, 10, 0.45, sz=12, col=GRAY, name=f"sub_{num}")

def mono_badge(slide, text, l, t, w, h, col=GREEN, name="mb"):
    """Code-style monospace badge."""
    r = rect(slide, l, t, w, h, fill=RGBColor(0x0D,0x1F,0x12), name=f"{name}_bg")
    txt(slide, text, l+0.12, t+0.05, w-0.2, h-0.05,
        sz=10, col=col, italic=False, bold=False, name=name, wrap=False)
    return r

def row_divider(slide, t):
    line(slide, 0.5, t, 12.3, col=BORDER, th=0.4)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDES
# ═══════════════════════════════════════════════════════════════════════════════

# ── Slide 1 : Title ────────────────────────────────────────────────────────────
def s1_title(prs):
    s = blank(prs); bg(s)

    # decorative vertical bars
    for i, (x, c) in enumerate([(0.0, RGBColor(0x00,0x3A,0x1F)),
                                  (12.83, RGBColor(0x1A,0x10,0x40))]):
        rect(s, x, 0, 0.5, 7.5, fill=c, name=f"bar_{i}")

    pill(s, "INTERNAL · MANAGER PRESENTATION · 2026", 0.7, 0.42, 5.5, 0.33,
         bg_c=MUTED, fg=GRAY, sz=10, name="tag")

    txt(s, "FinShield AI", 0.7, 1.1, 10, 1.5,
        sz=74, bold=True, col=WHITE, name="title##01")
    line(s, 0.7, 2.72, 5.0, col=GREEN)

    txt(s, "Real-Time ML-Powered Fraud Detection\nfor Banks · Fintechs · Insurance · Payment Processors",
        0.7, 2.9, 10, 1.1, sz=22, col=GRAY, name="sub##01")

    # Three stat pills
    for i, (v, c) in enumerate([
        ("<100ms  scoring", BLUE),
        ("200+  ML features", PURPLE),
        ("20+  fraud rules", GREEN),
    ]):
        pill(s, v, 0.7 + i*3.3, 4.45, 2.9, 0.42,
             bg_c=c, fg=RGBColor(0x0A,0x0A,0x0F), sz=13, name=f"stat_{i}")

    txt(s, "backend/  ·  frontend/  ·  FastAPI + Next.js 16  ·  AWS ECS",
        0.7, 6.9, 9, 0.4, sz=10, col=DGRAY, name="foot")
    morph(s)

# ── Slide 2 : Need / Problem ───────────────────────────────────────────────────
def s2_need(prs):
    s = blank(prs); bg(s)
    section_header(s, "01", "NEED", "Why This Project Exists", RED)

    # Big numbers row
    for val, lbl, col, lx in [
        ("$485B",  "lost to fraud globally/yr",     RED,    0.5),
        ("72%",    "fraud undetected in real-time",  YELLOW, 4.7),
        ("<300ms", "window to block pre-settlement", BLUE,   8.9),
    ]:
        rect(s, lx, 2.05, 3.8, 1.8, fill=CARD, line=col, lw=1.2, name=f"stat_{lx}")
        rect(s, lx, 2.05, 3.8, 0.06, fill=col, name=f"sbar_{lx}")
        txt(s, val, lx+0.2, 2.2, 3.4, 0.85, sz=44, bold=True, col=col, name=f"sv_{lx}")
        txt(s, lbl, lx+0.2, 3.05, 3.4, 0.65, sz=12, col=GRAY, name=f"sl_{lx}")

    # Pain points
    pains = [
        ("Rule-based systems miss novel fraud patterns — attackers adapt in days"),
        ("Batch scoring detects fraud hours after money has already moved"),
        ("Building in-house ML fraud stack costs Rs.5Cr+ and 18+ months"),
        ("No single SaaS covers Banks, Fintechs, Insurance and Payment Processors"),
    ]
    for i, p in enumerate(pains):
        y = 4.1 + i*0.62
        rect(s, 0.5, y, 12.3, 0.5, fill=CARD, name=f"pain_bg_{i}")
        txt(s, "x", 0.65, y+0.1, 0.3, 0.35, sz=11, bold=True, col=RED, name=f"px_{i}")
        txt(s, p, 1.0, y+0.08, 11.4, 0.38, sz=12, col=GRAY, name=f"pt_{i}")
    morph(s)

# ── Slide 3 : Users ────────────────────────────────────────────────────────────
def s3_users(prs):
    s = blank(prs); bg(s)
    section_header(s, "02", "USERS", "Who Is It Built For?", BLUE)

    users = [
        ("Bank / Credit Union",    "Card-not-present fraud\nAccount takeovers\nImpossible travel",   BLUE,   0.4, 2.0),
        ("Fintech Startup",        "Add ML fraud detection\nwith zero infra cost\nFree plan to start", GREEN,  3.5, 2.0),
        ("Insurance Company",      "Claim fraud via spending\npattern change detection\nBatch + real-time", PURPLE, 6.6, 2.0),
        ("Payment Processor",      "Screen before settlement\n<100ms per transaction\nWebhook + Kafka feed", YELLOW, 9.7, 2.0),
    ]
    for label, body, col, l, t in users:
        rect(s, l, t, 3.0, 5.2, fill=CARD, line=BORDER, name=f"u_{l}")
        rect(s, l, t, 3.0, 0.06, fill=col, name=f"ua_{l}")
        txt(s, label, l+0.15, t+0.2, 2.7, 0.55,
            sz=15, bold=True, col=col, name=f"ul_{l}")
        line(s, l+0.15, t+0.82, 2.7, col=MUTED, th=0.4)
        txt(s, body, l+0.15, t+1.0, 2.7, 3.8,
            sz=12, col=GRAY, name=f"ub_{l}")

        # Subscription plan badge
        plan = "Free / Pro / Adv" if l == 0.4 else ("Pro / Adv" if l in [3.5, 6.6] else "All Plans")
        pill(s, plan, l+0.15, t+4.6, 2.7, 0.34,
             bg_c=MUTED, fg=col, sz=10, name=f"uplan_{l}")
    morph(s)

# ── Slide 4 : Tech Stack ───────────────────────────────────────────────────────
def s4_stack(prs):
    s = blank(prs); bg(s)
    section_header(s, "03", "TECH STACK", "Components Used to Build This", PURPLE,
                   sub="Every layer maps to a real directory in the repository")

    rows = [
        # Layer, colour, Component, Path
        ("FRONTEND",   BLUE,   "Next.js 16 · TypeScript · Tailwind 4 · Zustand · Framer Motion · Recharts · shadcn/ui",
                                "frontend/app/  ·  frontend/components/  ·  frontend/.env.local"),
        ("BACKEND",    GREEN,  "FastAPI (Python 3.12) · SQLAlchemy 2.0 async · Pydantic v2 · python-jose JWT · passlib bcrypt",
                                "backend/app/api/v1/  ·  backend/app/services/  ·  backend/app/config.py"),
        ("ML ENGINE",  PURPLE, "Isolation Forest · XGBoost · Random Forest · LightGBM · SHAP explainability · ONNX runtime",
                                "backend/app/ml/  ·  backend/app/ml/models/  ·  backend/app/ml/pipeline.py"),
        ("DATABASE",   TEAL,   "Supabase (PostgreSQL) primary  ·  SQLite for local dev  ·  Redis for cache & sessions",
                                "backend/app/db/session.py  ·  backend/app/db/migrations/versions/"),
        ("STREAMING",  YELLOW, "WebSocket manager (Socket.IO-style)  ·  Celery task queue  ·  Redis broker",
                                "backend/app/streaming/websocket_manager.py  ·  backend/app/services/"),
        ("INFRA / CI", RED,    "AWS ECS Fargate · ECR · RDS · ElastiCache · ALB  ·  GitHub Actions CI/CD · Docker",
                                ".github/workflows/ci.yml  ·  .github/workflows/cd-staging.yml  ·  infrastructure/"),
    ]

    for i, (layer, col, comp, path) in enumerate(rows):
        y = 2.05 + i * 0.88
        rect(s, 0.5, y, 12.3, 0.8, fill=CARD, name=f"row_{i}")
        # colour left stripe
        rect(s, 0.5, y, 0.06, 0.8, fill=col, name=f"stripe_{i}")
        pill(s, layer, 0.65, y+0.21, 1.6, 0.34, bg_c=col,
             fg=RGBColor(0x0A,0x0A,0x0F), sz=10, name=f"layer_{i}")
        txt(s, comp, 2.45, y+0.08, 9.9, 0.42, sz=11, col=WHITE, name=f"comp_{i}")
        txt(s, path, 2.45, y+0.5,  9.9, 0.32, sz=9.5, col=GRAY,
            italic=True, name=f"path_{i}")
        if i < len(rows)-1: row_divider(s, y+0.82)
    morph(s)

# ── Slide 5a : Database Connectors ────────────────────────────────────────────
def s5_apikeys(prs):
    """Split into TWO slides — databases first, then alert services."""
    _s5a_databases(prs)
    _s5b_alerts(prs)


def _db_row(slide, i, logo, name, conn_var, example, col, y):
    """Render one database connector row."""
    row_bg = CARD if i % 2 == 0 else RGBColor(0x0F, 0x0F, 0x18)
    rect(slide, 0.4, y, 12.5, 0.72, fill=row_bg, name=f"drow_{i}")
    rect(slide, 0.4, y, 0.07, 0.72, fill=col,    name=f"dstripe_{i}")

    # Logo pill
    pill(slide, logo, 0.56, y+0.18, 1.55, 0.32,
         bg_c=col, fg=RGBColor(0x0A,0x0A,0x0F), sz=10, name=f"dlogo_{i}")

    # DB name
    txt(slide, name, 2.22, y+0.08, 2.5, 0.32, sz=13, bold=True, col=WHITE,
        name=f"dname_{i}")

    # ENV var badge
    rect(slide, 2.22, y+0.41, 2.5, 0.24, fill=RGBColor(0x06,0x18,0x10),
         name=f"denv_bg_{i}")
    txt(slide, conn_var, 2.3, y+0.43, 2.4, 0.22,
        sz=8.5, col=GREEN, wrap=False, name=f"denv_{i}")

    # Example connection string
    rect(slide, 4.9, y+0.06, 8.0, 0.58, fill=RGBColor(0x08,0x08,0x14),
         line=BORDER, lw=0.5, name=f"dex_bg_{i}")
    txt(slide, example, 5.05, y+0.13, 7.7, 0.4, sz=9, col=TEAL,
        wrap=False, name=f"dex_{i}")


def _s5a_databases(prs):
    s = blank(prs); bg(s)
    section_header(s, "04a", "DATABASES",
                   "Databases You Can Connect",
                   TEAL,
                   sub="Set  DATABASE_URL  in  backend/.env  — SQLAlchemy handles the rest  |  No code change needed to switch DB")

    # Column headers
    rect(s, 0.4, 2.0, 12.5, 0.36, fill=MUTED, name="dbhdr")
    for lx, label, w in [(0.56,"CONNECTOR",1.55),(2.22,"DATABASE",2.5),(4.9,"CONNECTION STRING / ENV KEY",8.0)]:
        txt(s, label, lx, 2.05, w, 0.26, sz=9, bold=True, col=GRAY, name=f"dhdr_{lx}")

    dbs = [
        # logo-label,  display name,         ENV key shown,          example string,                   colour
        ("Supabase",   "Supabase (PostgreSQL)","SUPABASE_URL + KEYS",
         "SUPABASE_URL=https://xyz.supabase.co  |  SUPABASE_ANON_KEY=eyJ...  |  SUPABASE_SERVICE_KEY=eyJ...",
         TEAL),
        ("PostgreSQL", "PostgreSQL (Generic)", "DATABASE_URL",
         "DATABASE_URL=postgresql+asyncpg://user:password@host:5432/finshield_db",
         BLUE),
        ("MySQL",      "MySQL / MariaDB",      "DATABASE_URL",
         "DATABASE_URL=mysql+aiomysql://user:password@host:3306/finshield_db",
         RGBColor(0xF2,0x9E,0x11)),
        ("MongoDB",    "MongoDB (transactions)","DATABASE_URL",
         "DATABASE_URL=mongodb+srv://user:password@cluster.mongodb.net/finshield",
         GREEN),
        ("MS SQL",     "MS SQL Server",        "DATABASE_URL",
         "DATABASE_URL=mssql+aioodbc://user:password@host/finshield?driver=ODBC+Driver+18",
         RGBColor(0xCC,0x44,0x00)),
        ("SQLite",     "SQLite (local dev)",   "DATABASE_URL",
         "DATABASE_URL=sqlite+aiosqlite:///./finshield_dev.db  (default — zero config)",
         DGRAY),
        ("Redis",      "Redis (cache + WS)",   "REDIS_URL",
         "REDIS_URL=redis://localhost:6379/0  |  or  rediss://user:pass@host:6380/0  (TLS)",
         RED),
    ]

    for i, (logo, name, env_k, example, col) in enumerate(dbs):
        _db_row(s, i, logo, name, env_k, example, col, 2.4 + i * 0.74)

    morph(s)


def _alert_row(slide, i, icon, service, env_vars, channel, trigger, col, y):
    """Render one alert-service row."""
    row_bg = CARD if i % 2 == 0 else RGBColor(0x0F, 0x0F, 0x18)
    rect(slide, 0.4, y, 12.5, 0.76, fill=row_bg, name=f"arow_{i}")
    rect(slide, 0.4, y, 0.07, 0.76, fill=col,    name=f"astripe_{i}")

    # Icon + service name
    txt(slide,  icon,    0.58, y+0.18, 0.5,  0.45, sz=20, name=f"aicon_{i}")
    txt(slide,  service, 1.2,  y+0.06, 2.4,  0.38, sz=13, bold=True, col=WHITE,  name=f"asvc_{i}")
    txt(slide,  channel, 1.2,  y+0.44, 2.4,  0.28, sz=10, col=col,   italic=True, name=f"achan_{i}")

    # ENV vars block
    rect(slide, 3.75, y+0.08, 4.2, 0.58, fill=RGBColor(0x06,0x12,0x06),
         line=RGBColor(0x00,0x40,0x20), lw=0.5, name=f"aenv_bg_{i}")
    txt(slide, env_vars, 3.9, y+0.13, 3.95, 0.5,
        sz=8.5, col=GREEN, wrap=True, name=f"aenv_{i}")

    # Trigger/when
    txt(slide, trigger, 8.1, y+0.1, 4.7, 0.55,
        sz=10, col=GRAY, name=f"atrig_{i}")


def _s5b_alerts(prs):
    s = blank(prs); bg(s)
    section_header(s, "04b", "ALERT SERVICES",
                   "Alert & Notification Services",
                   RED,
                   sub="All channels are optional — platform degrades gracefully with no keys set  |  backend/app/services/notification_service.py")

    # Column headers
    rect(s, 0.4, 2.0, 12.5, 0.36, fill=MUTED, name="ahdr_bg")
    for lx, label, w in [(0.58,"SERVICE / CHANNEL",3.0),
                          (3.75,"ENV VARIABLES  (backend/.env)",4.2),
                          (8.1,"WHEN IT FIRES",4.7)]:
        txt(s, label, lx, 2.05, w, 0.26, sz=9, bold=True, col=GRAY, name=f"ahdr_{lx}")

    alerts = [
        # icon, service,        env_vars,                          channel,    trigger,                                col
        ("📧", "Resend.com",
         "RESEND_API_KEY=re_xxxx\nEMAIL_FROM=noreply@finshield.ai",
         "Email  (Primary)",
         "fraud_score >= 0.30 · Any FLAG / ALERT / BLOCK\nSent to customer + ALERT_COMPANY_EMAIL\n3,000 free emails/month",
         GREEN),

        ("📧", "Brevo",
         "BREVO_API_KEY=xkeysib-xxxx",
         "Email  (Fallback)",
         "Auto-used when RESEND_API_KEY is empty\nSame triggers as Resend\nFree tier: 300 emails/day",
         RGBColor(0x0C,0xCA,0x8A)),

        ("📱", "Twilio SMS",
         "TWILIO_ACCOUNT_SID=ACxxxx\nTWILIO_AUTH_TOKEN=xxxx\nTWILIO_FROM_NUMBER=+1XXXXXXXXXX",
         "SMS  (Pro+ plan only)",
         "fraud_score >= 0.60 · HIGH or CRITICAL only\nCustomer phone  +  analyst on-call\n~Rs. 0.10 per SMS India",
         RED),

        ("🔔", "In-App WebSocket",
         "No key needed — always active\n(built into WebSocket manager)",
         "Real-time push  (all plans)",
         "Every scored transaction broadcast live\nws://host/ws/{tenant_id}\nDashboard alert queue auto-updates",
         BLUE),

        ("🪝", "Outbound Webhook",
         "Configured via  /api/v1/settings\nStored encrypted in tenant_credentials",
         "HTTP POST  (Pro+)",
         "POST to your URL on fraud_alert_created\nHMAC-SHA256 signed payload\nRetry with exponential backoff on failure",
         YELLOW),

        ("💬", "Slack Webhook",
         "Configured via  /api/v1/settings\nSlack Incoming Webhook URL",
         "Slack  (Pro+)",
         "Critical fraud alerts to analyst channel\nRich message with score + SHAP top features\nFree via Slack Apps",
         PURPLE),
    ]

    for i, (icon, svc, env_v, channel, trigger, col) in enumerate(alerts):
        _alert_row(s, i, icon, svc, env_v, channel, trigger, col, 2.42 + i * 0.83)

    # Graceful degradation note
    rect(s, 0.4, 7.15, 12.5, 0.28, fill=RGBColor(0x0A,0x1A,0x0A), name="degrade_bg")
    txt(s, "No keys configured?  Platform falls back to in-app WebSocket notifications only — zero downtime, zero config required.",
        0.6, 7.18, 12.1, 0.24, sz=9.5, col=GREEN, bold=True, name="degrade_note")

    morph(s)

# ── Slide 6 : ML Engine deep-dive ─────────────────────────────────────────────
def s6_ml(prs):
    s = blank(prs); bg(s)
    section_header(s, "05", "ML ENGINE", "Fraud Detection Pipeline", PURPLE,
                   sub="backend/app/ml/  ·  models trained on 10,000 sample transactions (3% fraud rate)")

    # Pipeline boxes
    steps = [
        ("1\nData In",      "20+ connectors\nKafka · CSV · Supabase\nWebhook",               BLUE),
        ("2\nFeatures",     "200+ engineered\nVelocity · Geo · Device\nBehavioural · Amount", TEAL),
        ("3\nUnsupervised", "Isolation Forest\nDBSCAN clustering\nAnomaly score",              PURPLE),
        ("4\nSupervised",   "XGBoost (primary)\nRandom Forest\nLightGBM",                     GREEN),
        ("5\nEnsemble",     "Weighted combiner\nCalibrated 0.0-1.0\nSHAP explainability",      YELLOW),
        ("6\nDecision",     "<0.30 PASS\n0.30-0.79 FLAG/ALERT\n>=0.80 BLOCK",                 RED),
    ]
    for i, (step, desc, col) in enumerate(steps):
        l = 0.4 + i * 2.16
        rect(s, l, 2.05, 2.0, 2.4, fill=CARD, line=col, lw=1.2, name=f"pipe_{i}")
        rect(s, l, 2.05, 2.0, 0.05, fill=col, name=f"pbar_{i}")
        txt(s, step, l+0.15, 2.15, 1.7, 0.65, sz=13, bold=True, col=col, name=f"pstep_{i}")
        txt(s, desc, l+0.15, 2.85, 1.7, 1.5, sz=10, col=GRAY, name=f"pdesc_{i}")
        if i < 5:
            txt(s, "->", l+1.96, 3.05, 0.3, 0.4, sz=14, col=DGRAY, name=f"arr_{i}")

    # Trained model artifacts
    txt(s, "Trained model artifacts  ( backend/app/ml/models/ )", 0.5, 4.65, 8, 0.38,
        sz=12, bold=True, col=WHITE, name="artifacts_hdr")
    line(s, 0.5, 5.05, 7, col=PURPLE, th=0.4)

    artifacts = [
        ("anomaly_detector_v1.pkl",    "Isolation Forest — unsupervised outlier detection"),
        ("fraud_classifier_v1.pkl",    "XGBoost primary classifier"),
        ("ensemble_scorer_v1.pkl",     "Weighted ensemble combiner"),
        ("shap_explainer_v1.pkl",      "SHAP TreeExplainer for feature attribution"),
        ("feature_names_v1.json",      "Feature list for pipeline consistency"),
        ("evaluation_report.json",     "Precision · Recall · AUC-ROC metrics"),
    ]
    for i, (fname, desc) in enumerate(artifacts):
        col_idx = i % 2
        lx = 0.5 if col_idx == 0 else 6.7
        y  = 5.12 + (i // 2) * 0.7
        mono_badge(s, fname, lx, y, 3.2, 0.38, col=GREEN, name=f"art_{i}")
        txt(s, desc, lx+3.35, y+0.05, 3.1, 0.35, sz=10, col=GRAY, name=f"adesc_{i}")
    morph(s)

# ── Slide 7 : Project View ─────────────────────────────────────────────────────
def s7_project(prs):
    s = blank(prs); bg(s)
    section_header(s, "06", "PROJECT VIEW", "Directory Map & Key Files", GREEN,
                   sub="Monorepo  ·  backend/ (FastAPI)  ·  frontend/ (Next.js 16)  ·  infrastructure/ (AWS CDK)")

    # Directory tree left panel
    rect(s, 0.4, 2.0, 5.5, 5.2, fill=CARD, name="tree_bg")
    rect(s, 0.4, 2.0, 5.5, 0.38, fill=MUTED, name="tree_hdr")
    txt(s, "  REPOSITORY STRUCTURE", 0.55, 2.05, 5.2, 0.3, sz=10, bold=True, col=GREEN)

    tree = [
        ("AI-Financial-Intelligence-Fraud/",   WHITE,  0),
        ("  backend/",                          BLUE,   1),
        ("    app/api/v1/          <- REST endpoints",  GRAY, 2),
        ("    app/ml/              <- ML pipeline",     GRAY, 2),
        ("    app/models/          <- SQLAlchemy ORM",  GRAY, 2),
        ("    app/services/        <- business logic",  GRAY, 2),
        ("    app/config.py        <- all settings",    GREEN,2),
        ("    scripts/seed_data.py  train_models.py",   GRAY, 2),
        ("    .env                 <- API keys here",   YELLOW,2),
        ("  frontend/",                         PURPLE, 1),
        ("    app/(dashboard)/     <- dashboard UI",    GRAY, 2),
        ("    app/landing/         <- marketing page",  GRAY, 2),
        ("    .env.local           <- FE config",       YELLOW,2),
        ("  .github/workflows/     <- CI/CD",           TEAL,  1),
        ("  infrastructure/        <- AWS CDK/TF",      RED,   1),
    ]
    for i, (line_txt, col, _) in enumerate(tree):
        txt(s, line_txt, 0.55, 2.48 + i*0.31, 5.1, 0.3,
            sz=9, col=col, wrap=False, name=f"tree_{i}")

    # Right panel — key API routes
    rect(s, 6.2, 2.0, 6.6, 2.5, fill=CARD, name="api_bg")
    rect(s, 6.2, 2.0, 6.6, 0.38, fill=MUTED, name="api_hdr")
    txt(s, "  KEY API ENDPOINTS  (port 8003)", 6.35, 2.05, 6.3, 0.3,
        sz=10, bold=True, col=BLUE)

    endpoints = [
        ("POST", "/api/v1/auth/signup",        "Register institution"),
        ("POST", "/api/v1/auth/login",         "JWT tokens"),
        ("POST", "/api/v1/transactions",       "Score + ingest"),
        ("POST", "/api/v1/transactions/test",  "Test transaction"),
        ("GET",  "/api/v1/fraud-alerts",       "Alert queue"),
        ("GET",  "/api/v1/analytics/overview", "KPI data"),
        ("POST", "/api/v1/models/retrain",     "Trigger retraining"),
    ]
    for i, (method, path, desc) in enumerate(endpoints):
        y = 2.5 + i * 0.28
        mcol = GREEN if method=="GET" else YELLOW
        pill(s, method, 6.25, y, 0.75, 0.23, bg_c=MUTED, fg=mcol, sz=8, name=f"ep_m_{i}")
        txt(s, path, 7.08, y+0.02, 3.0, 0.24, sz=9, col=WHITE, wrap=False, name=f"ep_path_{i}")
        txt(s, desc, 10.15, y+0.02, 2.5, 0.24, sz=9, col=GRAY, name=f"ep_desc_{i}")

    # WebSocket + Docs
    rect(s, 6.2, 4.6, 6.6, 0.55, fill=CARD, line=TEAL, lw=0.8, name="ws_bg")
    txt(s, "WebSocket:  ws://localhost:8003/ws/{tenant_id}", 6.35, 4.68, 6.3, 0.3,
        sz=10, col=TEAL, name="ws_txt")
    txt(s, "Swagger UI:  http://localhost:8003/docs", 6.35, 4.95, 6.3, 0.25,
        sz=10, col=GRAY, name="docs_txt")

    # Bottom: default test credentials
    rect(s, 6.2, 5.25, 6.6, 1.75, fill=CARD, name="cred_bg")
    rect(s, 6.2, 5.25, 6.6, 0.35, fill=MUTED, name="cred_hdr")
    txt(s, "  DEFAULT TEST CREDENTIALS  (seed_data.py)", 6.35, 5.3, 6.3, 0.28,
        sz=9.5, bold=True, col=YELLOW)
    creds = [
        ("Admin",   "admin@finshield.local",   "Admin123!@#"),
        ("Analyst", "analyst@finshield.local", "Analyst123!@#"),
    ]
    for i, (role, email, pwd) in enumerate(creds):
        y = 5.68 + i * 0.56
        pill(s, role, 6.25, y, 1.0, 0.3, bg_c=MUTED, fg=YELLOW, sz=9, name=f"cr_{i}")
        mono_badge(s, email, 7.35, y, 2.7, 0.3, col=GREEN, name=f"cemail_{i}")
        mono_badge(s, pwd, 10.1, y, 2.5, 0.3, col=GRAY, name=f"cpwd_{i}")
    morph(s)

# ── Slide 8 : Future ───────────────────────────────────────────────────────────
def s8_future(prs):
    s = blank(prs); bg(s)
    section_header(s, "07", "FUTURE", "Growth Opportunities", YELLOW)

    opps = [
        ("Cross-Institution\nFraud Network",
         "Federated ML — share anonymised fraud signals across institutions.\nCatch fraud rings that span multiple banks without sharing PII.",
         BLUE,   0.4,  2.1, 5.9),
        ("Mobile SDK &\nEmbedded API",
         "Drop-in iOS/Android SDK — device fingerprinting, behavioural\nbiometrics and real-time scoring directly in the client app.",
         PURPLE, 7.0,  2.1, 5.9),
        ("Gen-AI Case\nSummaries",
         "LLM-powered auto-generated investigation reports.\nSummarise fraud evidence and suggest resolution in plain language.",
         GREEN,  0.4,  4.8, 5.9),
        ("Regulatory\nAuto-Reporting",
         "One-click SAR generation (RBI, FinCEN, EU directives).\nReduces compliance documentation overhead by ~80%.",
         YELLOW, 7.0,  4.8, 5.9),
    ]
    for title, body, col, l, t, w in opps:
        rect(s, l, t, w, 2.35, fill=CARD, line=BORDER, name=f"op_{l}")
        rect(s, l, t, w, 0.06, fill=col, name=f"opb_{l}")
        txt(s, title, l+0.2, t+0.18, 5.5, 0.75, sz=16, bold=True, col=col, name=f"opt_{l}")
        line(s, l+0.2, t+1.0, w-0.4, col=MUTED, th=0.4)
        txt(s, body, l+0.2, t+1.1, w-0.4, 1.1, sz=11, col=GRAY, name=f"opd_{l}")
    morph(s)

# ── Slide 9 : Demo ─────────────────────────────────────────────────────────────
def s9_demo(prs):
    s = blank(prs); bg(s)

    for r, col in [(7, RGBColor(0x00,0x18,0x0D)), (4.5, RGBColor(0x08,0x08,0x20))]:
        c = s.shapes.add_shape(9, Inches(13.33/2-r/2), Inches(7.5/2-r/2),
                                Inches(r), Inches(r))
        c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background()

    txt(s, "Live Demo", 0.5, 2.5, 12.33, 1.2,
        sz=62, bold=True, col=WHITE, align=PP_ALIGN.CENTER, name="demo##09")
    line(s, 3.8, 3.8, 5.7, col=GREEN)
    txt(s, "Walk-through  ·  FinShield AI  ·  End-to-End",
        0.5, 3.95, 12.33, 0.55, sz=18, col=GRAY,
        align=PP_ALIGN.CENTER, name="demo_sub##09")

    steps = ["Sign Up &\nChoose Plan", "Connect\nDatabase", "Score a\nTransaction",
             "Review\nAlerts", "Test Me\nTab", "Model\nMetrics"]
    for i, step in enumerate(steps):
        l = 0.6 + i*2.15
        pill(s, f"{i+1}", l+0.75, 4.9, 0.5, 0.38,
             bg_c=GREEN, fg=RGBColor(0x0A,0x0A,0x0F), sz=14, name=f"num_{i}")
        txt(s, step, l+0.05, 5.38, 2.05, 0.65, sz=10, col=GRAY,
            align=PP_ALIGN.CENTER, name=f"step_{i}")

    txt(s, "Thank you  ·  Questions welcome",
        0.5, 7.0, 12.33, 0.4, sz=12, col=DGRAY,
        align=PP_ALIGN.CENTER, name="thanks")
    morph(s)

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    prs = prs_new()
    s1_title(prs)
    s2_need(prs)
    s3_users(prs)
    s4_stack(prs)
    s5_apikeys(prs)
    s6_ml(prs)
    s7_project(prs)
    s8_future(prs)
    s9_demo(prs)

    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "FinShield_AI_Presentation_v3.pptx"
    )
    prs.save(out)
    print(f"[OK] Saved -> {out}")
    print(f"     {len(prs.slides)} slides  |  16:9 widescreen  |  Morph on every slide")

if __name__ == "__main__":
    main()
