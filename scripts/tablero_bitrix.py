"""Tablero CRM: agrega leads y deals de Bitrix24 y escribe la nota al vault.

Lee BITRIX_WEBHOOK_URL del .env y NUNCA la imprime. Solo agregados:
conteos por fuente/estado/embudo y montos — ningún dato personal de leads
(nombres, teléfonos, cédulas y documentos quedan sin leer).

Uso:
    venv/bin/python scripts/tablero_bitrix.py
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
VAULT = RAIZ / "Buyer Persona"
DIAS = 90

load_dotenv(RAIZ / ".env")
BASE = os.environ.get("BITRIX_WEBHOOK_URL", "").strip().rstrip("/")
if not BASE:
    sys.exit("BITRIX_WEBHOOK_URL vacío en .env")

MARCAS = ["renault", "jac", "jetour", "mitsubishi", "gwm", "zeekr", "soueast",
          "leapmotor", "renew", "xpeng", "karry", "jmev"]


# Red y cuota de Bitrix: bitrix_cliente (reintentos en 503/red, espera al reset en 429
# OPERATION_TIME_LIMIT, pausa entre páginas). Antes vivía acá sin reintentos y un solo 503 a
# mitad de las ~377 páginas de leads tiraba el tablero entero (lunes 7 y 14/9/2026).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bitrix_cliente import llamar as _llamar, listar_todo as _listar_todo   # noqa: E402


def llamar(metodo: str, params: dict | None = None) -> dict:
    return _llamar(BASE, metodo, params)


def listar_todo(metodo: str, params: dict) -> list[dict]:
    return _listar_todo(BASE, metodo, params)


def sin_acentos(v: str) -> str:
    b = unicodedata.normalize("NFKD", str(v).lower())
    return "".join(c for c in b if not unicodedata.combining(c))


def marca_de_texto(texto: str) -> str | None:
    t = sin_acentos(texto)
    for m in MARCAS:
        if m in t:
            return m.upper() if m in ("jac", "gwm", "jmev") else m.capitalize()
    return None


def canal_de_fuente(nombre_fuente: str) -> str:
    t = sin_acentos(nombre_fuente)
    if "meta ads" in t or "facebook" in t or "instagram" in t:
        if "asesor" in t:
            return "Meta asesores"
        if "madre" in t:
            return "Meta madre"
        return "Meta otros"
    if "google" in t:
        return "Google Ads"
    return "Otros canales"


desde = (datetime.now(timezone.utc) - timedelta(days=DIAS)).strftime("%Y-%m-%d")
hoy = date.today().isoformat()

# ---------------- catálogos ----------------
fuentes = {s["STATUS_ID"]: s["NAME"] for s in llamar(
    "crm.status.list", {"filter": {"ENTITY_ID": "SOURCE"}}).get("result", [])}
embudos = {str(c["ID"]): c["NAME"] for c in llamar(
    "crm.dealcategory.list", {"select": ["ID", "NAME"]}).get("result", [])}
embudos["0"] = "General"

# ---------------- leads (90 días, solo campos agregables) ----------------
print(f"Trayendo leads desde {desde}...")
leads = listar_todo("crm.lead.list", {
    "select": ["ID", "STATUS_ID", "STATUS_SEMANTIC_ID", "SOURCE_ID", "DATE_CREATE"],
    "filter": {">=DATE_CREATE": desde},
})
print(f"  {len(leads)} leads en ventana")

por_marca_canal: dict[str, Counter] = defaultdict(Counter)
convertidos: dict[str, Counter] = defaultdict(Counter)
canal_global = Counter()

for l in leads:
    fuente = fuentes.get(l.get("SOURCE_ID", ""), l.get("SOURCE_ID", "") or "—")
    canal = canal_de_fuente(fuente)
    marca = marca_de_texto(fuente) or "Sin marca"
    canal_global[canal] += 1
    por_marca_canal[marca][canal] += 1
    if l.get("STATUS_SEMANTIC_ID") == "S" or l.get("STATUS_ID") == "CONVERTED":
        convertidos[marca][canal] += 1

# ---------------- deals (todos; son pocos) ----------------
print("Trayendo deals...")
deals = listar_todo("crm.deal.list", {
    "select": ["ID", "CATEGORY_ID", "STAGE_SEMANTIC_ID", "OPPORTUNITY", "DATE_CREATE"],
    "filter": {">=DATE_CREATE": desde},
})
print(f"  {len(deals)} deals en ventana")

deal_marca: dict[str, dict] = defaultdict(lambda: {"total": 0, "won": 0, "lose": 0, "proceso": 0, "monto_won": 0.0})
for d in deals:
    nombre_embudo = embudos.get(str(d.get("CATEGORY_ID")), "General")
    marca = marca_de_texto(nombre_embudo) or nombre_embudo
    m = deal_marca[marca]
    m["total"] += 1
    sem = d.get("STAGE_SEMANTIC_ID")
    if sem == "S":
        m["won"] += 1
        m["monto_won"] += float(d.get("OPPORTUNITY") or 0)
    elif sem == "F":
        m["lose"] += 1
    else:
        m["proceso"] += 1


def pct(n, base):
    return f"{100 * n / base:.1f}%" if base else "—"


def fmt_usd(v):
    return f"${v:,.0f}"


# ---------------- nota ----------------
L = []
L.append("---")
L.append("tipo: embudo-crm")
L.append("fuente: Bitrix24")
L.append(f"periodo_dias: {DIAS}")
L.append(f"leads_ventana: {len(leads)}")
L.append(f"deals_ventana: {len(deals)}")
L.append(f"actualizado: {hoy}")
L.append("tags: [bitrix, crm, embudo]")
L.append("---")
L.append("")
L.append("# Embudo CRM (Bitrix) — últimos 90 días")
L.append("")
L.append(f"**{len(leads):,} leads** y **{len(deals)} deals** creados en la ventana. "
         "Solo agregados: ningún dato personal sale del CRM.")
L.append("")
L.append("Relacionado: [[Campañas Meta - ultimos 90 dias|Campañas]] · [[Scorecard Asesores - ultimos 90 dias|Asesores]] · [[Buyer Persona Real - Meta 90 dias|Buyer Persona]]")
L.append("")

L.append("## Leads por canal (global)")
L.append("")
L.append("| Canal | Leads | % |")
L.append("| --- | --: | --: |")
for canal, n in canal_global.most_common():
    L.append(f"| {canal} | {n:,} | {pct(n, len(leads))} |")
L.append("")

L.append("## Leads Meta por marca: madre vs asesores")
L.append("")
L.append("| Marca | Meta madre | Meta asesores | Convertidos madre | Convertidos asesores |")
L.append("| --- | --: | --: | --: | --: |")
filas_m = [(m, c) for m, c in por_marca_canal.items() if c.get("Meta madre") or c.get("Meta asesores")]
for marca, c in sorted(filas_m, key=lambda x: -(x[1].get("Meta madre", 0) + x[1].get("Meta asesores", 0))):
    conv = convertidos.get(marca, Counter())
    madre, ases = c.get("Meta madre", 0), c.get("Meta asesores", 0)
    L.append(f"| {marca} | {madre:,} | {ases:,} | "
             f"{conv.get('Meta madre', 0):,} ({pct(conv.get('Meta madre', 0), madre)}) | "
             f"{conv.get('Meta asesores', 0):,} ({pct(conv.get('Meta asesores', 0), ases)}) |")
L.append("")

L.append("## Deals por marca (embudos de venta)")
L.append("")
L.append("| Marca | Deals | Ganados | Perdidos | En proceso | Monto ganado | Ticket medio |")
L.append("| --- | --: | --: | --: | --: | --: | --: |")
for marca, m in sorted(deal_marca.items(), key=lambda x: -x[1]["total"]):
    ticket = fmt_usd(m["monto_won"] / m["won"]) if m["won"] else "—"
    L.append(f"| {marca} | {m['total']} | {m['won']} | {m['lose']} | {m['proceso']} | {fmt_usd(m['monto_won'])} | {ticket} |")
L.append("")

L.append("## Notas sobre los datos")
L.append("")
L.append("- *Convertido* = lead con estado semántico de éxito en Bitrix (pasó a deal/contacto).")
L.append("- La marca del lead sale del NOMBRE de su fuente (las fuentes ya vienen etiquetadas por marca y madre/asesores).")
L.append("- La marca del deal sale de su embudo (JAC Ventas, GWM Ventas, ...). Embudos no de venta (Cobranza, Posventa, Marketing) aparecen con su nombre.")
L.append(f"- Ventana: creados desde {desde}. Un deal ganado hoy puede venir de un lead anterior a la ventana.")
L.append("")

destino = VAULT / "CRM"
destino.mkdir(parents=True, exist_ok=True)
(destino / "Embudo Bitrix - ultimos 90 dias.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"\nNota escrita: CRM/Embudo Bitrix - ultimos 90 dias.md")
print(f"  canales: {dict(canal_global.most_common(4))}")
