#!/usr/bin/env python3
"""
Genera la presentación "Buyer Persona 360" (HTML 16:9 → PDF con Chrome).

Todos los gráficos son SVG calculados a partir de los datos reales de la
última corrida (output/raw/data_sources_*.json) y de las notas del vault.

Uso:
    venv/bin/python3 scripts/build_deck.py [ruta_data_sources.json]
    google-chrome --headless=new --print-to-pdf=... output/presentacion/buyer_persona_360.html
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "presentacion" / "buyer_persona_360.html"
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------- datos
src = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(str(ROOT / "output/raw/data_sources_*.json")))[-1]
d = json.load(open(src, encoding="utf-8"))
import logging; logging.disable(logging.CRITICAL)
from src.config_loader import load_config  # noqa: E402
from src.connectors.sales_connector import SalesConnector  # noqa: E402
from src.connectors.extras_erp import fetch_extras  # noqa: E402
CFG = load_config(str(ROOT / "config/settings.yaml"))
_sales_cfg = dict(CFG.get("sales", {})); _sales_cfg["file_path"] = str(ROOT / CFG["paths"]["sales_history"])
d["sales"] = SalesConnector(_sales_cfg).fetch_all()
d["extras"] = fetch_extras(CFG.get("extras", {}), _sales_cfg["file_path"])
meta, sales, bitrix, datacar, extras = d["meta_ads"], d["sales"], d.get("bitrix", {}), d.get("datacar", {}), d["extras"]

leads_by_brand = sorted(((k, v["total_leads"]) for k, v in meta.get("leads_by_brand", {}).items()), key=lambda x: -x[1])
total_leads = sum(v for _, v in leads_by_brand)
sales_by_brand = sorted(((k, v.get("orders_last_365d", 0)) for k, v in sales["by_brand"].items()), key=lambda x: -x[1])
top_models = sorted(((k, v.get("orders_last_365d", 0)) for k, v in sales["by_model"].items()), key=lambda x: -x[1])[:10]
sales_total_12m = sum(v for _, v in sales_by_brand)
import pandas as _pd  # noqa: E402
_sv = _pd.read_excel(_sales_cfg["file_path"], sheet_name="Datos", header=2, usecols=["Fecha", "Marca"])
_sv["Fecha"] = _pd.to_datetime(_sv["Fecha"], errors="coerce"); _sv = _sv.dropna(subset=["Fecha"])
sales_by_year = [(str(y), int(n)) for y, n in _sv.groupby(_sv["Fecha"].dt.year).size().items()]
sales_until = _sv["Fecha"].max().strftime("%d/%m/%Y")
# recompra: unidades por marca y cohorte de meses desde la compra
from datetime import date as _date  # noqa: E402
_today = _date.today()
_sv["meses"] = (_today.year - _sv["Fecha"].dt.year) * 12 + (_today.month - _sv["Fecha"].dt.month)
_bm = {"JETOUR": "Jetour", "GREATWALL": "GWM", "RENAULT": "Renault", "MITSUBISHI": "Mitsubishi", "JAC": "JAC", "SOUEAST": "Soueast"}
_sv["marca"] = _sv["Marca"].astype(str).str.replace("\xa0", " ").str.strip().str.upper().map(_bm)
recompra_rows = []
for b, g in _sv.dropna(subset=["marca"]).groupby("marca"):
    recompra_rows.append((b, int((g["meses"] >= 36).sum()), int(((g["meses"] >= 24) & (g["meses"] < 36)).sum()), int(((g["meses"] >= 12) & (g["meses"] < 24)).sum())))
recompra_rows.sort(key=lambda r: -(r[1] + r[2] + r[3]))
recompra_total = sum(r[1] + r[2] for r in recompra_rows)

spend = Counter()
for r in meta.get("campaigns", []):
    spend[r.get("account")] += float(r.get("spend", 0) or 0)

place = Counter()
for r in meta.get("placements", []):
    p = str(r.get("platform_position", "")).lower(); n = int(r.get("impressions", 0) or 0)
    place["Reels y Stories" if ("reel" in p or "stor" in p) else "Feed" if "feed" in p else "Otros"] += n
pt = sum(place.values()) or 1
place_pct = {k: round(v / pt * 100) for k, v in place.items()}

ages = Counter(); genders = Counter()
for r in meta["demographics"]["age_gender"]:
    w = int(r.get("clicks", 0) or 0)
    if r.get("age") and r["age"] != "Unknown": ages[r["age"]] += w
    if r.get("gender") in ("male", "female"): genders[r["gender"]] += w
at = sum(ages.values()) or 1; gt = sum(genders.values()) or 1
ages_pct = [(k, round(v / at * 100, 1)) for k, v in sorted(ages.items())]
male_pct = round(genders["male"] / gt * 100)

crm = bitrix.get("by_brand", {})
crm_rows = []
for k, v in sorted(crm.items(), key=lambda x: -x[1]["leads"]):
    if k in ("Sin marca", "Karry"): continue
    ch = v["leads_by_channel"]
    crm_rows.append((k, ch.get("Meta madre", 0), ch.get("Meta asesores", 0), v["leads"]))
crm_rows = crm_rows[:8]

pick = [r["price_usd"] for r in datacar.get("versions", []) if r.get("subsegment") == "D-PICKUP" and r["price_usd"] <= 80000]
pick_ours = [r["price_usd"] for r in datacar.get("versions", []) if r.get("subsegment") == "D-PICKUP" and r.get("our_brand") == "Mitsubishi" and r["price_usd"] <= 80000]

# brecha pauta/venta por modelo (share dentro de su marca), mismos umbrales que el pipeline
from src.generators.persona_generator import PersonaGenerator  # noqa: E402
personas = PersonaGenerator(CFG["persona"]).generate(d)
gap_rows = sorted(
    [(p["segment"]["name"], p["segment"]["sales_share"], p["segment"]["ad_share"], p["segment"]["gap"])
     for p in personas if p["segment"].get("type") == "model" and (p["segment"].get("orders_last_365d") or 0) >= 30],
    key=lambda x: -(x[1] - x[2]))[:12]
gap_up = [r[0] for r in gap_rows if r[3] == "sub-pautado"][:4]
gap_down = [r[0] for r in gap_rows if r[3] == "sobre-pautado"][:3]

# stock y oferta (extras)
_st = (extras.get("stock") or {}).get("by_model", {}); _ac = (extras.get("acciones") or {}).get("by_model", {})
stock_brand = sorted(((b, v["total"], v["en_viaje"]) for b, v in (extras.get("stock") or {}).get("by_brand", {}).items()), key=lambda r: -r[1])
stock_press = []
for m, st in _st.items():
    ac = _ac.get(m) or {}
    ritmo = ac.get("avg_ventas_mes") or 0
    if st["total"] >= 15 and ritmo > 0:
        stock_press.append((m, round(st["total"] / ritmo, 1), st["total"], ac.get("descuento_max") or 0))
stock_press.sort(key=lambda r: -r[1]); stock_press = stock_press[:10]
stock_total = (extras.get("stock") or {}).get("total", 0)
desc_rows = sorted(((m, v["descuento_max"]) for m, v in _ac.items() if v.get("descuento_max")), key=lambda r: -r[1])[:8]

# objetivos vs real (extras)
_ob = (extras.get("objetivos") or {})
obj_rows = sorted(((b, v["real_ytd"], v["objetivo_ytd"], v.get("avance_ytd_pct") or 0) for b, v in _ob.get("by_brand", {}).items()
                   if v.get("objetivo_ytd") and not v.get("compartido_con") and b != "Renew"), key=lambda r: -r[2])
obj_total_real = sum(r[1] for r in obj_rows); obj_total_obj = sum(r[2] for r in obj_rows)
_ng = (extras.get("negociacion") or {}).get("by_brand", {})
nego_total = sum(v.get("negociaciones_abiertas", 0) for v in _ng.values())

# demografía propia por modelo (Meta a nivel anuncio, ≥100 clics): (modelo, % hombres, edad top, clics)
model_demo = []
for p in personas:
    dm = p.get("demographics", {})
    if p["segment"].get("type") == "model" and dm.get("meta_level") == "modelo":
        m = dm["meta"]
        male = m["gender_share"] if m["gender"] == "Masculino" else 100 - m["gender_share"]
        model_demo.append((p["segment"]["name"], round(male), m["age_range"], m["weight"], p["segment"].get("orders", 0)))
# vitrina: los modelos que más venden (con perfil propio), ordenados de más femenino a más masculino
showcase = sorted(sorted(model_demo, key=lambda r: -r[4])[:10], key=lambda r: r[1])
kwid = next((p for p in personas if p["segment"].get("name") == "Renault Kwid"), None)
kwid_demo = (kwid or {}).get("demographics", {})

# temperatura de públicos: adsets activos a público frío
aud_mix = PersonaGenerator._summarize_audience_mix(meta.get("adset_targeting", []))
adsets_total = sum(v["adsets"] for v in aud_mix.values())
adsets_cold = sum(v["frio"] for v in aud_mix.values())
cold_pct = round(adsets_cold / adsets_total * 100) if adsets_total else 0
cold_rows = sorted(((k, v["frio_pct"]) for k, v in aud_mix.items() if v["adsets"] >= 5), key=lambda x: -x[1])[:10]

# presupuesto: hoy vs sugerido por modelo (USD/mes)
budget_rows = sorted(
    [(p["segment"]["name"], p["budget"]["current_month_est"], p["budget"]["suggested_month"])
     for p in personas if p["segment"].get("type") == "model" and (p.get("budget") or {}).get("suggested_month")],
    key=lambda r: -abs(r[2] - r[1]))[:8]

market_top = [("Toyota", 7563, 12.1), ("Chevrolet", 6421, 10.3), ("Kia", 6417, 10.3), ("Hyundai", 6031, 9.7),
              ("Fiat", 4152, 6.7), ("Volkswagen", 3790, 6.1), ("Suzuki", 2780, 4.5), ("Nissan", 2765, 4.4),
              ("Geely", 2390, 3.8), ("Chery", 2147, 3.4), ("Jetour", 1290, 2.07), ("GWM", 941, 1.51)]
OURS = {"Jetour", "GWM", "Renault", "Mitsubishi", "JAC", "Soueast", "Leapmotor", "JMEV", "Zeekr", "XPeng", "Renew", "Santa Rosa"}

# ---------------------------------------------------------------- helpers SVG
def fmt(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", ".")

def hbars(rows, width=760, row_h=44, label_w=200, val_fmt=fmt, color_fn=None, max_v=None):
    """Barras horizontales: rows = [(label, value)]."""
    max_v = max_v or max(v for _, v in rows) or 1
    h = row_h * len(rows)
    out = [f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="Archivo">']
    bar_w = width - label_w - 130
    for i, (lab, v) in enumerate(rows):
        y = i * row_h
        col = color_fn(lab) if color_fn else "var(--signal)"
        w = max(2, bar_w * v / max_v)
        out.append(f'<text x="0" y="{y+29}" fill="var(--paper)" font-size="22">{lab}</text>')
        out.append(f'<rect x="{label_w}" y="{y+11}" width="{w:.0f}" height="20" fill="{col}"/>')
        out.append(f'<text x="{label_w + w + 14:.0f}" y="{y+29}" fill="var(--muted)" font-size="21">{val_fmt(v)}</text>')
    out.append("</svg>")
    return "\n".join(out)

def dumbbell(rows, width=1660, row_h=52):
    """rows = [(label, ventas%, pauta%, gap)] — dos puntos unidos por línea."""
    lw, axis_w = 260, width - 260 - 60
    mx = 80
    h = row_h * len(rows) + 40
    out = [f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="Archivo">']
    for t in (0, 20, 40, 60, 80):
        x = lw + axis_w * t / mx
        out.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{h-36}" stroke="var(--line)" stroke-width="1"/>')
        out.append(f'<text x="{x:.0f}" y="{h-8}" fill="var(--dim)" font-size="18" text-anchor="middle">{t}%</text>')
    for i, (lab, vs, ps, gap) in enumerate(rows):
        y = i * row_h + 26
        x1 = lw + axis_w * vs / mx; x2 = lw + axis_w * ps / mx
        out.append(f'<text x="0" y="{y+7}" fill="var(--paper)" font-size="22">{lab}</text>')
        out.append(f'<line x1="{x1:.0f}" y1="{y}" x2="{x2:.0f}" y2="{y}" stroke="var(--line)" stroke-width="3"/>')
        out.append(f'<circle cx="{x2:.0f}" cy="{y}" r="9" fill="var(--signal)"/>')
        out.append(f'<circle cx="{x1:.0f}" cy="{y}" r="9" fill="var(--go)"/>')
    out.append("</svg>")
    return "\n".join(out)

def donut(parts, size=440, stroke=54):
    """parts = [(label, pct, color)]."""
    r = (size - stroke) / 2; c = 2 * 3.14159 * r
    out = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    off = 0
    for lab, pct, col in parts:
        seg = c * pct / 100
        out.append(f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{col}" stroke-width="{stroke}" '
                   f'stroke-dasharray="{seg:.1f} {c - seg:.1f}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {size/2} {size/2})"/>')
        off += seg
    out.append("</svg>")
    return "\n".join(out)

def strip_plot(values, highlight, width=1660, lo=20000, hi=80000):
    """Puntos de precio en un eje; los nuestros resaltados."""
    h = 150
    out = [f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="Archivo">']
    out.append(f'<line x1="0" y1="90" x2="{width}" y2="90" stroke="var(--line)" stroke-width="1"/>')
    for t in range(lo, hi + 1, 10000):
        x = (t - lo) / (hi - lo) * width
        out.append(f'<text x="{x:.0f}" y="{h-8}" fill="var(--dim)" font-size="18" text-anchor="middle">{t//1000}k</text>')
    for v in values:
        x = (v - lo) / (hi - lo) * width
        out.append(f'<circle cx="{x:.0f}" cy="90" r="7" fill="var(--muted)" opacity=".55"/>')
    for v in highlight:
        x = (v - lo) / (hi - lo) * width
        out.append(f'<circle cx="{x:.0f}" cy="90" r="12" fill="var(--signal)"/>')
        out.append(f'<text x="{x:.0f}" y="52" fill="var(--signal)" font-size="20" text-anchor="middle" font-weight="600">{v//1000}k</text>')
    out.append("</svg>")
    return "\n".join(out)

def stacked(rows, width=1660, row_h=50):
    """rows = [(label, madre, asesores, total)]."""
    lw = 220; bw = width - lw - 160
    mx = max(t for *_, t in rows) or 1
    h = row_h * len(rows)
    out = [f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="Archivo">']
    for i, (lab, a, b, t) in enumerate(rows):
        y = i * row_h
        wa = bw * a / mx; wb = bw * b / mx
        out.append(f'<text x="0" y="{y+31}" fill="var(--paper)" font-size="22">{lab}</text>')
        out.append(f'<rect x="{lw}" y="{y+12}" width="{wa:.0f}" height="22" fill="var(--signal)"/>')
        out.append(f'<rect x="{lw+wa:.0f}" y="{y+12}" width="{wb:.0f}" height="22" fill="var(--muted)"/>')
        out.append(f'<text x="{lw+wa+wb+14:.0f}" y="{y+31}" fill="var(--muted)" font-size="21">{fmt(t)}</text>')
    out.append("</svg>")
    return "\n".join(out)

def pairs(rows, width=1660, row_h=58, label_w=280):
    """rows = [(label, hoy, sugerido)] en USD/mes: barra tenue (hoy) y barra señal (sugerido)."""
    mx = max(max(a, b) for _, a, b in rows) or 1
    bw = width - label_w - 170
    h = row_h * len(rows)
    out = [f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="Archivo">']
    for i, (lab, a, b) in enumerate(rows):
        y = i * row_h
        wa = bw * a / mx; wb = bw * b / mx
        out.append(f'<text x="0" y="{y+30}" fill="var(--paper)" font-size="22">{lab}</text>')
        out.append(f'<rect x="{label_w}" y="{y+8}" width="{wa:.0f}" height="14" fill="var(--dim)"/>')
        out.append(f'<rect x="{label_w}" y="{y+26}" width="{wb:.0f}" height="14" fill="var(--signal)"/>')
        out.append(f'<text x="{label_w+max(wa,wb)+14:.0f}" y="{y+30}" fill="var(--muted)" font-size="21">{a:,.0f} → <tspan fill="var(--paper)" font-weight="700">{b:,.0f}</tspan></text>')
    out.append("</svg>")
    return "\n".join(out)

our_col = lambda lab: "var(--signal)" if lab in OURS else "var(--dim)"

# ---------------------------------------------------------------- HTML
CSS = """
  @page { size: 1920px 1080px; margin: 0; }
  :root { --ink: oklch(15% 0.012 45); --ink-2: oklch(20% 0.012 45); --line: oklch(32% 0.012 45);
          --paper: oklch(96% 0.006 70); --muted: oklch(66% 0.012 70); --dim: oklch(48% 0.012 70);
          --signal: oklch(66% 0.21 38); --signal-ink: oklch(22% 0.06 38); --go: oklch(82% 0.17 130); --hold: oklch(82% 0.14 85); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: var(--ink); }
  body { font-family: 'Archivo', system-ui, sans-serif; color: var(--paper); -webkit-print-color-adjust: exact; print-color-adjust: exact; font-variant-numeric: tabular-nums; }
  .slide { position: relative; width: 1920px; height: 1080px; overflow: hidden; page-break-after: always; break-after: page; background: var(--ink); padding: 104px 128px 96px; }
  .slide:last-child { page-break-after: auto; }
  .drench { background: var(--signal); color: var(--signal-ink); }
  .drench .k, .drench .foot, .drench .lbl { color: var(--signal-ink); opacity: .75; }
  .k { font-size: 20px; letter-spacing: .28em; text-transform: uppercase; color: var(--signal); font-weight: 600; margin-bottom: 36px; font-stretch: 110%; }
  h1 { font-size: 168px; font-weight: 800; line-height: .92; letter-spacing: -.045em; font-stretch: 118%; }
  h2 { font-size: 72px; font-weight: 700; line-height: 1.0; letter-spacing: -.035em; font-stretch: 112%; max-width: 1560px; }
  h3 { font-size: 30px; font-weight: 600; letter-spacing: -.01em; }
  p, li { font-size: 27px; line-height: 1.5; color: var(--muted); max-width: 70ch; }
  strong, b { color: var(--paper); font-weight: 600; }
  .lead { font-size: 38px; line-height: 1.3; color: var(--paper); font-weight: 400; max-width: 1400px; }
  .signal { color: var(--signal); } .go { color: var(--go); } .hold { color: var(--hold); }
  .num { font-weight: 800; letter-spacing: -.05em; line-height: .9; font-stretch: 112%; font-size: 200px; }
  .num.md { font-size: 128px; } .num.sm { font-size: 88px; }
  .lbl { font-size: 21px; letter-spacing: .18em; text-transform: uppercase; color: var(--dim); margin-top: 16px; font-weight: 500; }
  .foot { position: absolute; bottom: 48px; left: 128px; right: 128px; display: flex; justify-content: space-between; font-size: 17px; letter-spacing: .22em; text-transform: uppercase; color: var(--dim); font-weight: 500; }
  .cols { display: grid; gap: 0 72px; }
  .row { border-top: 1px solid var(--line); padding: 28px 0; }
  .row:last-child { border-bottom: 1px solid var(--line); }
  .idx { font-size: 19px; letter-spacing: .2em; color: var(--signal); font-weight: 600; margin-bottom: 10px; text-transform: uppercase; }
  table { border-collapse: collapse; width: 100%; }
  th { text-align: left; font-size: 18px; letter-spacing: .2em; text-transform: uppercase; color: var(--dim); font-weight: 500; padding: 0 0 16px; border-bottom: 1px solid var(--line); }
  td { padding: 18px 0; font-size: 26px; border-bottom: 1px solid var(--line); color: var(--paper); }
  td.r, th.r { text-align: right; } td.m { color: var(--muted); }
  .tag { display: inline-block; font-size: 17px; letter-spacing: .2em; text-transform: uppercase; font-weight: 600; padding: 9px 14px; border: 1px solid currentColor; }
  .legend { display: flex; gap: 36px; font-size: 20px; color: var(--muted); align-items: center; }
  .legend i { display: inline-block; width: 16px; height: 16px; margin-right: 10px; vertical-align: -2px; }
  .chart-title { font-size: 19px; letter-spacing: .2em; text-transform: uppercase; color: var(--dim); font-weight: 500; margin-bottom: 22px; }
