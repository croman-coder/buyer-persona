#!/usr/bin/env python3
"""Láminas del comité: cómo van las pruebas con el Buyer Persona y el estado de las 11 marcas.

Pedido de Valentina (05-10-2026): agregar a la press de comité la actualización de las pruebas de
Renault y Mitsubishi, pero para todas las marcas. Mismo formato que las láminas del 21/09:
1920×1080, se pegan como imagen en Google Slides. Salen 7 láminas: las pruebas y una tarjeta por
marca (de a dos). Sin la tabla de las 11 marcas y sin la inversión mensual de cada marca en Meta
(Croman, 05-10: «sacar esto» y «sacar meta mes»).

Entra
- Los JSON de la última corrida del pipeline (output/raw/personas_*, materiales_meta_*,
  centro_de_compra_*), en el servidor o copiados con scp.
- Para las pruebas, la API de Meta, solo lectura: de los formularios solo se cuentan respuestas,
  nunca se guarda un dato de una persona. El resultado queda en output/raw/pruebas_comite_<fecha>.json
  y con --sin-meta se reutiliza sin llamar a la API.

Sale: output/presentacion/comite_<fecha>/ (HTML + PNG) y la nota del vault Sistema/Comité <fecha>/.

Uso:
    venv/bin/python3 scripts/laminas_comite.py [--fecha AAAA-MM-DD] [--raw DIR] [--sin-meta] [--sin-vault]
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API = "https://graph.facebook.com/v21.0"
VAULT = ROOT / "Buyer Persona"
GENERO = {"Masculino": "Hombre", "Femenino": "Mujer"}
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
PERSONAL = re.compile(r"full_name|first_name|last_name|nombre|apellido|phone|tel[eé]fono|email|correo|city|ciudad|"
                      r"street|zip|c[eé]dula|documento", re.I)

# Las pruebas con el Buyer Persona (ver Campañas/ en el vault). La cuenta y la campaña IA no cambian.
PRUEBAS = {
    "Renault": {"cuenta": "act_956049245637827", "campana": "120250583223260518", "desde": "2026-09-18",
                "modelos": {"Koleos": "koleos", "Master": "master"}, "piezas_desde": "2026-10-01"},
    "Mitsubishi": {"cuenta": "act_506680188632635", "campana": "120252656563550663", "desde": "2026-09-21",
                   "modelos": {"L200": "l200", "Montero": "montero"}, "piezas_desde": "2026-10-01"},
}
RENEW = {"Clavos": "120250602052540465", "Mantecas": "120250602078240465"}
GWM_H6_ANUNCIO = "120252026124490123"
ORDEN_MARCAS = ("GWM", "Jetour", "Renault", "Soueast", "JAC", "Mitsubishi", "Renew", "Leapmotor", "Zeekr", "XPeng", "JMEV")


# ---------------------------------------------------------------------------
# Formato de números y fechas
# ---------------------------------------------------------------------------

def miles(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def usd(x: float | None, dec: int = 2) -> str:
    if x is None:
        return "—"
    return "USD " + (miles(x) if x >= 100 else f"{x:.{dec}f}".replace(".", ","))


def dec(x: float | None, n: int = 1) -> str:
    """Número con coma decimal: 7,0"""
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def stock_txt(st: dict[str, Any] | None, largo: bool = False) -> str:
    """«20 disponibles + 83 en viaje» (el total mezcla lo que está en el país con lo que viene en barco)."""
    if not st or not st.get("total"):
        return "sin stock cargado"
    disp, viaje = st.get("disponible") or 0, st.get("en_viaje") or 0
    uno = "disponible" if disp == 1 else "disponibles"
    if largo:
        return f"{st['total']} en stock ({disp} {uno})"
    return f"{disp} {uno}" + (f" + {viaje} en viaje" if viaje else "")


def pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0f} %"


def corta(iso: str) -> str:
    """2026-10-04 → 04/10"""
    return f"{iso[8:10]}/{iso[5:7]}"


def esc(s: Any) -> str:
    return html.escape(str(s), quote=False)


# ---------------------------------------------------------------------------
# Datos del pipeline
# ---------------------------------------------------------------------------

def ultimo(raw: Path, prefijo: str) -> Path:
    archivos = sorted(glob.glob(str(raw / f"{prefijo}_*.json")))
    if not archivos:
        raise SystemExit(f"No hay {prefijo}_*.json en {raw}")
    return Path(archivos[-1])


def cargar(raw: Path) -> dict[str, Any]:
    out = {}
    for clave, prefijo in (("personas", "personas"), ("materiales", "materiales_meta"),
                           ("centro", "centro_de_compra"), ("ventas", "ventas_meta")):
        try:
            out[clave] = json.loads(ultimo(raw, prefijo).read_text(encoding="utf-8"))
        except SystemExit:
            if clave in ("personas",):
                raise
            out[clave] = {}
    return out


def por_marca(personas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    marcas: dict[str, dict[str, Any]] = {}
    for p in personas:
        s = p.get("segment", {})
        if s.get("type") == "brand":
            marcas.setdefault(s["name"], {"marca": None, "modelos": []})["marca"] = p
        elif s.get("type") == "model":
            marcas.setdefault(s["brand"], {"marca": None, "modelos": []})["modelos"].append(p)
    for m in marcas.values():
        m["modelos"].sort(key=lambda p: -(p["segment"].get("orders_last_365d") or 0))
    return marcas


# ---------------------------------------------------------------------------
# Textos de las tarjetas de marca
# ---------------------------------------------------------------------------

def publico(p: dict[str, Any]) -> str:
    d = p.get("demographics") or {}
    meta = d.get("meta") or {}
    gen = GENERO.get(d.get("gender") or "", d.get("gender") or "")
    txt = f"{gen} {d.get('age_range', '')}".strip()
    if meta.get("gender_share"):
        txt += f" ({meta['gender_share']:.0f} %)"
    if d.get("meta_level") == "marca":
        txt += " · dato de la marca"
    return txt or "—"


def ventas_con_meta(v: dict[str, Any] | None, desde: str, hasta: str) -> str:
    """Cuántas ventas del ERP tuvieron antes un lead de Meta (cruce con claves cifradas: es un mínimo)."""
    n = (v or {}).get("ventas", 0)
    if n < 10:
        return f"pocas ventas para cruzar con Meta ({n} del {corta(desde)} al {corta(hasta)})"
    return f"al menos <b>{v['con_meta']} de {n} ventas</b> ({v['con_meta'] / n * 100:.0f} %) vinieron de un lead de Meta"


AGENCIA = {"Renault", "Mitsubishi"}   # la cuenta de la marca también tiene campañas de la agencia (CLAUDE.md, regla 3)
SUJETO = {"Imagen": "la imagen (gráfica)", "Video": "el video", "Carrusel": "el carrusel", "Mixto": "imagen y video juntos"}
UNIDAD = {"formulario": ("lead", "leads", "de formulario"), "chat": ("conversación", "conversaciones", "de WhatsApp")}


def may(t: str) -> str:
    return t[:1].upper() + t[1:]


def y_lista(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def modelo_corto(nombre: str, marca: str) -> str:
    return nombre[len(marca) + 1:] if nombre.startswith(marca + " ") else nombre


def _ok(comp: dict[str, Any]) -> bool:
    """Ganó por 15 % o más y se repite en al menos el 60 % de los meses comparables (nota 🎬 de la marca)."""
    return comp.get("estado") == "gana" and comp.get("meses", 0) >= 2 and comp["meses_ganados"] / comp["meses"] >= 0.6


def destinos(mat_m: dict[str, Any] | None) -> list[tuple[str, dict[str, Any]]]:
    """Formularios y WhatsApp, del que más gastó al que menos (6 meses)."""
    return sorted(((d, r) for d, r in ((mat_m or {}).get("destinos") or {}).items() if d in UNIDAD),
                  key=lambda dr: -dr[1]["total"]["gasto"])


def costo_reciente(r: dict[str, Any], hoy: str) -> tuple[float | None, int, str]:
    """Costo por resultado de los últimos 3 meses completos, solo en campañas de ese destino."""
    meses = [m for m in sorted(r.get("meses") or {}) if m < hoy[:7]][-3:]
    if not meses:
        return None, 0, ""
    tot = [((r["meses"][m] or {}).get("Total") or {}) for m in meses]
    g, n = sum(t.get("gasto", 0) for t in tot), sum(t.get("resultados", 0) for t in tot)
    etiqueta = MESES[int(meses[0][5:]) - 1] + (f" a {MESES[int(meses[-1][5:]) - 1]}" if len(meses) > 1 else "")
    return (g / n if n else None), int(n), etiqueta


def linea_hoy(mat_m: dict[str, Any] | None, ventas: dict[str, Any] | None, rango: tuple[str, str], hoy: str) -> str:
    partes = []
    ds = destinos(mat_m)
    total = sum(r["total"]["gasto"] for _, r in ds) or 1
    for d, r in ds:
        if partes and r["total"]["gasto"] / total < 0.25:
            continue
        c, _, et = costo_reciente(r, hoy)
        if c is not None:
            u, _, de = UNIDAD[d]
            partes.append(f"<b>{usd(c)}</b> por {u} {de} ({et})")
    return " · ".join(partes + [ventas_con_meta(ventas, *rango)])


def que_funciona(mat_m: dict[str, Any] | None, centro_m: dict[str, Any] | None) -> list[str]:
    """Lo que dicen los 6 meses de anuncios de la marca, comparando solo campañas parecidas."""
    ds = destinos(mat_m)
    if not ds:
        return ["Todavía sin análisis de materiales"]
    d, r = ds[0]
    u = UNIDAD[d][0]
    art, barato = ("el", "más barato") if u == "lead" else ("la", "más barata")
    out = []
    comp = r["comparaciones"]["formato"]
    est = comp.get("estado")
    if est == "gana":
        g, riv = SUJETO.get(comp["ganador"], comp["ganador"]), SUJETO.get(comp["rival"], comp["rival"])
        if _ok(comp):
            t = (f"{may(g)} trae {art} {u} {comp['dif'] * 100:.0f} % {barato} que {riv} "
                 f"({comp['meses_ganados']} de {comp['meses']} meses)")
            v = r["comparaciones"].get(f"vertical|{comp['ganador']}") or {}
            if _ok(v) and v["ganador"].endswith("Con versión vertical"):
                t += ", mejor con versión vertical (9:16)"
        else:
            t = (f"{may(g)} parece rendir más que {riv} ({comp['dif'] * 100:.0f} % menos), pero no todos los meses: "
                 "tener los dos")
        out.append(t)
    elif est == "empate":
        out.append(f"{may(SUJETO.get(comp['ganador'], comp['ganador']))} y {SUJETO.get(comp['rival'], comp['rival'])} "
                   "rinden parecido: tener los dos")
    elif est == "uno":
        out.append(f"Casi todo fue {SUJETO.get(comp['ganador'], comp['ganador'])}: falta probar otro formato")
    tramo = r["comparaciones"].get("tramo") or {}
    if _ok(tramo):
        out.append(f"En video, los de {tramo['ganador'].lower()}: {tramo['dif'] * 100:.0f} % {'más baratos' if u == 'lead' else 'más baratas'} "
                   f"({tramo['meses_ganados']} de {tramo['meses']} meses)")
    ubic = sorted((x for x in r["ubicaciones"] if x["clave"] in ("Feed", "Reels", "Stories") and x["suficiente"] and x["costo"]),
                  key=lambda x: x["costo"])
    if len(ubic) >= 2:
        if 1 - ubic[0]["costo"] / ubic[-1]["costo"] >= 0.15:
            out.append(f"{may(art)} {u} {barato} sale en {ubic[0]['clave']} ({usd(ubic[0]['costo'])} contra "
                       f"{usd(ubic[-1]['costo'])} en {ubic[-1]['clave']}): tener la pieza en ese tamaño")
        else:
            out.append("Feed, Reels y Stories cuestan parecido: no forzar una ubicación")
    e = (centro_m or {}).get("embudo") or {}
    if e.get("lectura") == "ellas_avanzan" and e.get("ellas_vs_ellos"):
        out.append(f"Ellas son pocas en los clics, pero contactan {dec(e['ellas_vs_ellos'], 2)}× lo que ellos")
    return out[:3]


def texto_rec(rec: dict[str, Any], centro_m: dict[str, Any], marca: str) -> str:
    """Una recomendación del centro de compra (👥 Quién mira y quién decide), en una línea."""
    clave = rec.get("clave")
    emp = (centro_m or {}).get("empresa") or {}
    if clave == "acompañante":
        t = "Pieza para quien acompaña la decisión"
    elif clave == "empresa" and emp.get("empresa_pct"):
        t = f"Pieza «Para tu empresa»: el {emp['empresa_pct']:.0f} % lo factura una empresa"
    elif clave == "ellas_avanzan":
        t = "Pieza que les hable a ellas, que avanzan más"
    elif clave == "compartir":
        t = "Algo para que el cliente le muestre a quien decide con él"
    else:
        t = rec.get("titulo", "")
    mods = [modelo_corto(m, marca) for m in rec.get("modelos") or []][:3]
    return t + (f" ({y_lista(mods)})" if mods else "")


def buenas_practicas(marca: str, mat_m: dict[str, Any] | None, centro_m: dict[str, Any] | None,
                     marca_p: dict[str, Any], mods: list[dict[str, Any]], hoy: str) -> list[str]:
    """Las reglas del Manual (sección 4) con los números de la marca, y lo que pide su centro de compra."""
    out = []
    ds = destinos(mat_m)
    if ds:
        d, r = ds[0]
        c, _, _ = costo_reciente(r, hoy)
        if c:
            u, us, _ = UNIDAD[d]
            minimo = max(5, round(7 * c)) if d == "chat" else max(1, round(7 * c))
            out.append(f"USD {minimo}/día o más por conjunto (~50 {us} por semana); juzgar a las 3-4 semanas y cortar "
                       f"antes solo si a las 2 semanas pasa de {usd(2 * c)} por {u}")
    for rec in ((centro_m or {}).get("meta_ads") or [])[:2]:
        out.append(texto_rec(rec, centro_m or {}, marca))
    mix = marca_p.get("audience_mix") or {}
    if mix.get("frio_pct", 0) >= 95:
        out.append(f"Sumar similares y retargeting: el {mix['frio_pct']:.0f} % de los conjuntos va a público frío")
    if marca in AGENCIA:
        out.append("No pautarle al mismo público que la agencia en la misma cuenta: se encarecen las dos")
    con_td = [p for p in mods if ((p.get("extras") or {}).get("stock") or {}).get("test_drive")]
    if con_td:
        nombres = [modelo_corto(p["name"], marca) for p in con_td]
        lista = y_lista(nombres) if len(nombres) <= 3 else f"{', '.join(nombres[:3])} y {len(nombres) - 3} más"
        fecha = ((con_td[0].get("extras") or {}).get("stock") or {}).get("fecha", "")
        out.append(f"Test drive solo con unidad de prueba: {lista}" + (f" (stock del {corta(fecha)})" if fecha else ""))
    else:
        out.append("Sin unidad de test drive en stock: invitar al salón")
    return out[:5]


def proximo_paso(marca: str, mods: list[dict[str, Any]], marca_p: dict[str, Any]) -> str:
    """Dónde probar primero (o qué mover) según la brecha pauta/venta de cada modelo."""
    frases = []

    def falta(p: dict[str, Any]) -> float:
        b = p.get("budget") or {}
        return (b.get("suggested_month") or 0) - (b.get("current_month_est") or 0)

    # Solo cuenta si la diferencia vale la pena: 10 ventas o más y USD 100/mes entre lo que se gasta y lo que sugiere el motor
    sub = [p for p in mods if p["segment"].get("gap") == "sub-pautado" and (p["segment"].get("orders_last_365d") or 0) >= 10
           and falta(p) >= 100]
    if sub:
        # Primero los que tienen unidades para vender hoy; un modelo sin stock disponible espera a que lleguen
        def con_stock(p: dict[str, Any]) -> int:
            st = (p.get("extras") or {}).get("stock") or {}
            return 0 if (st.get("total") and not st.get("disponible")) else 1
        p = max(sub, key=lambda p: (con_stock(p), p["segment"]["orders_last_365d"]))
        s, b = p["segment"], p.get("budget") or {}
        st = (p.get("extras") or {}).get("stock") or {}
        nombre = esc(modelo_corto(p["name"], marca))
        sin_unidades = bool(st.get("total")) and not st.get("disponible")
        f = (f"<b>{'Esperar el stock de' if sin_unidades else 'Probar primero'} {nombre}</b>: vende {s['orders_last_365d']} al año con "
             f"{s['ad_count']} anuncios (sub-pautado)")
        if sin_unidades:
            f += f", pero hoy no tiene unidades disponibles ({st.get('en_viaje') or 0} en viaje): pautarlo cuando lleguen"
        elif st.get("total"):
            f += f" y tiene {stock_txt(st)}"
        if b.get("suggested_month") and b.get("current_month_est") is not None:
            f += f"; sugerido USD {b['suggested_month'] / 30:.0f}/día, hoy USD {b['current_month_est'] / 30:.0f}/día"
        frases.append(f + ".")
        if not sin_unidades and (VAULT / "Buyer Personas" / marca / "Marketing" / f"Meta Ads - {p['name']}.md").exists():
            frases.append(f"Textos listos en Marketing/Meta Ads - {esc(p['name'])}.")
    else:
        # Un modelo sin ninguna venta es un lanzamiento (o un agrupador como «Usados»): no es para mover pauta
        sobre = [p for p in mods if p["segment"].get("gap") == "sobre-pautado" and falta(p) <= -100
                 and (p["segment"].get("orders_last_365d") or 0) >= 1]
        if sobre:
            p = max(sobre, key=lambda p: p["segment"].get("ad_count") or 0)
            s = p["segment"]
            frases.append(f"<b>Mover pauta de {esc(modelo_corto(p['name'], marca))}</b> a los modelos que venden más: "
                          f"{s['ad_count']} anuncios para {s.get('orders_last_365d') or 0} ventas en 12 meses (sobre-pautado).")
        elif mods:
            total = sum(p["segment"].get("orders_last_365d") or 0 for p in mods)
            gasto = ((marca_p.get("budget") or {}).get("spend_month") or 0)
            ventas = f"{total} venta{'s' if total != 1 else ''}"
            if total < 5 and gasto >= 500:
                frases.append(f"<b>Mucha pauta para pocas ventas</b>: {ventas} en 12 meses "
                              "(se mide por leads, no por ventas, mientras no haya más).")
            else:
                frases.append(f"<b>Mantener el reparto</b>: ningún modelo vende mucho más o mucho menos de lo que se pauta "
                              f"({ventas} en 12 meses).")
    if marca in PRUEBAS:
        frases.append(f"Prueba en curso con {' y '.join(PRUEBAS[marca]['modelos'])}: ver la lámina 1.")
    return " ".join(frases)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{background:#fff;font-family:Inter,Arial,Helvetica,sans-serif;color:#111}
.slide{width:1920px;height:1080px;position:relative;overflow:hidden;background:#fff;padding:56px 110px}
.k{font-size:22px;letter-spacing:.18em;text-transform:uppercase;color:#6b6b6b;font-weight:600}
h1{font-size:50px;font-weight:800;letter-spacing:-.02em;line-height:1.06;margin-top:12px}
h1 span{color:#e8590c}
.tests{display:grid;grid-template-columns:1fr 1fr;gap:36px;margin-top:22px}
.t{border:2px solid #111;padding:16px 26px}
.t.m{background:#111;color:#fff}
.t h3{font-size:32px;font-weight:800;letter-spacing:-.01em}
.t h3 small{font-size:18px;font-weight:600;color:#e8590c;margin-left:14px;letter-spacing:.06em;text-transform:uppercase}
.t.m h3 small{color:#ffb27a}
table{width:100%;border-collapse:collapse;margin-top:12px}
th{text-align:left;font-size:16px;letter-spacing:.08em;text-transform:uppercase;color:#777;font-weight:600;padding:0 0 7px;border-bottom:1px solid #ccc}
.t.m th{color:#aaa;border-color:#444}
td{padding:7px 12px 7px 0;font-size:18px;line-height:1.28;vertical-align:top;border-bottom:1px solid #eee}
.t.m td{border-color:#333}
td:first-child{font-weight:800;width:150px}
.res{margin-top:12px;font-size:19px;line-height:1.34}
.t ul{padding-left:20px;margin:0}
.t li{margin:2px 0}
.t li::marker{color:#e8590c}
.t.m li::marker{color:#ffb27a}
.vault{margin-top:8px;font-size:15px;color:#777;line-height:1.3}
.t.m .vault{color:#aaa}
.ref{font-size:14px;color:#777;margin-top:3px;line-height:1.3}
.t.m .ref{color:#aaa}
.reglas{margin-top:12px;font-size:19px;line-height:1.36}
.reglas li{margin:6px 0}
.dense .t{padding:14px 22px}
.dense .t h3{font-size:26px}
.dense .t h3 small{font-size:16px;margin-left:12px}
.dense table{margin-top:10px}
.dense th{font-size:15px;padding-bottom:6px}
.dense td{padding:5px 10px 5px 0;font-size:17px;line-height:1.28}
.dense td:first-child{width:122px}
.dense .res{margin-top:9px;font-size:18px;line-height:1.34}
.res b{color:#e8590c}.t.m .res b{color:#ffb27a}
.t b{font-weight:800}
.aprend{margin-top:16px;display:grid;grid-template-columns:1.35fr 1fr;gap:40px;border-top:3px solid #111;padding-top:12px}
.aprend .l{font-size:19px;line-height:1.4;color:#222}
.aprend .l b{color:#111}
.aprend .h{font-size:16px;letter-spacing:.1em;text-transform:uppercase;color:#777;font-weight:700;margin-bottom:4px}
.foot{position:absolute;left:110px;right:110px;bottom:34px;font-size:18px;color:#777;display:flex;justify-content:space-between;border-top:1px solid #ddd;padding-top:11px;gap:40px}
.res .tag{display:inline-block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:#777;margin-right:8px}
.nota{margin-top:14px;font-size:17px;color:#333;line-height:1.4;border-left:3px solid #e8590c;padding-left:14px}
"""


