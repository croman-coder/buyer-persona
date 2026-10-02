#!/usr/bin/env python3
"""
Láminas Buyer Persona para el directorio · Mitsubishi y JAC (pedido de Cecilia, 24-09-2026).

Mismo estilo que las del comité de Valentina (output/presentacion/comite_2026-09-21):
HTML de 1920×1080 → PNG con Chrome sin ventana, para pegar en el PowerPoint.
Cuatro por marca, en el orden que pidió Cecilia:

  1. Buyer persona de la marca
  2. Buyer persona por segmento  (MMC: Comerciales livianos / SUV · JAC: Utilitarios / Pasajeros)
  3. Buyer persona por modelo    (los modelos foco de su lista)
  4. Intereses por modelo        (matriz de temas)

Datos: el JSON de personas del día (output/raw/personas_*.json, solo agregados)
y la matriz de temas por modelo calculada sobre los anuncios de Meta del mismo
día. Los segmentos se arman sumando los modelos: ventas y pedidos se suman,
edad y género se ponderan por clics, ticket por ventas, temas por anuncios.

Uso:
  python3 scripts/laminas_directorio_mmc_jac.py <personas.json> <matriz_intereses.json>
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "presentacion" / "directorio_2026-09-24"
OUT.mkdir(parents=True, exist_ok=True)
PERSONAS = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
PERSONAS = PERSONAS.get("personas", PERSONAS) if isinstance(PERSONAS, dict) else PERSONAS
MATRIZ = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
P = {p["name"]: p for p in PERSONAS}
VM = MATRIZ["ventana_meta"]

# ------------------------------------------------------------------ formato
def n(x):   return f"{int(round(x or 0)):,}".replace(",", ".")
def usd(x): return f"USD {n(x)}"
def usd2(x): return f"USD {x:.2f}".replace(".", ",") if x else "—"
def pct(x, d=0): return (f"{x:.{d}f}".replace(".", ",") if d else str(int(round(x or 0)))) + " %"
def fecha(iso): y, m, d = iso.split("-"); return f"{d}-{m}"

TEMAS_CORTOS = {
    "Financiación en cuotas": "Financiación en cuotas",
    "Garantía y respaldo posventa": "Garantía y respaldo",
    "Tecnología y conectividad": "Tecnología",
    "Diseño y estatus": "Diseño y estatus",
    "Seguridad y asistencias a la conducción": "Seguridad",
    "Familia y espacio": "Familia y espacio",
    "Probar antes de comprar (test drive)": "Test drive",
    "Trabajo, negocio y carga": "Trabajo y carga",
    "Autos eléctricos y ahorro de combustible": "Eléctrico / ahorro",
}

# ------------------------------------------------------------------ datos
def modelo(nombre):
    p = P[nombre]; s = p["segment"]; dm = p["demographics"]; m = dm.get("meta") or {}
    rl = p.get("real_leads") or {}; e = p.get("erp") or {}; ex = p.get("extras") or {}
    return dict(
        nombre=nombre, corto=nombre.split(" ", 1)[1] if " " in nombre else nombre,
        v12=s.get("orders_last_365d") or 0, total=s.get("orders") or 0,
        anuncios=s.get("ad_count") or 0, sales_share=s.get("sales_share"), ad_share=s.get("ad_share"), gap=s.get("gap"),
        propio=dm.get("meta_level") == "modelo", clics=m.get("weight") or 0,
        hombre=m.get("gender_share") if dm.get("gender") == "Masculino" else 100 - (m.get("gender_share") or 0),
        edad=dm.get("age_range"), edad_pct=m.get("age_share"), edades=m.get("age_distribution") or {},
        nse=(p.get("nse") or {}).get("nivel", ""), ticket=(e.get("price") or {}).get("avg"),
        pedidos=((rl.get("this_model") or {}).get("count")) or 0, pedidos_pct=((rl.get("this_model") or {}).get("pct")) or 0,
        versiones=e.get("top_versions") or [], stock=(ex.get("stock") or {}).get("total"),
        dias=(ex.get("stock") or {}).get("dias_promedio"),
        temas=MATRIZ["modelos"].get(nombre, {}).get("temas", {}), n_anuncios=MATRIZ["modelos"].get(nombre, {}).get("n", 0),
    )

def marca(nombre_marca):
    p = P[f"Comprador {nombre_marca}"]; dm = p["demographics"]; m = dm.get("meta") or {}
    b = p.get("budget") or {}; rl = p.get("real_leads") or {}; ex = p.get("extras") or {}
    modelos = [modelo(q["name"]) for q in PERSONAS if q["segment"].get("type") == "model" and q["segment"].get("brand") == nombre_marca]
    return dict(
        nombre=nombre_marca, modelos=modelos, v12=sum(x["v12"] for x in modelos),
        hombre=m.get("gender_share"), edad=dm.get("age_range"), edad_pct=m.get("age_share"), edades=m.get("age_distribution") or {},
        clics=m.get("weight"), nse=(p.get("nse") or {}).get("nivel", ""), nse_senales=(p.get("nse") or {}).get("senales", []),
        ticket=((p.get("erp") or {}).get("price") or {}).get("avg"),
        leads=b.get("leads_90d"), cpl=b.get("cpl"), gasto_mes=b.get("spend_month"),
        ciudades=list((rl.get("city") or {}).items())[:4], pedidos=list((rl.get("model_interest_norm") or {}).items())[:6],
        intencion=rl.get("purchase_intent") or {}, total_leads=rl.get("total_leads") or 0,
        objetivo=ex.get("objetivos") or {}, mix=p.get("audience_mix") or {}, formato=p.get("creative_format") or {},
        temas=MATRIZ["modelos"].get(f"{nombre_marca} (marca)", {}).get("temas", {}),
        n_anuncios=MATRIZ["modelos"].get(f"{nombre_marca} (marca)", {}).get("n", 0),
    )

def segmento(nombres):
    ms = [modelo(x) for x in nombres if x in P]
    demo = [x for x in ms if x["propio"] and x["clics"]]
    w = sum(x["clics"] for x in demo) or 1
    edades = {}
    for x in demo:
        for k, v in x["edades"].items():
            edades[k] = edades.get(k, 0) + v * x["clics"] / w
    v12 = sum(x["v12"] for x in ms)
    na = sum(x["n_anuncios"] for x in ms) or 1
    temas = {}
    for x in ms:
        for t, v in x["temas"].items():
            temas[t] = temas.get(t, 0) + v * x["n_anuncios"] / na
    top_edad = max(edades.items(), key=lambda kv: kv[1]) if edades else ("—", 0)
    return dict(
        modelos=ms, v12=v12, pedidos=sum(x["pedidos"] for x in ms),
        hombre=sum(x["hombre"] * x["clics"] for x in demo) / w if demo else None,
        edades=edades, edad=top_edad[0], edad_pct=top_edad[1],
        ticket=sum((x["ticket"] or 0) * x["v12"] for x in ms) / v12 if v12 else None,
        temas=dict(sorted(temas.items(), key=lambda kv: -kv[1])), n_anuncios=na, clics=w,
    )

# ------------------------------------------------------------------ piezas HTML
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#fff;font-family:Inter,Arial,Helvetica,sans-serif;color:#111}
.slide{width:1920px;height:1080px;position:relative;overflow:hidden;background:#fff;padding:56px 100px}
.k{font-size:21px;letter-spacing:.18em;text-transform:uppercase;color:#6b6b6b;font-weight:600}
h1{font-size:52px;font-weight:800;letter-spacing:-.02em;line-height:1.06;margin-top:10px;max-width:1720px}
h1 span{color:#e8590c}
.grid{display:grid;gap:44px;margin-top:30px}
.col h2{font-size:17px;letter-spacing:.14em;text-transform:uppercase;color:#777;font-weight:700;border-top:3px solid #111;padding-top:12px;margin-bottom:14px}
.big{font-size:54px;font-weight:800;letter-spacing:-.03em;line-height:1}
.big small{font-size:24px;font-weight:700;color:#555;letter-spacing:0;margin-left:6px}
.sub{font-size:19px;color:#444;margin-top:6px;line-height:1.35}
.bar{display:grid;grid-template-columns:150px 1fr 64px;align-items:center;gap:12px;margin:9px 0;font-size:19px}
.bar .t{height:22px;background:#f1f1f1;position:relative}
.bar .t i{position:absolute;left:0;top:0;bottom:0;background:#111}
.bar.hi .t i{background:#e8590c}
.bar b{text-align:right;font-weight:800}
.kpi{border-bottom:1px solid #e3e3e3;padding:12px 0}
.kpi:first-of-type{padding-top:0}
.kpi .v{font-size:38px;font-weight:800;letter-spacing:-.02em}
.kpi .v.o{color:#e8590c}
.kpi .l{font-size:18px;color:#444;margin-top:4px;line-height:1.35}
.nota{font-size:17px;color:#555;line-height:1.4;margin-top:12px;border-left:4px solid #e8590c;padding-left:14px}
.foot{position:absolute;left:100px;right:100px;bottom:34px;font-size:16px;color:#777;display:flex;justify-content:space-between;gap:48px;border-top:1px solid #ddd;padding-top:12px;line-height:1.35}
.foot span:first-child{flex:1}
.foot span:last-child{max-width:520px;text-align:right}
.seg{border:2px solid #111;padding:22px 28px}
.seg.dark{background:#111;color:#fff}
.seg h3{font-size:34px;font-weight:800;letter-spacing:-.02em}
.seg h3 small{display:block;font-size:18px;font-weight:600;color:#e8590c;letter-spacing:.06em;text-transform:uppercase;margin-top:6px}
.seg.dark h3 small{color:#ffb27a}
.seg .row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-top:18px}
.seg .row div b{display:block;font-size:34px;font-weight:800;letter-spacing:-.02em}
.seg .row div span{font-size:16px;color:#666;text-transform:uppercase;letter-spacing:.06em}
.seg.dark .row div span{color:#aaa}
.seg ul{list-style:none;margin-top:16px}
.seg li{font-size:19px;line-height:1.4;padding:5px 0;border-top:1px solid #e3e3e3}
.seg.dark li{border-color:#333}
.seg li b{font-weight:800}
.seg .bar .t{background:#ececec}
.seg.dark .bar .t{background:#2a2a2a}
.seg.dark .bar .t i{background:#fff}
.seg.dark .bar.hi .t i{background:#ffb27a}
.cards{display:grid;gap:18px;margin-top:26px}
.card{border:2px solid #111;padding:18px 20px;display:flex;flex-direction:column}
.card.o{border-color:#e8590c}
.card .tag{font-size:14px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#e8590c;margin-bottom:6px}
.card h3{font-size:27px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.card h3 small{display:block;font-size:15px;color:#777;font-weight:600;letter-spacing:.04em;margin-top:5px;text-transform:uppercase}
.card .nums{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin:14px 0 10px;padding:10px 0;border-top:1px solid #e3e3e3;border-bottom:1px solid #e3e3e3}
.card .nums b{display:block;font-size:26px;font-weight:800;letter-spacing:-.02em}
.card .nums span{font-size:14px;color:#666;text-transform:uppercase;letter-spacing:.05em}
.card p{font-size:17px;line-height:1.38;color:#222;margin-top:6px}
.card p b{font-weight:800}
.card .clave{margin-top:auto;padding-top:10px;font-size:16.5px;line-height:1.35;color:#e8590c;font-weight:700}
table.hm{width:100%;border-collapse:collapse;margin-top:26px}
table.hm th{font-size:16px;letter-spacing:.06em;text-transform:uppercase;color:#666;font-weight:700;padding:8px 6px;text-align:center;border-bottom:3px solid #111;vertical-align:bottom}
table.hm th:first-child{text-align:left}
table.hm td{font-size:21px;font-weight:700;text-align:center;padding:11px 6px;border-bottom:1px solid #fff}
table.hm td:first-child{text-align:left;font-weight:800;font-size:21px;background:#fff!important;color:#111!important;padding-left:0}
table.hm td:first-child small{display:block;font-size:14px;color:#777;font-weight:600}
table.hm tr.marca td{border-top:2px solid #111}
table.hm.compacta td{padding:7px 6px;font-size:19px}
table.hm.compacta td:first-child{font-size:19px}
table.hm.compacta td:first-child small{font-size:13px}
table.hm.compacta tr.grupo td{padding:9px 0 3px}
table.hm tr.grupo td{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:#777;font-weight:700;background:#fff!important;padding:14px 0 4px;text-align:left}
"""

