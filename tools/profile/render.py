"""Renders the profile README's SVG slices into assets/ using the Rosé Pine theme.

Every slice is part of one continuous console frame. Run fetch.py first to refresh
data/*.json; this script only reads those files and draws.

Every slice is W=880 wide, a multiple of 40px tall (so the grid lines up across slices),
and draws the same side rails; only the first slice has the top edge and title bar,
only the last one closes the frame.
"""
import base64
import datetime
import hashlib
import html
import io
import json
import math
import pathlib
import re
import textwrap

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = HERE / "data"
OUT = ROOT / "assets"
FONT_DIR = HERE / "fonts"

# Rosé Pine Palette
BASE = "#191724"          # Base void
SURFACE = "#1f1d2e"       # Card / tile fill
OVERLAY = "#26233a"       # Borders & higher elevation
MUTED = "#6e6a86"         # Dim labels
SUBTLE = "#908caa"        # Medium contrast
TEXT = "#e0def4"          # Body text
FOAM = "#9ccfd8"          # Cool aqua / primary rails & glow
IRIS = "#c4a7e7"          # Lavender / secondary accents
PINE = "#31748f"          # Deep teal
PINE_BRIGHT = "#56949f"   # Vibrant teal / success
GOLD = "#f6c177"          # Amber / stars / highlight
ROSE = "#ebbcba"          # Soft rose
LOVE = "#eb6f92"          # Coral / glitch / alert

W, M = 880, 16            # slice width, transparent side margin
FL, FR = M, W - M         # frame left (16) / right (864)
X = 52                    # content left edge
e = html.escape