def lamina(kicker: str, titulo: str, naranja: str, cuerpo: str, pie_izq: str, pie_der: str) -> str:
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<section class="slide"><div class="k">{esc(kicker)}</div><h1>{titulo} <span>{naranja}</span></h1>{cuerpo}'
            f'<div class="foot"><span>{pie_izq}</span><span>{pie_der}</span></div></section></body></html>')


def fila(label: str, *celdas: str, ancho: int = 2) -> str:
    if len(celdas) == 1:
        return f'<tr><td>{label}</td><td colspan="{ancho}">{celdas[0]}</td></tr>'
    return f"<tr><td>{label}</td>" + "".join(f"<td>{c}</td>" for c in celdas) + "</tr>"


def tarjeta(titulo: str, etiqueta: str, columnas: list[str], filas: list[str], res: str, oscura: bool = False) -> str:
    cab = ("<tr><th></th>" + "".join(f"<th>{esc(c)}</th>" for c in columnas) + "</tr>") if columnas else ""
    chico = f"<small>{esc(etiqueta)}</small>" if etiqueta else ""
    return (f'<div class="t{" m" if oscura else ""}"><h3>{esc(titulo)}{chico}</h3>'
            f'<table>{cab}{"".join(filas)}</table><div class="res">{res}</div></div>')