def pagina(cuerpo):
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style></head><body><section class="slide">{cuerpo}</section></body></html>'

def barras(pares, hi=None, escala=None):
    escala = escala or max([v for _, v in pares] + [1])
    out = []
    for etq, v in pares:
        cls = " hi" if hi and etq == hi else ""
        out.append(f'<div class="bar{cls}"><span>{etq}</span><div class="t"><i style="width:{min(100, v / escala * 100):.1f}%"></i></div><b>{pct(v)}</b></div>')
    return "".join(out)

ORDEN_EDADES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
def edades(dist, top):
    return barras([(e, dist.get(e, 0)) for e in ORDEN_EDADES], hi=top, escala=45)

def temas_top(temas, k=6):
    pares = [(TEMAS_CORTOS.get(t, t), v) for t, v in sorted(temas.items(), key=lambda kv: -kv[1]) if t in TEMAS_CORTOS][:k]
    return barras(pares, escala=100)

def pie(izq, der):
    return f'<div class="foot"><span>{izq}</span><span>{der}</span></div>'

FUENTE = (f"Edad y género: quién hace clic en los anuncios de Meta ({fecha(VM['start'])} → {fecha(VM['end'])}), no quién firmó la compra · "
          "ventas: ERP hasta 11-09")

# ------------------------------------------------------------------ 1. marca
def lamina_marca(M, titulo, destacado, nota):
    ob = M["objetivo"]
    top_ped = sorted(((x["corto"], x["pedidos"]) for x in M["modelos"] if x["pedidos"]), key=lambda kv: -kv[1])[:5]
    tl = M["total_leads"] or 1
    pedidos_html = "".join(f"<div class='bar'><span>{x}</span><div class='t'><i style='width:{v / top_ped[0][1] * 100:.1f}%'></i></div><b>{pct(v / tl * 100)}</b></div>" for x, v in top_ped)
    ciudades = " · ".join(f"{c} {n(v)}" for c, v in M["ciudades"])
    cuerpo = f"""
<div class="k">Buyer Persona 360 · {M['nombre']} · la marca</div>
<h1>{titulo} <span>{destacado}</span></h1>
<div class="grid" style="grid-template-columns:1.05fr 1fr 1fr">
  <div class="col">
    <h2>Quién es</h2>
    <div class="big">Hombre · {pct(M['hombre'])}<small>de los clics</small></div>
    <div class="sub">Edad más frecuente <b>{M['edad']}</b> ({pct(M['edad_pct'])}) · {n(M['clics'])} clics medidos</div>
    <div style="margin-top:16px">{edades(M['edades'], M['edad'])}</div>
    <div class="nota">Leads por ciudad: {ciudades}.</div>
  </div>
  <div class="col">
    <h2>Qué le interesa</h2>
    {temas_top(M['temas'])}
    <div class="sub" style="font-size:16px;margin-top:10px">% de sus {n(M['n_anuncios'])} anuncios que tocan cada tema: es lo que este público ve y clickea. Meta no entrega intereses declarados desde 2021.</div>
    <h2 style="margin-top:26px">Nivel socioeconómico</h2>
    <div class="big" style="font-size:40px">{M['nse']}<small>estimado</small></div>
    <div class="sub" style="font-size:17px">Ticket facturado {usd(M['ticket'])} · se estima con precio, financiación, dispositivo (iPhone/Android) y zona.</div>
  </div>
  <div class="col">
    <h2>Cómo le va</h2>
    <div class="kpi"><div class="v">{n(M['v12'])} unidades</div><div class="l">vendidas en los últimos 12 meses (ERP)</div></div>
    <div class="kpi"><div class="v o">{n(ob.get('real_ytd'))} de {n(ob.get('objetivo_ytd'))} · {pct(ob.get('avance_ytd_pct'))}</div><div class="l">avance del objetivo 2026 a septiembre · anual {n(ob.get('objetivo_anual'))}</div></div>
    <div class="kpi"><div class="v">{n(M['leads'])} leads · CPL {usd2(M['cpl'])}</div><div class="l">formularios de Meta en 90 días · ~{usd(M['gasto_mes'])}/mes de pauta</div></div>
    <h2 style="margin-top:18px">Qué modelo pide en el formulario</h2>
    {pedidos_html}
  </div>
</div>
<div class="nota" style="position:absolute;left:100px;right:100px;bottom:92px;font-size:19px;color:#222">{nota}</div>
{pie(FUENTE, 'Fuente: Buyer Persona 360 · vault Obsidian y cerebro.santarosa.lat')}"""
    return pagina(cuerpo)

