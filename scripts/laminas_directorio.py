#!/usr/bin/env python3
"""Láminas de directorio: todo lo que el Buyer Persona sabe de cada marca, en una lámina por marca.

Pedido de Croman (05-10-2026), para la reunión de directorio: «explicar todo lo que tenemos para cada
marca: la decisión de compra (centro de compra), tipo de segmentación, retargeting, qué funciona, nivel
socioeconómico y toda la data, resumido para que entre en un slide, técnico y entendible».

Mismo estilo que las láminas de directorio del 24-09 (output/presentacion/directorio_2026-09-24/):
1920×1080, se pegan como imagen. Sale una lámina que explica los términos y una por marca, más un PDF
con todas. Sin la inversión mensual de cada marca en Meta (Croman, 05-10: «sacar meta mes»).

Desde el 12-10 (Croman: «lo que quería Valentina era el comparativo»; «solo las pautas que ya hicimos y un
slide más del roadmap») el PDF trae tres láminas: qué pasó en las pruebas de Renew, Renault y Mitsubishi
contra las campañas habituales (solo pauta de Meta, en palabras simples), cómo seguir con las demás marcas y
lo que hay detrás (competencia, benchmark, mercado, ventas y stock, píxel, Google Ads, clasificación con IA y memoria).
Con --completo suma «Qué es el Buyer Persona», el glosario y una lámina por marca (la versión del 05-10).

Lee los JSON de la última corrida (como scripts/laminas_comite.py): personas_*, materiales_meta_*,
centro_de_compra_* y ventas_meta_*. Para las pruebas lee la API de Meta, solo lectura; el resultado
queda en output/raw/pruebas_directorio_<fecha>.json y con --sin-meta se reutiliza.

Uso:
    venv/bin/python3 scripts/laminas_directorio.py [--fecha AAAA-MM-DD] [--raw DIR] [--sin-meta] [--completo] [--sin-vault]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import laminas_comite as base  # noqa: E402  (mismos datos, formatos y textos que las láminas del comité)

from laminas_comite import (  # noqa: E402
    GENERO, ORDEN_MARCAS, corta, dec, esc, miles, modelo_corto, pct, usd, y_lista)

EDADES = ("18-24", "25-34", "35-44", "45-54", "55-64", "65+")
LECTURA_CENTRO = {"ella_mira": "ella investiga y él da el paso",
                  "ellas_avanzan": "ellas son pocas en los clics, pero avanzan más que ellos",
                  "parejo": "ellas y ellos contactan parejo con el mismo anuncio"}

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{background:#fff;font-family:Inter,Arial,Helvetica,sans-serif;color:#111}
.slide{width:1920px;height:1080px;position:relative;overflow:hidden;background:#fff;padding:50px 100px}
.k{font-size:20px;letter-spacing:.18em;text-transform:uppercase;color:#6b6b6b;font-weight:600}
h1{font-size:44px;font-weight:800;letter-spacing:-.02em;line-height:1.08;margin-top:10px;max-width:1720px}
h1 span{color:#e8590c}
.grid{display:grid;grid-template-columns:1fr 1.08fr 1fr;gap:40px;margin-top:24px}
.col h2{font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:#777;font-weight:700;border-top:3px solid #111;
  padding-top:9px;margin-bottom:9px}
.col h2+*{margin-top:0}
.col section+section{margin-top:18px}
.big{font-size:44px;font-weight:800;letter-spacing:-.03em;line-height:1}
.big small{font-size:20px;font-weight:700;color:#555;letter-spacing:0;margin-left:6px}
.big.o{color:#e8590c}
.sub{font-size:16px;color:#444;margin-top:5px;line-height:1.35}
.bar{display:grid;grid-template-columns:200px 1fr 50px;align-items:center;gap:10px;margin:3px 0;font-size:16px}
.bar .t{height:15px;background:#f1f1f1;position:relative}
.bar .t i{position:absolute;left:0;top:0;bottom:0;background:#111}
.bar.hi .t i{background:#e8590c}
.bar b{text-align:right;font-weight:800}
.lin{font-size:16px;line-height:1.36;color:#222;margin-top:6px}
.lin b{font-weight:800;color:#111}
ul.l{list-style:none}
ul.l li{font-size:16px;line-height:1.34;padding:5px 0 5px 14px;border-top:1px solid #e6e6e6;position:relative}
ul.l li:first-child{border-top:0;padding-top:0}
ul.l li::before{content:"";position:absolute;left:0;top:12px;width:6px;height:6px;background:#e8590c;border-radius:50%}
ul.l li:first-child::before{top:7px}
.chips{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:2px}
.chips div{border:1px solid #ddd;padding:6px 6px 5px;text-align:center}
.chips b{display:block;font-size:22px;font-weight:800;letter-spacing:-.02em}
.chips b.o{color:#e8590c}
.chips span{font-size:11.5px;color:#666;text-transform:uppercase;letter-spacing:.05em;line-height:1.2;display:block;margin-top:2px}
.expl{font-size:13.5px;color:#666;line-height:1.35;margin-top:6px}
.nota{position:absolute;left:100px;right:100px;bottom:86px;font-size:17px;color:#222;line-height:1.4;border-left:4px solid #e8590c;padding-left:14px}
.nota b{color:#111}
.foot{position:absolute;left:100px;right:100px;bottom:30px;font-size:14px;color:#777;display:flex;justify-content:space-between;gap:40px;
  border-top:1px solid #ddd;padding-top:10px;line-height:1.35}
.foot span:last-child{text-align:right;max-width:560px}
.glos{display:grid;grid-template-columns:1fr 1fr;gap:18px 48px;margin-top:28px}
.glos div{border-top:3px solid #111;padding-top:10px}
.glos b{display:block;font-size:21px;font-weight:800;margin-bottom:4px}
.glos p{font-size:17px;color:#333;line-height:1.4}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:40px 26px;margin-top:44px}
.tile{border-top:4px solid #111;padding-top:12px}
.tile b{display:block;font-size:64px;font-weight:800;letter-spacing:-.03em;line-height:1}
.tile b.o{color:#e8590c}
.tile span{display:block;font-size:21px;color:#333;margin-top:10px;line-height:1.32}
.usos{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:56px}
.uso{background:#111;color:#fff;padding:26px 30px}
.uso h3{font-size:30px;font-weight:800;color:#ffb27a;margin-bottom:8px}
.uso p{font-size:21px;line-height:1.42;color:#eee}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;margin-top:26px}
.card .big small{font-size:22px}
.card.d .big small{color:#bbb}
.card{border:2px solid #111;padding:18px 22px}
.card.d{background:#111;color:#fff}
.card .tag{display:inline-block;font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:4px 9px;
  background:#e8590c;color:#fff}
.card.d .tag{background:#ffb27a;color:#111}
.card h3{font-size:30px;font-weight:800;letter-spacing:-.02em;margin-top:10px}
.card .big{margin-top:10px}
.card .sub{font-size:18px}
.card.d .sub,.card.d .lin{color:#ddd}
.vs{margin-top:14px}
.vs .bar{grid-template-columns:210px 1fr 100px;font-size:17px}
.card.d .vs .bar .t{background:#333}
.card.d .vs .bar .t i{background:#fff}
.card .vs .bar.hi .t i{background:#e8590c}
.card ul.l li{font-size:18px}
.card.d ul.l li{border-color:#333;color:#eee}
.card.d .expl{color:#aaa}
.inversion{display:grid;grid-template-columns:repeat(4,1fr);gap:26px;margin-top:24px;border-top:3px solid #111;padding-top:14px}
.inversion b{display:block;font-size:34px;font-weight:800;letter-spacing:-.02em}
.inversion span{font-size:17px;color:#444;line-height:1.3}
.resumen{margin-top:22px;font-size:21px;line-height:1.45;border-left:5px solid #e8590c;padding-left:16px;color:#111}
.etapas{display:grid;grid-template-columns:repeat(3,1fr);gap:30px;margin-top:34px}
.etapa{border-top:5px solid #111;padding-top:12px}
.etapa.o{border-color:#e8590c}
.etapa .cuando{font-size:17px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#e8590c}
.etapa h3{font-size:31px;font-weight:800;letter-spacing:-.01em;margin:6px 0 10px}
.etapa ul.l li{font-size:18.5px;padding-top:6px;padding-bottom:6px}
.etapa ul.l li::before{top:15px}
.respuesta{position:absolute;left:100px;right:100px;bottom:96px;background:#111;color:#fff;padding:24px 30px;font-size:23px;line-height:1.45}
.respuesta b{color:#ffb27a}
.cards3 .card .nota-n{font-size:15px;color:#666;margin-top:8px;line-height:1.35}
.card.d .nota-n{color:#aaa}
.b2{margin:14px 0}.b2 .l{display:flex;justify-content:space-between;gap:12px;font-size:20px}.b2 .l b{font-weight:800}
.b2 .t{height:20px;background:#f1f1f1;margin-top:7px;position:relative}.b2 .t i{position:absolute;left:0;top:0;bottom:0;background:#111}.b2.hi .t i{background:#e8590c}
.leer{margin-top:20px;font-size:20px;line-height:1.5;border-left:5px solid #e8590c;padding-left:18px;color:#111}
.conv .card{padding:24px 28px}.conv .card .sub{font-size:21px}.conv .vs .bar{font-size:19px;margin:12px 0}
.conv ul.l li{font-size:20px;padding-top:8px;padding-bottom:8px}.conv ul.l li::before{top:18px}.conv ul.l li:first-child::before{top:12px}
.conv .card h3{font-size:34px}
.embudo{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:20px 0 14px;border-top:1px solid #e3e3e3;padding-top:14px}
.embudo b{display:block;font-size:44px;font-weight:800;letter-spacing:-.03em;line-height:1}
.embudo span{display:block;font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#666;margin-top:6px}
.defs{position:absolute;left:100px;right:100px;bottom:92px;display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;gap:26px;border-top:3px solid #111;padding-top:14px}
.defs div{font-size:16.5px;line-height:1.4;color:#333}
.defs b{color:#111}
.sis{display:grid;grid-template-columns:repeat(5,1fr);gap:44px 26px;margin-top:38px}
.bloque{border-top:4px solid #111;padding-top:10px}
.bloque.o{border-color:#e8590c}
.bloque h3{font-size:16px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#e8590c}
.bloque b{display:block;font-size:52px;font-weight:800;letter-spacing:-.03em;line-height:1.05;margin-top:6px}
.bloque b small{font-size:20px;font-weight:700;color:#555;letter-spacing:0;margin-left:4px}
.bloque p{font-size:19px;line-height:1.36;color:#222;margin-top:6px}
.banda{position:absolute;left:100px;right:100px;bottom:96px;background:#111;color:#fff;padding:20px 28px;font-size:20px;line-height:1.45}
.banda b{color:#ffb27a}
"""


TEMA_CORTO = {"Seguridad y asistencias a la conducción": "Seguridad y asistencias",
              "Autos eléctricos y ahorro de combustible": "Eléctricos y ahorro",
              "Probar antes de comprar (test drive)": "Test drive",
              "Garantía y respaldo posventa": "Garantía y posventa",
              "Tecnología y conectividad": "Tecnología"}
MARCA_USADO = {"Greatwall": "GWM", "Great Wall": "GWM", "Gwm": "GWM", "Jac": "JAC", "Jmev": "JMEV", "Byd": "BYD",
               "Bmw": "BMW", "Mg": "MG"}


def senales_nse(nse: dict[str, Any], ticket: float | None) -> list[str]:
    """Las señales del NSE con un formato parejo: «74 % pide financiación (436 respuestas)»."""
    import re
    out = [f"ticket facturado <b>{usd(ticket)}</b>"] if ticket else []
    for s in nse.get("senales") or []:
        m = re.search(r"([\d.]+)% pide financiaci[oó]n.*?\((\d+) respuestas\)", s)
        if m and int(m.group(2)) >= 30:     # con pocas respuestas el % no dice nada (Renew: 1)
            out.append(f"{float(m.group(1)):.0f} % pide financiación ({m.group(2)} respuestas)")
        m = re.search(r"([\d.]+)% de los clics desde iPhone \(promedio del portfolio ~([\d.]+)%\)", s)
        if m:
            out.append(f"{float(m.group(1)):.0f} % de los clics desde iPhone (promedio {float(m.group(2)):.0f} %)")
    return out


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower().strip()