def lista_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def tarjeta_marca(marca: str, datos: dict[str, Any], oscura: bool) -> str:
    """Resumen de la marca: quién compra, cómo está hoy, qué funciona, buenas prácticas y próximo paso."""
    mp, mods = datos["marca"] or {}, datos["modelos"]
    quien = " · ".join(f"<b>{esc(modelo_corto(p['name'], marca))}</b> {esc(publico(p)).lower()}" for p in mods[:2]) \
        or esc(publico(mp))
    # Pedido de Croman (05-10): aclarar que son modelos de referencia tomados como ejemplo, con datos reales
    n = len(mods[:2])
    if n:
        que = ("marca de usados" if n == 1 else "marcas de usados") if marca == "Renew" else ("modelo" if n == 1 else "modelos")
        cual = ("la" if n == 1 else "las") if marca == "Renew" else ("el" if n == 1 else "los")
        quien += (f'<div class="ref">Ejemplo con datos reales: {n} {que} de referencia, {cual} que más '
                  f'{"vendió" if n == 1 else "vendieron"} en 12 meses (Meta y ERP)</div>')
    filas = [
        fila("Quién compra", quien, ancho=1),
        fila("Hoy", linea_hoy(datos["material"], datos["ventas"], datos["rango_ventas"], datos["hoy"]), ancho=1),
        fila("Qué funciona", lista_html(que_funciona(datos["material"], datos["centro"])), ancho=1),
        fila("Buenas prácticas", lista_html(buenas_practicas(marca, datos["material"], datos["centro"], mp, mods, datos["hoy"])), ancho=1),
    ]
    res = (f"<b>Próximo paso:</b> {proximo_paso(marca, mods, mp)}"
           f'<div class="vault">En el vault (Buyer Personas/{esc(marca)}/): Materiales que funcionan · Quién mira y quién decide · '
           "textos listos en Marketing/</div>")
    return tarjeta(marca, "", [], filas, res, oscura)