# ------------------------------------------------------------------ 2. segmentos
def bloque_seg(nombre, sub, S, modelos_txt, clave, dark=False):
    return f"""
  <div class="seg{' dark' if dark else ''}">
    <h3>{nombre}<small>{sub}</small></h3>
    <div class="row">
      <div><b>{n(S['v12'])}</b><span>ventas 12 meses</span></div>
      <div><b>{n(S['pedidos'])}</b><span>pedidos en formularios</span></div>
      <div><b>{usd(S['ticket'])}</b><span>ticket facturado</span></div>
    </div>
    <ul>
      <li><b>Hombre {pct(S['hombre'])}</b> · edad más frecuente <b>{S['edad']}</b> ({pct(S['edad_pct'])})</li>
      <li>Modelos: {modelos_txt}</li>
    </ul>
    <div style="margin-top:14px">{temas_top(S['temas'], 5)}</div>
    <div class="{'' if dark else 'nota'}" style="{'margin-top:14px;font-size:19px;color:#ffb27a;font-weight:700' if dark else 'font-size:19px;color:#111;font-weight:700'}">{clave}</div>
  </div>"""

def lamina_segmentos(M, titulo, destacado, A, B, pie_extra):
    cuerpo = f"""
<div class="k">Buyer Persona 360 · {M['nombre']} · por segmento</div>
<h1>{titulo} <span>{destacado}</span></h1>
<div class="grid" style="grid-template-columns:1fr 1fr;gap:40px">{A}{B}</div>
{pie(FUENTE + ' · temas ponderados por anuncios, edad y género por clics', pie_extra)}"""
    return pagina(cuerpo)