def visible(markup):
    """The characters a piece of SVG markup actually displays (so the font subset never misses one)."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def faces(text, weights=(400, 700)):
    text += "0123456789"
    out = []
    for w in weights:
        f = TTFont(FONT_DIR / f"jetbrains-mono-latin-{w}-normal.woff2", recalcTimestamp=False)
        o = subset.Options()
        o.flavor = "woff2"
        o.layout_features = []
        s = subset.Subsetter(o)
        s.populate(text=text)
        s.subset(f)
        b = io.BytesIO()
        f.flavor = "woff2"
        f.save(b)
        out.append(
            f"@font-face{{font-family:'JBM';font-weight:{w};src:url(data:font/woff2;base64,"
            f"{base64.b64encode(b.getvalue()).decode()}) format('woff2')}}"
        )
    return "".join(out)


BASE_CSS = f"""text{{font-family:'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:15px}}
.dim{{fill:{SUBTLE}}}.fm{{fill:{FOAM}}}.ir{{fill:{IRIS}}}.fg{{fill:{TEXT}}}.gr{{fill:{PINE_BRIGHT}}}.gd{{fill:{GOLD}}}.lv{{fill:{LOVE}}}.wh{{fill:#f5f4fd}}
@keyframes fadein{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:none}}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.ln{{animation:fadein .35s ease-out both}}
.cursor{{animation:blink 1.05s step-end infinite}}
.dot{{animation:pulse 2s ease-in-out infinite}}"""

DEFS = f"""<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{FOAM}" stroke-opacity=".06"/></pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>"""


def slice_svg(h, body, *, title, desc, text, top=False, bottom=False, css="", defs="", weights=(400, 700)):
    assert h % 40 == 0, f"height {h} not divisible by 40"
    y0 = M if top else 0
    y1 = h - M if bottom else h
    rails = f"M{FL} {y0}V{y1}M{FR} {y0}V{y1}"
    if top:
        rails += f"M{FL} {y0}H{FR}"
    if bottom:
        rails += f"M{FL} {y1}H{FR}"
    gy0 = y0 if top else -40
    gy1 = y1 if bottom else h + 40
    glow = f"M{FL} {gy0}V{gy1}M{FR} {gy0}V{gy1}" + (f"M{FL} {y0}H{FR}" if top else "") + (f"M{FL} {y1}H{FR}" if bottom else "")
    corners = ""
    if top:
        corners += f'<path d="M{FL-7} {y0+18}V{y0-7}H{FL+18}"/><path d="M{FR-18} {y0-7}H{FR+7}V{y0+18}"/>'
    if bottom:
        corners += f'<path d="M{FL-7} {y1-18}V{y1+7}H{FL+18}"/><path d="M{FR-18} {y1+7}H{FR+7}V{y1-18}"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-labelledby="t d">
<title id="t">{e(title)}</title>
<desc id="d">{e(desc)}</desc>
<style>
{faces(text + visible(body), weights)}
{BASE_CSS}
{css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
{DEFS}
{defs}
</defs>
<path d="{glow}" fill="none" stroke="{FOAM}" stroke-width="3" opacity=".45" filter="url(#glow)"/>
<rect x="{FL}" y="{y0}" width="{FR-FL}" height="{y1-y0}" fill="{BASE}"/>
<rect x="{FL}" y="{y0}" width="{FR-FL}" height="{y1-y0}" fill="url(#grid)"/>
{body}
<path d="{rails}" fill="none" stroke="{FOAM}" stroke-width="1.2"/>
<g fill="none" stroke="{FOAM}" stroke-width="2">{corners}</g>
</svg>
'''


def heading(y, name, counter):
    return f'''<text x="{X}" y="{y}" font-weight="700" fill="{FOAM}" filter="url(#g)" opacity=".7" style="font-size:20px">~/</text>
<text x="{X}" y="{y}" font-weight="700" style="font-size:20px"><tspan class="fm">~/</tspan><tspan class="wh">{e(name)}</tspan></text>
<text x="{FR-36}" y="{y}" text-anchor="end" letter-spacing="2" fill="{MUTED}" style="font-size:12px">{e(counter)}</text>
<line x1="{X}" y1="{y+14}" x2="{FR-36}" y2="{y+14}" stroke="{FOAM}" stroke-opacity=".3"/>
<line x1="{X}" y1="{y+14}" x2="{X+120}" y2="{y+14}" stroke="{FOAM}" stroke-width="2"/>
<line x1="{X}" y1="{y+14}" x2="{X+120}" y2="{y+14}" stroke="{FOAM}" stroke-width="3" filter="url(#g)"/>'''


def stagger(rows, y0, lh, delay0=0.15, step=0.12):
    """rows: markup strings with {y}, or None for a spacer."""
    out, y, i = [], y0, 0
    for r in rows:
        if r is None:
            y += 14
            continue
        i += 1
        out.append(f'<g class="ln" style="animation-delay:{delay0 + i*step:.2f}s">' + r.replace("{y}", str(y)) + "</g>")
        y += lh
    return "\n".join(out), y


def up40(v):
    return int(math.ceil(v / 40) * 40)


# ─────────────────────────────── header ───────────────────────────────
def build_header():
    bar_left = "SYS://MOHAMED-BADRY // NODE:CAIRO"
    bar_right = "ONLINE · ALL SYSTEMS NOMINAL"
    name = "MOHAMED BADRY"
    lines = [
        "building developer tools, terminal interfaces, and ml systems",
        "rust · python · linux",
    ]
    text = bar_left + bar_right + name + "$ whoami>>" + "".join(lines)
    h = 320
    css = f"""@keyframes type{{from{{width:0}}}}
@keyframes flicker{{0%{{opacity:0}}10%{{opacity:1}}14%{{opacity:.2}}22%{{opacity:1}}30%{{opacity:.4}}40%,100%{{opacity:1}}}}
@keyframes gm{{0%,92%,100%{{transform:translate(0,0)}}93%{{transform:translate(4px,-1px)}}95%{{transform:translate(-3px,1px)}}97%{{transform:translate(2px,0)}}}}
@keyframes gc{{0%,92%,100%{{transform:translate(0,0)}}93%{{transform:translate(-4px,1px)}}95%{{transform:translate(3px,-1px)}}97%{{transform:translate(-2px,0)}}}}
.typing{{animation:type .7s steps(8) .3s both}}
.name{{animation:flicker .9s linear 1.1s both}}
.gm{{animation:gm 6s linear 2s infinite}}.gc{{animation:gc 6s linear 2s infinite}}"""
    defs = f"""<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".18"/></pattern>
<filter id="tglow" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="sglow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
<clipPath id="typeclip"><rect class="typing" x="{X}" y="80" width="140" height="30"/></clipPath>"""
    dotx = FR - 20 - len(bar_right) * 8.2 - 16
    rows = [
        f'<text class="fg" x="{X}" y="{{y}}"><tspan class="fm">&gt;&gt;</tspan> {e(lines[0])}</text>',
        f'<text class="fg" x="{X}" y="{{y}}"><tspan class="fm">&gt;&gt;</tspan> {e(lines[1])}</text>',
    ]
    desc_lines, _ = stagger(rows, 216, 26, delay0=1.6, step=0.22)
    body = f'''<rect x="{FL}" y="{M}" width="{FR-FL}" height="34" fill="{FOAM}" fill-opacity=".08"/>
<line x1="{FL}" y1="{M+34}" x2="{FR}" y2="{M+34}" stroke="{FOAM}" stroke-opacity=".5"/>
<text x="{FL+16}" y="{M+22}" letter-spacing="1" class="fm" style="font-size:12px">{e(bar_left)}</text>
<text x="{FR-20}" y="{M+22}" letter-spacing="1" class="dim" text-anchor="end" style="font-size:12px">{e(bar_right)}</text>
<circle class="dot" cx="{dotx}" cy="{M+18}" r="4" fill="{PINE_BRIGHT}"/>
<circle class="dot" cx="{dotx}" cy="{M+18}" r="4" fill="{PINE_BRIGHT}" filter="url(#sglow)"/>
<g clip-path="url(#typeclip)"><text x="{X}" y="102" class="dim"><tspan class="gr">$</tspan> whoami</text></g>
<g class="name" font-weight="800" letter-spacing="2" style="font-size:56px">
<text x="{X}" y="172" fill="{FOAM}" opacity=".45" filter="url(#tglow)" style="font-size:56px">{name}</text>
<g class="gm"><text x="{X+3}" y="172" fill="{LOVE}" opacity=".65" style="font-size:56px">{name}</text></g>
<g class="gc"><text x="{X-3}" y="172" fill="{IRIS}" opacity=".75" style="font-size:56px">{name}</text></g>
<text x="{X}" y="172" fill="#f5f4fd" style="font-size:56px">{name}</text>
</g>
{desc_lines}
<g class="ln" style="animation-delay:2.4s">
<text x="{X}" y="280" class="gr">$</text>
<rect class="cursor" x="{X+18}" y="267" width="10" height="17" fill="{FOAM}"/>
<rect class="cursor" x="{X+18}" y="267" width="10" height="17" fill="{FOAM}" filter="url(#sglow)"/>
</g>
<rect x="{FL}" y="{M+35}" width="{FR-FL}" height="{h-M-35}" fill="url(#scan)"/>'''
    return slice_svg(
        h,
        body,
        title="Mohamed Badry",
        desc="Building developer tools, terminal interfaces, and machine learning systems.",
        text=text,
        top=True,
        css=css,
        defs=defs,
        weights=(400, 700, 800),
    )


# ─────────────────────────────── footer ───────────────────────────────
def build_footer():
    h = 80
    text = "$ exit connection to Mohamed-Badry closed. // EOF inspired by @georgekobaidze ↗"
    body = f'''<text x="{X}" y="30" class="dim"><tspan class="gr">$</tspan> exit</text>
<text x="{X}" y="52" class="dim">connection to <tspan class="fm">Mohamed-Badry</tspan> closed. <tspan fill="{MUTED}">// EOF</tspan></text>
<text x="{FR-36}" y="52" text-anchor="end" fill="{MUTED}" style="font-size:11px">// inspired by <tspan class="fm">@georgekobaidze</tspan> ↗</text>'''
    return slice_svg(h, body, title="End of profile", desc="Connection closed. Theme inspired by @georgekobaidze.", text=text, bottom=True)


# ──────────────────────────────── links ───────────────────────────────
LINKS = [
    ("linkedin", "LinkedIn", "in/mohamed0badry", "https://www.linkedin.com/in/mohamed0badry/"),
    ("discord", "Discord", "crim02", "https://discord.com/users/571315867426488330"),
    ("devdotto", "DEV", "@mohamedbadry", "https://dev.to/mohamedbadry"),
    ("mail", "Email", "m.badry.fl@gmail.com", "mailto:m.badry.fl@gmail.com"),
]
ICONS = json.load(open(HERE / "icons.json"))
SEG = W // len(LINKS)     # 220 px per button slice
BTN_W, BTN_GAP = 158, 48


def icon_markup(key, x, y, size=18):
    if key == "linkedin":
        return (
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="{FOAM}"/>'
            f'<text x="{x + size/2}" y="{y + size - 4.5}" text-anchor="middle" font-weight="700" fill="{BASE}" style="font-size:12px">in</text>'
        )
    d = ICONS.get(key, "")
    return f'<path transform="translate({x} {y}) scale({size/24})" d="{d}" fill="{FOAM}"/>'


def build_links_head():
    body = (
        heading(44, "links", "// 01")
        + f'''\n<g class="ln" style="animation-delay:.15s"><text x="{X}" y="96" class="dim"><tspan class="gr">$</tspan> ping mohamed-badry --all-channels</text></g>'''
    )
    return slice_svg(120, body, title="Links", desc="Where to find me", text="~/links// 01$ ping mohamed-badry --all-channels")


def build_link_button(k):
    key, label, handle, url = LINKS[k]
    h = 80
    x0 = SEG * k
    lx = X + k * (BTN_W + BTN_GAP) - x0
    first, last = k == 0, k == len(LINKS) - 1
    bg0 = FL - x0 if first else 0
    bg1 = FR - x0 if last else SEG
    rails = (f"M{FL - x0} 0V{h}" if first else "") + (f"M{FR - x0} 0V{h}" if last else "")
    glow = (f"M{FL - x0} -40V{h+40}" if first else "") + (f"M{FR - x0} -40V{h+40}" if last else "")
    by, bh, cut = 12, 56, 12
    box = f"M{lx} {by}H{lx+BTN_W-cut}L{lx+BTN_W} {by+cut}V{by+bh}H{lx}Z"
    text = label + handle + "in"
    body = f'''<g class="ln" style="animation-delay:{.25 + k*.08:.2f}s">
<path d="{box}" fill="{FOAM}" fill-opacity=".06"/>
<path d="{box}" fill="none" stroke="{FOAM}" stroke-opacity=".55"/>
<path d="M{lx+BTN_W-cut} {by}L{lx+BTN_W} {by+cut}" stroke="{FOAM}" stroke-width="2"/>
<g filter="url(#g)" opacity=".4">{icon_markup(key, lx+12, by+11)}</g>
{icon_markup(key, lx+12, by+11)}
<text x="{lx+38}" y="{by+25}" font-weight="700" class="fm" style="font-size:13px">{e(label)}</text>
<text x="{lx+12}" y="{by+46}" class="dim" style="font-size:10px">{e(handle)}</text>
</g>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SEG}" height="{h}" viewBox="0 0 {SEG} {h}" role="img" aria-labelledby="t d">
<title id="t">{e(label)}</title>
<desc id="d">{e(label)}: {e(url)}</desc>
<style>
{faces(text + visible(body))}
{BASE_CSS}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<pattern id="grid" x="{(-x0) % 40}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{FOAM}" stroke-opacity=".06"/></pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
{f'<path d="{glow}" fill="none" stroke="{FOAM}" stroke-width="3" opacity=".45" filter="url(#glow)"/>' if glow else ""}
<rect x="{bg0}" y="0" width="{bg1-bg0}" height="{h}" fill="{BASE}"/>
<rect x="{bg0}" y="0" width="{bg1-bg0}" height="{h}" fill="url(#grid)"/>
{body}
{f'<path d="{rails}" fill="none" stroke="{FOAM}" stroke-width="1.2"/>' if rails else ""}
</svg>
'''


# ─────────────────────────────── stats ────────────────────────────────
def fmt(n):
    return "—" if n is None else f"{n:,}"


def tile(x, y, w, h, label, value, sub, delay):
    return f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{SURFACE}" stroke="{FOAM}" stroke-opacity=".35"/>
<path d="M{x} {y+12}V{y}H{x+12}" fill="none" stroke="{FOAM}" stroke-width="2"/>
<text x="{x+16}" y="{y+22}" letter-spacing="1.5" class="dim" style="font-size:10.5px">{e(label)}</text>
<text x="{x+16}" y="{y+50}" font-weight="700" fill="{FOAM}" filter="url(#g)" opacity=".45" style="font-size:30px">{e(value)}</text>
<text x="{x+16}" y="{y+50}" font-weight="700" class="fm" style="font-size:30px">{e(value)}</text>
<text x="{x+16}" y="{y+h-12}" fill="{SUBTLE}" style="font-size:12px">{e(sub)}</text>
</g>'''


def build_stats(d):
    y = datetime.date.fromisoformat(d["updated"])
    since = datetime.date.fromisoformat(d["created_at"][:10])
    yrs = (y - since).days // 365
    parts = [
        heading(44, "stats", "// 02"),
        f'<g class="ln" style="animation-delay:.15s"><text x="{X}" y="96" class="dim"><tspan class="gr">$</tspan> gh stats --user Mohamed-Badry</text></g>',
    ]

    # Row 1 — Large metrics tiles
    tw, gap, ty, th = 182, 16, 118, 92
    t1 = [
        ("TOTAL STARS", fmt(d["stars"]), "across all repos"),
        (f"CONTRIBUTIONS {d['year']}", fmt(d["contributions_year"]), f"{fmt(d['contributions_all'])} all time"),
        ("PULL REQUESTS", fmt(d["prs"]), f"{fmt(d['prs_merged'])} merged"),
        ("CURRENT STREAK", f"{d['streak_current']}d", f"longest: {d['streak_longest']} days"),
    ]
    for i, (lab, val, sub) in enumerate(t1):
        parts.append(tile(X + i * (tw + gap), ty, tw, th, lab, val, sub, 0.25 + i * 0.08))

    # Row 2 — Account overview & language distribution
    ry, rh = ty + th + 16, 150
    lw = 300
    kv = [
        ("followers", fmt(d["followers"])),
        ("forks", fmt(d["forks"])),
        ("member since", f"{since:%b %Y} ({yrs}y)"),
        ("status", "active"),
    ]
    rows = "\n".join(
        f'<text x="{X+16}" y="{ry+38+i*28}" xml:space="preserve"><tspan class="fm">{e(k)}</tspan><tspan class="dim">{"." * (16 - len(k))}</tspan> <tspan class="fg">{e(v)}</tspan></text>'
        for i, (k, v) in enumerate(kv)
    )
    parts.append(f'''<g class="ln" style="animation-delay:.6s">
<rect x="{X}" y="{ry}" width="{lw}" height="{rh}" fill="{SURFACE}" stroke="{FOAM}" stroke-opacity=".35"/>
<path d="M{X} {ry+12}V{ry}H{X+12}" fill="none" stroke="{FOAM}" stroke-width="2"/>
{rows}
</g>''')

    lx = X + lw + gap
    lwid = (FR - 36) - lx

    # Focus language bar on real programming languages
    EXCLUDE_LANGS = {"Jupyter Notebook", "HTML", "TeX", "Less", "CSS", "AutoHotkey"}
    filtered_langs = {k: v for k, v in d["languages"].items() if k not in EXCLUDE_LANGS}
    langs = sorted(filtered_langs.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    top = langs[:5]
    other = total - sum(v for _, v in top)
    items = [(k, v / total) for k, v in top] + ([("Other", other / total)] if other > 0 else [])

    cols = [FOAM, IRIS, PINE_BRIGHT, GOLD, ROSE, MUTED]
    bx, by, bw = lx + 16, ry + 42, lwid - 32
    segs, cx = [], bx
    for (k, p), c in zip(items, cols):
        w = bw * p
        segs.append(f'<rect x="{cx:.1f}" y="{by}" width="{max(w-2,1):.1f}" height="8" fill="{c}"/>')
        segs.append(f'<rect x="{cx:.1f}" y="{by}" width="{max(w-2,1):.1f}" height="8" fill="{c}" filter="url(#g)" opacity=".5"/>')
        cx += w

    legend = []
    for i, ((k, p), c) in enumerate(zip(items, cols)):
        col, row = i % 2, i // 2
        lxx = bx + col * (bw / 2)
        lyy = by + 36 + row * 26
        legend.append(
            f'<rect x="{lxx}" y="{lyy-9}" width="9" height="9" fill="{c}"/>'
            f'<text x="{lxx+18}" y="{lyy}" class="fg" style="font-size:13px">{e(k)}</text>'
            f'<text x="{lxx + bw/2 - 24}" y="{lyy}" text-anchor="end" class="dim" style="font-size:13px">{p*100:.1f}%</text>'
        )

    parts.append(f'''<g class="ln" style="animation-delay:.7s">
<rect x="{lx}" y="{ry}" width="{lwid}" height="{rh}" fill="{SURFACE}" stroke="{FOAM}" stroke-opacity=".35"/>
<path d="M{lx} {ry+12}V{ry}H{lx+12}" fill="none" stroke="{FOAM}" stroke-width="2"/>
<text x="{lx+16}" y="{ry+24}" letter-spacing="1.5" class="dim" style="font-size:10.5px">TOP LANGUAGES</text>
<rect x="{bx}" y="{by}" width="{bw}" height="8" fill="{OVERLAY}"/>
{"".join(segs)}
{"".join(legend)}
</g>''')

    fy = ry + rh + 28
    parts.append(f'<text x="{FR-36}" y="{fy}" text-anchor="end" fill="{MUTED}" style="font-size:11px">// last sync {d["updated"]}</text>')
    h = up40(fy + 16)
    text = "".join(str(x) for x in ["~/stats// 02$ gh stats --user Mohamed-Badry", "".join(parts)])
    text = re.sub(r"<[^>]+>", "", text) + "0123456789,—%.()d"
    desc = (
        f"GitHub stats: {d['stars']} total stars; {d['contributions_year']} contributions in {d['year']}, "
        f"{d['contributions_all']} all time; {d['prs']} pull requests ({d['prs_merged']} merged); "
        f"current streak {d['streak_current']} days, longest {d['streak_longest']} days; "
        f"{d['followers']} followers; {d['forks']} forks; member since {since:%B %Y}. "
        "Top languages: " + ", ".join(f"{k} {p*100:.1f}%" for k, p in items) + "."
    )
    return slice_svg(h, "\n".join(parts), title="Stats", desc=desc, text=html.unescape(text))


# ─────────────────────────── contribution city ────────────────────────
CITY_TW, CITY_TH = 25, 12.5                  # iso tile width / height
CITY_OX, CITY_OY = 152.5, 262                # grid origin inside the 880-wide slice
CITY_HMAX = 118                              # tallest building, px

# Rosé Pine rooftop quartiles
ROOFS = [PINE, FOAM, IRIS, ROSE]
WIN_ON, WIN_ON_SIDE, WIN_OFF = GOLD, FOAM, "#1f1d2e"


def _p(x, y):
    return f"{x:.1f},{y:.1f}"


def _rng(seed):
    """Deterministic PRNG so the same data renders identically."""
    state = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2**64
        yield (state >> 11) / 2**53


def _levels(counts):
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [1, 1, 1]
    q = lambda f: nz[min(len(nz) - 1, int(len(nz) * f))]
    return [q(0.25), q(0.5), q(0.75)]


def build_city(calendar, updated):
    days = [(datetime.date.fromisoformat(d), n) for d, n in calendar]
    counts = [n for _, n in days]
    total, peak = sum(counts), max(counts) if counts else 0
    lv = _levels(counts)
    rnd = _rng(f"{updated}-{total}")
    start = days[0][0]

    cells = []
    for d, n in days:
        idx = (d - start).days
        cells.append((idx // 7, (d.weekday() + 1) % 7, n))
    cells.sort(key=lambda c: (c[0] + c[1], c[0]))                 # back to front

    shapes, flick = [], 0
    for w, dow, n in cells:
        cx = CITY_OX + (w - dow) * CITY_TW / 2
        cy = CITY_OY + (w + dow) * CITY_TH / 2
        L, R = (cx - CITY_TW / 2, cy), (cx + CITY_TW / 2, cy)
        T, B = (cx, cy - CITY_TH / 2), (cx, cy + CITY_TH / 2)
        if n == 0:
            shapes.append(f'<path d="M{_p(*T)}L{_p(*R)}L{_p(*B)}L{_p(*L)}Z" fill="#1b1928" stroke="#14121f" stroke-width=".6"/>')
            continue
        h = 8 + (CITY_HMAX - 8) * math.sqrt(n / peak)
        level = sum(n > t for t in lv)
        Tu, Ru, Bu, Lu = [(x, y - h) for x, y in (T, R, B, L)]
        shapes.append(
            f'<path d="M{_p(*L)}L{_p(*B)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="#232136"/>'
            f'<path d="M{_p(*B)}L{_p(*R)}L{_p(*Ru)}L{_p(*Bu)}Z" fill="#1b1928"/>'
            f'<path d="M{_p(*Tu)}L{_p(*Ru)}L{_p(*Bu)}L{_p(*Lu)}Z" fill="{ROOFS[level]}"/>'
        )
        on, side, off, fl = [], [], [], []
        for face, (a, b) in (("l", (L, B)), ("r", (B, R))):
            for r in range(int((h - 6) // 7)):
                v0 = 5 + r * 7
                for u0 in (0.18, 0.58):
                    lit = next(rnd) < 0.55
                    if not lit and next(rnd) < 0.5:
                        continue
                    pts = [
                        (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - v)
                        for u, v in ((u0, v0), (u0 + 0.26, v0), (u0 + 0.26, v0 + 3.2), (u0, v0 + 3.2))
                    ]
                    seg = "M" + "L".join(_p(*q) for q in pts) + "Z"
                    if not lit:
                        off.append(seg)
                    elif next(rnd) < 0.03:
                        fl.append((seg, face))
                    else:
                        (on if face == "l" else side).append(seg)
        if off:
            shapes.append(f'<path d="{"".join(off)}" fill="{WIN_OFF}"/>')
        if on:
            shapes.append(f'<path d="{"".join(on)}" fill="{WIN_ON}"/>')
        if side:
            shapes.append(f'<path d="{"".join(side)}" fill="{WIN_ON_SIDE}"/>')
        for seg, face in fl:
            flick += 1
            shapes.append(f'<path class="f{flick % 3}" d="{seg}" fill="{WIN_ON if face == "l" else WIN_ON_SIDE}"/>')

    # Starry sky
    stars = []
    for i in range(46):
        x, y = 470 + next(rnd) * 350, 118 + next(rnd) * 150
        if x > 700 and y < 215:
            continue
        cls = f' class="s{i % 3}"' if i % 3 == 0 else ""
        stars.append(f'<circle{cls} cx="{x:.1f}" cy="{y:.1f}" r="{(.6, .8, 1.1)[i % 3]}" fill="{TEXT}" opacity="{.35 + next(rnd) * .5:.2f}"/>')

    busiest_d, busiest_n = max(days, key=lambda t: t[1]) if days else (None, 0)
    info = [
        f'<tspan class="fm" font-weight="700">{total:,}</tspan> contributions · last 365 days',
        f'busiest day <tspan class="fg">{busiest_d:%b} {busiest_d.day}</tspan> · {busiest_n}' if busiest_n else "",
        f'{sum(1 for n in counts if n)} active days',
    ]
    info_svg = "".join(f'<text x="{FR-36}" y="{300 + i*20}" text-anchor="end" class="dim" style="font-size:12px">{t}</text>' for i, t in enumerate(info) if t)

    legend_colors = ["#1b1928"] + ROOFS
    legend = "".join(f'<rect x="{X + 52 + i*16}" y="{642}" width="11" height="11" fill="{c}"/>' for i, c in enumerate(legend_colors))

    # Low Earth Orbit (LEO) Satellite markup:
    # Central bus (x: 8..14), solar wings (0..7 and 15..22), beacon dot
    satellite_svg = f'''<g clip-path="url(#sky-clip)">
<g class="satellite">
<g transform="translate(0 136)">
  <!-- Left solar panel array -->
  <rect x="0" y="1" width="7" height="4" rx="0.5" fill="{PINE}" stroke="{FOAM}" stroke-width="0.5"/>
  <line x1="3.5" y1="1" x2="3.5" y2="5" stroke="{FOAM}" stroke-width="0.3"/>
  <!-- Boom / connector -->
  <line x1="7" y1="3" x2="9" y2="3" stroke="{TEXT}" stroke-width="0.8"/>
  <!-- Satellite central body -->
  <rect x="9" y="0.5" width="6" height="5" rx="0.8" fill="{SURFACE}" stroke="{FOAM}" stroke-width="0.8"/>
  <circle cx="12" cy="3" r="1.2" fill="{GOLD}"/>
  <!-- Right boom / connector -->
  <line x1="15" y1="3" x2="17" y2="3" stroke="{TEXT}" stroke-width="0.8"/>
  <!-- Right solar panel array -->
  <rect x="17" y="1" width="7" height="4" rx="0.5" fill="{PINE}" stroke="{FOAM}" stroke-width="0.5"/>
  <line x1="20.5" y1="1" x2="20.5" y2="5" stroke="{FOAM}" stroke-width="0.3"/>
  <!-- Blinking telemetry beacon -->
  <circle class="bl" cx="12" cy="0" r="1.4" fill="{LOVE}"/>
  <circle class="bl" cx="12" cy="0" r="2.8" fill="{LOVE}" opacity="0.4" filter="url(#sglow)"/>
</g>
</g>
</g>'''

    body = (
        heading(44, "contribution-city", "// 03")
        + f'''
<g class="ln" style="animation-delay:.15s"><text x="{X}" y="96" class="dim"><tspan class="gr">$</tspan> render-skyline --last 365d <tspan fill="{MUTED}"># one building per day</tspan></text></g>
<g>{"".join(stars)}</g>
<!-- Moon -->
<circle cx="{FR-80}" cy="160" r="40" fill="url(#moonglow)"/>
<circle cx="{FR-80}" cy="160" r="14" fill="#e0def4"/>
<circle cx="{FR-74}" cy="155" r="12.5" fill="{BASE}"/>
{satellite_svg}
{info_svg}
{"".join(shapes)}
<text x="{X}" y="652" class="dim" style="font-size:11px">quiet</text>{legend}<text x="{X + 52 + 5*16 + 6}" y="652" class="dim" style="font-size:11px">skyscraper</text>'''
    )

    css = f"""@keyframes tw{{0%,100%{{opacity:.9}}50%{{opacity:.15}}}}
@keyframes fl{{0%,40%,100%{{opacity:1}}45%,60%{{opacity:.1}}}}
@keyframes blink{{0%,90%,100%{{opacity:0}}93%{{opacity:1}}}}
@keyframes orbit{{from{{transform:translate({FL - 26}px, 0)}}to{{transform:translate({FR + 6}px, -32px)}}}}
.s0{{animation:tw 3s infinite}}
.f0{{animation:fl 5s infinite}}.f1{{animation:fl 7s infinite 2s}}.f2{{animation:fl 9s infinite 4s}}
.satellite{{animation:orbit 13s linear infinite}}.bl{{animation:blink 1.2s infinite}}"""

    defs = f'''<clipPath id="sky-clip"><rect x="{FL}" y="0" width="{FR-FL}" height="680"/></clipPath>
<radialGradient id="moonglow"><stop offset="0" stop-color="{TEXT}" stop-opacity=".2"/><stop offset="1" stop-color="{TEXT}" stop-opacity="0"/></radialGradient>'''
    desc = (
        f"Contribution skyline: an isometric night skyline with one building per day of the last year, "
        f"taller and brighter for busier days. {total:,} contributions"
        + (f", busiest day {busiest_d:%B} {busiest_d.day} with {busiest_n}" if busiest_n else "")
        + "."
    )
    return slice_svg(
        680,
        body,
        title="Contribution city",
        desc=desc,
        text="~/contribution-city// 03$ render-skyline --last 365d # one building per dayquietskyscraper",
        css=css,
        defs=defs,
    )


# ────────────────────────────── projects ──────────────────────────────
HW = W // 2   # 440 px half-slice width
CARD_H = 200


def half_slice(h, side, body, *, title, desc, text, weights=(400, 700)):
    """Left or right half of a full-width row; only its outer side has a rail."""
    assert h % 40 == 0
    rx = FL if side == "L" else HW - M
    bx0, bx1 = (FL, HW) if side == "L" else (0, HW - M)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{HW}" height="{h}" viewBox="0 0 {HW} {h}" role="img" aria-labelledby="t d">
<title id="t">{e(title)}</title>
<desc id="d">{e(desc)}</desc>
<style>
{faces(text + visible(body), weights)}
{BASE_CSS}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
{DEFS}
</defs>
<path d="M{rx} -40V{h+40}" fill="none" stroke="{FOAM}" stroke-width="3" opacity=".45" filter="url(#glow)"/>
<rect x="{bx0}" y="0" width="{bx1-bx0}" height="{h}" fill="{BASE}"/>
<rect x="{bx0}" y="0" width="{bx1-bx0}" height="{h}" fill="url(#grid)"/>
{body}
<path d="M{rx} 0V{h}" fill="none" stroke="{FOAM}" stroke-width="1.2"/>
</svg>
'''


PROJECTS = [
    dict(
        slug="statui",
        name="Statui",
        url="https://github.com/Mohamed-Badry/statui",
        tag="TERMINAL DASHBOARD",
        tagc=GOLD,
        stars=117,
        stack="Rust · Ratatui · Tokio",
        desc="Async terminal API health check dashboard. HTTP connection pooling, shell variable expansion, zero UI lockup.",
    ),
    dict(
        slug="islp-solutions",
        name="ISLP Solutions",
        url="https://github.com/Mohamed-Badry/islp-solutions",
        tag="INTERACTIVE TEXTBOOK",
        tagc=FOAM,
        stars=20,
        stack="Python · Jupyter Book · Scikit-Learn",
        desc="Programmatic solutions and mathematical proofs for An Introduction to Statistical Learning with Python.",
    ),
    dict(
        slug="nixos-dotfiles",
        name="nixos-dotfiles",
        url="https://github.com/Mohamed-Badry/nixos-dotfiles",
        tag="DECLARATIVE DESKTOP",
        tagc=IRIS,
        stars=1,
        stack="Nix · NixOS · Flakes",
        desc="Declarative Linux system configuration with NixOS, Flakes, Home Manager, and Niri.",
    ),
    dict(
        slug="wedjat",
        name="Wedjat",
        url="https://github.com/Mohamed-Badry/wedjat",
        tag="SATELLITE TELEMETRY",
        tagc=PINE_BRIGHT,
        stars=0,
        stack="Python · PyTorch · SvelteKit · TimescaleDB",
        desc="Satellite telemetry anomaly detection on a ground station. SGP4 orbit tracking, PyTorch VAE, and live dashboard.",
    ),
]


def build_projects_head():
    h = 120
    body = (
        heading(44, "projects", "// 04")
        + f'''\n<g class="ln" style="animation-delay:.2s"><text x="{X}" y="96" class="dim"><tspan class="gr">$</tspan> ls -l ~/projects</text></g>'''
    )
    return slice_svg(h, body, title="Projects", desc="Featured projects", text="~/projects// 04$ ls -l")


def build_card(p, side, delay, stars=None):
    p = dict(p, stars=stars.get(p["slug"], p["stars"]) if stars else p["stars"])
    x0 = 52 if side == "L" else 10
    cw, y0, ch = 378, 12, 176
    pad = 18
    tx = x0 + pad
    cut = 16
    box = f"M{x0} {y0}H{x0+cw-cut}L{x0+cw} {y0+cut}V{y0+ch}H{x0+cut}L{x0} {y0+ch-cut}Z"
    lines = textwrap.wrap(p["desc"], 44)
    assert len(lines) <= 3, lines
    tag_w = len(p["tag"]) * 7.6 + 16
    title_w = len(p["name"]) * 10.2
    desc = "\n".join(f'<text x="{tx}" y="{100 + i*20}" class="fg" style="font-size:13px">{e(l)}</text>' for i, l in enumerate(lines))
    sx = x0 + cw - pad
    star = f'<path transform="translate({sx - len(str(p["stars"]))*7.2 - 20} 158) scale(.55)" d="M10 0l2.9 6.6 7.1.6-5.4 4.7 1.6 7L10 15.2 3.8 18.9l1.6-7L0 7.2l7.1-.6z" fill="{GOLD}"/>'
    body = f'''<g class="ln" style="animation-delay:{delay:.2f}s">
<path d="{box}" fill="{SURFACE}"/>
<path d="{box}" fill="none" stroke="{FOAM}" stroke-opacity=".4"/>
<path d="M{x0+cw-cut} {y0}L{x0+cw} {y0+cut}" stroke="{FOAM}" stroke-width="2"/>
<text x="{tx}" y="{y0+34}" font-weight="700" fill="{FOAM}" filter="url(#g)" opacity=".6" style="font-size:17px">{e(p["name"])}</text>
<text x="{tx}" y="{y0+34}" font-weight="700" class="fm" style="font-size:17px">{e(p["name"])}</text>
<path d="M{tx+title_w+11} {y0+31}l8-8M{tx+title_w+13} {y0+23}h6v6" fill="none" stroke="{FOAM}" stroke-width="1.6"/>
<rect x="{tx}" y="{y0+46}" width="{tag_w}" height="18" fill="none" stroke="{p["tagc"]}" stroke-opacity=".8"/>
<text x="{tx+8}" y="{y0+59}" letter-spacing="1" fill="{p["tagc"]}" style="font-size:11px">{e(p["tag"])}</text>
{desc}
<text x="{tx}" y="{y0+158}" class="dim" style="font-size:12px">{e(p["stack"])}</text>
{star}
<text x="{sx}" y="{y0+158}" text-anchor="end" class="dim" style="font-size:12px">{p["stars"]}</text>
</g>'''
    text = p["name"] + p["tag"] + p["desc"] + p["stack"] + str(p["stars"])
    return half_slice(
        CARD_H,
        side,
        body,
        title=p["name"],
        desc=f'{p["name"]}: {p["desc"]} Built with {p["stack"].replace(" · ", ", ")}. {p["stars"]} stars.',
        text=text,
    )


# ─────────────────────────────── stack ────────────────────────────────
STACK = [
    ("languages", ["Python", "Rust", "Java", "SQL", "Bash"]),
    ("ml & data", ["PyTorch", "Scikit-learn", "NumPy", "Pandas", "Matplotlib", "Seaborn", "Plotly"]),
    ("backend", ["FastAPI", "PostgreSQL", "SQLite", "TimescaleDB"]),
    ("infra & cloud", ["Linux", "Nix", "Docker", "GCP"]),
    ("frontend & ui", ["Ratatui", "Svelte", "Tailwind CSS"]),
]


def build_stack():
    parts = [
        heading(44, "stack", "// 05"),
        f'<g class="ln" style="animation-delay:.15s"><text x="{X}" y="96" class="dim"><tspan class="gr">$</tspan> scan --loadout --top-level</text></g>',
    ]
    y, rowh = 126, 44
    cw = 0.6 * 13
    for r, (cat, items) in enumerate(STACK):
        parts.append(f'<g class="ln" style="animation-delay:{.25 + r*.1:.2f}s">')
        parts.append(f'<text x="{X}" y="{y+20}" class="dim" style="font-size:13px">{e(cat)}</text>')
        parts.append(f'<text x="{X+130}" y="{y+20}" class="fm" style="font-size:13px">›</text>')
        x = X + 150
        for it in items:
            w = len(it) * cw + 24
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="30" fill="{SURFACE}" stroke="{FOAM}" stroke-opacity=".5"/>')
            parts.append(f'<path d="M{x:.1f} {y+8}V{y}H{x+8:.1f}" fill="none" stroke="{FOAM}" stroke-width="2"/>')
            parts.append(f'<text x="{x+12:.1f}" y="{y+20}" font-weight="700" class="fm" style="font-size:13px">{e(it)}</text>')
            x += w + 8
        parts.append("</g>")
        y += rowh
    h = up40(y + 10)
    text = "~/stack// 05$ scan --loadout --top-level›" + "".join(c + "".join(i) for c, i in STACK)
    desc = "Tech stack. " + " ".join(f"{c}: {', '.join(i)}." for c, i in STACK)
    return slice_svg(h, "\n".join(parts), title="Tech stack", desc=desc, text=text)


def write(rel, svg):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)


def main():
    global OUT
    import argparse
    ap = argparse.ArgumentParser(description="Render the profile SVGs from data/*.json.")
    ap.add_argument("--data", type=pathlib.Path, default=DATA, help="folder with stats.json")
    ap.add_argument("--out", type=pathlib.Path, default=OUT, help="folder to write the SVGs into")
    args = ap.parse_args()
    OUT = args.out

    stats = json.load(open(args.data / "stats.json"))
    stars = stats.get("repo_stars", {})

    write("header.svg", build_header())
    write("links.svg", build_links_head())
    for k, (key, *_) in enumerate(LINKS):
        write(f"links/{key}.svg", build_link_button(k))
    write("stats.svg", build_stats(stats))
    if (args.data / "calendar.json").exists():
        write("contribution-city.svg", build_city(json.load(open(args.data / "calendar.json")), stats["updated"]))
    write("projects.svg", build_projects_head())
    for i, p in enumerate(PROJECTS):
        write(f"card-{p['slug']}.svg", build_card(p, "L" if i % 2 == 0 else "R", 0.3 + i * 0.12, stars))
    write("stack.svg", build_stack())
    write("footer.svg", build_footer())
    print("rendered", len(list(OUT.rglob("*.svg"))), "SVGs into", OUT)


if __name__ == "__main__":
    main()
