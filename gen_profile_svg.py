#!/usr/bin/env python3
"""Generate the terminal-style GitHub profile SVG for jeojdi1.

Fetches real data (contribution calendar, recent events, languages) from the
GitHub API using GITHUB_TOKEN / GH_TOKEN, caches it in data.json, and falls
back to the cache when offline. Run in CI on a schedule to keep it live.
"""
import html, json, os, sys, urllib.request
from datetime import date, datetime, timedelta, timezone

LOGIN = "jeojdi1"
HERE = os.path.dirname(os.path.abspath(__file__)) or "."
CACHE = os.path.join(HERE, "data.json")

# ---------------------------------------------------------------- data fetch
def _req(url, data=None, headers=None):
    h = {"User-Agent": LOGIN, "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_data():
    # contribution calendar (GraphQL)
    q = """query($login:String!){ user(login:$login){
      contributionsCollection{ contributionCalendar{
        totalContributions weeks{ contributionDays{ date contributionCount contributionLevel } } } } } }"""
    gql = _req("https://api.github.com/graphql",
               data=json.dumps({"query": q, "variables": {"login": LOGIN}}).encode(),
               headers={"Content-Type": "application/json"})
    cal = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]

    # recent public events (last ~90 days, newest first)
    events = []
    for page in (1, 2, 3):
        batch = _req(f"https://api.github.com/users/{LOGIN}/events/public?per_page=100&page={page}")
        events += batch
        if len(batch) < 100:
            break

    # languages across non-fork repos
    repos = _req(f"https://api.github.com/users/{LOGIN}/repos?per_page=100")
    langs = {}
    for r in repos:
        if r.get("fork"):
            continue
        try:
            for lang, n in _req(r["languages_url"]).items():
                langs[lang] = langs.get(lang, 0) + n
        except Exception:
            pass

    data = {"fetched_at": datetime.now(timezone.utc).isoformat(),
            "calendar": cal, "events": events, "langs": langs}
    with open(CACHE, "w") as f:
        json.dump(data, f)
    return data

try:
    DATA = fetch_data()
except Exception as e:
    if not os.path.exists(CACHE):
        sys.exit(f"fetch failed and no cache: {e}")
    print(f"fetch failed ({e}); using cached data.json", file=sys.stderr)
    with open(CACHE) as f:
        DATA = json.load(f)

# ------------------------------------------------------------- derive stats
weeks = DATA["calendar"]["weeks"]
days = [d for w in weeks for d in w["contributionDays"]]
by_date = {d["date"]: d["contributionCount"] for d in days}
total_year = DATA["calendar"]["totalContributions"]
today = date.fromisoformat(days[-1]["date"])

def count_on(d):
    return by_date.get(d.isoformat(), 0)

# streak (today may still be 0 — start from yesterday then)
streak, d = 0, today
if count_on(d) == 0:
    d -= timedelta(days=1)
while count_on(d) > 0:
    streak += 1
    d -= timedelta(days=1)

week_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
week_counts = [(d.strftime("%a").lower(), count_on(d)) for d in week_days]
week_total = sum(c for _, c in week_counts)

month_cut = today - timedelta(days=29)
month_days = [d for d in days if date.fromisoformat(d["date"]) >= month_cut]
month_total = sum(d["contributionCount"] for d in month_days)
month_active = sum(1 for d in month_days if d["contributionCount"] > 0)

# events within past 30 days
cut_iso = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
recent = [e for e in DATA["events"] if e["created_at"] >= cut_iso]
commits = sum(e.get("payload", {}).get("size", 0) for e in recent if e["type"] == "PushEvent")
created_repos = sum(1 for e in recent
                    if e["type"] == "CreateEvent" and e.get("payload", {}).get("ref_type") == "repository")
prs = sum(1 for e in recent
          if e["type"] == "PullRequestEvent" and e.get("payload", {}).get("action") == "opened")
repo_hits = {}
for e in recent:
    name = e["repo"]["name"].split("/")[-1]
    repo_hits[name] = repo_hits.get(name, 0) + 1
top_repos = [n for n, _ in sorted(repo_hits.items(), key=lambda kv: -kv[1])[:3]]

# languages → short labels, top 3 + other
SHORT = {"Python": "py", "TypeScript": "ts", "JavaScript": "js", "C++": "c++",
         "HTML": "html", "CSS": "css", "Jupyter Notebook": "ipynb", "Shell": "sh"}
total_bytes = sum(DATA["langs"].values()) or 1
ranked = sorted(DATA["langs"].items(), key=lambda kv: -kv[1])
LANGS = [(SHORT.get(k, k.lower()), round(100 * v / total_bytes)) for k, v in ranked[:3]]
other = 100 - sum(p for _, p in LANGS)
if other > 0:
    LANGS.append(("other", other))