# ------------------------------------------------------------------ 3. modelos
def tarjeta(x, titulo, sub, clave, extra="", naranja=False, tag=""):
    top3 = [TEMAS_CORTOS.get(t, t) + f" {pct(v)}" for t, v in sorted(x["temas"].items(), key=lambda kv: -kv[1]) if t in TEMAS_CORTOS][:3]
    stock = f" · stock {n(x['stock'])}" + (f" ({n(x['dias'])} días)" if x.get("dias") else "") if x.get("stock") else ""
    return f"""
  <div class="card{' o' if naranja else ''}">
    <div class="tag">{tag}</div>
    <h3>{titulo}<small>{sub}</small></h3>
    <div class="nums">
      <div><b>{n(x['v12'])}</b><span>ventas 12 m</span></div>
      <div><b>{n(x['pedidos']) if x['pedidos'] else '—'}</b><span>pedidos</span></div>
      <div><b>{pct(x['hombre'])}</b><span>hombre</span></div>
      <div><b>{x['edad']}</b><span>edad ({pct(x['edad_pct'])})</span></div>
    </div>
    <p><b>{usd(x['ticket'])}</b> ticket · NSE {x['nse'].split(' ')[0]}{stock}</p>
    <p>Le mueve: {' · '.join(top3)}</p>
    {extra}
    <div class="clave">{clave}</div>
  </div>"""