def ciudades(real_leads: dict[str, Any], n: int = 3) -> list[tuple[str, int]]:
    """Ciudades de los leads, juntando «Asuncion» con «Asunción»."""
    tot: Counter = Counter()
    nombre: dict[str, str] = {}
    for c, k in (real_leads.get("city") or {}).items():
        clave = _norm(c)
        tot[clave] += k
        if clave not in nombre or c != _norm(c).title() and any(ch in c for ch in "áéíóúñ"):
            nombre[clave] = c
    return [(nombre[c], k) for c, k in tot.most_common(n)]


def segmentos(mods: list[dict[str, Any]]) -> list[tuple[str, float]]:
    """Reparto de las ventas de 12 meses por tipo de vehículo (SUV, pickup…)."""
    c: Counter = Counter()
    for p in mods:
        c[p["segment"].get("category") or "Otro"] += p["segment"].get("orders_last_365d") or 0
    total = sum(c.values())
    return [(k, v / total * 100) for k, v in c.most_common(3)] if total else []


def rango_edad(dist: dict[str, float]) -> str:
    orden = sorted(((e, dist.get(e, 0)) for e in EDADES), key=lambda x: -x[1])
    (e1, s1), (e2, _) = orden[0], orden[1]
    if s1 < 25:
        return "de todas las edades"
    i1, i2 = EDADES.index(e1), EDADES.index(e2)
    if abs(i1 - i2) == 1:
        lo, hi = EDADES[min(i1, i2)], EDADES[max(i1, i2)]
        return f"de {lo.split('-')[0]} a {hi.split('-')[1]} años" if hi != "65+" else f"de {lo.split('-')[0]} años o más"
    return f"de {e1.split('-')[0]} a {e1.split('-')[1]} años" if e1 != "65+" else "de 65 años o más"


def titular(marca: str, mp: dict[str, Any], cm: dict[str, Any]) -> tuple[str, str]:
    d = mp.get("demographics") or {}
    meta = d.get("meta") or {}
    quien = "hombre" if d.get("gender") == "Masculino" else "mujer"
    nse = ((mp.get("nse") or {}).get("nivel") or "").strip()
    negro = f"Quién compra {esc(marca)}: {quien} {rango_edad(meta.get('age_distribution') or {})}" + (f", NSE {esc(nse)}" if nse else "")
    lect = ((cm or {}).get("embudo") or {}).get("lectura")
    emp = ((cm or {}).get("empresa") or {}).get("empresa_pct") or 0
    temas = ((mp.get("observed_interests") or {}).get("temas") or [])
    tema = TEMA_CORTO.get(temas[0]["tema"], temas[0]["tema"]).lower() if temas else ""
    if emp >= 40:
        naranja = f"el {emp:.0f} % compra a nombre de una empresa" + (f" y lo que más mira es {tema}." if tema else ".")
    elif lect in ("ella_mira", "ellas_avanzan"):
        naranja = LECTURA_CENTRO[lect] + "."
    elif tema:
        naranja = f"lo que más mira es {tema}."
    else:
        naranja = "."
    return negro + ";", naranja


def barras(items: list[tuple[str, float]], resaltar: str | None = None) -> str:
    tope = max((v for _, v in items), default=1) or 1
    return "".join(f'<div class="bar{" hi" if k == resaltar else ""}"><span>{esc(k)}</span><div class="t">'
                   f'<i style="width:{v / tope * 100:.0f}%"></i></div><b>{v:.0f} %</b></div>' for k, v in items)


def ul(items: list[str]) -> str:
    return '<ul class="l">' + "".join(f"<li>{x}</li>" for x in items if x) + "</ul>"


# ---------------------------------------------------------------------------
# Bloques de la lámina
# ---------------------------------------------------------------------------

def col_perfil(mp: dict[str, Any], mods: list[dict[str, Any]]) -> str:
    d = mp.get("demographics") or {}
    meta = d.get("meta") or {}
    dist = meta.get("age_distribution") or {}
    edad_top = max(dist, key=dist.get) if dist else ""
    gen = GENERO.get(d.get("gender") or "", d.get("gender") or "")
    segs = segmentos(mods)
    cds = ciudades(mp.get("real_leads") or {})
    nse = mp.get("nse") or {}
    erp = mp.get("erp") or {}
    ticket = (erp.get("price") or {}).get("avg") or (mp.get("spending") or {}).get("avg_order_value")
    senales = senales_nse(nse, ticket)
    base = "contactos" if meta.get("basis") == "contactos" else "clics"   # desde el 14-10-2026, por contactos
    html = ['<section><h2>Quién es</h2>',
            f'<div class="big">{esc(gen)} · {meta.get("gender_share", 0):.0f} %<small>de los {base}</small></div>',
            f'<div class="sub">Edad más frecuente <b>{esc(edad_top)}</b> ({dist.get(edad_top, 0):.0f} %) · '
            f'{miles(meta.get("weight") or 0)} {base} medidos en Meta</div>',
            barras([(e, dist.get(e, 0)) for e in EDADES], edad_top)]
    if len(segs) == 1 and mods:
        tops = [(modelo_corto(p["name"], p["segment"].get("brand", "")), p["segment"].get("orders_last_365d") or 0) for p in mods[:3]]
        html.append('<div class="lin">Más vendidos en 12 meses: ' + " · ".join(f"<b>{esc(k)}</b> {n}" for k, n in tops) + "</div>")
    elif segs:
        html.append('<div class="lin">Ventas de 12 meses por tipo: ' + " · ".join(f"<b>{esc(k)}</b> {v:.0f} %" for k, v in segs) + "</div>")
    if cds:
        html.append('<div class="lin">Leads por ciudad: ' + " · ".join(f"{esc(c)} {miles(n)}" for c, n in cds) + "</div>")
    html.append("</section>")
    if nse.get("nivel"):
        html += ['<section><h2>Nivel socioeconómico</h2>',
                 f'<div class="big">{esc(nse["nivel"])}<small>estimado</small></div>',
                 f'<div class="sub">{" · ".join(senales)}.</div>',
                 '<div class="expl">Meta no informa NSE en Paraguay: se estima con el ticket que se factura (ERP), cuántos piden '
                 'financiación en el formulario, el dispositivo desde el que hacen clic y la zona.</div></section>']
    temas = ((mp.get("observed_interests") or {}).get("temas") or [])[:3]
    base_ads = (mp.get("observed_interests") or {}).get("base_anuncios")
    if temas:
        html += ['<section><h2>Qué le interesa</h2>', barras([(TEMA_CORTO.get(t["tema"], t["tema"]), t["pct"]) for t in temas]),
                 f'<div class="expl">% de sus {miles(base_ads or 0)} anuncios que tocan cada tema: lo que este público ve y '
                 "clickea (Meta no entrega intereses declarados).</div></section>"]
    return "".join(html)


def col_decision(marca: str, mp: dict[str, Any], cm: dict[str, Any]) -> str:
    e = (cm or {}).get("embudo") or {}
    emp = (cm or {}).get("empresa") or {}
    conv = (cm or {}).get("conversaciones") or {}
    erp = mp.get("erp") or {}
    centro = []
    if e.get("mujeres_clics_pct"):
        t = f"<b>Ellas: {e['mujeres_clics_pct']:.0f} % de los clics</b>"
        r, lect = e.get("ellas_vs_ellos"), e.get("lectura")
        if r and lect == "ella_mira":
            t += (f". Con el mismo anuncio contactan {dec(r, 2)}× lo que ellos (menos en {e.get('conjuntos_ellas_menos')} de "
                  f"{e.get('conjuntos')} conjuntos): ella investiga y él da el paso.")
        elif r and lect == "ellas_avanzan":
            t += f", pero con el mismo anuncio contactan {dec(r, 2)}× lo que ellos: las que miran, avanzan más."
        elif r and lect == "parejo":
            t += f"; con el mismo anuncio contactan igual que ellos ({dec(r, 2)}×)."
        elif r:
            t += f"; contactan {dec(r, 2)}× lo que ellos, pero con {e.get('conjuntos')} conjuntos todavía es una tendencia."
        else:
            t += "."
        centro.append(t)
    if emp.get("empresa_pct"):
        rec = next((r for r in (cm or {}).get("meta_ads") or [] if r.get("clave") == "empresa"), {})
        mods = [modelo_corto(m, marca) for m in rec.get("modelos") or []][:3]
        centro.append(f"<b>Empresa: {emp['empresa_pct']:.0f} % de las compras</b> las factura una empresa"
                      + (f" (más en {y_lista(mods)})" if mods else "") + ": decide el dueño o un gerente.")
    if conv.get("con_otra_persona_pct"):
        centro.append(f"<b>En el {conv['con_otra_persona_pct']:.0f} % de los chats</b> el cliente nombra a otra persona que decide con él.")
    if erp.get("tradein_rate"):
        marcas_u = list(dict.fromkeys(MARCA_USADO.get(k, k) for k in (erp.get("tradein_brands") or {})))[:3]
        centro.append(f"<b>Permuta: {dec(erp['tradein_rate'])} % de las compras</b> entrega un usado"
                      + (f" (sobre todo {y_lista(marcas_u)})" if marcas_u else "") + ".")
    mix = mp.get("audience_mix") or {}
    b = mp.get("budget") or {}
    crm = mp.get("crm") or {}
    chips = ""
    if mix.get("adsets"):
        chips = ('<div class="chips">'
                 f'<div><b>{mix["adsets"]}</b><span>conjuntos activos</span></div>'
                 f'<div><b class="{"o" if mix["frio_pct"] >= 95 else ""}">{mix["frio_pct"]:.0f} %</b><span>a público frío</span></div>'
                 f'<div><b>{mix.get("advantage", 0)}</b><span>con Advantage+</span></div>'
                 f'<div><b class="{"o" if not mix.get("caliente") else ""}">{mix.get("caliente", 0)}</b><span>retargeting / base propia</span></div>'
                 f'<div><b>{mix.get("lookalike", 0)}</b><span>similares (lookalike)</span></div></div>')
    leads = []
    if b.get("form_leads_90d") or b.get("conversations_90d"):
        leads.append(f"Leads en 90 días: <b>{miles(b.get('form_leads_90d') or 0)} formularios</b> + "
                     f"<b>{miles(b.get('conversations_90d') or 0)} chats</b> de WhatsApp.")
    if crm.get("leads"):
        canales = crm.get("leads_by_channel") or {}
        ases = canales.get("Meta asesores", 0)
        leads.append(f"Bitrix: {miles(crm['leads'])} leads"
                     + (f", el {ases / crm['leads'] * 100:.0f} % por cuentas de asesores" if ases else "")
                     + f"; {dec(crm.get('conversion_rate'))} % marcados como convertidos.")
    def corto(a: str) -> str:
        a = a.replace(".csv", "").replace("_", " ").strip()
        return a if len(a) <= 42 else a[:40].rstrip() + "…"
    aud = list(dict.fromkeys(corto(a) for a in mix.get("custom_audiences") or []))[:3]
    if aud:
        leads.append("Públicos propios en uso: " + ", ".join(f"«{esc(a)}»" for a in aud) + ".")
    html = ['<section><h2>Centro de compra · quién mira y quién decide</h2>', ul(centro), "</section>",
            '<section><h2>Segmentación y retargeting hoy</h2>', chips,
            '<div class="expl">Frío: gente que no interactuó con la marca. Advantage+: Meta amplía el público solo. '
            'Retargeting: volver a quien abrió el formulario, visitó la web o interactuó. Similares: parecidos a quienes ya '
            'compraron o dejaron datos.</div>',
            "".join(f'<div class="lin">{x}</div>' for x in leads), "</section>"]
    return "".join(html)