REGLAS = [
    "Toda campaña nueva se crea <b>en pausa</b>; la activa Innovación con el OK de la marca.",
    "Ley de Paraguay: ningún texto nombra marcas o modelos de la competencia.",
    "Sin tasas, plazos, garantías ni urgencias inventadas. La oferta sale de la planilla del mes y se confirma con la "
    "marca: si la planilla es de un mes anterior, la nota la marca vencida.",
    "Test drive solo si hay unidad de prueba en stock (lo dice cada ficha).",
    "Un conjunto necesita ~50 resultados por semana para aprender: presupuesto diario ≈ 7 × el costo por resultado. "
    "En WhatsApp, nunca menos de USD 5 por día. Mejor un conjunto con plata que tres chicos.",
    "Juzgar a las 3-4 semanas, con el promedio de 4: la primera semana engaña. Cortar antes solo si compite con otra "
    "campaña nuestra o si a las 2 semanas cuesta el doble del promedio.",
    "No pautarle al mismo público que otra campaña de la misma cuenta: se encarecen las dos (pasó con la L200).",
    "Formatos: comparar solo campañas parecidas (misma cuenta y tipo de formulario) y creerle a lo que se repite mes a mes.",
]


def tarjeta_reglas(fecha: str) -> str:
    return (f'<div class="t m"><h3>Buenas prácticas para todas las marcas</h3>'
            f'<div class="reglas">{lista_html(REGLAS)}</div>'
            '<div class="res">Cada tarjeta suma lo propio de la marca: qué formato rinde, qué pieza pide su centro de compra, '
            f'cuánto presupuesto por conjunto y dónde hay unidad de test drive. Detalle en el Manual, sección 4. Datos al {fecha}.</div></div>')