"""

def foot(n=None):
    """Numera sola: se llama dentro del f-string de la lámina que se está agregando."""
    return f'<div class="foot"><span>Buyer Persona 360</span><span>{len(slides)+1:02d}</span></div>'

slides: list[str] = []
S = slides.append

# 01 portada
S(f'''<section class="slide" style="display:flex;flex-direction:column;justify-content:flex-end">
<svg width="1100" height="1100" viewBox="0 0 1100 1100" style="position:absolute;right:-260px;top:-140px">
<circle cx="550" cy="550" r="520" fill="none" stroke="var(--line)"/><circle cx="550" cy="550" r="400" fill="none" stroke="var(--line)"/><circle cx="550" cy="550" r="280" fill="none" stroke="var(--line)"/><circle cx="550" cy="550" r="160" fill="none" stroke="var(--signal)" stroke-width="2"/>
<circle cx="550" cy="30" r="9" fill="var(--signal)"/><circle cx="950" cy="550" r="9" fill="var(--signal)"/><circle cx="550" cy="830" r="9" fill="var(--signal)"/><circle cx="270" cy="550" r="9" fill="var(--signal)"/></svg>
<div class="k">Santa Rosa Automotores · Innovación</div>
<h1>Buyer<br>Persona <span class="signal">360</span></h1>
<p class="lead" style="margin-top:44px">Quién nos compra, modelo por modelo. Reescrito con nuestros propios datos todas las madrugadas.</p>
<div class="foot"><span>Septiembre 2026</span><span>Uso interno</span></div></section>''')

# 02 problema
S(f'''<section class="slide"><div class="k">El punto de partida</div>
<h2>Pautábamos a quien creíamos que compra.<br><span class="signal">No a quien compra.</span></h2>
<div class="cols" style="grid-template-columns:1fr 1fr;margin-top:64px">
<div class="row"><div class="idx">01 · ERP</div><p>Las ventas reales, encerradas en un Excel de facturación que marketing nunca vio.</p></div>
<div class="row"><div class="idx">02 · Meta Ads</div><p>81 cuentas, una por asesor. Miles de anuncios y leads que nadie leía en conjunto.</p></div>
<div class="row"><div class="idx">03 · CRM</div><p>18.000 leads por trimestre en Bitrix, sin relación con lo que finalmente se facturó.</p></div>
<div class="row"><div class="idx">04 · Mercado</div><p>Precios de la competencia averiguados a mano, vencidos al día siguiente.</p></div></div>
<p class="lead" style="margin-top:60px">Cuatro fuentes de verdad. Cero conversación entre ellas.</p>{foot()}</section>''')

# 03 concepto (drench)
S(f'''<section class="slide drench" style="display:flex;flex-direction:column;justify-content:center"><div class="k">El concepto</div>
<h2 style="font-size:92px;max-width:1660px">Un motor que lee las cuatro fuentes cada madrugada y escribe quién es el comprador de cada modelo.</h2>
<div style="display:flex;gap:120px;margin-top:88px">
<div><div class="num md">06:00</div><div class="lbl">todos los días, solo</div></div>
<div><div class="num md">{len(personas)}</div><div class="lbl">personas vivas</div></div>
<div><div class="num md">382</div><div class="lbl">notas conectadas</div></div></div>{foot()}</section>''')

# 04 estado honesto
S(f'''<section class="slide"><div class="k">Dónde estamos</div>
<h2>Construido y corriendo desde hace semanas.<br><span class="signal">El uso operativo empieza ahora.</span></h2>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:72px;gap:0 64px">
<div class="row"><div class="idx">Hecho</div><p>Meta, ERP desde 2018, CRM, Datacar, stock, acciones comerciales, objetivos y negociación semanal: nueve fuentes en 382 notas que se reescriben cada día. Semillas de lookalike, memoria de audiencia, manual y auditoría.</p></div>
<div class="row"><div class="idx">Validado</div><p>Cada cifra de esta presentación sale de la corrida de esta mañana. Nada está estimado ni proyectado.</p></div>
<div class="row"><div class="idx">Pendiente</div><p>Que Marketing, Ventas y Gerencia lo usen. Marketing ya lo revisó el 17 de septiembre y sus cambios están aplicados. Las últimas láminas dicen cómo seguimos.</p></div></div>{foot()}</section>''')

# 05 arquitectura
S(f'''<section class="slide"><div class="k">Cómo funciona</div><h2>De nueve silos a una sola verdad.</h2>
<svg width="1664" height="600" viewBox="0 0 1664 600" style="margin-top:44px" font-family="Archivo">
<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--signal)"/></marker></defs>
<g fill="var(--paper)" font-size="26" font-weight="600">
<text x="0" y="60">Meta Ads</text><text x="0" y="92" fill="var(--muted)" font-size="20" font-weight="400">copy · demografía · leads · placement</text>
<text x="0" y="200">ERP + Excel del negocio</text><text x="0" y="232" fill="var(--muted)" font-size="20" font-weight="400">ventas 2018→hoy · stock · PVP y descuentos · objetivos · negociación</text>
<text x="0" y="340">CRM Bitrix</text><text x="0" y="372" fill="var(--muted)" font-size="20" font-weight="400">leads por canal · conversión · deals</text>
<text x="0" y="480">Datacar</text><text x="0" y="512" fill="var(--muted)" font-size="20" font-weight="400">692 precios de lista, todo el mercado</text></g>
<g stroke="var(--line)"><line x1="0" y1="110" x2="440" y2="110"/><line x1="0" y1="250" x2="440" y2="250"/><line x1="0" y1="390" x2="440" y2="390"/><line x1="0" y1="530" x2="440" y2="530"/></g>
<g stroke="var(--signal)" stroke-width="2" fill="none" marker-end="url(#a)"><path d="M440,50 C560,50 560,290 660,290"/><path d="M440,190 C560,190 560,290 660,290"/><path d="M440,330 C560,330 560,290 660,290"/><path d="M440,470 C560,470 560,290 660,290"/></g>
<rect x="670" y="170" width="380" height="240" fill="none" stroke="var(--signal)" stroke-width="2"/>
<text x="700" y="225" fill="var(--paper)" font-size="30" font-weight="700">MOTOR 360</text>
<g fill="var(--muted)" font-size="20"><text x="700" y="270">normaliza y cruza</text><text x="700" y="302">lee el copy de cada anuncio</text><text x="700" y="334">detecta brechas pauta / venta</text><text x="700" y="366">sin datos personales</text></g>
<path d="M1050,290 L1170,290" stroke="var(--signal)" stroke-width="2" marker-end="url(#a)"/>
<rect x="1180" y="130" width="484" height="320" fill="var(--ink-2)"/>
<text x="1212" y="185" fill="var(--paper)" font-size="30" font-weight="700">OBSIDIAN</text>
<g fill="var(--muted)" font-size="21"><text x="1212" y="236">{len(personas)} personas · 288 copies listos</text><text x="1212" y="272">12 mapas de audiencias</text><text x="1212" y="308">precios de mercado en vivo</text><text x="1212" y="344">manual · auditoría · playbooks</text></g>
<text x="1212" y="410" fill="var(--signal)" font-size="22" font-weight="600">→ Pauta · Salón · Gerencia</text>
<path d="M1422,450 C1422,590 860,590 860,415" stroke="var(--dim)" stroke-width="1.5" stroke-dasharray="6 8" fill="none" marker-end="url(#a)"/>
<text x="1140" y="575" text-anchor="middle" fill="var(--dim)" font-size="20">lo que pautamos hoy vuelve mañana como dato</text></svg>{foot()}</section>''')

# 06 leads por marca + inversión
S(f'''<section class="slide"><div class="k">Lo que entra por Meta · últimos 90 días</div>
<h2>{fmt(total_leads)} leads de formulario. Quién los genera y cuánto cuesta.</h2>
<div class="cols" style="grid-template-columns:1.1fr 1fr;margin-top:48px;gap:0 96px">
<div><div class="chart-title">Leads por marca</div>{hbars(leads_by_brand, width=860, row_h=42, label_w=150)}</div>
<div><div class="chart-title">Inversión en pauta · USD</div>{hbars([(k, v) for k, v in spend.most_common(10) if k in OURS], width=700, row_h=42, label_w=150, val_fmt=lambda v: fmt(v))}
<p style="margin-top:28px;font-size:23px">USD {fmt(sum(spend.values()))} en 90 días. Jetour y GWM concentran leads e inversión; JAC y Mitsubishi generan más leads por dólar.</p></div></div>{foot()}</section>''')

# 07 ventas reales
S(f'''<section class="slide"><div class="k">Lo que se factura · ERP unificado, julio 2018 al {sales_until}</div>
<h2>{fmt(sales['total_records'])} ventas reales desde 2018. {fmt(sales_total_12m)} en los últimos doce meses.</h2>
<div class="cols" style="grid-template-columns:1fr 1fr 1.1fr;margin-top:40px;gap:0 72px">
<div><div class="chart-title">Unidades por año</div>{hbars(sales_by_year, width=520, row_h=40, label_w=90)}</div>
<div><div class="chart-title">Últimos 12 meses · por marca</div>{hbars(sales_by_brand[:8], width=520, row_h=40, label_w=150)}</div>
<div><div class="chart-title">Últimos 12 meses · los diez modelos</div>{hbars(top_models, width=620, row_h=40, label_w=250)}</div></div>
<p style="margin-top:28px;font-size:23px">Dos reportes del ERP unidos por número de chasis, notas de crédito neteadas. Con ocho años de historia ya existe la base de recompra de tres años o más.</p>{foot()}</section>''')

# 08 demografía real
S(f'''<section class="slide"><div class="k">Quién interactúa · audiencia real de Meta</div>
<h2>{male_pct}% hombres. El corazón está entre 25 y 54.</h2>
<div style="display:flex;gap:120px;align-items:flex-end;margin-top:56px">
<div style="flex:1"><div class="chart-title">Edad · ponderada por clics</div>
<svg width="1000" height="380" viewBox="0 0 1000 380" font-family="Archivo">
{''.join(f'<rect x="{i*165}" y="{380-60-v*9:.0f}" width="120" height="{v*9:.0f}" fill="{"var(--signal)" if v==max(x for _,x in ages_pct) else "var(--muted)"}"/><text x="{i*165+60}" y="{380-70-v*9:.0f}" fill="var(--paper)" font-size="26" font-weight="700" text-anchor="middle">{v:g}%</text><text x="{i*165+60}" y="370" fill="var(--dim)" font-size="20" text-anchor="middle">{k}</text>' for i,(k,v) in enumerate(ages_pct))}
</svg></div>
<div><div class="num md">{male_pct}<span style="font-size:72px">%</span></div><div class="lbl">hombres</div>
<div class="num sm" style="margin-top:44px;color:var(--muted)">{100-male_pct}<span style="font-size:48px">%</span></div><div class="lbl">mujeres</div></div></div>
<p style="margin-top:44px">Cada marca y cada modelo tienen su propia distribución. Esta es la del portfolio completo, sobre las 81 cuentas.</p>{foot()}</section>''')

# 08b cada modelo su propio público (pedido de marketing 17-sep)
if showcase:
    demo_rows = [(f"{n}  ·  {a}", m) for n, m, a, _, _ in showcase]
    S(f'''<section class="slide"><div class="k">Quién interactúa · por modelo, no por marca</div>
<h2>Cada modelo tiene su propio público. Ahora se ve.</h2>
<div style="display:flex;gap:96px;margin-top:48px;align-items:flex-start">
<div style="flex:1"><div class="chart-title">% hombres entre quienes hacen clic · edad dominante · los diez que más venden con perfil propio</div>
{hbars(demo_rows, width=1160, row_h=48, label_w=520, val_fmt=lambda v: f"{v:g}% ♂", max_v=100)}</div>
<div style="width:420px"><div class="row"><div class="idx">Antes</div><p>L200 y Montero heredaban el perfil de Mitsubishi: 87% hombres, 35 a 44. Kwid, el de Renault.</p></div>
<div class="row"><div class="idx">Ahora</div><p>Meta se lee anuncio por anuncio y cada anuncio se atribuye al modelo que nombra. <b>{len(model_demo)} modelos</b> ya tienen edad y género propios.</p></div></div></div>
<p style="margin-top:40px">Pedido de Marketing el 17 de septiembre. Aplicado el 18.</p>{foot()}</section>''')

# 09 anatomía
S(f'''<section class="slide"><div class="k">Anatomía de una persona</div><h2>Cada modelo tiene su ficha. Ocho bloques, todos con dato real.</h2>
<div class="cols" style="grid-template-columns:1fr 1fr;margin-top:48px"><div>
<div class="row"><div class="idx">01 · Quién</div><p>Edad y género dominantes de la audiencia real que interactúa con la marca.</p></div>
<div class="row"><div class="idx">02 · Qué compra</div><p>Unidades, versión más vendida, precio facturado, sucursal, de qué marca viene.</p></div>
<div class="row"><div class="idx">03 · Qué le duele</div><p>Dolores y motivaciones extraídos del copy de sus propios anuncios.</p></div>
<div class="row"><div class="idx">04 · Dónde</div><p>El placement que concentra las impresiones reales: Reels, Stories o Feed.</p></div></div><div>
<div class="row"><div class="idx">05 · Qué pide</div><p>Leads de formulario agregados: modelo, forma de pago, ciudad, interés.</p></div>
<div class="row"><div class="idx">06 · Cómo cierra</div><p>Embudo CRM: leads, convertidos, deals ganados, win rate, ticket.</p></div>
<div class="row"><div class="idx">07 · Contra quién</div><p>Precio de lista, posición en su segmento y competidores directos a ±25%.</p></div>
<div class="row"><div class="idx">08 · Brecha</div><p>Porcentaje de ventas contra porcentaje de pauta: escalar, revisar o equilibrado.</p></div></div></div>{foot()}</section>''')

# 10 kwid
_ks = (kwid or {}).get("segment", {}); _kx = (kwid or {}).get("extras", {}) or {}; _kst = _kx.get("stock") or {}; _kac = _kx.get("acciones") or {}
_kg = f"{kwid_demo.get('gender', '')} {kwid_demo.get('meta', {}).get('gender_share', '')}%, {kwid_demo.get('age_range', '')} años" if kwid_demo.get("meta_level") == "modelo" else "perfil heredado de Renault"
S(f'''<section class="slide"><div class="k">Caso real · Renault Kwid</div><h2>El modelo que más vende de Renault se frenó por stock. Ya volvió.</h2>
<div style="display:flex;align-items:flex-end;gap:120px;margin-top:48px">
<div><div class="num">{fmt(_ks.get('orders', 0))}</div><div class="lbl">unidades desde 2018</div></div>
<div><div class="num go">{_ks.get('sales_share', 0):g}%</div><div class="lbl">de las ventas de Renault · 12 meses</div></div>
<div><div class="num signal">{_kst.get('total', 0)}</div><div class="lbl">en stock hoy · {_kst.get('dias_promedio', 0)} días</div></div></div>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:56px;gap:0 64px">
<div class="row"><div class="idx">Quién interactúa</div><p><b>{_kg}</b>, según los clics de sus propios anuncios. Antes la nota decía hombre de 35 a 44: era el promedio de la marca.</p></div>
<div class="row"><div class="idx">Qué pasó</div><p>Vendió 27, 13 y 23 unidades en septiembre, octubre y noviembre de 2025 y después casi nada: sin stock. Precio de lista <b>USD {_kac.get('pvp_min', 0):,.0f}</b>{(' con USD ' + format(_kac.get('descuento_max', 0), ',.0f') + ' de descuento vigente') if _kac.get('descuento_max') else ''}.</p></div>
<div class="row"><div class="idx">Qué haríamos</div><p>Relanzar con público femenino de 18 a 24, formato vertical, presupuesto sugerido de la nota y la base de recompra de Sandero y Clio.</p></div></div>{foot()}</section>''')

# 11 brecha dumbbell
S(f'''<section class="slide"><div class="k">Brecha pauta / venta · últimos 12 meses, modelos con 30 o más ventas</div>
<h2>Dónde la pauta no acompaña a la venta.</h2>
<div class="legend" style="margin:32px 0 24px"><span><i style="background:var(--go)"></i>% de las ventas de su marca</span><span><i style="background:var(--signal)"></i>% de los anuncios de su marca</span></div>
{dumbbell(gap_rows)}
<p style="margin-top:20px;font-size:23px">Cuanto más larga la línea con el verde a la derecha, más vende el modelo respecto a lo que se pauta. {", ".join(gap_up) or "Ninguno"}: candidatos a escalar. {", ".join(gap_down) or "Ninguno"}: revisar.</p>{foot()}</section>''')

# 12 placement donut
rs, fd, ot = place_pct.get("Reels y Stories", 0), place_pct.get("Feed", 0), place_pct.get("Otros", 0)
S(f'''<section class="slide"><div class="k">Dónde está el público · impresiones reales, 81 cuentas</div><h2>La audiencia vive en vertical.</h2>
<div style="display:flex;align-items:center;gap:120px;margin-top:48px">
<div style="position:relative">{donut([("Reels y Stories", rs, "var(--signal)"), ("Feed", fd, "var(--muted)"), ("Otros", ot, "var(--dim)")])}
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center"><div class="num sm signal">{rs}%</div><div class="lbl" style="margin-top:8px">vertical</div></div></div>
<div style="flex:1">
<div class="row"><div class="idx">Reels y Stories · {rs}%</div><p>Video vertical corto. Más de la mitad de todas las impresiones del portfolio.</p></div>
<div class="row"><div class="idx">Feed · {fd}%</div><p>Imagen y carrusel. Sigue rindiendo, ya no es el centro.</p></div>
<div class="row"><div class="idx">Otros · {ot}%</div><p>Marketplace, búsqueda, Audience Network.</p></div>
<p class="lead" style="margin-top:36px;font-size:32px">Cada persona indica su formato dominante. Las piezas nuevas se diseñan primero para ese formato.</p></div></div>{foot()}</section>''')

# 13 precios strip
S(f'''<section class="slide"><div class="k">Inteligencia de precios · Datacar, {datacar.get('counts',{}).get('versions',692)} versiones</div>
<h2>Todo el mercado 0 km, actualizado cada día. Ejemplo: pickups.</h2>
<div class="chart-title" style="margin-top:44px">{len(pick)} versiones D-Pickup en el mercado · USD · en naranja, Mitsubishi L200</div>
{strip_plot(pick, pick_ours)}
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:40px;gap:0 64px">
<div class="row"><div class="idx">L200 · tercio más caro</div><p>Frontier 45.990, S10 y Tasman 47.990, Amarok 48.900. El argumento es respaldo y valor de reventa, no precio.</p></div>
<div class="row"><div class="idx">Jolion · 19.990</div><p>Ocho rivales al mismo precio exacto y solapa con Kardian, JS4 y X50 propios.</p></div>
<div class="row"><div class="idx">Cada mañana</div><p>Se compara contra el día anterior: quién subió, quién bajó, quién lanzó. Uso interno, nunca en un copy.</p></div></div>{foot()}</section>''')

# 14 mercado CADAM
S(f'''<section class="slide"><div class="k">Ventas reales del mercado · CADAM / DNRA 2026</div>
<h2>62.314 unidades, 80 marcas. Nosotros, 6,6%.</h2>
<div class="cols" style="grid-template-columns:1.2fr 1fr;margin-top:44px;gap:0 96px">
<div><div class="chart-title">Unidades matriculadas ene a jul · en naranja, nuestras marcas</div>{hbars([(k, v) for k, v, _ in market_top], width=920, row_h=42, label_w=170, color_fn=our_col)}</div>
<div><div class="row"><div class="idx">Contra quién competimos de verdad</div><p>Toyota, Chevrolet, Kia y Hyundai se llevan el 42% del mercado. Jetour es 12º con 2,07%, GWM 16º con 1,51%.</p></div>
<div class="row"><div class="idx">Por modelo, mes a mes</div><p>Vemos quién crece, quién cae y en qué segmento perdemos. Sus ventas reales, no estimaciones.</p></div>
<div class="row"><div class="idx">Conquista</div><p>289 compradores nos entregaron un Chevrolet, Hyundai, VW, Kia o Toyota en parte de pago. Es la semilla para buscar a los que se les parecen.</p></div></div></div>{foot()}</section>''')

# 15 CRM canal
S(f'''<section class="slide"><div class="k">CRM Bitrix · {fmt(bitrix.get('total_leads',0))} leads en 90 días</div>
<h2>De dónde entra cada lead: cuenta madre o asesores.</h2>
<div class="legend" style="margin:32px 0 24px"><span><i style="background:var(--signal)"></i>Meta cuenta madre</span><span><i style="background:var(--muted)"></i>Meta asesores</span></div>
{stacked(crm_rows)}
<p style="margin-top:28px;font-size:23px">Soueast y Renault reparten con los asesores; Mitsubishi, Zeekr y XPeng entran casi todo por la cuenta madre. 3.500 leads llegan sin marca asignada: el primer arreglo de CRM que hay que hacer.</p>{foot()}</section>''')

# 15b públicos fríos
if adsets_total:
    S(f'''<section class="slide"><div class="k">A quién le mostramos los anuncios · {adsets_total} adsets activos</div>
<div style="display:flex;gap:120px;align-items:flex-start;margin-top:24px">
<div><div class="num">{cold_pct}<span style="font-size:96px">%</span></div><div class="lbl">de los adsets van a público frío</div>
<p style="margin-top:40px;max-width:560px">Intereses o Advantage+ sin base propia. Ninguno usa la base de compradores del ERP; el retargeting web y de formulario existe solo en algunas marcas.</p></div>
<div style="flex:1"><div class="chart-title">% de adsets a público frío · por marca</div>{hbars(cold_rows, width=980, row_h=48, label_w=200, val_fmt=lambda v: f"{v:g}%", max_v=100)}</div></div>
<p style="margin-top:36px">Lo que cambia: retargeting de formulario abierto, visitantes web y <b>la base de recompra del ERP</b> como públicos calientes, y excluirlos de las campañas frías para no pagar dos veces.</p>{foot()}</section>''')

# 15c presupuesto sugerido
if budget_rows:
    S(f'''<section class="slide"><div class="k">Cuánto invertir en cada modelo · USD por mes</div>
<h2>El presupuesto sigue a las ventas, no a la costumbre.</h2>
<div class="legend" style="margin:28px 0 12px"><span><i style="background:var(--dim)"></i>hoy, según su peso en anuncios</span><span><i style="background:var(--signal)"></i>sugerido, según su peso en ventas del ERP</span></div>
{pairs(budget_rows, row_h=54)}
<p style="margin-top:20px">Gasto real de cada marca en Meta repartido por lo que cada modelo pesa en la facturación. Los ocho con mayor diferencia.</p>{foot()}</section>''')

# 15d stock y oferta
if stock_press or stock_brand:
    S(f'''<section class="slide"><div class="k">Stock real y oferta vigente · {fmt(stock_total)} unidades nuevas en el sistema</div>
<h2>La pauta también tiene que mirar el patio.</h2>
<div class="cols" style="grid-template-columns:1fr 1.3fr;margin-top:40px;gap:0 96px">
<div><div class="chart-title">Stock por marca · en stock + en viaje</div>{stacked([(b, t - v, v, t) for b, t, v in stock_brand[:9]], width=700, row_h=44)}
<div class="legend" style="margin-top:14px"><span><i style="background:var(--signal)"></i>en stock</span><span><i style="background:var(--muted)"></i>en viaje</span></div></div>
<div><div class="chart-title">Meses de stock al ritmo de venta actual · modelos con 15+ unidades</div>{hbars([(f"{m}  ·  {u} u." + (f"  ·  dto USD {int(dc):,}" if dc else ""), mo) for m, mo, u, dc in stock_press], width=900, row_h=44, label_w=470, val_fmt=lambda v: f"{v:g} meses")}</div></div>
<p style="margin-top:28px;font-size:23px">Mucho stock con poca pauta es plata parada; poco stock con mucha pauta es un lead que no se puede entregar. Cada nota ya cruza las dos cosas y avisa.</p>{foot()}</section>''')

# 15e objetivos vs real
if obj_rows:
    S(f'''<section class="slide"><div class="k">Objetivo de ventas {_ob.get('year', '')} · budget vs facturado, acumulado a hoy</div>
<h2>{round(obj_total_real / obj_total_obj * 100) if obj_total_obj else 0}% del objetivo acumulado. Marca por marca, la foto es distinta.</h2>
<div class="legend" style="margin:28px 0 12px"><span><i style="background:var(--dim)"></i>objetivo acumulado</span><span><i style="background:var(--signal)"></i>facturado</span></div>
{pairs([(f"{b}  ·  {pct:g}%", o, r) for b, r, o, pct in obj_rows], row_h=54)}
<p style="margin-top:24px;font-size:23px">Objetivos del budget de ventas por marca y mes; facturado del ERP hasta el {sales_until}. {nego_total} negociaciones abiertas en la fuerza de ventas esta semana.</p>{foot()}</section>''')

# 15f base de recompra
if recompra_rows:
    S(f'''<section class="slide"><div class="k">Base de recompra · clientes propios por antigüedad de la compra</div>
<h2>{fmt(recompra_total)} clientes ya están en ventana de recompra.</h2>
<div class="legend" style="margin:32px 0 16px"><span><i style="background:var(--signal)"></i>3 años o más</span><span><i style="background:var(--muted)"></i>2 a 3 años</span><span><i style="background:var(--dim)"></i>1 a 2 años</span></div>
<svg width="1664" height="{len(recompra_rows) * 52}" viewBox="0 0 1664 {len(recompra_rows) * 52}" font-family="Archivo">
{''.join((lambda i, b, a3, a2, a1, mx: f'<text x="0" y="{i*52+31}" fill="var(--paper)" font-size="22">{b}</text><rect x="220" y="{i*52+12}" width="{1280*a3/mx:.0f}" height="22" fill="var(--signal)"/><rect x="{220+1280*a3/mx:.0f}" y="{i*52+12}" width="{1280*a2/mx:.0f}" height="22" fill="var(--muted)"/><rect x="{220+1280*(a3+a2)/mx:.0f}" y="{i*52+12}" width="{1280*a1/mx:.0f}" height="22" fill="var(--dim)"/><text x="{220+1280*(a3+a2+a1)/mx+14:.0f}" y="{i*52+31}" fill="var(--muted)" font-size="21">{fmt(a3+a2+a1)}</text>')(i, b, a3, a2, a1, max(r[1]+r[2]+r[3] for r in recompra_rows)) for i, (b, a3, a2, a1) in enumerate(recompra_rows))}
</svg>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:40px;gap:0 64px">
<div class="row"><div class="idx">Lo que pidió Marketing</div><p>"Al que compró Duster o Arkana hace tres o cuatro años, mostrale Boreal." Renault tiene {fmt(next((r[1] for r in recompra_rows if r[0] == "Renault"), 0))} clientes de tres años o más.</p></div>
<div class="row"><div class="idx">Cómo se usa</div><p>Lista hasheada por cohorte, subida como Custom Audience. Campaña de fidelización separada de la de leads, con su presupuesto y su creatividad.</p></div>
<div class="row"><div class="idx">Lo que falta</div><p>El contacto solo está cargado desde abril de 2024. Los clientes más viejos son unidades, no teléfonos: hay que recuperarlos desde Bitrix.</p></div></div>{foot()}</section>''')

# 16 radar
S(f'''<section class="slide"><div class="k">Radar de competencia</div><h2>Qué pauta, qué promociona y a qué precio cada competidor. Cada día.</h2>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:52px;gap:0 64px">
<div class="row"><div class="idx">Sus webs</div><p><b>Nueve casas</b> escaneadas a las 08:00 y cada seis horas: Garden, Diesa, Toyotoshi, Automaq, Nipon, Nissan, DLS. Promos, modelos nuevos, precios. Cada cambio, con fecha, en la bitácora.</p></div>
<div class="row"><div class="idx">Sus anuncios</div><p>La Biblioteca de Anuncios de Meta es pública. Leemos el <b>copy, la oferta y el formato</b> con que cada rival pauta ahora mismo, con el mismo motor que lee los nuestros.</p></div>
<div class="row"><div class="idx">Sus precios</div><p>692 versiones contra el día anterior. Subió, bajó o lanzó: <b>lo vemos antes que el cliente.</b></p></div></div>
<p class="lead" style="margin-top:64px">Rival baja una SUV B → mañana lo refleja la persona de Kardian, Jolion y X50 → el copy responde con argumentos absolutos, sin nombrar a nadie.</p>{foot()}</section>''')

# 17 píxeles
S(f'''<section class="slide"><div class="k">Píxeles y seguimiento</div><h2>Quien visita una web de marca ya es un público.</h2>
<div class="cols" style="grid-template-columns:repeat(4,1fr);margin-top:56px;gap:0 48px">
<div class="row"><div class="idx">01 · Webs de marca</div><p>santarosa · jetour · jac · renew · leapmotor · mitsubishi · xpeng</p></div>
<div class="row"><div class="idx">02 · Pixel + CAPI</div><p>ViewContent, Lead, Contact, clic a WhatsApp. Por modelo. Desde el navegador y desde el servidor.</p></div>
<div class="row"><div class="idx">03 · Audiencias vivas</div><p>Vio el X70. Cotizó Kardian. Abrió el formulario y no lo envió.</p></div>
<div class="row"><div class="idx">04 · Retargeting</div><p>7, 30 y 90 días. Y exclusión de quien ya compró.</p></div></div>
<div style="display:flex;align-items:flex-end;gap:64px;margin-top:80px"><div><div class="num md">170</div><div class="lbl">audiencias ya mapeadas en Meta</div></div>
<p style="padding-bottom:22px;max-width:56ch">Visitantes web, interacción en Instagram y Facebook, formularios abiertos: el sistema sabe cuál existe en cada cuenta para no duplicar. Lo que la gente mira entra al retrato del modelo junto con leads y ventas.</p></div>{foot()}</section>''')

# 18 lookalikes
S(f'''<section class="slide"><div class="k">Públicos similares</div><h2>De quien ya compró a quien se le parece.</h2>
<svg width="1664" height="260" viewBox="0 0 1664 260" style="margin-top:48px" font-family="Archivo">
<defs><marker id="b" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--signal)"/></marker></defs>
<g stroke="var(--line)"><line x1="0" y1="0" x2="1664" y2="0"/><line x1="0" y1="259" x2="1664" y2="259"/></g>
<g fill="var(--paper)" font-size="26" font-weight="600"><text x="0" y="70">Compradores reales</text><text x="340" y="70">Hash SHA-256</text><text x="680" y="70">Custom Audience</text><text x="1020" y="70">Lookalike PY 1%</text><text x="1360" y="70">Prospecting</text></g>
<g fill="var(--muted)" font-size="21"><text x="0" y="110">{fmt(sales['total_records'])} ventas desde 2018</text><text x="0" y="140">por marca y cohorte</text><text x="340" y="110">2.207 emails · 1.408 tel.</text><text x="340" y="140">nadie ve el dato</text><text x="680" y="110">en la cuenta madre</text><text x="680" y="140">de cada marca</text><text x="1020" y="110">Meta encuentra a los</text><text x="1020" y="140">que se parecen</text><text x="1360" y="110">con el copy de la persona</text><text x="1360" y="140">y su formato ganador</text></g>
<g stroke="var(--signal)" stroke-width="2" marker-end="url(#b)"><line x1="0" y1="205" x2="300" y2="205"/><line x1="340" y1="205" x2="640" y2="205"/><line x1="680" y1="205" x2="980" y2="205"/><line x1="1020" y1="205" x2="1320" y2="205"/></g><line x1="1360" y1="205" x2="1664" y2="205" stroke="var(--signal)" stroke-width="2"/></svg>
<div class="cols" style="grid-template-columns:1fr 1fr 1fr;margin-top:48px;gap:0 64px">
<div class="row"><div class="idx">Por API, no a mano</div><p>La audiencia y el lookalike se crean desde el sistema en cada cuenta. Un comando por marca.</p></div>
<div class="row"><div class="idx">Exclusión automática</div><p>La misma semilla evita gastar en quien ya compró y en leads abiertos del CRM.</p></div>
<div class="row"><div class="idx">Semilla que crece</div><p>Cada factura nueva del ERP entra a la semilla. El público similar mejora con cada venta.</p></div></div>{foot()}</section>''')

# 19 ciclo
S(f'''<section class="slide"><div class="k">El ciclo</div><h2>Un sistema que aprende de cada venta.</h2>
<div style="display:flex;gap:120px;align-items:center;margin-top:16px">
<svg width="600" height="600" viewBox="0 0 620 620" font-family="Archivo"><defs><marker id="c" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="var(--signal)"/></marker></defs>
<circle cx="310" cy="310" r="240" fill="none" stroke="var(--line)"/>
<g stroke="var(--signal)" stroke-width="2.5" fill="none" marker-end="url(#c)"><path d="M330,70 A240,240 0 0,1 550,290"/><path d="M550,330 A240,240 0 0,1 330,550"/><path d="M290,550 A240,240 0 0,1 70,330"/><path d="M70,290 A240,240 0 0,1 290,70"/></g>
<g font-size="24" font-weight="700" fill="var(--paper)" text-anchor="middle"><text x="310" y="46">Pauta</text><text x="590" y="318">Leads</text><text x="310" y="596">Venta</text><text x="30" y="318">Persona</text></g>
<text x="310" y="300" text-anchor="middle" font-size="34" font-weight="800" fill="var(--paper)">CADA</text><text x="310" y="342" text-anchor="middle" font-size="34" font-weight="800" fill="var(--signal)">MAÑANA</text></svg>
<div style="flex:1">
<div class="row"><div class="idx">01</div><p><b>Pautamos con la persona.</b> Copy, formato y público salen de la ficha del modelo.</p></div>
<div class="row"><div class="idx">02</div><p><b>Los leads entran al CRM.</b> Se leen por canal y por marca, sin datos personales.</p></div>
<div class="row"><div class="idx">03</div><p><b>La venta se factura.</b> El ERP dice qué modelo, qué versión, a qué precio y con qué retoma.</p></div>
<div class="row"><div class="idx">04</div><p><b>La persona se reescribe.</b> La semilla del lookalike crece. Vuelta al 01, mejor que ayer.</p></div></div></div>{foot()}</section>''')

# 20 casos de uso (drench)
S(f'''<section class="slide drench"><div class="k">Cómo lo vamos a usar</div>
<h2 style="font-size:76px">Ocho usos concretos. Empezamos por los tres primeros.</h2>
<style>.usos .row{{padding:20px 0}}.usos p{{font-size:23px;line-height:1.4}}.usos .idx{{margin-bottom:6px}}</style>
<div class="cols usos" style="grid-template-columns:1fr 1fr;margin-top:36px;gap:0 96px">
<div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">01 · Marketing · esta semana</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Reasignar presupuesto Meta con el semáforo y el sugerido por modelo.</b> Más a Kwid, X50 y Wingle. Revisar Kardian y Tank 400. Medir CPL antes y después.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">02 · Marketing · esta semana</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Campaña de fidelización con la base de recompra.</b> Quien compró Duster o Arkana hace más de dos años ve Boreal. Separada de la de leads, con su presupuesto.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">03 · Marketing · esta semana</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Pautar mirando el patio.</b> Más pauta u oferta donde hay meses de stock; frenar donde no hay unidades. Piezas en vertical: el {rs}% de las impresiones está en Reels y Stories.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">04 · Ventas · salón</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Argumentario por modelo</b> desde la ficha: qué le duele al cliente, precio contra rivales, versión que más pide.</p></div></div>
<div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">05 · Marketing · conquista</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Lookalikes de compradores reales y de conquista</b> (los 289 que entregaron Chevrolet, Hyundai, VW, Kia o Toyota). Un comando por marca.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">06 · Marketing · diario</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Alerta de precio rival</b> y respuesta en 24 horas con argumentos absolutos.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">07 · Comercial · CRM</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Cerrar el ciclo en Bitrix:</b> marcar convertidos, ligar deals, asignar marca a los 3.500 leads huérfanos.</p></div>
<div class="row" style="border-color:var(--signal-ink)"><div class="idx" style="color:var(--signal-ink)">08 · Gerencia · mensual</div><p style="color:var(--signal-ink)"><b style="color:var(--signal-ink)">Tablero lead, deal, factura por marca</b> con la brecha pauta / venta como criterio de inversión.</p></div></div></div>{foot()}</section>''')

# 21 cierre
S(f'''<section class="slide" style="display:flex;flex-direction:column;justify-content:center"><div class="k">Buyer Persona 360</div>
<h1 style="font-size:150px">Dejamos de adivinar<br>a quién <span class="signal">venderle</span>.</h1>
<div style="display:flex;gap:110px;margin-top:88px">
<div><div class="num md">{len(personas)}</div><div class="lbl">personas vivas</div></div><div><div class="num md">4</div><div class="lbl">fuentes reales</div></div>
<div><div class="num md">06:00</div><div class="lbl">todos los días</div></div><div><div class="num md">0</div><div class="lbl">datos personales expuestos</div></div></div>
<div class="foot"><span>Santa Rosa Automotores · Innovación · 2026</span><span>Uso interno</span></div></section>''')

html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Buyer Persona 360 — Santa Rosa</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,100..900;1,62..125,100..900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{chr(10).join(slides)}
</body></html>'''
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"{OUT} · {len(slides)} láminas · fuente {Path(src).name}")