def col_resultados(marca: str, d: dict[str, Any]) -> str:
    mp, mods, mm, cm = d["marca"] or {}, d["modelos"], d["material"], d["centro"]
    ex = mp.get("extras") or {}
    obj = ex.get("objetivos") or {}
    st = ex.get("stock") or {}
    html = ['<section><h2>Cómo le va</h2>']
    if obj.get("objetivo_ytd"):
        html.append(f'<div class="big o">{miles(obj.get("real_ytd") or 0)} de {miles(obj["objetivo_ytd"])} · '
                    f'{obj.get("avance_ytd_pct", 0):.0f} %</div>'
                    f'<div class="sub">unidades vendidas en 2026 contra el objetivo a la fecha · anual {miles(obj.get("objetivo_anual") or 0)} '
                    f'(ERP hasta {corta(obj.get("sales_until") or "")})</div>')
    lineas = [base.linea_hoy(mm, d["ventas"], d["rango_ventas"], d["hoy"])]
    if st.get("total"):
        lineas.append(f"Stock: <b>{base.stock_txt(st)}</b> (al {corta(st.get('fecha') or '')}).")
    html += [f'<div class="lin">{x}</div>' for x in lineas] + ["</section>"]
    html += ['<section><h2>Qué funciona · 6 meses de anuncios</h2>', ul(base.que_funciona(mm, cm)), "</section>"]
    hacer = [base.proximo_paso(marca, mods, mp)]
    for x in base.buenas_practicas(marca, mm, cm, mp, mods, d["hoy"]):
        if x.startswith(("Pieza", "Sumar similares", "No pautarle")) and len(hacer) < 3:
            hacer.append(x)
    html += ['<section><h2>Qué hacer</h2>', ul(hacer), "</section>"]
    return "".join(html)


def lectura(marca: str, mp: dict[str, Any], cm: dict[str, Any], mm: dict[str, Any] | None) -> str:
    """Dos frases para el directorio: el hueco más grande en la pauta y la oportunidad del centro de compra."""
    mix = mp.get("audience_mix") or {}
    e = (cm or {}).get("embudo") or {}
    emp = (cm or {}).get("empresa") or {}
    frases = []
    if mix.get("frio_pct", 0) >= 95:
        frases.append(f"el {mix['frio_pct']:.0f} % de los conjuntos le habla a gente que no conoce la marca y "
                      f"{'ninguno' if not mix.get('caliente') else 'casi ninguno'} vuelve a buscar a quien ya dejó datos o visitó la web")
    elif mix.get("frio_pct", 0) >= 70 and mix.get("adsets"):
        n = mix.get("caliente") or 0
        frases.append(f"el {mix['frio_pct']:.0f} % de los conjuntos va a público frío y solo {n} "
                      f"{'usa' if n == 1 else 'usan'} retargeting o base propia")
    elif mix.get("frio_pct") is not None and mix.get("adsets"):
        frases.append(f"ya hay retargeting o base propia en {100 - mix['frio_pct']:.0f} % de los conjuntos: falta medir si baja el costo")
    if e.get("lectura") == "ella_mira":
        frases.append("ella investiga y él decide: conviene sumar una pieza para quien acompaña la decisión")
    elif emp.get("empresa_pct", 0) >= 30:
        frases.append(f"el {emp['empresa_pct']:.0f} % compra a nombre de una empresa: conviene sumar la pieza «Para tu empresa»")
    elif e.get("lectura") == "ellas_avanzan":
        frases.append("las mujeres que hacen clic avanzan más que los hombres: conviene una pieza pensada para ellas")
    if not frases:
        return ""
    txt = "; ".join(frases)
    return f"<b>Lectura:</b> {txt[0].upper() + txt[1:]}."


def lamina_marca(marca: str, d: dict[str, Any], fecha_c: str, periodo: str) -> str:
    mp, cm = d["marca"] or {}, d["centro"]
    negro, naranja = titular(marca, mp, cm)
    cuerpo = (f'<div class="grid"><div class="col">{col_perfil(mp, d["modelos"])}</div>'
              f'<div class="col">{col_decision(marca, mp, cm)}</div>'
              f'<div class="col">{col_resultados(marca, d)}</div></div>')
    nota = lectura(marca, mp, cm, d["material"])
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<section class="slide"><div class="k">Buyer Persona 360 · {esc(marca)} · directorio</div>'
            f'<h1>{negro} <span>{naranja}</span></h1>{cuerpo}'
            + (f'<div class="nota">{nota}</div>' if nota else "")
            + f'<div class="foot"><span>Edad y género: quienes contactan por los anuncios de Meta ({periodo}); intereses: los temas de los anuncios; no quién firma '
              f'la compra · ventas y permutas: ERP · stock y objetivos: planillas de la marca · sin datos personales</span>'
              f'<span>Fuente: Buyer Persona 360 · vault Obsidian y cerebro.santarosa.lat · datos al {fecha_c}</span></div>'
              "</section></body></html>")


# ---------------------------------------------------------------------------
# Resultados del proyecto (pedido del 12-10: el comparativo para el directorio)
# ---------------------------------------------------------------------------

RENEW_CUENTA = "act_1006324631233144"
RENEW_PRUEBA = ("2026-09-23", "2026-09-30")


def renew_habitual(token: str) -> dict[str, float]:
    """Lo que pagó la campaña habitual de WhatsApp de Renew en la misma cuenta y los mismos días que la prueba."""
    datos = base._get(f"{RENEW_CUENTA}/insights", token, level="campaign", fields="campaign_id,spend,actions", limit=200,
                      time_range=json.dumps({"since": RENEW_PRUEBA[0], "until": RENEW_PRUEBA[1]})).get("data", [])
    gasto = conv = 0.0
    for x in datos:
        if x.get("campaign_id") in base.RENEW.values():
            continue
        c = sum(float(a["value"]) for a in x.get("actions") or []
                if a["action_type"] == "onsite_conversion.messaging_conversation_started_7d")
        if c:
            gasto += float(x["spend"])
            conv += c
    return {"gasto": round(gasto, 2), "conversaciones": conv}


def datos_resultados(fecha: str, sin_meta: bool) -> dict[str, Any]:
    cache = ROOT / "output" / "raw" / f"pruebas_directorio_{fecha}.json"
    if sin_meta:
        return json.loads(cache.read_text(encoding="utf-8"))
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    hasta = (date.fromisoformat(fecha) - timedelta(days=1)).isoformat()
    pr = base.datos_pruebas(hasta)
    pr["renew_habitual"] = renew_habitual(os.environ["META_ADS_ACCESS_TOKEN"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(pr, ensure_ascii=False, indent=1), encoding="utf-8")
    return pr


def _cpl(x: list[float]) -> float | None:
    return x[0] / x[1] if x and x[1] else None


def _pagina(kicker: str, negro: str, naranja: str, cuerpo: str, pie_izq: str, pie_der: str) -> str:
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<section class="slide"><div class="k">{esc(kicker)}</div><h1>{negro} <span>{naranja}</span></h1>{cuerpo}'
            f'<div class="foot"><span>{pie_izq}</span><span>{pie_der}</span></div></section></body></html>')


def numeros_proyecto(datos: dict[str, Any], marcas: dict[str, Any]) -> dict[str, Any]:
    """Lo que el sistema lee y produce, contado de la última corrida."""
    cuentas = len([x for x in os.environ.get("META_ADS_AD_ACCOUNT_IDS", "").split(",") if x.strip()]) or 85
    anuncios = sum(m.get("anuncios", 0) for m in (datos["materiales"].get("marcas") or {}).values())
    leads = sum(((d["marca"] or {}).get("budget") or {}).get("form_leads_90d", 0)
                + ((d["marca"] or {}).get("budget") or {}).get("conversations_90d", 0) for d in marcas.values() if d["marca"])
    pm = (datos["ventas"].get("por_marca") or {}).values()
    textos = len(list((ROOT / "Buyer Persona" / "Buyer Personas").glob("*/Marketing/*.md")))
    return {"cuentas": cuentas, "anuncios": anuncios, "fichas": len(datos["personas"]), "leads": leads,
            "ventas_meta": sum(m.get("con_meta", 0) for m in pm), "ventas": sum(m.get("ventas", 0) for m in pm),
            "textos": textos, "marcas": len([m for m in marcas.values() if m["marca"]]),
            "ventas_periodo": (f"{corta(datos['ventas']['ventas_desde'])} al {corta(datos['ventas']['ventas_hasta'])}"
                               if datos["ventas"].get("ventas_desde") else "último mes")}


def lamina_proyecto(n: dict[str, Any], fecha_c: str) -> str:
    tiles = [("o", f"{n['marcas']}", "marcas con su comprador descripto: quién es, nivel socioeconómico y quién decide"),
             ("", miles(n["fichas"]), "fichas de comprador, por marca y por modelo"),
             ("", f"{n['cuentas']}", "cuentas de Meta leídas todos los días"),
             ("", miles(n["anuncios"]), "anuncios de los últimos 6 meses analizados uno por uno"),
             ("", miles(n["leads"]), "leads de los últimos 90 días: formularios y chats de WhatsApp"),
             ("o", miles(n["ventas_meta"]), f"de {miles(n['ventas'])} ventas ({n['ventas_periodo']}) tenían antes un lead de Meta: cruce con el ERP, es un mínimo"),
             ("", miles(n["textos"]), "textos listos para Meta, Google, Email y WhatsApp, sin promesas que no se puedan cumplir"),
             ("o", "06:00", "se actualiza solo, todos los días, sin trabajo manual")]
    cuerpo = ('<div class="tiles">' + "".join(f'<div class="tile"><b class="{c}">{esc(v)}</b><span>{esc(t)}</span></div>'
                                             for c, v, t in tiles) + "</div>"
              '<div class="usos">'
              '<div class="uso"><h3>A quién hablarle</h3><p>Edad, género, nivel socioeconómico y quién decide la compra en cada '
              'marca y modelo, con datos reales de la pauta y de las ventas.</p></div>'
              '<div class="uso"><h3>Qué anuncio poner</h3><p>Qué formato rinde en cada marca (imagen, video o carrusel), textos '
              'listos, la oferta vigente y el stock disponible para no prometer lo que no hay.</p></div>'
              '<div class="uso"><h3>Qué pauta vende</h3><p>Cruza las ventas con los leads de Meta para saber qué campañas terminan '
              'en una venta, no solo cuáles traen consultas.</p></div></div>')
    return _pagina("Buyer Persona 360 · directorio · qué es",
                   "Qué es el Buyer Persona:", "un sistema que todos los días lee la pauta, las ventas y el CRM, y dice a quién "
                   "hablarle y qué anuncio poner.", cuerpo,
                   "Fuentes: Meta Ads, ERP de ventas, Bitrix (solo totales), stock, objetivos y planilla de acciones · sin datos personales",
                   f"Datos al {fecha_c}")


def _vs(con: float, sin: float, unidad: str, etiqueta_sin: str) -> str:
    tope = max(con, sin) or 1
    return ('<div class="vs">'
            f'<div class="bar hi"><span>Con Buyer Persona</span><div class="t"><i style="width:{con / tope * 100:.0f}%"></i></div>'
            f'<b>{usd(con)}</b></div>'
            f'<div class="bar"><span>{esc(etiqueta_sin)}</span><div class="t"><i style="width:{sin / tope * 100:.0f}%"></i></div>'
            f'<b>{usd(sin)}</b></div></div><div class="expl">Costo por {unidad}: lo pagado en Meta ÷ resultados.</div>')