# ---------------------------------------------------------------------------
# Pruebas: datos de la API y lámina
# ---------------------------------------------------------------------------

def _get(path: str, token: str, **p: Any) -> dict[str, Any]:
    import requests
    p["access_token"] = token
    url = path if path.startswith("http") else f"{API}/{path}"
    return requests.get(url, params=p, timeout=120).json()


def datos_pruebas(hasta: str) -> dict[str, Any]:
    """Resultados de las pruebas hasta ``hasta``. Solo lectura; de los formularios solo conteos."""
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    token = os.environ["META_ADS_ACCESS_TOKEN"]
    subprocess.run([sys.executable, str(ROOT / "scripts" / "informe_pautas_ia.py"), hasta], check=True,
                   stdout=subprocess.DEVNULL, cwd=ROOT)
    informe = json.loads((ROOT / "output" / f"informe_pautas_ia_{hasta}.json").read_text(encoding="utf-8"))
    paginas = {x["id"]: x["access_token"] for x in _get("me/accounts", token, fields="id,access_token", limit=200).get("data", [])}
    out: dict[str, Any] = {"hasta": hasta}
    for marca, cfg in PRUEBAS.items():
        r = informe[marca]
        total: dict[str, list[float]] = {}
        for dia, v in r["diario"].items():
            if dia < cfg["desde"]:
                continue
            for q in ("ia", "resto"):
                t = total.setdefault(f"cuenta|{q}", [0.0, 0.0])
                t[0] += v[q][0]
                t[1] += v[q][1]
            for m in cfg["modelos"]:
                for q in ("ia", "resto"):
                    t = total.setdefault(f"{m}|{q}", [0.0, 0.0])
                    t[0] += v[m][q][0]
                    t[1] += v[m][q][1]
        fases = {nombre: f for nombre, f in r["fases"].items()}
        # estado actual de los conjuntos de la campaña IA
        conj = _get(f"{cfg['campana']}/adsets", token, fields="name,effective_status,daily_budget", limit=20).get("data", [])
        estado = {}
        for c in conj:
            for m, clave in cfg["modelos"].items():
                if clave in c["name"].lower():
                    estado[m] = {"estado": c["effective_status"], "dia": int(c.get("daily_budget") or 0) / 100}
        # por anuncio, hasta la fecha
        ads = _get(f"{cfg['campana']}/insights", token, level="ad", fields="ad_name,spend,actions", limit=100,
                   time_range=json.dumps({"since": cfg["desde"], "until": hasta})).get("data", [])
        anuncios = []
        for x in ads:
            acc = {y["action_type"]: float(y["value"]) for y in x.get("actions", [])}
            anuncios.append({"nombre": x["ad_name"], "gasto": float(x["spend"]), "leads": acc.get("lead", 0)})
        # respuestas de los formularios: solo conteos
        respuestas: dict[str, dict[str, Any]] = {}
        creativos = _get(f"{cfg['campana']}/ads", token, fields="name,creative{object_story_spec,asset_feed_spec}", limit=50).get("data", [])
        formularios = set(re.findall(r"'lead_gen_form_id': '(\d+)'", str(creativos)))
        for fid in formularios:
            pagina = (_get(fid, token, fields="page").get("page") or {}).get("id")
            if pagina not in paginas:
                continue
            leads = _get(f"{fid}/leads", paginas[pagina], fields="created_time,field_data,campaign_id,ad_name", limit=200).get("data", [])
            for l in leads:
                if l.get("campaign_id") != cfg["campana"] or dia_local(l.get("created_time", "")) > hasta:
                    continue
                modelo = next((m for m, k in cfg["modelos"].items() if k in (l.get("ad_name") or "").lower()), "?")
                a = respuestas.setdefault(modelo, {"leads": 0, "este_mes": 0, "financiacion": 0, "usado": 0, "empresa": 0,
                                                   "cotizando": 0, "uso": {}})
                a["leads"] += 1
                for c in l.get("field_data", []):
                    nombre, valor = c.get("name", ""), (c.get("values") or [""])[0]
                    if PERSONAL.search(nombre):
                        continue
                    if nombre.startswith("cuando") and valor == "este_mes":
                        a["este_mes"] += 1
                    elif nombre.startswith("cuando") and valor in ("cotizando", "mirando"):
                        a["cotizando"] += 1
                    elif nombre in ("como_compras", "pago") and valor == "financiacion":
                        a["financiacion"] += 1
                    elif nombre in ("como_compras", "pago") and valor == "usado":
                        a["usado"] += 1
                    elif nombre == "como_compras" and valor == "empresa":
                        a["empresa"] += 1
                    elif nombre == "uso":
                        a["uso"][valor] = a["uso"].get(valor, 0) + 1
        nuevos = _get(f"{cfg['campana']}/ads", token, fields="name,created_time", limit=50).get("data", [])
        # Piezas que alguien sumó a la campaña después del lanzamiento (para contarlo en la lámina)
        creadas = sorted({str(a.get("created_time", ""))[:10] for a in nuevos} - {cfg["desde"]})
        out[marca] = {"desde": cfg["desde"], "acumulado": {k: [round(v[0], 2), round(v[1])] for k, v in total.items()},
                      "fases": {n: {"dias": f["dias"], "desde": f["desde"], "hasta": f["hasta"], "cuenta": f["cuenta"],
                                    "ia": f["ia"], "resto": f["resto"], "modelos": f["modelos"]} for n, f in fases.items()},
                      "conjuntos": estado, "anuncios": anuncios, "respuestas": respuestas,
                      "piezas_nuevas": [d for d in creadas if d >= cfg.get("piezas_desde", "2026-10-01")]}
    # Renew y GWM H6
    renew = {}
    for nombre, cid in RENEW.items():
        c = _get(cid, token, fields="name,lifetime_budget,stop_time")
        ins = (_get(f"{cid}/insights", token, fields="spend,actions", date_preset="maximum").get("data") or [{}])[0]
        acc = {y["action_type"]: float(y["value"]) for y in ins.get("actions", [])}
        renew[nombre] = {"gasto": float(ins.get("spend") or 0), "conversaciones": acc.get("onsite_conversion.messaging_conversation_started_7d", 0),
                         "fin": str(c.get("stop_time", ""))[:10]}
    out["renew"] = renew
    out["gwm_h6"] = _get(GWM_H6_ANUNCIO, token, fields="effective_status").get("effective_status")
    return out


