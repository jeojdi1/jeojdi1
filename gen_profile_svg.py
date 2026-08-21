#!/usr/bin/env python3
"""Generate the terminal-style GitHub profile SVG for jeojdi1."""
import random, html

W = 830
PAD = 42
FONT = "'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#080c08"          # page behind terminal
TERM = "#0b120c"        # terminal body
BAR = "#101a11"         # title bar
BORDER = "#1d2b1e"
GREEN = "#56e07a"       # main bright green
GREEN_HI = "#7dffa0"    # headers / bold
DIM = "#4a6b4f"         # prompts / muted
MID = "#3fae5c"         # secondary green
CELL_SHADES = ["#12301a", "#1d4d28", "#2e7a3d", "#41ab55", "#56e07a"]

LINE = 26
FS = 15
FS_BIG = 26

random.seed(20260821)

parts = []
y = 0  # content cursor, set after title bar

def esc(s):
    return html.escape(s, quote=True)

def text(x, yy, s, fill=GREEN, size=FS, weight="normal", spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    parts.append(
        f'<text x="{x}" y="{yy}" font-size="{size}" fill="{fill}" font-weight="{weight}"{sp}>{s}</text>'
    )

def tspan(s, fill=GREEN, weight="normal"):
    return f'<tspan fill="{fill}" font-weight="{weight}">{esc(s)}</tspan>'

# ---------- build content ----------
body = []
cy = 118  # first baseline inside terminal

def emit(x, s_parts, size=FS, dy=LINE):
    global cy
    body.append(f'<text x="{x}" y="{cy}" font-size="{size}">{s_parts}</text>')
    cy += dy

def prompt(cmd):
    global cy
    cy += 10
    emit(PAD, tspan("$ ", DIM) + tspan(cmd, DIM))

def gap(px):
    global cy
    cy += px

# whoami
emit(PAD, tspan("$ whoami", DIM))
gap(10)
body.append(f'<text x="{PAD}" y="{cy}" font-size="{FS_BIG}" font-weight="bold" fill="{GREEN_HI}" letter-spacing="1">JAMES (XINDA) YANG</text>')
cy += 34
emit(PAD, tspan("@jeojdi1 · hackathon builder · agents / CV / quantum-curious", MID))
emit(PAD, tspan("building ", MID) + tspan("brevitassystems.com", GREEN_HI, "bold") + tspan(" · SF (Founders Inc.) × Toronto", MID))

# roles (founder)
prompt("gh roles --all")
gap(6)
emit(PAD, tspan("★ ", MID) + tspan("co-founder @ Brevitas Systems", GREEN_HI, "bold") + tspan(" — AI agent orchestration,", GREEN))
emit(PAD + 18, tspan("cutting multi-agent token costs · Founders Inc. Off Season, SF", GREEN))
emit(PAD, tspan("★ ", MID) + tspan("founding engineer @ Vivirion Solutions", GREEN_HI, "bold") + tspan(" — full-stack:", GREEN))
emit(PAD + 18, tspan("Vi-Learn · Vi-Connect · Vi-Nav (Dec 2025 – now)", GREEN))
emit(PAD, tspan("★ ", MID) + tspan("co-founder @ Caestus Labs", GREEN_HI, "bold") + tspan(" — VR haptic wearables (2026)", GREEN))
emit(PAD, tspan("★ ", MID) + tspan("incoming @ Laurier × Waterloo", GREEN_HI, "bold") + tspan(" — BBA + BMath double degree ('26)", GREEN))

# achievements
prompt("gh achievements --proud-of")
gap(6)
emit(PAD, tspan("★ ", MID) + tspan("4× hackathon winner", GREEN_HI, "bold") + tspan(" — slicefund · ferdinand · simteach ·", GREEN))
emit(PAD + 18, tspan("biobuddyai", GREEN))
emit(PAD, tspan("★ ", MID) + tspan("contributor @ LMCache", GREEN_HI, "bold") + tspan(" — open-source LLM serving (recent)", GREEN))
emit(PAD, tspan("★ ", MID) + tspan("12 hackathons · 11 projects shipped", GREEN_HI, "bold"))

# repos
prompt("gh repos --sort recent | head -9")
gap(6)
REPOS = [
    ("slicefund/",   ["agentic arbitrage across prediction", "markets [WIN]"]),
    ("ferdinand/",   ["voice → multi-step computer actions [WIN]"]),
    ("simteach/",    ["AI classroom scenarios for teachers [WIN]"]),
    ("biobuddyai/",  ["quantum + AI wildlife threat detection [WIN]"]),
    ("opendrone/",   ["indoor autonomous drone navigation"]),
    ("gpt-wrapper/", ["browser beat maker from everyday sounds"]),
    ("mcgestures/",  ["play Minecraft with hand gestures"]),
    ("autispark/",   ["AI literacy platform for autism"]),
    ("ureminders/",  ["location-aware adaptive to-do list"]),
]
COL2 = PAD + 210
for name, desc_lines in REPOS:
    first = True
    for d in desc_lines:
        win = "[WIN]" in d
        dtxt = d.replace(" [WIN]", "")
        spans = ""
        if first:
            spans += f'<tspan x="{PAD}" fill="{GREEN_HI}" font-weight="bold">{esc(name)}</tspan>'
        spans += f'<tspan x="{COL2}" fill="{MID}">{esc(dtxt)}</tspan>'
        if win:
            spans += tspan(" [WIN]", GREEN_HI, "bold")
        body.append(f'<text y="{cy}" font-size="{FS}">{spans}</text>')
        cy += LINE - 3
        first = False

# contrib graph
prompt("gh contrib --graph")
gap(12)
cell, gutter = 13, 4
cols, rows = 42, 7
gx0, gy0 = PAD, cy
for r in range(rows):
    for c in range(cols):
        v = random.random()
        if v < 0.18:
            continue
        shade = CELL_SHADES[min(int((v - 0.18) / 0.82 * len(CELL_SHADES)), len(CELL_SHADES) - 1)]
        x = gx0 + c * (cell + gutter)
        yy = gy0 + r * (cell + gutter)
        body.append(f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="2" fill="{shade}"/>')
cy = gy0 + rows * (cell + gutter) + 10

# langs
prompt("gh langs")
gap(8)
LANGS = [("py", 44), ("ts", 28), ("c++", 15), ("other", 13)]
bar_w, bar_h = 250, 12
for i in range(0, len(LANGS), 2):
    row = LANGS[i:i+2]
    for j, (lang, pct) in enumerate(row):
        lx = PAD + j * 380
        body.append(f'<text x="{lx}" y="{cy}" font-size="{FS}" fill="{GREEN_HI}" font-weight="bold">{esc(lang)}</text>')
        bx = lx + 62
        by = cy - bar_h + 1
        body.append(f'<rect x="{bx}" y="{by}" width="{bar_w}" height="{bar_h}" rx="2" fill="#14261a"/>')
        body.append(f'<rect x="{bx}" y="{by}" width="{bar_w*pct/100:.0f}" height="{bar_h}" rx="2" fill="{GREEN}"/>')
        body.append(f'<text x="{bx + bar_w + 12}" y="{cy}" font-size="{FS}" fill="{GREEN}">{pct}%</text>')
    cy += LINE

# info / stack
prompt("gh info --stack")
gap(6)
STACK = [
    ("langs",     "python · typescript · c++"),
    ("ml/agents", "pytorch · vllm · lmcache · opencv · whisper"),
    ("web",       "react · next.js · fastapi · supabase"),
    ("weird",     "qiskit · drones · VR haptics · smart contact lenses"),
]
for label, vals in STACK:
    body.append(
        f'<text y="{cy}" font-size="{FS}">'
        f'<tspan x="{PAD}" fill="{GREEN_HI}" font-weight="bold">{esc(label)}</tspan>'
        f'<tspan x="{PAD+150}" fill="{GREEN}">{esc(vals)}</tspan></text>'
    )
    cy += LINE - 3

# status
prompt("gh status")
gap(6)
emit(PAD, tspan("● ", MID) + tspan("building @ Founders Inc. Off Season — Fort Mason, SF", GREEN))
emit(PAD, tspan("● ", MID) + tspan("open to: ", GREEN) + tspan("design partners · hackathon teams · coffee chats", GREEN_HI, "bold"))

# ping
prompt("ping brevitassystems.com")
gap(6)
emit(PAD, tspan("64 bytes from brevitassystems.com: time=0.9 ms — ", GREEN) + tspan("always shipping", GREEN_HI, "bold"))

# footer
gap(14)
emit(PAD, tspan("github/jeojdi1  devpost/Jeojdi  in/yangjam  x/@jamyanges", GREEN_HI, "bold"))
emit(PAD, tspan("yjames1103@gmail.com", GREEN) + tspan("   streak: 23d", DIM))

# cursor line
gap(8)
body.append(f'<text x="{PAD}" y="{cy}" font-size="{FS}" fill="{DIM}">$ </text>')
body.append(
    f'<rect x="{PAD+20}" y="{cy-13}" width="9" height="17" fill="{GREEN}">'
    f'<animate attributeName="opacity" values="1;1;0;0" dur="1.2s" repeatCount="indefinite"/></rect>'
)
cy += 30

H = cy + 24

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect x="8" y="8" width="{W-16}" height="{H-16}" rx="14" fill="{TERM}" stroke="{BORDER}" stroke-width="1.5"/>
  <path d="M8 8 h{W-16} a14 14 0 0 1 0 0" fill="none"/>
  <rect x="9" y="9" width="{W-18}" height="52" rx="13" fill="{BAR}"/>
  <rect x="9" y="40" width="{W-18}" height="22" fill="{BAR}"/>
  <line x1="9" y1="62" x2="{W-9}" y2="62" stroke="{BORDER}" stroke-width="1.5"/>
  <circle cx="40" cy="35" r="7" fill="#1e3322"/>
  <circle cx="64" cy="35" r="7" fill="#1e3322"/>
  <circle cx="88" cy="35" r="7" fill="#1e3322"/>
  <text x="{W-36}" y="41" font-size="14" fill="{DIM}" text-anchor="end">jeojdi1@github: ~</text>
  {chr(10).join(body)}
</svg>'''

out = "profile.svg"
import os
if os.path.dirname(out): os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write(svg)
print(f"wrote {out}  ({W}x{H})")