def lamina_resultados(pr: dict[str, Any], fecha_c: str) -> str:
    # Renew: la prueba contra la campaña habitual, misma cuenta y mismos días
    rn, rh = pr["renew"], pr.get("renew_habitual") or {}
    g_rn = sum(v["gasto"] for v in rn.values())
    c_rn = sum(v["conversaciones"] for v in rn.values())
    con_rn = g_rn / c_rn if c_rn else None
    sin_rn = rh["gasto"] / rh["conversaciones"] if rh.get("conversaciones") else None
    ahorro = (1 - con_rn / sin_rn) * 100 if con_rn and sin_rn else None
    clavos = rn["Clavos"]["gasto"] / rn["Clavos"]["conversaciones"] if rn["Clavos"]["conversaciones"] else None
    renew = ('<div class="card"><span class="tag">El mejor resultado</span><h3>Renew</h3>'
             f'<div class="big o">{usd(con_rn)}<small>por conversación</small></div>'
             f'<div class="sub">{"<b>" + f"{ahorro:.0f} % más barato</b> que" if ahorro and ahorro > 0 else "Comparado con"} la '
             f'campaña habitual de WhatsApp, en la misma cuenta y los mismos días ({corta(RENEW_PRUEBA[0])} al {corta(RENEW_PRUEBA[1])}).</div>'
             + (_vs(con_rn, sin_rn, "conversación de WhatsApp", "Campaña habitual") if con_rn and sin_rn else "")
             + ul([f"<b>USD {g_rn:.0f} → {c_rn:.0f} conversaciones</b> de WhatsApp en 8 días.",
                   "10 autos usados elegidos con el Buyer Persona: 5 difíciles de vender y 5 de los más buscados.",
                   f"Los difíciles de vender consiguieron conversaciones a <b>{usd(clavos)}</b>." if clavos else ""])
             + "</div>")
    # Renault: lo que ganó la cuenta y el modelo que se abrió
    r = pr["Renault"]
    f_ant, f_act = r["fases"]["antes"], r["fases"]["IA corregida"]
    ac = r["acumulado"]
    sube = (f_act["cuenta"]["leads_dia"] / f_ant["cuenta"]["leads_dia"] - 1) * 100
    mas_a, mas = f_ant["modelos"]["Master"]["total"], f_act["modelos"]["Master"]
    resp = r["respuestas"].get("Master", {})
    renault = ('<div class="card d"><span class="tag">Abrió un modelo</span><h3>Renault</h3>'
               f'<div class="big o">+{sube:.0f} %<small>leads por día en la cuenta</small></div>'
               f'<div class="sub">Toda la cuenta, con las campañas de la agencia incluidas. {corta(f_ant["desde"])} al {corta(f_ant["hasta"])}: '
               f'{dec(f_ant["cuenta"]["leads_dia"])} leads por día. {corta(f_act["desde"])} al {corta(f_act["hasta"])}: '
               f'{dec(f_act["cuenta"]["leads_dia"])}. Mismo costo por lead ({usd(f_ant["cuenta"]["cpl"])} → {usd(f_act["cuenta"]["cpl"])}).</div>'
               + _vs(_cpl(ac["cuenta|ia"]), _cpl(ac["cuenta|resto"]), "lead", "Campañas de la agencia")
               + ul([f"<b>Master</b>, que casi no se pautaba, pasó de <b>{dec(mas_a['leads_dia'])} a {dec(mas['total']['leads_dia'])} "
                     f"leads por día</b> ({dec(mas['ia']['leads_dia'])} de la prueba y {dec(mas['resto']['leads_dia'])} de la agencia, "
                     "que después también lo sumó).",
                     "La campaña de prueba (Koleos y Master) recién arrancaba; las de la agencia llevan meses optimizándose.",
                     (f"Qué contestan: de {resp['leads']} leads de Master, {resp['este_mes']} compran este mes y "
                      f"{resp['empresa']} a nombre de una empresa.") if resp.get("leads") else ""])
               + "</div>")
    # Mitsubishi: el aprendizaje
    m = pr["Mitsubishi"]
    am = m["acumulado"]
    l2 = m["respuestas"].get("L200", {})
    mitsu = ('<div class="card"><span class="tag">Aprendizaje</span><h3>Mitsubishi</h3>'
             f'<div class="big">{usd(_cpl(am["cuenta|ia"]))}<small>por lead</small></div>'
             '<div class="sub">Se probó sobre todo en L200, el modelo que la agencia ya pauta bien: ahí el Buyer Persona no mejoró el costo.</div>'
             + _vs(_cpl(am["cuenta|ia"]), _cpl(am["cuenta|resto"]), "lead", "Campañas de la agencia")
             + ul([(f"Qué contestan: el <b>{l2['este_mes'] / l2['leads'] * 100:.0f}&nbsp;%</b> dice que compra este mes y el "
                    f"{l2['financiacion'] / l2['leads'] * 100:.0f}&nbsp;% pide financiación.") if l2.get("leads") else "",
                   "El Buyer Persona suma más <b>abriendo modelos o públicos nuevos</b> que repitiendo lo que ya funciona."])
             + "</div>")
    g_ra, g_mi = r["acumulado"]["cuenta|ia"][0], am["cuenta|ia"][0]
    inversion = ('<div class="inversion">'
                 f'<div><b>USD {g_rn + g_ra + g_mi:,.0f}</b><span>invertidos en Meta en las tres pruebas</span></div>'.replace(",", ".")
                 + f'<div><b>USD {g_rn:.0f}</b><span>Renew · {c_rn:.0f} conversaciones</span></div>'
                 f'<div><b>USD {g_ra:.0f}</b><span>Renault · {ac["cuenta|ia"][1]:.0f} leads</span></div>'
                 f'<div><b>USD {g_mi:.0f}</b><span>Mitsubishi · {am["cuenta|ia"][1]:.0f} leads</span></div></div>')
    resumen = ('<div class="resumen">' + (f"<b>En simple:</b> con el Buyer Persona pagamos {ahorro:.0f} % menos por conversación en Renew "
               if ahorro and ahorro > 0 else "<b>En simple:</b> en Renew el Buyer Persona trajo conversaciones a bajo costo ")
               + f"y la cuenta de Renault ganó {sube:.0f} % más leads por día sin subir el costo por lead. Donde la agencia ya pautaba "
               "bien el mismo modelo, no lo mejoró.</div>")
    uso = ('<div class="respuesta"><b>Cómo recomendamos usarlo:</b> como guía de los anuncios que ya están hechos (a quién hablarles, '
           "qué formato y qué texto), no como campañas nuevas. Una campaña aparte solo vale donde hay algo nuevo que abrir, "
           "como pasó con Renew y con Master.</div>")
    return _pagina("Buyer Persona 360 · directorio · resultados de las pruebas",
                   "Las pruebas con el Buyer Persona:", "Renew pagó menos por conversación y Renault ganó leads sin subir el costo.",
                   f'<div class="cards3">{renew}{renault}{mitsu}</div>{inversion}{resumen}{uso}',
                   f"Solo lo que se pagó en Meta (sin honorarios ni costos internos) · Meta hasta el {corta(pr['hasta'])} · "
                   "Renault desde el 18/09, Mitsubishi desde el 21/09, Renew del 23 al 30/09",
                   "Las campañas de prueba las crea Innovación y las activa cada marca")


def _stock_corto(st: dict[str, Any]) -> str:
    fecha = f" al {corta(st['fecha'])}" if st.get("fecha") else ""
    return f"{st.get('disponible') or 0} disponibles + {st.get('en_viaje') or 0} en viaje{fecha}"


def candidatos_roadmap(marcas: dict[str, Any], centro: dict[str, Any]) -> dict[str, list[str]]:
    """Dónde conviene la próxima prueba, con las mismas reglas que las tarjetas de cada marca.

    «Falta pauta»: 10 ventas o más al año y una pauta sugerida (gasto de la marca × % de sus ventas que es el
    modelo) que supera en USD 100 al mes o más a la actual (gasto de la marca × % de sus anuncios).
    """
    probar, esperar, confirmar, frio, acompana = [], [], [], [], []
    for marca in ORDEN_MARCAS:
        d = marcas.get(marca)
        if not d or not d["marca"]:
            continue
        for p in d["modelos"]:
            s, b = p["segment"], p.get("budget") or {}
            if s.get("gap") != "sub-pautado" or (s.get("orders_last_365d") or 0) < 10:
                continue
            if (b.get("suggested_month") or 0) - (b.get("current_month_est") or 0) < 100:
                continue
            st = (p.get("extras") or {}).get("stock") or {}
            nombre = f"{marca} {modelo_corto(p['name'], marca)}"
            ventas = f"{s['orders_last_365d']} ventas al año"
            if not st:
                confirmar.append(f"{nombre} ({ventas}; sin dato de stock)")
            elif st.get("disponible"):
                probar.append(f"{nombre} ({ventas}; {_stock_corto(st)})")
            else:
                esperar.append(f"{nombre} ({ventas}; {_stock_corto(st)})")
        if ((d["marca"].get("audience_mix") or {}).get("frio_pct") or 0) >= 95:
            frio.append(marca)
        if (((centro.get("marcas") or {}).get(marca) or {}).get("embudo") or {}).get("lectura") == "ella_mira":
            acompana.append(marca)
    return {"probar": probar, "esperar": esperar, "confirmar": confirmar, "frio": frio, "acompana": acompana}


def lamina_roadmap(c: dict[str, list[str]], fecha_c: str) -> str:
    pruebas = []
    if c["probar"]:
        pruebas.append("<b>Modelos que venden más de lo que se anuncian</b>, con unidades disponibles: " + y_lista(c["probar"]) + ".")
    if c["esperar"]:
        pruebas.append("<b>Esperar el stock</b> (hoy no hay unidades disponibles): " + y_lista(c["esperar"]) + ".")
    if c["confirmar"]:
        pruebas.append("<b>Confirmar el stock antes de pautar</b>: " + y_lista(c["confirmar"]) + ".")
    if c["frio"]:
        pruebas.append("<b>Volver a mostrarle anuncios a quien ya consultó</b> (retargeting). En " + y_lista(c["frio"])
                       + ", 95 % o más de los conjuntos de anuncios le habla a gente nueva.")
    if c["acompana"]:
        pruebas.append("<b>Una pieza para quien acompaña la decisión.</b> En " + y_lista(c["acompana"]) + " ella investiga y él da el paso.")
    pruebas.append("Cada prueba con plata suficiente para que Meta aprenda; se mide a las 3-4 semanas contra la campaña habitual de la marca.")
    etapas = (
        '<div class="etapas">'
        '<div class="etapa o"><div class="cuando">Ya · sin gastar más</div><h3>Guía de los anuncios hechos</h3>'
        + ul(["El Buyer Persona se usa para ajustar los anuncios que ya están hechos: a quién hablarles, qué formato rinde y qué texto conviene.",
              "Los anuncios nuevos de cada marca salen de la misma ficha.",
              "Oferta vigente y stock al día: test drive solo donde hay unidad para probar.",
              "Cada marca y su agencia deciden su pauta: el Buyer Persona les da la información, no la reemplaza.",
              "Costo por lead y ventas se siguen en los dashboards que ya tenemos (Meta Ads y Comercial Bitrix), con revisión mensual en el comité."])
        + "</div>"
        '<div class="etapa"><div class="cuando">Solo si falta pauta · 4 a 6 semanas</div><h3>Pruebas chicas</h3>'
        + ul(pruebas) + "</div>"
        '<div class="etapa"><div class="cuando">Después</div><h3>Que la pauta aprenda de las ventas</h3>'
        + ul(["Avisarle a Meta qué leads terminaron comprando, para que busque más gente parecida (con OK de Innovación).",
              "Llevar la misma ficha a Google Ads cuando la cuenta quede conectada."]) + "</div></div>")
    defs = ('<div class="defs">'
            "<div><b>Falta pauta:</b> el modelo vende 10 unidades o más al año y la pauta que le corresponde por sus ventas supera en "
            "USD 100 al mes o más a la que tiene. Corresponde = gasto de la marca × % de sus ventas que es el modelo; tiene = gasto de la "
            "marca × % de sus anuncios que es el modelo.</div>"
            "<div><b>Retargeting:</b> volver a mostrarle anuncios a quien ya miró la web o abrió el formulario. <b>Gente nueva (público "
            "frío):</b> quien todavía no conoce la marca.</div>"
            "<div><b>Conjunto de anuncios:</b> cada grupo de anuncios, con su público y su presupuesto, dentro de una campaña.</div>"
            "<div><b>Quien acompaña la decisión:</b> la segunda persona que influye en la compra. Se lee de quién hace clic y quién deja "
            "sus datos en cada marca (nota «Centro de compra»).</div></div>")
    return _pagina("Buyer Persona 360 · directorio · cómo seguir",
                   "Cómo seguir con las demás marcas:", "el Buyer Persona como guía de los anuncios ya hechos, y pruebas chicas solo donde falta pauta.",
                   etapas + defs,
                   "Los modelos y marcas de cada etapa salen de las fichas de hoy: se actualizan solos cada mañana",
                   f"Datos al {fecha_c}")


# ---------------------------------------------------------------------------
# Conversión de las pruebas (pedido del 12-10: «saber si realmente convirtió»)
# ---------------------------------------------------------------------------

SERVIDOR = "srpy-servidor"
BASE_ROI = "bitrix-supabase-db"      # ahí está roi_embudo, la tabla del menú «ROI Pauta» del Dashboard Meta