CERO = {"nombre": "", "gasto": 0.0, "leads": 0.0}


def inv_prueba(d: dict[str, Any], modelo: str, stock: Any, nota: str = "") -> str:
    """«USD 9/día · USD 145 gastados · 49 en stock» o «Pausada (23/09) · …», según el estado de hoy del conjunto."""
    c = (d.get("conjuntos") or {}).get(modelo) or {}
    base = f"Pausada{nota}" if c.get("estado") == "PAUSED" else f"USD {c.get('dia', 0):.0f}/día{nota}"
    gastado = d["acumulado"].get(f"{modelo}|ia", [0, 0])[0]
    return f"{base} · {usd(gastado)} gastados · {stock_txt(stock, largo=True)}"


def dia_local(creado: str) -> str:
    """Fecha en hora de Paraguay (UTC-3) de un created_time de Meta: un lead de las 22 h del 04/10 viene como 05/10 UTC."""
    try:
        return (datetime.fromisoformat(creado.replace("+0000", "+00:00")) - timedelta(hours=3)).date().isoformat()
    except ValueError:
        return creado[:10]


def anuncio_por(anuncios: list[dict[str, Any]], modelo_clave: str, tipo: str, nueva: bool = False) -> dict[str, Any] | None:
    for a in anuncios:
        n = a["nombre"].lower()
        if modelo_clave in n and tipo in n and (("2026-10" in n) == nueva):
            return a
    return None


def cpl(x: list[float]) -> float | None:
    return x[0] / x[1] if x and x[1] else None


def tarjeta_renault(pr: dict[str, Any], mp: dict[str, dict[str, Any]], fecha: str) -> str:
    d = pr["Renault"]
    ac, f = d["acumulado"], d["fases"]
    kol, mas = d["respuestas"].get("Koleos", {}), d["respuestas"].get("Master", {})
    kg, mg = (anuncio_por(d["anuncios"], "koleos", "gráfica") or CERO), (anuncio_por(d["anuncios"], "master", "gráfica") or CERO)
    kr, mr = (anuncio_por(d["anuncios"], "koleos", "reel") or CERO), (anuncio_por(d["anuncios"], "master", "reel") or CERO)
    nuevas = d.get("piezas_nuevas") or []
    cuenta_antes, cuenta_ahora = f["antes"]["cuenta"], f["IA corregida"]["cuenta"]
    mas_m = f["IA corregida"]["modelos"]["Master"]
    mas_antes, mas_ahora = f["antes"]["modelos"]["Master"]["total"], mas_m["total"]
    ia_total = ac["cuenta|ia"]
    filas = [
        fila("Público", esc(publico(mp["Koleos"])), esc(publico(mp["Master"]))),
        fila("Inversión", inv_prueba(d, "Koleos", (mp["Koleos"].get("extras") or {}).get("stock")),
             inv_prueba(d, "Master", (mp["Master"].get("extras") or {}).get("stock"))),
        fila("CPL", f"<b>{usd(cpl(ac['Koleos|ia']))}</b> ({ac['Koleos|ia'][1]:.0f} leads) · agencia {usd(cpl(ac['Koleos|resto']))}",
             f"<b>{usd(cpl(ac['Master|ia']))}</b> ({ac['Master|ia'][1]:.0f} leads) · agencia {usd(cpl(ac['Master|resto']))}"),
        fila("Contestan", f"{kol.get('este_mes', 0)} de {kol.get('leads', 0)} compran este mes · {kol.get('financiacion', 0)} con financiación · "
                          f"{kol.get('usado', 0)} entregan un usado",
             f"{mas.get('este_mes', 0)} de {mas.get('leads', 0)} compran este mes · {mas.get('cotizando', 0)} solo cotizan · "
             f"{mas.get('empresa', 0)} compran por empresa"),
        fila("Anuncios", f"La gráfica rinde más que el reel: Master {usd(cpl([mg['gasto'], mg['leads']]))} contra {usd(cpl([mr['gasto'], mr['leads']]))}, "
                         f"Koleos {usd(cpl([kg['gasto'], kg['leads']]))} contra {usd(cpl([kr['gasto'], kr['leads']]))} (pocos leads)."
                         + (f" Desde el {corta(nuevas[0])} corren piezas nuevas (post 1:1 y reel)." if nuevas else "")),
        fila("Públicos", "Similares (1 %) + retargeting + intereses del segmento. Koleos se corrigió el 22/09: formulario, ubicaciones e intereses."),
    ]
    res = (f"{usd(ia_total[0], 0)} gastados y {ia_total[1]:.0f} leads: <b>{usd(cpl(ia_total))}</b> contra {usd(cpl(ac['cuenta|resto']))} de la agencia en la "
           f"misma cuenta. <b>Master sí abrió el modelo:</b> de {dec(mas_antes['leads_dia'])} a {dec(mas_ahora['leads_dia'])} leads por día en la cuenta "
           f"({dec(mas_m['ia']['leads_dia'])} de la prueba y {dec(mas_m['resto']['leads_dia'])} de la agencia, que sumó un conjunto en CDE). "
           f"<b>Koleos no:</b> la agencia ya llega a ese público a {usd(cpl(ac['Koleos|resto']))}. La cuenta pasó de {dec(cuenta_antes['leads_dia'])} a "
           f"{dec(cuenta_ahora['leads_dia'])} leads por día con el mismo CPL ({usd(cuenta_antes['cpl'])} → {usd(cuenta_ahora['cpl'])}).")
    return tarjeta("Prueba 1 · Renault", f"activa desde el {corta(d['desde'])} · datos al {corta(pr['hasta'])}", ["Koleos", "Master"], filas, res)