def lamina_modelos(M, titulo, destacado, tarjetas, cols, pie_extra):
    cuerpo = f"""
<div class="k">Buyer Persona 360 · {M['nombre']} · por modelo</div>
<h1>{titulo} <span>{destacado}</span></h1>
<div class="cards" style="grid-template-columns:repeat({cols},1fr)">{''.join(tarjetas)}</div>
{pie(FUENTE + ' · pedidos: formularios de Meta en 90 días', pie_extra)}"""
    return pagina(cuerpo)

# ------------------------------------------------------------------ 4. intereses
def color(v):
    if v is None: return "background:#fafafa;color:#bbb", "·"
    a = min(1, v / 100)
    fondo = f"rgba(232,89,12,{0.08 + a * 0.85:.2f})"
    return f"background:{fondo};color:{'#fff' if a > 0.55 else '#111'}", pct(v)

def lamina_intereses(M, titulo, destacado, filas, temas, lecturas, compacta=False):
    ths = "".join(f"<th>{TEMAS_CORTOS[t]}</th>" for t in temas)
    trs = []
    for f in filas:
        if isinstance(f, str):
            trs.append(f'<tr class="grupo"><td colspan="{len(temas) + 1}">{f}</td></tr>'); continue
        etq, sub, tm, es_marca = f
        celdas = "".join(f'<td style="{color(tm.get(t))[0]}">{color(tm.get(t))[1]}</td>' for t in temas)
        trs.append(f'<tr class="{"marca" if es_marca else ""}"><td>{etq}<small>{sub}</small></td>{celdas}</tr>')
    cuerpo = f"""
<div class="k">Buyer Persona 360 · {M['nombre']} · intereses por modelo</div>
<h1>{titulo} <span>{destacado}</span></h1>
<div class="grid" style="grid-template-columns:1.9fr 1fr;gap:48px;margin-top:6px">
  <div><table class="hm{' compacta' if compacta else ''}"><tr><th style="width:230px">Modelo</th>{ths}</tr>{''.join(trs)}</table></div>
  <div class="col" style="margin-top:26px"><h2>Cómo leerlo</h2>{''.join(f'<div class="kpi"><div class="l" style="font-size:19px;color:#111">{l}</div></div>' for l in lecturas)}</div>
</div>
{pie('Cada celda: % de los anuncios reales del modelo que tocan ese tema; es lo que su público ve y clickea (Meta, ' + fecha(VM['start']) + ' → ' + fecha(VM['end']) + ')', 'Meta no entrega intereses declarados desde 2021')}"""
    return pagina(cuerpo)