def _iso(x: str) -> str:
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", x), x
    return x


def sql_conversion(cuenta: str, campana: str, antes: tuple[str, str], con: tuple[str, str], madura: str) -> str:
    """Solo conteos sobre roi_embudo: nada de nombres, teléfonos ni mails."""
    assert re.fullmatch(r"act_\d+", cuenta) and re.fullmatch(r"\d+", campana)
    cuentas = ("count(*), count(bitrix_lead_id), count(*) filter (where contactado), "
               "count(*) filter (where test_drive), count(*) filter (where venta)")
    r = (f"with r as (select *, (created_time at time zone 'America/Asuncion')::date d, "
         f"case when campaign_id = '{campana}' then 'prueba' else 'resto' end g from roi_embudo where account_id = '{cuenta}') ")
    return (r + f"select 'con', g, {cuentas} from r where d between '{_iso(con[0])}' and '{_iso(con[1])}' group by g union all "
            f"select 'madura', g, {cuentas} from r where d between '{con[0]}' and '{_iso(madura)}' group by g union all "
            f"select 'antes', 'cuenta', {cuentas} from r where d between '{_iso(antes[0])}' and '{_iso(antes[1])}';")


def consulta_servidor(sql: str) -> list[list[str]]:
    out = subprocess.run(["ssh", "-o", "ConnectTimeout=15", SERVIDOR, f"docker exec -i {BASE_ROI} psql -U postgres -d postgres -At -F'|'"],
                         input=sql, capture_output=True, text=True, timeout=120, check=True).stdout
    return [ln.split("|") for ln in out.splitlines() if ln.strip()]


def _fila(x: list[str]) -> list[int]:
    return [int(v) for v in x]


def datos_conversion(fecha: str, pr: dict[str, Any], sin_meta: bool) -> dict[str, Any]:
    cache = ROOT / "output" / "raw" / f"conversion_directorio_{fecha}.json"
    if sin_meta and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out: dict[str, Any] = {"fecha": fecha}
    for marca in ("Renault", "Mitsubishi"):
        cfg = base.PRUEBAS[marca]
        f = pr[marca]["fases"]
        con = (f["IA corregida"]["desde"], f["IA corregida"]["hasta"])
        madura = (date.fromisoformat(con[1]) - timedelta(days=7)).isoformat()
        filas = consulta_servidor(sql_conversion(cfg["cuenta"], cfg["campana"], (f["antes"]["desde"], f["antes"]["hasta"]), con, madura))
        d: dict[str, Any] = {"fechas": {"con": list(con), "antes": [f["antes"]["desde"], f["antes"]["hasta"]], "madura_hasta": madura}}
        for periodo, grupo, *n in filas:
            d.setdefault(periodo, {})[grupo] = _fila(n)
        out[marca] = d
    sept = consulta_servidor("select count(*), count(*) filter (where contactado), count(*) filter (where test_drive), "
                             "count(*) filter (where venta) from roi_embudo where created_time >= '2026-09-01';")
    out["septiembre"] = _fila(sept[0])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _pct(a: int, b: int) -> float | None:
    return a / b * 100 if b else None


def _barra_pct(etiqueta: str, v: float | None, resaltar: bool) -> str:
    ancho = min(v or 0, 100)
    return (f'<div class="b2{" hi" if resaltar else ""}"><div class="l"><span>{etiqueta}</span><b>{dec(v)} %</b></div>'
            f'<div class="t"><i style="width:{ancho:.0f}%"></i></div></div>')


def tarjeta_conversion(marca: str, d: dict[str, Any], oscura: bool = False) -> str:
    """% de leads contactados por un asesor: la campaña de prueba contra el resto de la misma cuenta, en las mismas fechas."""
    f = d["fechas"]
    p, r = d["con"]["prueba"], d["con"]["resto"]                         # [leads, en_bitrix, contactados, test_drive, ventas]
    mp, mr = d["madura"].get("prueba"), d["madura"].get("resto")
    madura = (f"Con los leads de 7 días o más (hasta el {corta(f['madura_hasta'])}): <b>{dec(_pct(mp[2], mp[0]))} %</b> "
              f"({mp[2]} de {mp[0]}) contra {dec(_pct(mr[2], mr[0]))} % ({mr[2]} de {mr[0]})." if mp and mr and mp[0] and mr[0] else "")
    return (f'<div class="card{" d" if oscura else ""}"><span class="tag">Primer paso: contacto</span><h3>{esc(marca)}</h3>'
            f'<div class="sub">Leads que un asesor trabajó, en la misma cuenta y las mismas fechas ({corta(f["con"][0])} al {corta(f["con"][1])}).</div>'
            '<div class="vs">' + _barra_pct(f"Campaña de prueba ({p[2]} de {p[0]})", _pct(p[2], p[0]), True)
            + _barra_pct(f"Resto de la cuenta ({r[2]} de {r[0]})", _pct(r[2], r[0]), False) + "</div>"
            + '<div class="embudo">' + "".join(f"<div><b>{v}</b><span>{t}</span></div>" for v, t in
                                              ((p[0], "leads de la prueba"), (p[2], "contactados"), (p[3], "test drive"), (p[4], "venta"))) + "</div>"
            + ul([madura, "Test drive y venta: todavía no se alcanzan a medir."]) + "</div>")


def lamina_conversion(cv: dict[str, Any], inv: dict[str, Any], datos: dict[str, Any], fecha_c: str) -> str:
    sep = cv["septiembre"]
    hasta = datos["ventas"].get("ventas_hasta")
    mediana = _num(r"pasan (\d+) días \(mediana", _texto("Sistema/💰 Ventas que vinieron de Meta.md"))
    hechos = ul([f"El reporte de ventas del ERP llega al <b>{corta(hasta) if hasta else '—'}</b> y las pruebas empezaron el 18/09 y el 21/09.",
                 f"Del lead a la venta pasan <b>{mediana or '—'} días</b> (mediana).",
                 f"El ERP casi no trae teléfono ni mail: el cruce busca por nombre y encuentra {n_(inv, 'ventas_meta')} de {n_(inv, 'ventas')} "
                 "ventas. Es un mínimo.",
                 f"Desde septiembre, de <b>{miles(sep[0])}</b> leads: {miles(sep[1])} contactados, {sep[2]} con test drive y {sep[3]} con venta registrada."])
    oscura = ('<div class="card d"><span class="tag">Lo que falta</span><h3>La venta</h3>'
              '<div class="sub">Por qué todavía no se ve si los leads de la prueba terminaron en una venta:</div>' + hechos + "</div>")
    cuerpo = (f'<div class="cards3 conv">{tarjeta_conversion("Renault", cv["Renault"])}{tarjeta_conversion("Mitsubishi", cv["Mitsubishi"])}{oscura}</div>'
              '<div class="leer"><b>Cómo leerlo:</b> se compara la campaña de prueba con el resto de la misma cuenta en las mismas fechas, para que '
              "el equipo de asesores y la época sean los mismos. Con los leads de 7 días o más se evita contar a los que todavía no tuvieron tiempo "
              "de ser trabajados.</div>"
              '<div class="respuesta"><b>Cómo se va a medir:</b> ROI Pauta (dashboardmeta.santarosa.lat, menú «ROI Pauta») ya sigue cada campaña del '
              "lead a la venta, con las cuentas madre y las de asesores. Falta sumar el total por marca (madre y asesores juntos) y el "
              "comparativo con el período anterior, como ya se hace con los leads.</div>")
    return _pagina("Buyer Persona 360 · directorio · conversión",
                   "¿Esos leads convirtieron?", "Los de la prueba los trabajan los asesores igual o más que los demás; la venta todavía no se alcanza a medir.",
                   cuerpo,
                   "«Contactado»: un asesor movió el lead de etapa o lo convirtió en negocio (el pase automático de las 2 h no cuenta) · "
                   "Renew no se puede seguir hasta Bitrix: sus campañas son de WhatsApp y Meta no entrega el teléfono",
                   f"Datos de ROI Pauta al {fecha_c}")


def n_(inv: dict[str, Any], k: str) -> str:
    return miles(inv[k]) if inv.get(k) is not None else "—"


# ---------------------------------------------------------------------------
# Lo que hay detrás (pedido del 12-10: «todo lo que tiene Obsidian… es un proyecto muy ambicioso»)
# ---------------------------------------------------------------------------

VAULT = ROOT / "Buyer Persona"


def _texto(rel: str) -> str:
    try:
        return (VAULT / rel).read_text(encoding="utf-8")
    except OSError:
        return ""


def _num(patron: str, texto: str, grupo: int = 1) -> int | None:
    m = re.search(patron, texto, re.M)
    return int(m.group(grupo).replace(".", "").replace(",", "")) if m else None


def inventario(datos: dict[str, Any], marcas: dict[str, Any]) -> dict[str, Any]:
    """Cuánto hay en cada parte del sistema, leído del vault y de la corrida: nada escrito a mano."""
    promo = _texto("Buyer Personas/📢 Promociones Competencia.md")
    bitacora = _texto("Competencia/⚔️ Bitácora de Competencia.md")
    datacar = _texto("Competencia/💰 Precios Mercado 0km (Datacar).md")
    bench = _texto("Buyer Personas/⚔️ Benchmark Competitivo.md")
    mercado = _texto("Competencia/📊 Mercado Automotor PY 2026.md")
    erp = _texto("CRM/Ventas Reales - abril 2024 a abril 2026.md")
    memoria = _texto("Sistema/🧠 Memoria de Audiencia.md")
    jev = _texto("Campañas/🏷️ Clasificación de Anuncios.md")
    biblioteca = _texto("Competencia/📣 Anuncios de la Competencia.md")
    manual = _texto("Sistema/📘 Manual Buyer Persona.md")
    sabemos = memoria.split("## ✅ Lo que ya sabemos", 1)[-1].split("\n## ", 1)[0] if memoria else ""
    pm = (datos["ventas"].get("por_marca") or {}).values()
    return {
        "competidores": len(re.findall(r"^### ", promo, re.M)) or None,
        "cambios": len(re.findall(r"^- \*\*\d", bitacora, re.M)) or None,
        "versiones": _num(r"^versiones: (\d+)", datacar), "marcas_datacar": _num(r"(\d+) marcas · \d+ modelos", datacar),
        "nuestras_versiones": _num(r"lista vigente — (\d+) versiones", bench),
        "mercado": _num(r"^unidades_mercado: (\d+)", mercado), "unidades_sr": _num(r"^unidades_santa_rosa: (\d+)", mercado), "marcas_mercado": _num(r"^marcas_en_el_mercado: (\d+)", mercado),
        "share": (re.search(r"^share_santa_rosa: ([\d.]+)", mercado, re.M) or [None, None])[1],
        "facturadas": _num(r"^unidades_netas: (\d+)", erp),
        "ventas_meta": sum(m.get("con_meta", 0) for m in pm), "ventas": sum(m.get("ventas", 0) for m in pm),
        "ventas_hasta": datos["ventas"].get("ventas_hasta"),
        "corridas": _num(r"\*\*(\d+) corridas\*\*", memoria),
        "publicos": len(re.findall(r"🟢 sólido", sabemos)) or None,
        "anuncios_activos": _num(r"^anuncios_activos: (\d+)", jev),
        "bib_fecha": (re.search(r"^generado: '(\d{4})-(\d{2})-(\d{2})'", biblioteca, re.M) or re.search("(x)(y)(z)", "xyz")).groups()
        if biblioteca else (None, None, None),
        "bib_anuncios": _num(r"De \*\*(\d+)\*\* anuncios leídos", biblioteca),
        "bib_competidores": len([x for x in re.findall(r"^\| [^|]+\| (\d+) \|", biblioteca.split("## Resumen", 1)[-1].split("\n## ", 1)[0], re.M)
                                 if int(x) > 0]) or None,
        "comparativos": _num(r"posible publicidad comparativa \((\d+)\)", jev),
        "sitios": _num(r"en (\d+) sitios: Santa Rosa", manual) or 8,
        "google": len(list((VAULT / "Buyer Personas").glob("*/Marketing/Google Ads - *.md"))),
        "anuncios": sum(m.get("anuncios", 0) for m in (datos["materiales"].get("marcas") or {}).values()),
        "conjuntos": sum(((d["marca"] or {}).get("audience_mix") or {}).get("adsets", 0) for d in marcas.values() if d["marca"]),
        "notas": len([x for x in VAULT.rglob("*.md") if "Seguridad" not in x.relative_to(VAULT).parts[:1]]),
    }