def tarjeta_mitsubishi(pr: dict[str, Any], mp: dict[str, dict[str, Any]]) -> str:
    d = pr["Mitsubishi"]
    ac, f = d["acumulado"], d["fases"]
    l2, mo = d["respuestas"].get("L200", {}), d["respuestas"].get("Montero", {})
    grafica = anuncio_por(d["anuncios"], "l200", "gráfica") or {"gasto": 0, "leads": 0}
    motion = anuncio_por(d["anuncios"], "l200", "motion") or {"gasto": 0, "leads": 0}
    remk = anuncio_por(d["anuncios"], "l200", "remarketing") or {"gasto": 0, "leads": 0}
    antes, ahora = f["antes"], f["IA corregida"]
    l200_antes = antes["modelos"]["L200"]["total"]["cpl"]
    uso = l2.get("uso", {})
    filas = [
        fila("Público", esc(publico(mp["L200"])), esc(publico(mp["Montero Sport"]))),
        fila("Inversión", inv_prueba(d, "L200", (mp["L200"].get("extras") or {}).get("stock"), " desde el 23/09"),
             inv_prueba(d, "Montero", (mp["Montero Sport"].get("extras") or {}).get("stock"), " el 23/09")),
        fila("CPL", f"<b>{usd(cpl(ac['L200|ia']))}</b> ({ac['L200|ia'][1]:.0f} leads) · agencia {usd(cpl(ac['L200|resto']))} (antes de la prueba: {usd(l200_antes)})",
             f"<b>{usd(cpl(ac['Montero|ia']))}</b> ({ac['Montero|ia'][1]:.0f} lead) · agencia {usd(cpl(ac['Montero|resto']))}"),
        fila("Contestan", f"{l2.get('este_mes', 0)} de {l2.get('leads', 0)} compran este mes · {l2.get('financiacion', 0)} con financiación · "
                          f"{uso.get('trabajo', 0)} para trabajo y {uso.get('personal', 0)} personal",
             f"{mo.get('leads', 0)} lead: este mes, con financiación, test drive esta semana" if mo.get("leads") == 1 else f"{mo.get('leads', 0)} leads"),
        fila("Anuncios", f"La gráfica trae casi todo: {usd(cpl([grafica['gasto'], grafica['leads']]))} por lead ({grafica['leads']:.0f} leads). "
                         f"Motion: {motion['leads']:.0f} leads con {usd(motion['gasto'])}. Remarketing: {remk['leads']:.0f} lead con {usd(remk['gasto'])} (se apagó el 23/09)."),
        fila("Públicos", "Desde el 23/09 solo prospección: similares e intereses, sin los públicos calientes de la agencia, para no competir en la misma subasta."),
    ]
    ia_total = ac["cuenta|ia"]
    res = (f"<b>No cumplió el criterio</b> (CPL de USD 5 o menos): L200 cuesta {usd(cpl(ac['L200|ia']))}. La primera versión usaba los mismos públicos calientes "
           f"que la agencia y le quitó leads (L200 de la agencia: {usd(l200_antes)} → {usd(cpl(ac['L200|resto']))}). La cuenta rinde menos que antes "
           f"({dec(antes['cuenta']['leads_dia'])} → {dec(ahora['cuenta']['leads_dia'])} leads por día; CPL {usd(antes['cuenta']['cpl'])} → {usd(ahora['cuenta']['cpl'])}) "
           f"y el CPL de la agencia también subió ({usd(antes['resto']['cpl'])} → {usd(ahora['resto']['cpl'])}): no todo es de la prueba.")
    return tarjeta("Prueba 2 · Mitsubishi", f"activa desde el {corta(d['desde'])} · datos al {corta(pr['hasta'])}", ["L200", "Montero Sport"], filas, res, oscura=True)


def lamina_pruebas(pr: dict[str, Any], marcas: dict[str, Any], fecha: str) -> str:
    mp = {p["name"].replace("Renault ", "").replace("Mitsubishi ", ""): p for m in ("Renault", "Mitsubishi") for p in marcas[m]["modelos"]}
    renault_ia, mitsu_ia = pr["Renault"]["acumulado"]["cuenta|ia"], pr["Mitsubishi"]["acumulado"]["cuenta|ia"]
    renault_ag, mitsu_ag = pr["Renault"]["acumulado"]["cuenta|resto"], pr["Mitsubishi"]["acumulado"]["cuenta|resto"]
    rn = pr["renew"]
    gasto_rn = sum(v["gasto"] for v in rn.values())
    conv_rn = sum(v["conversaciones"] for v in rn.values())
    mas = pr["Renault"]["fases"]
    cuerpo = ('<div class="tests dense">' + tarjeta_renault(pr, mp, fecha) + tarjeta_mitsubishi(pr, mp) + "</div>"
              '<div class="aprend"><div><div class="h">Qué aprendimos</div><div class="l">'
              "<b>La prueba suma donde el modelo casi no tenía pauta.</b> En Master, la cuenta pasó de "
              f"{dec(mas['antes']['modelos']['Master']['total']['leads_dia'])} a {dec(mas['IA corregida']['modelos']['Master']['total']['leads_dia'])} leads por día y de "
              f"{usd(mas['antes']['modelos']['Master']['total']['cpl'])} a {usd(mas['IA corregida']['modelos']['Master']['total']['cpl'])} por lead. "
              "<b>Donde la agencia ya llega al mismo público</b> (Koleos, L200), la prueba compite con ella y cuesta entre "
              f"{dec(cpl(pr['Mitsubishi']['acumulado']['L200|ia']) / cpl(pr['Mitsubishi']['acumulado']['L200|resto']))} y "
              f"{dec(cpl(pr['Renault']['acumulado']['Koleos|ia']) / cpl(pr['Renault']['acumulado']['Koleos|resto']))} veces más por lead. "
              "La gráfica rinde más que el reel o el motion en las dos marcas. "
              "<b>Próximo paso: probar donde un modelo vende más de lo que se pauta</b> (láminas siguientes).</div></div>"
              '<div><div class="h">Otras pruebas</div><div class="l">'
              f"<b>Renew</b> (23 al 30/09): {usd(gasto_rn, 0)} en 10 unidades → {conv_rn:.0f} conversaciones de WhatsApp a {usd(gasto_rn / conv_rn)} "
              f"(Clavos {usd(rn['Clavos']['gasto'] / rn['Clavos']['conversaciones'])} · Mantecas {usd(rn['Mantecas']['gasto'] / rn['Mantecas']['conversaciones'])}). "
              "<b>GWM H6</b> «Vengan a probarla juntos»: anuncio creado, "
              + ("en pausa: falta el OK para activarlo." if pr.get("gwm_h6") == "PAUSED" else "activo.") + "</div></div></div>")
    return lamina("Buyer Persona 360 · las pruebas con el Buyer Persona · actualización",
                  "Dos semanas de pruebas: la IA cuesta más por lead que la agencia,",
                  "pero abrió Master, que casi no traía leads en la cuenta.",
                  cuerpo,
                  f"Renault IA: {usd(cpl(renault_ia))} contra {usd(cpl(renault_ag))} de la agencia · Mitsubishi IA: {usd(cpl(mitsu_ia))} contra {usd(cpl(mitsu_ag))}",
                  "Meta (solo lectura) · del formulario solo se cuentan respuestas · detalle: Campañas/ en el vault")


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------

def _chrome() -> str:
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise SystemExit("Falta google-chrome o chromium para generar las láminas")
    return chrome