# ================================================================== MITSUBISHI
MM = marca("Mitsubishi")
mm = {x["corto"]: x for x in MM["modelos"]}
suv_n = ["Mitsubishi Montero Sport", "Mitsubishi Eclipse Cross", "Mitsubishi Outlander", "Mitsubishi Destinator"]
COM, SUV = segmento(["Mitsubishi L200"]), segmento(suv_n)

laminas = {}
laminas["mmc_1_marca"] = lamina_marca(
    MM, "Quién compra Mitsubishi: hombre de 35 a 44 años, de Asunción y CDE,",
    "que decide por la cuota y el respaldo.",
    f"<b>Lectura:</b> la L200 es la marca: 67 % de las ventas y 47 % de los pedidos. El comprador pregunta por la <b>cuota</b> (51 % de los anuncios) "
    f"y confía en la <b>garantía y el respaldo</b> (41 %). Reels y stories ya se llevan el {pct(MM['formato'].get('top_format_share', 0))} de las impresiones: ahí va la pieza nueva.")

laminas["mmc_2_segmentos"] = lamina_segmentos(
    MM, "Dos compradores distintos: la L200 se compra para trabajar;",
    "el SUV, por diseño, tecnología y seguridad.",
    bloque_seg("Comerciales livianos", "L200 · New L200 y Triton", COM, "New L200 · L200 Triton (una sola persona: los anuncios no las distinguen)",
               "Hablarle de cuota, respaldo y capacidad de trabajo."),
    bloque_seg("SUV", "Montero Sport · Eclipse Cross · New Outlander · Destinator", SUV, "Montero Sport · Eclipse Cross · New Outlander · Destinator",
               f"Pide casi lo mismo que la L200 ({n(SUV['pedidos'])} vs {n(COM['pedidos'])}) y vende la mitad ({n(SUV['v12'])} vs {n(COM['v12'])}): el trabajo está en convertir ese interés.", dark=True),
    "Outlander y Destinator recién llegan: pocas ventas, mucho interés")

versiones_l200 = "En el ERP, 175 de las 190 ventas son versiones Triton Sport y 15 cabina simple GL: New L200 y Triton comparten comprador."
laminas["mmc_3_modelos"] = lamina_modelos(
    MM, "Por modelo, cada Mitsubishi tiene su comprador.", "El Eclipse Cross es el más joven; el Outlander, el más caro.",
    [tarjeta(mm["L200"], "L200", "New L200 · L200 Triton", tag="Comercial liviano", clave= "Cuota + respaldo. 80 en stock con 245 días promedio: presión para acelerar.",
             extra=f"<p style='font-size:15px;color:#666'>{versiones_l200}</p>", naranja=True),
     tarjeta(mm["Montero Sport"], "Montero Sport", "7 plazas", tag="SUV", clave= "Respaldo y diseño. 89 en stock con 229 días: el otro candidato a más pauta u oferta."),
     tarjeta(mm["Eclipse Cross"], "Eclipse Cross", "compacto", tag="SUV", clave= "El público más joven (25-34) y con más mujeres: diseño y tecnología ante todo."),
     tarjeta(mm["Outlander"], "New Outlander", "premium", tag="SUV", clave= "Tecnología (88 %) y seguridad (67 %): el anuncio tiene que mostrar el equipamiento."),
     tarjeta(mm["Destinator"], "Destinator", "lanzamiento", tag="SUV", clave= "316 pedidos con 3 ventas: el interés está, falta convertirlo. Único que habla de familia (50 %).")],
    5, "Brecha pauta/venta en la ficha de cada modelo")