def _biblioteca_txt(inv: dict[str, Any]) -> str:
    """Lo que se sabe de la lectura de la Biblioteca de Anuncios de Meta (se hace a pedido, no corre sola)."""
    f = inv.get("bib_fecha")
    if not (f and f[0] and inv.get("bib_anuncios")):
        return "Sus anuncios en la Biblioteca de Meta se leen a pedido, con una sesión de Claude."
    return (f"Sus anuncios en la Biblioteca de Meta (ofertas, copys y estructura) se leen a pedido: {miles(inv['bib_anuncios'])} anuncios de "
            f"{inv['bib_competidores']} marcas o casas el {f[2]}/{f[1]}.")


def lamina_sistema(inv: dict[str, Any], fecha_c: str) -> str:
    def n(clave: str) -> str:
        return miles(inv[clave]) if inv.get(clave) is not None else "—"
    share = f"{float(inv['share']):.1f}".replace(".", ",") if inv.get("share") else "—"
    bloques = [
        ("o", "Pauta de Meta", f"{n('anuncios')}<small>anuncios</small>",
         "de los últimos 6 meses, uno por uno, en las 85 cuentas: costo por lead, qué formato rinde y qué campaña termina en venta."),
        ("", "Segmentación", f"{n('conjuntos')}<small>conjuntos</small>",
         "revisados: a quién le habla cada uno (público nuevo, quien ya consultó, base propia, similares o Advantage+)."),
        ("o", "Clasificación con IA", f"{n('anuncios_activos')}<small>anuncios</small>",
         "activos que una IA (Jev) lee todos los días: qué ofrecen, con qué argumento, si ponen precio o cuotas y si "
         f"llaman a actuar. Alerta de publicidad comparativa (ley PY): hoy {n('comparativos')}."),
        ("", "Competencia", f"{n('competidores')}<small>competidores</small>",
         f"con su web revisada cada mañana: promociones, precios y modelos nuevos ({n('cambios')} cambios desde agosto). " + _biblioteca_txt(inv)),
        ("", "Benchmark y precios", f"{n('versiones')}<small>versiones</small>",
         f"con precio de lista de {n('marcas_datacar')} marcas, comparadas con nuestras {n('nuestras_versiones')} versiones, y "
         "duelos modelo contra modelo. Solo uso interno."),
        ("", "Mercado", f"{share} %<small>del mercado</small>",
         f"de Santa Rosa en {n('mercado')} matriculaciones de 2026 (enero a julio, CADAM/DNRA), entre {n('marcas_mercado')} marcas."),
        ("o", "Ventas y stock", f"{n('facturadas')}<small>unidades</small>",
         f"facturadas de abril de 2024 a abril de 2026 (ERP), con stock disponible y en viaje por modelo. {n('ventas_meta')} de "
         f"{n('ventas')} ventas recientes tenían antes un lead de Meta."),
        ("", "Píxel y analítica web", f"{n('sitios')}<small>sitios</small>",
         "con píxel de Meta y Google Analytics: miden visitas, formularios y clics a WhatsApp, para volver a buscar a quien "
         "ya consultó."),
        ("", "Google Ads", f"{n('google')}<small>anuncios</small>",
         "de búsqueda ya redactados, uno por ficha. El conector está escrito: falta la credencial de solo lectura para "
         "traer sus resultados."),
        ("o", "Memoria que aprende", f"{n('publicos')}<small>públicos</small>",
         f"confirmados por modelo tras {n('corridas')} corridas diarias. Busca por significado en {n('notas')} notas con "
         "una IA local (EmbeddingGemma), sin mandar datos afuera."),
    ]
    cuerpo = ('<div class="sis">' + "".join(f'<div class="bloque {c}"><h3>{esc(t)}</h3><b>{v}</b><p>{x}</p></div>'
                                            for c, t, v, x in bloques) + "</div>"
              '<div class="banda"><b>No reemplaza a los dashboards:</b> el costo por lead y las ventas se siguen viendo en el de Meta Ads '
              "y en el Comercial de Bitrix. El Buyer Persona agrega quién es el comprador, qué anuncio poner y qué ventas vinieron de Meta. "
              f'<b>{n("notas")} notas en Obsidian</b> que se actualizan solas a las 06:00 y se consultan en cerebro.santarosa.lat. '
              "Sin datos personales de clientes: del CRM y las ventas solo se guardan totales.</div>")
    return _pagina("Buyer Persona 360 · directorio · lo que hay detrás",
                   "Lo que hay detrás:", "un sistema que junta pauta, ventas, stock, mercado y competencia, y aprende solo todos "
                   "los días.", cuerpo,
                   "Fuentes: Meta Ads, ERP, Bitrix (totales), stock, CADAM/DNRA, Datacar, webs de la competencia · "
                   "la competencia es solo para uso interno (ley de Paraguay)",
                   f"Datos al {fecha_c}")


# ---------------------------------------------------------------------------
# Guía para explicar las láminas (pedido del 12-10: «Valentina me pide cada detalle»)
# ---------------------------------------------------------------------------

def _estado_conjuntos(conj: dict[str, Any]) -> str:
    nombres = {"ACTIVE": "activo", "PAUSED": "en pausa"}
    return ", ".join(f"{m} {nombres.get(v['estado'], v['estado'].lower())}"
                     + (f" (USD {v['dia']:.0f} por día)" if v["estado"] == "ACTIVE" else "") for m, v in conj.items())


def guia_conversion(cv: dict[str, Any], inv: dict[str, Any], mediana: int | None) -> list[tuple[str, str]]:
    """Cómo se calcula cada número de la lámina de conversión y sus límites."""
    out = [("Qué se mide",
            "«Contactado» es que un asesor trabajó el lead: lo movió de etapa o lo convirtió en negocio. El pase automático de Bitrix a «Leads "
            "contactado» a las 2 horas no cuenta. Es el primer paso del embudo: lead, contactado, test drive, venta. Los datos salen de ROI Pauta "
            "del Dashboard Meta (tabla roi_embudo, que se recalcula cada noche), y solo se leyeron conteos.")]
    for marca in ("Renault", "Mitsubishi"):
        d = cv[marca]
        f, p, r = d["fechas"], d["con"]["prueba"], d["con"]["resto"]
        a = d["antes"]["cuenta"]
        con_total = [p[i] + r[i] for i in range(5)]
        mp, mr = d["madura"].get("prueba"), d["madura"].get("resto")
        txt = (f"Mismas fechas ({corta(f['con'][0])} al {corta(f['con'][1])}) y misma cuenta. Campaña de prueba: {p[0]} leads, {p[2]} contactados "
               f"({dec(_pct(p[2], p[0]))} %). Resto de la cuenta: {r[0]} leads, {r[2]} contactados ({dec(_pct(r[2], r[0]))} %). "
               f"Test drive y venta: {p[3] + r[3]} y {p[4] + r[4]} en total.")
        if mp and mr and mp[0] and mr[0]:
            txt += (f" Con los leads de 7 días o más (hasta el {corta(f['madura_hasta'])}, para que hayan tenido tiempo de ser trabajados): "
                    f"{dec(_pct(mp[2], mp[0]))} % ({mp[2]} de {mp[0]}) contra {dec(_pct(mr[2], mr[0]))} % ({mr[2]} de {mr[0]}).")
        if marca == "Mitsubishi":
            txt += " Son pocos leads de la prueba: leerlo como señal, no como promedio."
        else:
            txt += (f" Antes de la prueba ({corta(f['antes'][0])} al {corta(f['antes'][1])}) la cuenta tenía {a[0]} leads con {dec(_pct(a[2], a[0]))} % "
                    f"contactados, y con la prueba {con_total[0]} con {dec(_pct(con_total[2], con_total[0]))} %. La baja se ve igual en los leads de "
                    "la prueba que en el resto, así que no viene de la prueba; qué la causa no se midió.")
        out.append((f"{marca}: ¿se contactan?", txt))
    sep = cv["septiembre"]
    out += [("Por qué no se compara con el período anterior",
             "Se compara la campaña de prueba contra el resto de la misma cuenta en las mismas fechas, no antes contra después: el porcentaje de "
             "leads trabajados cambia de un período a otro para toda la cuenta (en Renault bajó parejo en la prueba y en el resto)."),
            ("Qué todavía no se mide",
             f"La venta: el reporte de ventas del ERP se exporta a mano y llega al {corta(inv['ventas_hasta']) if inv.get('ventas_hasta') else '—'}, "
             f"las pruebas empezaron después y del lead a la venta pasan {mediana or '—'} días (mediana). El ERP casi no trae teléfono ni mail desde "
             f"agosto, así que el cruce va por nombre y es un mínimo ({n_(inv, 'ventas_meta')} de {n_(inv, 'ventas')} ventas). Test drive: de {miles(sep[0])} "
             f"leads desde septiembre, {sep[2]} pasaron por «Test Drive realizado» y {sep[3]} tienen venta registrada. Renew: sus campañas son de WhatsApp, "
             "Meta no entrega el teléfono y no se pueden seguir hasta Bitrix."),
            ("Qué haría falta para medir la venta",
             "1) cargar con regularidad un reporte de ventas del ERP posterior; 2) que el reporte traiga teléfono y mail; 3) que los asesores marquen "
             "la etapa «Test Drive realizado» en Bitrix; 4) en ROI Pauta, sumar el total por marca (cuentas madre y de asesores juntas) y el "
             "comparativo con el período anterior, como ya se hace con los leads.")]
    return out