def render_png(html_path: Path, png_path: Path) -> None:
    subprocess.run([_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--window-size=1920,1080", f"--screenshot={png_path}", f"file://{html_path}"],
                   check=True, timeout=180, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def render_pdf(laminas_html: list[str], pdf_path: Path) -> None:
    """Todas las láminas en un PDF, una por página de 1920×1080, con el texto seleccionable (se puede copiar)."""
    cuerpos = [re.search(r'<section class="slide">.*</section>', h, re.S).group(0) for h in laminas_html]
    # Los estilos salen de las propias láminas: el directorio usa otros que el comité
    css = "".join(dict.fromkeys(m for h in laminas_html for m in re.findall(r"<style>(.*?)</style>", h, re.S)))
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{css}'
           "@page{size:1920px 1080px;margin:0}html,body{margin:0}"
           "*{-webkit-print-color-adjust:exact;print-color-adjust:exact}"   # sin esto las tarjetas oscuras salen en blanco
           ".slide{break-after:page}.slide:last-child{break-after:auto}</style></head><body>"
           + "".join(cuerpos) + "</body></html>")
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(doc, encoding="utf-8")
    subprocess.run([_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
                   check=True, timeout=180, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    html_path.unlink()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", default=date.today().isoformat(), help="fecha de las láminas (por defecto, hoy)")
    ap.add_argument("--raw", default=str(ROOT / "output" / "raw"), help="carpeta con los JSON de la última corrida")
    ap.add_argument("--sin-meta", action="store_true", help="reutiliza output/raw/pruebas_comite_<fecha>.json sin llamar a la API")
    ap.add_argument("--sin-vault", action="store_true", help="no escribe la nota ni copia los PNG al vault")
    a = ap.parse_args()
    fecha = a.fecha
    hasta = (date.fromisoformat(fecha) - timedelta(days=1)).isoformat()
    raw = Path(a.raw)
    datos = cargar(raw)
    marcas = por_marca(datos["personas"])
    per = ((datos["centro"].get("periodo_meta") or {}))
    cache = ROOT / "output" / "raw" / f"pruebas_comite_{fecha}.json"
    if a.sin_meta:
        pr = json.loads(cache.read_text(encoding="utf-8"))
    else:
        pr = datos_pruebas(hasta)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(pr, ensure_ascii=False, indent=1), encoding="utf-8")
    fecha_c = f"{fecha[8:10]}/{fecha[5:7]}"
    periodo = f"Meta del {corta(per['start'])} al {corta(per['end'])}" if per.get("start") else ""
    salida = ROOT / "output" / "presentacion" / f"comite_{fecha}"
    salida.mkdir(parents=True, exist_ok=True)
    for viejo in [*salida.glob("lamina_*.html"), *salida.glob("comite_actualizacion_*.png"), *salida.glob("*.pdf")]:
        viejo.unlink()          # si cambia la cantidad de láminas no quedan las de la corrida anterior

    laminas: list[tuple[str, str]] = [("pruebas", lamina_pruebas(pr, marcas, fecha_c))]
    titulos = ["Cómo van las pruebas: Renault y Mitsubishi"]
    presentes = [m for m in ORDEN_MARCAS if m in marcas and marcas[m]["marca"]]
    for i in range(0, len(presentes), 2):
        par = presentes[i:i + 2]
        tarjetas = []
        for j, m in enumerate(par):
            d = {**marcas[m], "fecha_corta": fecha_c, "hoy": fecha, "centro": (datos["centro"].get("marcas") or {}).get(m) or {},
                 "material": (datos["materiales"].get("marcas") or {}).get(m),
                 "ventas": ((datos["ventas"].get("por_marca") or {}).get(m)),
                 "rango_ventas": (datos["ventas"].get("ventas_desde", "2026-08-04"), datos["ventas"].get("ventas_hasta", "2026-09-11"))}
            tarjetas.append(tarjeta_marca(m, d, oscura=(j == 1)))
        if len(par) == 1:
            tarjetas.append(tarjeta_reglas(fecha_c))
        titulo = " y ".join(par)
        titulos.append(f"Qué funciona y buenas prácticas: {titulo}")
        laminas.append((f"marcas_{i // 2 + 1}", lamina(
            "Buyer Persona 360 · resumen por marca", "Qué funciona y qué conviene hacer:", f"{titulo}.",
            f'<div class="tests">{"".join(tarjetas)}</div>',
            "Fuentes: 6 meses de anuncios de Meta (todas las cuentas de la marca), ERP hasta 11/09, stock del 18/09 · se regenera a las 06:00",
            f"Datos al {fecha_c} · {periodo}")))
    pngs = []
    for n, (nombre, contenido) in enumerate(laminas, start=1):
        h = salida / f"lamina_{n}_{nombre}.html"
        h.write_text(contenido, encoding="utf-8")
        p = salida / f"comite_actualizacion_{n}.png"
        render_png(h, p)
        pngs.append(p)
        print(f"  {p.relative_to(ROOT)}")
    pdf = salida / f"Comité {fecha} - Buyer Persona 360.pdf"
    render_pdf([c for _, c in laminas], pdf)
    print(f"  {pdf.relative_to(ROOT)}")
    if not a.sin_vault:
        escribir_nota(ROOT / "Buyer Persona" / "Sistema" / f"Comité {fecha}", fecha, pngs, titulos, pdf)


def escribir_nota(carpeta: Path, fecha: str, pngs: list[Path], titulos: list[str], pdf: Path | None = None) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    for viejo in [*carpeta.glob("Lámina *.png"), *carpeta.glob("*.pdf")]:
        viejo.unlink()
    if pdf:
        shutil.copy2(pdf, carpeta / pdf.name)
    L = ["---", "type: presentacion", f"created: {fecha}", "tags: [buyer-persona, comite, presentacion]", "---",
         f"# 🗂️ Comité — actualización {fecha[8:10]}/{fecha[5:7]}",
         "", "> Láminas 1920×1080 para la press de comité (pedido de Valentina: la actualización de las pruebas de Renault y "
             "Mitsubishi, para todas las marcas). Se pegan como imagen en Google Slides. Se regeneran con "
             "`scripts/laminas_comite.py`; fuente HTML en `output/presentacion/comite_" + fecha + "/`.", ""]
    if pdf:
        L += [f"Todas las láminas en un PDF: [[{pdf.name}]]", ""]
    for n, (titulo, p) in enumerate(zip(titulos, pngs), start=1):
        shutil.copy2(p, carpeta / f"Lámina {n}.png")
        L += [f"## {n} · {titulo}", f"![[Lámina {n}.png]]", ""]
    L += ["Relacionado: [[🗂️ Comité 2026-09-21 — Buyer Persona]] · [[🚀 Pauta Renault IA — Koleos + Master 2026-09]] · "
          "[[🚀 Pauta Mitsubishi IA — L200 + Montero 2026-09]] · [[🎬 Materiales Meta — todas las marcas]]", ""]
    (carpeta / f"🗂️ Comité {fecha} — Actualización.md").write_text("\n".join(L), encoding="utf-8")
    print(f"  nota: {carpeta.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
