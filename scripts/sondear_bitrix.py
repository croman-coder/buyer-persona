"""Sondea la estructura del CRM de Bitrix24 para diseñar el conector.

Lee BITRIX_WEBHOOK_URL del .env y NUNCA la imprime (la URL contiene el
token). Imprime solo estructura y conteos: embudos, etapas, fuentes,
campos, y presencia de marcas en los deals — ningún dato personal.
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
BASE = os.environ.get("BITRIX_WEBHOOK_URL", "").strip().rstrip("/")

if not BASE:
    sys.exit("BITRIX_WEBHOOK_URL vacío en .env")

MARCAS = ["renault", "jac", "jetour", "mitsubishi", "gwm", "zeekr", "soueast",
          "leapmotor", "renew", "xpeng", "karry", "jmev"]


def llamar(metodo: str, params: dict | None = None) -> dict:
    r = requests.post(f"{BASE}/{metodo}.json", json=params or {}, timeout=30)
    if r.status_code != 200:
        # el cuerpo de error de Bitrix no incluye el token
        print(f"  [{metodo}] HTTP {r.status_code}: {r.text[:150]}")
        return {}
    return r.json()


def sin_acentos(v: str) -> str:
    b = unicodedata.normalize("NFKD", v.lower())
    return "".join(c for c in b if not unicodedata.combining(c))


# 1) ¿Responde?
perfil = llamar("profile")
if not perfil.get("result"):
    sys.exit("El webhook no responde o no tiene permisos (revisá el scope crm).")
print("✓ Webhook responde")

# 2) Embudos de deals
cats = llamar("crm.dealcategory.list", {"select": ["ID", "NAME"]})
embudos = cats.get("result", [])
print(f"\n=== Embudos de venta ({len(embudos)}) ===")
for e in embudos:
    print(f"  [{e['ID']}] {e['NAME']}")

# 3) Etapas por embudo (solo del default y primeros 2 extra para no inundar)
print("\n=== Etapas (embudo default) ===")
etapas = llamar("crm.status.list", {"filter": {"ENTITY_ID": "DEAL_STAGE"}})
for s in etapas.get("result", [])[:15]:
    print(f"  {s['STATUS_ID']}: {s['NAME']}")

# 4) Fuentes configuradas
print("\n=== Fuentes (SOURCE) ===")
fuentes = llamar("crm.status.list", {"filter": {"ENTITY_ID": "SOURCE"}})
for s in fuentes.get("result", []):
    print(f"  {s['STATUS_ID']}: {s['NAME']}")

# 5) Campos del deal: estándar UTM + custom UF_
campos = llamar("crm.deal.fields").get("result", {})
utm = [k for k in campos if k.startswith("UTM_")]
uf = {k: (campos[k].get("formLabel") or campos[k].get("title") or k) for k in campos if k.startswith("UF_")}
print(f"\n=== Campos del deal: {len(campos)} totales ===")
print(f"  UTM estándar: {utm}")
print(f"  Custom UF ({len(uf)}):")
for k, nombre in list(uf.items())[:25]:
    print(f"    {k}: {nombre}")

# 6) ¿Existen leads como entidad (modo CRM clásico)?
leads = llamar("crm.lead.list", {"select": ["ID"], "start": 0})
total_leads = leads.get("total", 0)
print(f"\n=== Leads (entidad) ===\n  total: {total_leads}")

# 7) Conteo de deals y presencia de marca en títulos/embudos (solo conteos)
deals = llamar("crm.deal.list", {"select": ["ID"], "start": 0})
print(f"\n=== Deals ===\n  total: {deals.get('total', 0)}")

muestra = llamar("crm.deal.list", {
    "select": ["ID", "TITLE", "CATEGORY_ID", "STAGE_ID", "SOURCE_ID", "UTM_SOURCE", "UTM_CAMPAIGN", "OPPORTUNITY", "DATE_CREATE"],
    "order": {"ID": "DESC"},
})
filas = muestra.get("result", [])
marcas_en_titulo = Counter()
con_utm = 0
con_monto = 0
por_embudo = Counter()
for d in filas:
    t = sin_acentos(str(d.get("TITLE", "")))
    for m in MARCAS:
        if m in t:
            marcas_en_titulo[m] += 1
            break
    if d.get("UTM_SOURCE"):
        con_utm += 1
    if float(d.get("OPPORTUNITY") or 0) > 0:
        con_monto += 1
    por_embudo[str(d.get("CATEGORY_ID"))] += 1

n = len(filas)
print(f"\n=== Análisis de los últimos {n} deals (solo conteos) ===")
print(f"  con marca reconocible en el título: {sum(marcas_en_titulo.values())}/{n} → {dict(marcas_en_titulo.most_common(6))}")
print(f"  con UTM_SOURCE cargado: {con_utm}/{n}")
print(f"  con monto (OPPORTUNITY) cargado: {con_monto}/{n}")
print(f"  por embudo (CATEGORY_ID): {dict(por_embudo)}")