def guia(pr: dict[str, Any], inv: dict[str, Any], c: dict[str, list[str]], fecha_c: str,
         cv: dict[str, Any]) -> list[tuple[str, list[tuple[str, str]]]]:
    """Cómo se calcula y de dónde sale cada número de las tres láminas, con las preguntas que suelen venir."""
    rn, rh = pr["renew"], pr.get("renew_habitual") or {}
    g_rn, c_rn = sum(v["gasto"] for v in rn.values()), sum(v["conversaciones"] for v in rn.values())
    r, m = pr["Renault"], pr["Mitsubishi"]
    f_ant, f_act, f_1 = r["fases"]["antes"], r["fases"]["IA corregida"], r["fases"]["IA 1ª versión"]
    mas_a, mas = f_ant["modelos"]["Master"]["total"], f_act["modelos"]["Master"]
    sube = (f_act["cuenta"]["leads_dia"] / f_ant["cuenta"]["leads_dia"] - 1) * 100
    ia_r, ag_r, ia_m, ag_m = (r["acumulado"]["cuenta|ia"], r["acumulado"]["cuenta|resto"],
                              m["acumulado"]["cuenta|ia"], m["acumulado"]["cuenta|resto"])
    total = g_rn + ia_r[0] + ia_m[0]
    n = lambda k: miles(inv[k]) if inv.get(k) is not None else "—"
    M = lambda x: miles(round(x))
    lista = lambda xs, vacio: y_lista(xs) if xs else vacio
    share = f"{float(inv['share']):.1f}".replace(".", ",") if inv.get("share") else "—"
    hasta = corta(pr["hasta"])
    mediana_dias = _num(r"pasan (\d+) días \(mediana", _texto("Sistema/💰 Ventas que vinieron de Meta.md"))
    return [
        (f"Lámina 1 · Las pruebas con el Buyer Persona (Meta hasta el {hasta})", [
            ("Qué es una prueba",
             "Una campaña de Meta armada con la ficha del Buyer Persona (a quién hablarle, qué formato y qué texto). Innovación la crea en "
             "pausa y se activa con el OK de la marca. Renault empezó el 18/09, Mitsubishi el 21/09 y Renew corrió del 23 al 30/09 con USD 100."),
            ("Cómo se calcula el costo por lead",
             "Lo pagado a Meta dividido por los leads que dejó. Un lead es un formulario completado. En Renew es una conversación de WhatsApp "
             "iniciada desde el anuncio, porque esa campaña pide mensajes y no formulario. No incluye honorarios de agencia ni costos internos."),
            (f"Renew: {usd(g_rn / c_rn)} contra {usd(rh['gasto'] / rh['conversaciones'])}",
             f"Prueba (campañas Clavos y Mantecas): {usd(g_rn)} y {c_rn:.0f} conversaciones. Campaña habitual de ventas por WhatsApp de la "
             f"misma cuenta, en los mismos días: USD {dec(rh['gasto'], 2)} y {rh['conversaciones']:.0f} conversaciones. La diferencia es de "
             f"{(1 - (g_rn / c_rn) / (rh['gasto'] / rh['conversaciones'])) * 100:.0f} %. Ojo: son 8 días y USD 100, sirve como señal y no como "
             "promedio. Los 10 autos se eligieron con la ficha: 5 difíciles de vender (campaña Clavos) y 5 de los más buscados (Mantecas)."),
            (f"Renault: +{sube:.0f} % de leads por día",
             f"Compara toda la cuenta, con las campañas de la agencia incluidas. Antes: {corta(f_ant['desde'])} al {corta(f_ant['hasta'])} "
             f"({f_ant['dias']} días), {dec(f_ant['cuenta']['leads_dia'])} leads por día a USD {dec(f_ant['cuenta']['cpl'], 2)} cada uno. "
             f"Con la prueba corregida: {corta(f_act['desde'])} al {corta(f_act['hasta'])} ({f_act['dias']} días), "
             f"{dec(f_act['cuenta']['leads_dia'])} leads por día a USD {dec(f_act['cuenta']['cpl'], 2)}. La primera versión de la prueba "
             f"({corta(f_1['desde'])} al {corta(f_1['hasta'])}) se reemplazó por la corregida y no entra en la comparación. "
             "Es un antes y después de la cuenta, no un experimento aislado: en ese tiempo la agencia también hizo cambios."),
            ("Renault: Master",
             f"Casi no se pautaba: {dec(mas_a['leads_dia'])} leads por día en la cuenta. Pasó a {dec(mas['total']['leads_dia'])}: "
             f"{dec(mas['ia']['leads_dia'])} de la campaña de prueba y {dec(mas['resto']['leads_dia'])} de la agencia, que sumó un conjunto "
             "propio en Ciudad del Este. Por eso se dice que la prueba «abrió» el modelo, no que lo hizo sola."),
            (f"Prueba contra agencia: Renault {usd(_cpl(ia_r))} contra {usd(_cpl(ag_r))}; Mitsubishi {usd(_cpl(ia_m))} contra {usd(_cpl(ag_m))}",
             f"Renault: USD {M(ia_r[0])} y {ia_r[1]:.0f} leads la prueba; USD {M(ag_r[0])} y {ag_r[1]:.0f} las demás campañas de la cuenta. "
             f"Mitsubishi: USD {M(ia_m[0])} y {ia_m[1]:.0f} la prueba; USD {M(ag_m[0])} y {ag_m[1]:.0f} las demás. Las campañas de la agencia llevan "
             "meses optimizándose y la de prueba recién aprende (Meta necesita unas 3 o 4 semanas y unos 50 resultados por semana). "
             "En Mitsubishi la prueba fue sobre todo L200, un modelo que la agencia ya pautaba bien: ahí no mejoró el costo."),
            ("Qué contestan los leads",
             "Del formulario solo se cuentan las respuestas (cuándo piensa comprar, cómo pagaría, para qué lo usa). No se guardan nombres, "
             "mails ni teléfonos."),
            ("Lo invertido",
             f"USD {M(total)} en Meta: Renew USD {M(g_rn)}, Renault USD {M(ia_r[0])} y Mitsubishi USD {M(ia_m[0])}, sin honorarios."),
            (f"Estado de las campañas de prueba al {hasta}",
             f"Renault: {_estado_conjuntos(r['conjuntos'])}. Mitsubishi: {_estado_conjuntos(m['conjuntos'])}. Las campañas de prueba las "
             "activa y las pausa cada marca."),
            ("Por qué se recomienda como guía y no como campañas nuevas",
             "Donde la prueba repitió un modelo que la agencia ya pautaba bien (Koleos, L200) el costo por lead no mejoró. Donde abrió algo "
             "nuevo (los usados de Renew, Master) sí funcionó. Por eso: primero se usa para ajustar los anuncios que ya corren, y una campaña "
             "aparte solo se justifica donde hay algo nuevo que abrir."),
        ]),
        ("Lámina 2 · ¿Esos leads convirtieron?", guia_conversion(cv, inv, mediana_dias)),
        ("Lámina 3 · Cómo seguir con las demás marcas", [
            ("Falta pauta",
             "Modelo con 10 ventas o más al año cuya pauta «que le corresponde» supera en USD 100 al mes o más a la que tiene. Corresponde = "
             "gasto mensual de la marca × % de las ventas de la marca que es ese modelo (ERP, 12 meses). Tiene = gasto mensual de la marca × % "
             "de los anuncios de la marca que son de ese modelo."),
            ("Modelos de la lista",
             "Con unidades disponibles: " + lista(c["probar"], "ninguno") + ". Esperar stock: " + lista(c["esperar"], "ninguno")
             + ". Confirmar stock antes de pautar: " + lista(c["confirmar"], "ninguno") + ". El stock sale de Cars (disponible + en viaje), "
             "con la fecha de la última lectura."),
            ("Retargeting y público nuevo",
             "Retargeting es volver a mostrarle anuncios a quien ya miró la web o abrió el formulario. Público nuevo (frío) es gente que "
             "todavía no conoce la marca: conjuntos con intereses o Advantage+ y sin base propia. Se cuentan conjuntos de anuncios, no gasto. "
             "En " + lista(c["frio"], "ninguna marca") + " el 95 % o más de los conjuntos es público nuevo."),
            ("Quien acompaña la decisión",
             "En " + lista(c["acompana"], "ninguna marca") + " la lectura del centro de compra es «ella investiga y él da el paso». "
             "Sale de comparar quién hace clic con quién deja sus datos. Detalle en la nota «Centro de compra — todas las marcas»."),
            ("Qué falta para la etapa «Después»",
             "Mandarle a Meta qué leads terminaron comprando necesita el OK de Innovación (usa datos de clientes). Google Ads necesita la "
             "cuenta de servicio de solo lectura de Google Cloud, que todavía no está creada."),
            ("Dashboards",
             "El costo por lead y las ventas ya se siguen en el dashboard de Meta Ads (dashboardmeta.santarosa.lat) y en el Comercial de Bitrix "
             "(bitrix.santarosa.lat). El Buyer Persona no los reemplaza: suma quién es el comprador y qué anuncio poner."),
        ]),
        ("Lámina 4 · Lo que hay detrás", [
            ("Pauta de Meta",
             f"{n('anuncios')} anuncios de los últimos 6 meses de las 85 cuentas: costo por lead, formato, ubicación y duración del video. API de "
             "Meta en solo lectura, todos los días a las 06:00. Se compara solo dentro del mismo tipo de cuenta (de la marca o de un asesor) y "
             "del mismo objetivo, para no mezclar cosas distintas. Nota «Materiales que funcionan» de cada marca."),
            ("Segmentación",
             f"{n('conjuntos')} conjuntos de anuncios activos clasificados por público: nuevo (frío), base propia, similares o Advantage+. "
             "Se ve en cada nota de marca, en «Públicos hoy»."),
            ("Clasificación con IA (Jev)",
             f"Una IA de TypeSafe lee el texto de {n('anuncios_activos')} anuncios activos y los clasifica: oferta, argumento, si pone precio o "
             "cuotas, si llama a actuar y si apura. También marca el riesgo de publicidad comparativa (hoy "
             f"{n('comparativos')} avisos para revisar). Lee solo el texto, no la imagen ni el video, y es una ayuda para revisar, no un "
             "dictamen. La corrida del 12/10 quedó incompleta (1.000 de 1.121 textos) por un límite de crédito del proveedor."),
            ("Competencia",
             f"{n('competidores')} casas (Nissan, Nipon, Garden, Chery, Geely, Diesa, DLS, Automaq y Toyotoshi): su web se revisa a las 08:00 "
             f"y cada cambio queda en la Bitácora ({n('cambios')} desde agosto). Sus anuncios activos en la Biblioteca de Anuncios de Meta "
             "se leen a pedido con una sesión de Claude y un navegador real, no corren solos: la API oficial de Meta no entrega anuncios "
             "comerciales de Paraguay y la página pública no se entrega a navegadores automatizados (y no se esquiva). "
             + (f"La lectura del {inv['bib_fecha'][2]}/{inv['bib_fecha'][1]} trae {n('bib_anuncios')} anuncios de {n('bib_competidores')} marcas o casas competidoras "
                "(los más vistos de cada uno, solo de sus páginas oficiales) y queda en la nota «Anuncios de la Competencia»: qué ofrecen, "
                "cómo arman el texto, hace cuánto corren y qué se puede responder con argumentos propios. " if inv.get("bib_fecha") and inv.get("bib_anuncios") else "")
             + "Lee el texto, no la imagen ni el video. Es solo de uso interno: la ley de Paraguay no permite nombrar marcas ni modelos "
             "de la competencia en publicidad."),
            ("Benchmark y precios",
             f"{n('versiones')} versiones con precio de lista de {n('marcas_datacar')} marcas (datacarpy.com), contra nuestras "
             f"{n('nuestras_versiones')} versiones (Cars, nuestro sistema). Competencia directa = mismo segmento y precio dentro del ±25 %. "
             "Los duelos modelo contra modelo usan solo precios verificados de los dos lados."),
            ("Mercado",
             f"{share} % = {n('unidades_sr')} de {n('mercado')} matriculaciones de enero a julio de 2026 entre {n('marcas_mercado')} marcas "
             "(CADAM/DNRA). Es matriculación, no facturación."),
            ("Ventas y stock",
             f"{n('facturadas')} unidades netas facturadas de abril de 2024 a abril de 2026 (ERP). {n('ventas_meta')} de {n('ventas')} ventas "
             "recientes tenían antes un lead de Meta: el cruce compara nombre, teléfono y mail cifrados solo en memoria y se guardan solo "
             "totales. Es un mínimo: desde agosto el ERP casi no trae teléfono ni mail y el cruce depende del nombre."),
            ("Píxel y analítica web",
             f"{n('sitios')} sitios (Santa Rosa, Jetour, JAC, JMEV, Mitsubishi, XPeng, Zeekr y Leapmotor) con Google Analytics (formulario "
             "enviado y clic a WhatsApp) y píxel de Meta desde el 24 y 25 de septiembre. Falta que el CRM le mande a Meta las conversiones "
             "(Conversions API): es el siguiente paso."),
            ("Google Ads",
             f"{n('google')} anuncios de búsqueda ya redactados, uno por ficha, listos para cargar. Todavía no hay resultados: Google dio de baja "
             "el token de desarrollador el 9 de septiembre de 2026 y el acceso ahora va por una cuenta de servicio de solo lectura."),
            ("Memoria que aprende",
             f"{n('publicos')} públicos confirmados (el mismo público se repitió en {n('corridas')} corridas diarias seguidas), reglas aprendidas "
             f"y tendencias. La búsqueda por significado usa EmbeddingGemma, un modelo que corre en la propia computadora: indexa "
             f"{n('notas')} notas y el texto no sale de ahí."),
        ]),
        ("Preguntas que puede hacer Valentina", [
            ("¿Esto reemplaza a la agencia?",
             "No. Es información: a quién hablarle, qué formato y qué texto. La pauta de cada marca la siguen manejando la marca y su agencia."),
            ("¿Por qué Renew salió mejor que Mitsubishi?",
             "Renew abrió 10 autos usados que no tenían campaña propia. En Mitsubishi se probó sobre todo L200, que la agencia ya pautaba bien."),
            ("¿Los leads de la prueba convirtieron?",
             "En el primer paso, sí: los de la prueba los trabaja un asesor igual o más que los demás de la misma cuenta (lámina 2). La venta "
             "todavía no se puede medir: el ERP llega al 11/09 y las pruebas empezaron el 18/09 y el 21/09."),
            ("¿Entonces el Buyer Persona vende más?",
             "Todavía no se puede afirmar. Se midió el costo por lead y que el lead se trabaje; falta la venta. Cuando se cargue un reporte de "
             "ventas posterior, ROI Pauta la va a mostrar por campaña y se podrá comparar la campaña de prueba con las demás."),
            ("¿Cuánto costó probarlo?", f"USD {M(total)} en Meta en las tres pruebas, sin honorarios."),
            ("¿Qué parte de la mejora de Renault es del Buyer Persona?",
             "No se puede separar del todo. Es un antes y después de toda la cuenta, y la agencia también sumó anuncios. Lo que sí se ve: Master "
             "pasó de casi no pautarse a 6,8 leads por día, y 1,8 de esos son de la prueba."),
            ("¿Cómo sabemos qué venta vino de Meta?",
             "Se cruza cada venta del ERP con los leads de Meta por teléfono, mail o nombre, cifrados solo en memoria. Es un mínimo, no el total."),
            ("¿Se puede nombrar a la competencia en un anuncio?",
             "No. Por ley de Paraguay solo se usan argumentos propios. La competencia se mira para decidir precio, pauta y argumentos de venta."),
        ]),
    ]