# ------------------------------------------------------------------- render
W = 830
PAD = 42
FONT = "'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#080c08"
TERM = "#0b120c"
BAR = "#101a11"
BORDER = "#1d2b1e"
GREEN = "#56e07a"
GREEN_HI = "#7dffa0"
DIM = "#4a6b4f"
MID = "#3fae5c"
LEVEL = {"NONE": "#15221a", "FIRST_QUARTILE": "#1d4d28", "SECOND_QUARTILE": "#2e7a3d",
         "THIRD_QUARTILE": "#41ab55", "FOURTH_QUARTILE": "#56e07a"}

LINE = 26
FS = 15
FS_BIG = 26

body = []
cy = 118

def esc(s):
    return html.escape(str(s), quote=True)

def tspan(s, fill=GREEN, weight="normal"):
    return f'<tspan fill="{fill}" font-weight="{weight}">{esc(s)}</tspan>'

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

# roles
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

# real contribution graph (full year, newest week rightmost)
prompt(f"gh contrib --graph   # {total_year} contributions in the last year")
gap(12)
cell, gutter = 10, 4
gx0, gy0 = PAD, cy
for c, w in enumerate(weeks):
    for r, dd in enumerate(w["contributionDays"]):
        x = gx0 + c * (cell + gutter)
        yy = gy0 + r * (cell + gutter)
        shade = LEVEL.get(dd["contributionLevel"], LEVEL["NONE"])
        body.append(f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="2" fill="{shade}"/>')
cy = gy0 + 7 * (cell + gutter) + 10

# past week
prompt("gh contrib --past-week")
gap(6)
maxc = max([c for _, c in week_counts] + [1])
bx = PAD
for label, c in week_counts:
    body.append(f'<text x="{bx}" y="{cy}" font-size="13" fill="{DIM}">{esc(label)}</text>')
    h = max(3, round(16 * c / maxc)) if c else 2
    fill = GREEN if c else "#15221a"
    body.append(f'<rect x="{bx + 36}" y="{cy - 4 - h}" width="14" height="{h}" rx="1.5" fill="{fill}"/>')
    body.append(f'<text x="{bx + 56}" y="{cy}" font-size="13" fill="{MID}">{c}</text>')
    bx += 96
cy += LINE
emit(PAD, tspan(f"{week_total} contributions in the last 7 days", GREEN_HI, "bold") + tspan(f" · streak: {streak}d", GREEN))

# past month highlights
prompt("gh highlights --past-month")
gap(6)
emit(PAD, tspan("★ ", MID) + tspan(f"{month_total} contributions", GREEN_HI, "bold") + tspan(f" across {month_active} active days", GREEN))
if commits:
    emit(PAD, tspan("★ ", MID) + tspan(f"{commits} commits pushed", GREEN_HI, "bold"))
if top_repos:
    emit(PAD, tspan("★ ", MID) + tspan("most active: ", GREEN) + tspan(" · ".join(top_repos), GREEN_HI, "bold"))
extras = []
if created_repos:
    extras.append(f"{created_repos} repos created")
if prs:
    extras.append(f"{prs} PRs opened")
if extras:
    emit(PAD, tspan("★ ", MID) + tspan(" · ".join(extras), GREEN))

# langs (real)
prompt("gh langs")
gap(8)
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
emit(PAD, tspan("yjames1103@gmail.com", GREEN) + tspan(f"   updated {today.strftime('%b %d')} · auto-refreshes every 6h", DIM))

# cursor
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
  <rect x="9" y="9" width="{W-18}" height="52" rx="13" fill="{BAR}"/>
  <rect x="9" y="40" width="{W-18}" height="22" fill="{BAR}"/>
  <line x1="9" y1="62" x2="{W-9}" y2="62" stroke="{BORDER}" stroke-width="1.5"/>
  <circle cx="40" cy="35" r="7" fill="#1e3322"/>
  <circle cx="64" cy="35" r="7" fill="#1e3322"/>
  <circle cx="88" cy="35" r="7" fill="#1e3322"/>
  <text x="{W-36}" y="41" font-size="14" fill="{DIM}" text-anchor="end">jeojdi1@github: ~</text>
  {chr(10).join(body)}
</svg>'''

out = os.path.join(HERE, "profile.svg")
with open(out, "w") as f:
    f.write(svg)
print(f"wrote {out}  ({W}x{H})  — {total_year} contribs/yr, streak {streak}d, week {week_total}, month {month_total}")