T_MMC = ["Financiación en cuotas", "Garantía y respaldo posventa", "Tecnología y conectividad", "Diseño y estatus",
         "Seguridad y asistencias a la conducción", "Familia y espacio", "Probar antes de comprar (test drive)"]
mi = MATRIZ["modelos"]
laminas["mmc_4_intereses"] = lamina_intereses(
    MM, "Intereses por modelo:", "la cuota es de todos; el resto cambia según el modelo.",
    [("Mitsubishi", f"marca · {mi['Mitsubishi (marca)']['n']} anuncios", mi["Mitsubishi (marca)"]["temas"], True),
     "Comerciales livianos",
     ("L200", f"{mi['Mitsubishi L200']['n']} anuncios", mi["Mitsubishi L200"]["temas"], False),
     "SUV",
     ("Montero Sport", f"{mi['Mitsubishi Montero Sport']['n']} anuncios", mi["Mitsubishi Montero Sport"]["temas"], False),
     ("Eclipse Cross", f"{mi['Mitsubishi Eclipse Cross']['n']} anuncios", mi["Mitsubishi Eclipse Cross"]["temas"], False),
     ("New Outlander", f"{mi['Mitsubishi Outlander']['n']} anuncios", mi["Mitsubishi Outlander"]["temas"], False),
     ("Destinator", f"{mi['Mitsubishi Destinator']['n']} anuncios", mi["Mitsubishi Destinator"]["temas"], False)],
    T_MMC,
    ["<b>Financiación</b> aparece en todos: la cuota es la primera pregunta del comprador Mitsubishi.",
     "<b>L200:</b> cuota, respaldo y tecnología. Casi no se le habla de diseño (8 %).",
     "<b>Eclipse Cross:</b> diseño (83 %) y tecnología (74 %). Es el modelo aspiracional.",
     "<b>New Outlander:</b> el más completo: tecnología, seguridad y test drive.",
     "<b>Destinator:</b> cuota, respaldo, diseño y <b>familia</b>. Pocos anuncios todavía (14)."])

# ================================================================== JAC
MJ = marca("JAC")
jm = {x["corto"]: x for x in MJ["modelos"]}
util_n = ["JAC X200", "JAC T9", "JAC T8", "JAC LD250", "JAC LD123", "JAC LE420", "JAC D8Bs0"]
pas_n = ["JAC JS4", "JAC Sunray", "JAC E30X", "JAC RF8", "JAC E-JS1"]
UTI, PAS = segmento(util_n), segmento(pas_n)
it = MJ["intencion"]
# El formulario solo ofrece "inmediatamente", "en 1 mes" y "en 2-3 meses": decir que
# casi todos compran en 3 meses sería un artefacto del formulario. Lo que sí dice algo
# es cuántos eligen "inmediatamente" entre esas tres opciones.
opciones = {k: v for k, v in it.items() if any(s in k.lower() for s in ("inmediat", "1_mes", "2–3", "2-3"))}
inmediato = sum(v for k, v in opciones.items() if "inmediat" in k.lower())
tot_it = sum(opciones.values()) or 1

laminas["jac_1_marca"] = lamina_marca(
    MJ, "Quién compra JAC: hombre de 35 a 44 años que compra para trabajar",
    "y valora, antes que nada, el respaldo.",
    f"<b>Lectura:</b> 69 % de las ventas son utilitarios. El comprador tiene apuro: <b>{pct(inmediato / tot_it * 100)} contesta que compra «inmediatamente»</b> "
    f"({n(inmediato)} de {n(tot_it)}). Pero la pauta va {pct(MJ['mix'].get('frio_pct', 0))} a público frío: solo {MJ['mix'].get('caliente', 0)} de {MJ['mix'].get('adsets', 0)} conjuntos vuelven a buscar a quien ya abrió el formulario.")

laminas["jac_2_segmentos"] = lamina_segmentos(
    MJ, "Utilitarios vende, Pasajeros atrae:", "dos compradores con motivos distintos.",
    bloque_seg("Utilitarios", "X200 · T9 · T8 · LD250 · LD123 · LE420 · LE79P", UTI, "X200, T9, T8, camiones LD y LE (LE79P recién entra: 1 venta)",
               "Respaldo y cuota para todos; trabajo y carga para el X200 y los camiones (las pickups T8 y T9 casi no lo tocan)."),
    bloque_seg("Pasajeros", "JS4 · Sunray 16+1 · E30X · RF8", PAS, "JS4, Sunray 16+1 minibús, E30X y RF8 (eléctricos e híbrido)",
               f"Genera más pedidos ({n(PAS['pedidos'])} vs {n(UTI['pedidos'])}) con menos ventas ({n(PAS['v12'])} vs {n(UTI['v12'])}): el E30X solo trae {n(jm['E30X']['pedidos'])}.", dark=True),
    "Sunray 16+1 va en Pasajeros, pero se compra para trabajar: transporte de personas")