def guia_md(secciones: list[tuple[str, list[tuple[str, str]]]], fecha: str, fecha_c: str) -> str:
    L = ["---", "type: guia", f"created: {fecha}", "tags: [buyer-persona, directorio, guia]", "---",
         f"# 📖 Guía para explicar las láminas del directorio ({fecha_c})", "",
         "> Cómo se calcula y de dónde sale cada número de las tres láminas, y las preguntas que suelen venir. "
         "La arma `scripts/laminas_directorio.py` junto con las láminas, con los mismos datos.", ""]
    for titulo, items in secciones:
        L += [f"## {titulo}", ""]
        for tema, texto in items:
            L += [f"**{tema}{'' if tema.endswith('?') else '.'}** {texto}", ""]
    return "\n".join(L)


def guia_pdf(secciones: list[tuple[str, list[tuple[str, str]]]], fecha_c: str, pdf: Path) -> None:
    css = ("@page{size:A4;margin:16mm 15mm}*{box-sizing:border-box}body{font-family:Inter,Arial,Helvetica,sans-serif;color:#111;"
           "font-size:10.5pt;line-height:1.45;margin:0}h1{font-size:19pt;letter-spacing:-.02em;margin:0 0 4px}"
           ".sub{color:#666;font-size:10pt;margin-bottom:6px}h2{font-size:12pt;color:#e8590c;border-top:3px solid #111;padding-top:8px;"
           "margin:20px 0 8px;break-after:avoid}p{margin:0 0 7px;break-inside:avoid}p b{color:#111}")
    cuerpo = "".join(f"<h2>{esc(t)}</h2>" + "".join(f"<p><b>{esc(a)}{'' if a.endswith('?') else '.'}</b> {esc(b)}</p>" for a, b in items) for t, items in secciones)
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{css}</style></head><body>'
           f"<h1>Guía para explicar las láminas del directorio</h1><div class=\"sub\">Buyer Persona 360 · datos al {esc(fecha_c)} · "
           f"para quien presenta, no para proyectar</div>{cuerpo}</body></html>")
    h = pdf.with_suffix(".html")
    h.write_text(doc, encoding="utf-8")
    subprocess.run([base._chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"file://{h}"], check=True, timeout=180,
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    h.unlink()


GLOSARIO = [
    ("Quién es", "Género y edad de quienes contactan por los anuncios de Meta de la marca (dejan sus datos o escriben; no es quien "
                 "firma la compra), con cuántos contactos se midió. Los leads por ciudad salen de los formularios."),
    ("Nivel socioeconómico (NSE) estimado", "Meta no informa NSE en Paraguay. Se estima con cuatro señales: el ticket que se "
                                            "factura (ERP), cuántos piden financiación en el formulario, cuántos hacen clic desde "
                                            "un iPhone y la zona."),
    ("Centro de compra · quién mira y quién decide", "Las personas que intervienen en la compra. Se mide cuánto contactan ellas "
                                                    "contra ellos viendo el mismo anuncio, cuántas compras factura una empresa, "
                                                    "si en los chats el cliente nombra a otra persona y cuántos entregan un usado."),
    ("Segmentación y retargeting", "A quién le habla hoy cada conjunto de anuncios. Público frío: no conoce la marca. "
                                   "Advantage+: Meta amplía el público solo. Retargeting: volver a quien abrió el formulario, "
                                   "visitó la web o interactuó. Similares (lookalike): gente parecida a compradores o leads."),
    ("Qué le interesa", "Temas de los anuncios que este público ve y clickea, en % de los anuncios de la marca. Meta dejó de "
                        "entregar intereses declarados en 2021: se infieren de lo que la gente mira."),
    ("Qué funciona", "Seis meses de anuncios, uno por uno: formato (imagen, video, carrusel), duración del video y ubicación. "
                     "Se compara solo entre campañas parecidas (misma cuenta y tipo de formulario) y vale lo que se repite mes a mes."),
    ("Costo por lead y ventas con lead de Meta", "Costo: inversión ÷ leads, solo en campañas de formulario (julio a septiembre). "
                                                 "Ventas con lead de Meta: ventas del ERP cuyo cliente antes dejó un formulario "
                                                 "(cruce cifrado, sin guardar datos personales). Es un mínimo."),
    ("Cómo le va", "Unidades vendidas en el año contra el objetivo a la fecha (ERP y planilla de objetivos), costo por lead, "
                   "ventas que vinieron de Meta y stock disponible y en viaje."),
    ("Qué hacer y lectura", "Dónde probar primero: un modelo que vende más de lo que se pauta y tiene stock. Más las piezas que "
                            "pide el centro de compra y los públicos que faltan. La lectura resume el hueco más grande de la pauta "
                            "y la oportunidad del centro de compra. Todo se crea en pausa y se activa con el OK de la marca."),
]


def lamina_glosario(fecha_c: str) -> str:
    cuerpo = '<div class="glos">' + "".join(f"<div><b>{esc(t)}</b><p>{esc(x)}</p></div>" for t, x in GLOSARIO) + "</div>"
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<section class="slide"><div class="k">Buyer Persona 360 · directorio · cómo leer las láminas por marca</div>'
            f'<h1>Una lámina por marca con todo lo que sabemos del comprador: <span>quién es, cómo decide, cómo le '
            f'hablamos hoy y qué funciona.</span></h1>{cuerpo}'
            f'<div class="foot"><span>Fuentes: Meta Ads (85 cuentas, 90 días; materiales: 6 meses), ERP de ventas, Bitrix (solo '
            f'agregados), stock, objetivos y planilla de acciones · se regenera cada día a las 06:00</span>'
            f'<span>Datos al {fecha_c} · sin datos personales</span></div></section></body></html>')


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", default=date.today().isoformat())
    ap.add_argument("--raw", default=str(ROOT / "output" / "raw"))
    ap.add_argument("--sin-meta", action="store_true", help="reutiliza output/raw/pruebas_directorio_<fecha>.json")
    ap.add_argument("--completo", action="store_true",
                    help="suma qué es el Buyer Persona, el glosario y una lámina por marca")
    ap.add_argument("--sin-vault", action="store_true")
    a = ap.parse_args()
    fecha = a.fecha
    fecha_c = corta(fecha)
    datos = base.cargar(Path(a.raw))
    marcas = base.por_marca(datos["personas"])
    per = datos["centro"].get("periodo_meta") or {}
    periodo = f"{corta(per['start'])} → {corta(per['end'])}" if per.get("start") else "90 días"
    salida = ROOT / "output" / "presentacion" / f"directorio_{fecha}"
    salida.mkdir(parents=True, exist_ok=True)
    for viejo in [*salida.glob("lamina_*.html"), *salida.glob("directorio_*.png"), *salida.glob("*.pdf")]:
        viejo.unlink()
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    pr = datos_resultados(fecha, a.sin_meta)
    cand = candidatos_roadmap(marcas, datos["centro"])
    inv = inventario(datos, marcas)
    cv = datos_conversion(fecha, pr, a.sin_meta)
    secciones = guia(pr, inv, cand, fecha_c, cv)
    laminas = [("pruebas", "Resultados de las pruebas", lamina_resultados(pr, fecha_c)),
               ("conversion", "¿Esos leads convirtieron?", lamina_conversion(cv, inv, datos, fecha_c)),
               ("como_seguir", "Cómo seguir con las demás marcas", lamina_roadmap(cand, fecha_c)),
               ("detras", "Lo que hay detrás", lamina_sistema(inv, fecha_c))]
    if a.completo:
        laminas = [("proyecto", "Qué es el Buyer Persona", lamina_proyecto(numeros_proyecto(datos, marcas), fecha_c)), *laminas,
                   ("glosario", "Cómo leer las láminas por marca", lamina_glosario(fecha_c))]
    rango = (datos["ventas"].get("ventas_desde", "2026-08-04"), datos["ventas"].get("ventas_hasta", "2026-09-11"))
    for m in ORDEN_MARCAS if a.completo else []:
        if m not in marcas or not marcas[m]["marca"]:
            continue
        d = {**marcas[m], "hoy": fecha, "centro": (datos["centro"].get("marcas") or {}).get(m) or {},
             "material": (datos["materiales"].get("marcas") or {}).get(m),
             "ventas": (datos["ventas"].get("por_marca") or {}).get(m), "rango_ventas": rango}
        laminas.append((m.lower(), m, lamina_marca(m, d, fecha_c, periodo)))
    pngs = []
    for n, (nombre, _, html) in enumerate(laminas, start=1):
        h = salida / f"lamina_{n:02d}_{nombre}.html"
        h.write_text(html, encoding="utf-8")
        p = salida / f"directorio_{n:02d}_{nombre}.png"
        base.render_png(h, p)
        pngs.append(p)
        print(f"  {p.relative_to(ROOT)}")
    pdf = salida / f"Directorio {fecha} - Buyer Persona 360.pdf"
    base.render_pdf([html for _, _, html in laminas], pdf)
    print(f"  {pdf.relative_to(ROOT)}")
    pdf_guia = salida / f"Guía para explicar - Directorio {fecha}.pdf"
    guia_pdf(secciones, fecha_c, pdf_guia)
    print(f"  {pdf_guia.relative_to(ROOT)}")
    if not a.sin_vault:
        carpeta = ROOT / "Buyer Persona" / "Sistema" / f"Directorio {fecha}"
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in [*carpeta.glob("Lámina *.png"), *carpeta.glob("*.pdf")]:
            viejo.unlink()
        shutil.copy2(pdf, carpeta / pdf.name)
        shutil.copy2(pdf_guia, carpeta / pdf_guia.name)
        (carpeta / "📖 Guía para explicar el directorio.md").write_text(guia_md(secciones, fecha, fecha_c), encoding="utf-8")
        L = ["---", "type: presentacion", f"created: {fecha}", "tags: [buyer-persona, directorio, presentacion]", "---",
             f"# 🗂️ Directorio — Buyer Persona 360 ({fecha_c})", "",
             "> Qué pasó en las pautas que ya hicimos con el Buyer Persona (Renew, Renault y Mitsubishi; solo pauta de Meta, "
             "contra las campañas habituales), cómo seguir con las demás marcas y todo lo que hay detrás del sistema "
             "(pedidos de Croman del 12-10). "
             + ("También qué es el Buyer Persona y una lámina por marca. " if a.completo else
                "La versión con una lámina por marca sale con `--completo`. ")
             + "Se regeneran con `scripts/laminas_directorio.py`; fuente HTML en `output/presentacion/directorio_" + fecha + "/`.", "",
             f"Todas en un PDF: [[{pdf.name}]] · Para quien presenta: [[📖 Guía para explicar el directorio]] ([[{pdf_guia.name}]])", ""]
        for n, ((_, titulo, _), p) in enumerate(zip(laminas, pngs), start=1):
            shutil.copy2(p, carpeta / f"Lámina {n}.png")
            L += [f"## {n} · {titulo}", f"![[Lámina {n}.png]]", ""]
        L += ["Relacionado: [[🗂️ Comité 2026-10-05 — Actualización]] · [[📘 Manual Buyer Persona]] · "
              "[[🎬 Materiales Meta — todas las marcas]]", ""]
        for vieja in carpeta.glob("🗂️ Directorio *.md"):
            vieja.unlink()
        (carpeta / f"🗂️ Directorio {fecha} — Buyer Persona 360.md").write_text("\n".join(L), encoding="utf-8")
        print(f"  nota: {carpeta.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
