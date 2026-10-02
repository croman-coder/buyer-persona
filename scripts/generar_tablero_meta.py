"""Genera las notas de Campañas y Scorecard de Asesores en el vault.

Fuente: el data_sources_*.json más reciente del pipeline (sin LLM, sin
costo de modelo). Una llamada liviana a la Graph API para resolver los
nombres de las cuentas (no trae datos de personas de leads).

Uso:
    venv/bin/python scripts/generar_tablero_meta.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
VAULT = RAIZ / "Buyer Persona"

# Palabras que identifican marca/sede: si el nombre de la cuenta se compone
# solo de estas, es cuenta oficial; si aparece cualquier otra palabra, es el
# nombre de un asesor.
PALABRAS_MARCA = {
    "renault", "jac", "jetour", "mitsubishi", "gwm", "zeekr", "zeerk",
    "soueast", "leapmotor", "leap", "renew", "xpeng", "karry", "jmev",
    "multimarcas", "santa", "rosa", "paraguay", "institucional", "oficial",
    "usados", "cde", "asu", "motors", "utilitarios",
}


def es_oficial(nombre: str) -> bool:
    palabras = [p for p in re.split(r"[|\-/\s]+", _sin_acentos(nombre).lower()) if p]
    return bool(palabras) and all(p in PALABRAS_MARCA for p in palabras)


def _sin_acentos(v: str) -> str:
    base = unicodedata.normalize("NFKD", v)
    return "".join(c for c in base if not unicodedata.combining(c))


def nombres_de_cuentas(token: str) -> dict[str, str]:
    """act_id -> nombre de cuenta. Una sola llamada paginada."""
    salida: dict[str, str] = {}
    url = "https://graph.facebook.com/v21.0/me/adaccounts"
    params = {"access_token": token, "fields": "name,account_id", "limit": 200}
    while url:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            break
        cuerpo = r.json()
        for c in cuerpo.get("data", []):
            salida[f"act_{c['account_id']}"] = c.get("name", "").strip()
        url = cuerpo.get("paging", {}).get("next")
        params = {}
    return salida


def _num(v, tipo=float):
    try:
        return tipo(v)
    except (TypeError, ValueError):
        return tipo(0)


def leads_de_campania(camp: dict) -> int:
    for a in camp.get("actions", []) or []:
        if a.get("action_type") == "lead":
            return _num(a.get("value"), int)
    return 0


def fmt_usd(v: float) -> str:
    return f"${v:,.0f}"


def fmt_cpl(spend: float, leads: int) -> str:
    return f"${spend / leads:,.2f}" if leads else "—"


def main() -> int:
    load_dotenv(RAIZ / ".env")
    token = os.environ.get("META_ADS_ACCESS_TOKEN", "").strip()

    candidatos = sorted(glob.glob(str(RAIZ / "output/raw/data_sources_*.json")), key=os.path.getmtime)
    if not candidatos:
        print("No hay data_sources_*.json — corré primero el pipeline.", file=sys.stderr)
        return 1
    fuente = candidatos[-1]
    meta = json.load(open(fuente, encoding="utf-8")).get("meta_ads", {})
    campanias = meta.get("campaigns", [])
    cuentas_por_marca = meta.get("accounts", {})
    leads_por_marca = meta.get("leads_by_brand", {})
    rango = meta.get("date_range", {})

    nombres = nombres_de_cuentas(token) if token else {}
    hoy = date.today().isoformat()
    periodo = f"{rango.get('since', '?')} → {rango.get('until', '?')}"

    # ---------------- rollup por marca ----------------
    por_marca: dict[str, dict] = {}
    for c in campanias:
        marca = c.get("account", "—")
        m = por_marca.setdefault(marca, {"spend": 0.0, "impr": 0, "clicks": 0, "leads": 0, "camps": []})
        spend = _num(c.get("spend"))
        leads = leads_de_campania(c)
        m["spend"] += spend
        m["impr"] += _num(c.get("impressions"), int)
        m["clicks"] += _num(c.get("clicks"), int)
        m["leads"] += leads
        m["camps"].append((c.get("campaign_name", "—"), spend, leads))

    total_spend = sum(m["spend"] for m in por_marca.values())
    total_leads_camp = sum(m["leads"] for m in por_marca.values())

    # ---------------- nota de campañas ----------------
    L = []
    L.append("---")
    L.append("tipo: campanias")
    L.append("fuente: Meta Ads (pipeline)")
    L.append(f"periodo: {periodo}")
    L.append(f"actualizado: {hoy}")
    L.append("tags: [meta-ads, campanias]")
    L.append("---")
    L.append("")
    L.append("# Campañas Meta — últimos 90 días")
    L.append("")
    L.append(f"**{len(campanias)} campañas** en el período {periodo}. Inversión total: "
             f"**{fmt_usd(total_spend)}** · Leads atribuidos a campañas: **{total_leads_camp:,}** · "
             f"CPL global: **{fmt_cpl(total_spend, total_leads_camp)}**.")
    L.append("")
    L.append("Relacionado: [[Buyer Persona Real - Meta 90 dias]] · [[Scorecard Asesores - ultimos 90 dias|Scorecard Asesores]] · [[Mapa de cuentas Meta]]")
    L.append("")
    L.append("## Inversión y CPL por marca")
    L.append("")
    L.append("| Marca | Inversión | Leads (campañas) | CPL | CTR medio | Leads (formularios) |")
    L.append("| --- | --: | --: | --: | --: | --: |")
    for marca, m in sorted(por_marca.items(), key=lambda x: -x[1]["spend"]):
        ctr = f"{100 * m['clicks'] / m['impr']:.2f}%" if m["impr"] else "—"
        forms = leads_por_marca.get(marca, {}).get("total_leads", 0)
        L.append(f"| {marca} | {fmt_usd(m['spend'])} | {m['leads']:,} | {fmt_cpl(m['spend'], m['leads'])} | {ctr} | {forms:,} |")
    L.append("")
    L.append("## Top 15 campañas por inversión")
    L.append("")
    L.append("| Campaña | Marca | Inversión | Leads | CPL |")
    L.append("| --- | --- | --: | --: | --: |")
    filas = [
        (nombre, marca, spend, leads)
        for marca, m in por_marca.items()
        for nombre, spend, leads in m["camps"]
    ]
    for nombre, marca, spend, leads in sorted(filas, key=lambda x: -x[2])[:15]:
        L.append(f"| {nombre[:60].replace('|', '/')} | {marca} | {fmt_usd(spend)} | {leads:,} | {fmt_cpl(spend, leads)} |")
    L.append("")
    L.append("## Notas sobre los datos")
    L.append("")
    L.append("- *Leads (campañas)* = acción `lead` reportada por Meta sobre cada campaña (atribución de anuncio).")
    L.append("- *Leads (formularios)* = conteo real de formularios por página de marca. No coinciden exactamente: ventanas de atribución distintas.")
    L.append("- CPL = inversión / leads de campañas del mismo período.")
    L.append("")

    destino_c = VAULT / "Campañas"
    destino_c.mkdir(parents=True, exist_ok=True)
    (destino_c / "Campañas Meta - ultimos 90 dias.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------- scorecard de asesores ----------------
    S = []
    S.append("---")
    S.append("tipo: scorecard-asesores")
    S.append("fuente: Meta Ads (pipeline)")
    S.append(f"periodo: {periodo}")
    S.append(f"actualizado: {hoy}")
    S.append("tags: [meta-ads, asesores]")
    S.append("---")
    S.append("")
    S.append("# Scorecard de Asesores — últimos 90 días")
    S.append("")
    S.append("Inversión y leads por cuenta de asesor, agrupado por marca. Las cuentas oficiales de marca van aparte al final.")
    S.append("")
    S.append("Relacionado: [[Campañas Meta - ultimos 90 dias|Campañas]] · [[Mapa de cuentas Meta]]")
    S.append("")

    oficiales_filas = []
    for marca in sorted(cuentas_por_marca):
        filas_marca = []
        for acc in cuentas_por_marca[marca]:
            acc_id = acc.get("account_id", "")
            nombre = nombres.get(acc_id, acc_id)
            spend = impr = clicks = leads = 0
            for c in acc.get("campaigns", []) or []:
                spend += _num(c.get("spend"))
                impr += _num(c.get("impressions"), int)
                clicks += _num(c.get("clicks"), int)
                leads += leads_de_campania(c)
            fila = (nombre, acc_id, spend, impr, clicks, leads)
            if es_oficial(nombre):
                oficiales_filas.append((marca,) + fila)
            else:
                filas_marca.append(fila)
        if not filas_marca:
            continue
        S.append(f"## {marca}")
        S.append("")
        S.append("| Asesor | Inversión | Impresiones | CTR | Leads | CPL |")
        S.append("| --- | --: | --: | --: | --: | --: |")
        for nombre, acc_id, spend, impr, clicks, leads in sorted(filas_marca, key=lambda x: -x[2]):
            ctr = f"{100 * clicks / impr:.2f}%" if impr else "—"
            S.append(f"| {nombre.replace('|', '/')} | {fmt_usd(spend)} | {impr:,} | {ctr} | {leads:,} | {fmt_cpl(spend, leads)} |")
        S.append("")

    if oficiales_filas:
        S.append("## Cuentas oficiales de marca")
        S.append("")
        S.append("| Cuenta | Marca | Inversión | Impresiones | CTR | Leads | CPL |")
        S.append("| --- | --- | --: | --: | --: | --: | --: |")
        for marca, nombre, acc_id, spend, impr, clicks, leads in sorted(oficiales_filas, key=lambda x: -x[3]):
            ctr = f"{100 * clicks / impr:.2f}%" if impr else "—"
            S.append(f"| {nombre.replace('|', '/')} | {marca} | {fmt_usd(spend)} | {impr:,} | {ctr} | {leads:,} | {fmt_cpl(spend, leads)} |")
        S.append("")

    S.append("## Notas sobre los datos")
    S.append("")
    S.append("- Leads y CPL por asesor salen de las acciones `lead` de las campañas de SU cuenta (atribución de Meta).")
    S.append("- Un asesor sin campañas con leads en el período muestra 0 — no significa que no venda, sino que no corrió campañas de leads.")
    if not nombres:
        S.append("- ⚠️ Sin token de Meta al generar: se muestran IDs de cuenta en vez de nombres.")
    S.append("")

    destino_a = VAULT / "Asesores"
    destino_a.mkdir(parents=True, exist_ok=True)
    (destino_a / "Scorecard Asesores - ultimos 90 dias.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    print(f"Campañas: {len(campanias)} · inversión {fmt_usd(total_spend)} · CPL global {fmt_cpl(total_spend, total_leads_camp)}")
    print(f"Notas escritas en {destino_c.name}/ y {destino_a.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