le79 = f"""
  <div class="card">
    <div class="tag">Utilitario</div>
    <h3>LE79P Chasis 6.0T<small>recién entra</small></h3>
    <div class="nums">
      <div><b>1</b><span>venta en el ERP</span></div><div><b>0</b><span>anuncios propios</span></div>
    </div>
    <p>Todavía no tiene comprador propio medido. El de referencia son los camiones JAC (LE420 y LD): <b>hombre 84-87 %, 35-44 años</b>, que busca cuota y respaldo.</p>
    <div class="clave">Pautarlo con pieza propia 2-3 semanas para medir su comprador real.</div>
  </div>"""
laminas["jac_3_modelos"] = lamina_modelos(
    MJ, "Por modelo: el X200 es el caballo de batalla;", "el JS4 y la T9 reciben más pauta de la que venden.",
    [tarjeta(jm["X200"], "X200", "HFC1028KW5000 · cab. simple · simple DE", tag="Utilitario", clave= "El más vendido. Trabajo y carga (52 %) y cuota (42 %): mensaje directo, precio y financiación.", naranja=True),
     le79,
     tarjeta(jm["T9"], "T9", "Advance Luxury 4x4 AT", tag="Utilitario", clave= f"Respaldo (75 %), tecnología y seguridad. 22 % de los anuncios para 9 % de las ventas: revisar oferta o público."),
     tarjeta(jm["JS4"], "JS4", "1.6 MT Comfort", tag="Pasajeros", clave= f"El que más mujeres atrae de los cinco (29 %). Tecnología y diseño. 16 % de los anuncios para 5 % de las ventas."),
     tarjeta(jm["Sunray"], "Sunray", "16+1 minibús", tag="Pasajeros", clave= "El comprador más maduro (45-54): transportistas. Trabajo, respaldo y espacio.")],
    5, "Ficha completa de cada modelo en el vault y en el cerebro")

T_JAC = ["Trabajo, negocio y carga", "Financiación en cuotas", "Garantía y respaldo posventa", "Tecnología y conectividad",
         "Diseño y estatus", "Seguridad y asistencias a la conducción", "Familia y espacio", "Autos eléctricos y ahorro de combustible"]
fila = lambda nom, etq: (etq, f"{mi[nom]['n']} anuncios", mi[nom]["temas"], False)
laminas["jac_4_intereses"] = lamina_intereses(
    MJ, "Intereses por modelo: respaldo en todos;", "trabajo en los camiones, tecnología y diseño en los de pasajeros.",
    [("JAC", f"marca · {mi['JAC (marca)']['n']} anuncios", mi["JAC (marca)"]["temas"], True),
     "Utilitarios",
     fila("JAC X200", "X200"), fila("JAC T9", "T9"), fila("JAC T8", "T8"), fila("JAC LD250", "LD250"), fila("JAC LE420", "LE420"),
     "Pasajeros",
     fila("JAC JS4", "JS4"), fila("JAC Sunray", "Sunray 16+1"), fila("JAC E30X", "E30X"), fila("JAC RF8", "RF8")],
    T_JAC,
    ["<b>Respaldo</b> es el tema de la marca (42 %): pesa más que la cuota.",
     "<b>X200 y camiones LD y LE:</b> trabajo y carga + cuota. Las pickups T8 y T9 no hablan de trabajo.",
     "<b>T9:</b> se vende como pickup premium: respaldo, tecnología y seguridad.",
     "<b>JS4 y E30X:</b> tecnología y diseño; el E30X, además, ahorro eléctrico (92 %).",
     "<b>Sunray:</b> trabajo y familia a la vez: transporte de personas."],
    compacta=True)

# ------------------------------------------------------------------ render
for nombre, html in laminas.items():
    f = OUT / f"{nombre}.html"
    f.write_text(html, encoding="utf-8")
    png = OUT / f"{nombre}.png"
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1920,1080", f"--screenshot={png}", f"file://{f}"],
                   check=True, capture_output=True, timeout=120)
    print("lámina", png.relative_to(ROOT))
