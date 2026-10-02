"""
Conector de Bitrix24 (CRM) — solo agregados, sin datos personales.

Trae leads y deals de la ventana configurada y los agrega por marca:
leads por canal (Meta madre / Meta asesores / Google / otros), convertidos,
deals ganados/perdidos/en proceso y monto ganado. Nunca lee nombres,
teléfonos ni documentos: los ``select`` piden solo campos de estado.

La marca del lead sale del NOMBRE de su fuente en Bitrix (ya vienen
etiquetadas por marca); la del deal, de su embudo (``JAC Ventas``...).
Misma lógica que ``scripts/tablero_bitrix.py``.
"""

from __future__ import annotations

import logging
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

MARCAS = ["renault", "jac", "jetour", "mitsubishi", "gwm", "zeekr", "soueast",
          "leapmotor", "renew", "xpeng", "karry", "jmev"]


def _sin_acentos(v: str) -> str:
    b = unicodedata.normalize("NFKD", str(v).lower())
    return "".join(c for c in b if not unicodedata.combining(c))


def marca_de_texto(texto: str) -> str | None:
    t = _sin_acentos(texto)
    for m in MARCAS:
        if m in t:
            return m.upper() if m in ("jac", "gwm", "jmev") else m.capitalize()
    return None


def canal_de_fuente(nombre_fuente: str) -> str:
    t = _sin_acentos(nombre_fuente)
    if "meta ads" in t or "facebook" in t or "instagram" in t:
        if "asesor" in t:
            return "Meta asesores"
        if "madre" in t:
            return "Meta madre"
        return "Meta otros"
    if "google" in t:
        return "Google Ads"
    return "Otros canales"


class BitrixConnector:
    """Agregados de leads y deals de Bitrix24 por marca."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.base = str(config.get("webhook_url", "")).strip().rstrip("/")
        self.days_back = int(config.get("days_back", 90))
        if not self.base:
            raise ValueError("Bitrix: webhook_url vacío (BITRIX_WEBHOOK_URL en .env)")

    # ------------------------------------------------------------------
    _MAX_RETRIES = 5

    def _call(self, method: str, params: dict | None = None) -> dict:
        """POST al webhook con reintento ante 5xx / 429 / QUERY_LIMIT_EXCEEDED."""
        backoff = 5
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                r = requests.post(f"{self.base}/{method}.json", json=params or {}, timeout=45)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < self._MAX_RETRIES:
                    logger.warning("Bitrix %s: HTTP %s, reintento %d/%d en %ds",
                                   method, r.status_code, attempt, self._MAX_RETRIES, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                r.raise_for_status()
                body = r.json()
                if "error" in body:
                    if body["error"] == "QUERY_LIMIT_EXCEEDED" and attempt < self._MAX_RETRIES:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    raise RuntimeError(f"{method}: {body.get('error_description', body['error'])}")
                return body
            except requests.exceptions.RequestException as exc:
                if attempt < self._MAX_RETRIES:
                    logger.warning("Bitrix %s: %s, reintento %d/%d en %ds",
                                   method, exc, attempt, self._MAX_RETRIES, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        return {}

    def _list_all(self, method: str, params: dict) -> list[dict]:
        """Paginación rápida de Bitrix: start=-1 + filtro >ID incremental."""
        rows: list[dict] = []
        last_id = 0
        base_filter = dict(params.get("filter", {}))
        while True:
            p = {
                **params,
                "order": {"ID": "ASC"},
                "filter": {**base_filter, ">ID": last_id},
                "start": -1,
            }
            batch = self._call(method, p).get("result", [])
            if not batch:
                break
            rows.extend(batch)
            last_id = int(batch[-1]["ID"])
            if len(batch) < 50:
                break
            time.sleep(0.25)  # Bitrix limita a ~2 req/s por webhook
        return rows

    # ------------------------------------------------------------------
    def fetch_all(self) -> dict[str, Any]:
        since = (datetime.now(timezone.utc) - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        logger.info("Bitrix: leyendo leads y deals desde %s (solo agregados)", since)

        sources = {s["STATUS_ID"]: s["NAME"] for s in self._call(
            "crm.status.list", {"filter": {"ENTITY_ID": "SOURCE"}}).get("result", [])}
        pipelines = {str(c["ID"]): c["NAME"] for c in self._call(
            "crm.dealcategory.list", {"select": ["ID", "NAME"]}).get("result", [])}

        leads = self._list_all("crm.lead.list", {
            "select": ["ID", "STATUS_ID", "STATUS_SEMANTIC_ID", "SOURCE_ID", "DATE_CREATE"],
            "filter": {">=DATE_CREATE": since},
        })
        deals = self._list_all("crm.deal.list", {
            "select": ["ID", "CATEGORY_ID", "STAGE_SEMANTIC_ID", "OPPORTUNITY", "DATE_CREATE"],
            "filter": {">=DATE_CREATE": since},
        })
        logger.info("Bitrix: %d leads, %d deals en ventana", len(leads), len(deals))

        by_brand: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "leads": 0, "leads_by_channel": Counter(), "converted": 0,
            "deals": 0, "won": 0, "lost": 0, "in_progress": 0, "won_amount": 0.0,
        })

        for l in leads:
            src_name = sources.get(l.get("SOURCE_ID", ""), l.get("SOURCE_ID", "") or "—")
            brand = marca_de_texto(src_name) or "Sin marca"
            b = by_brand[brand]
            b["leads"] += 1
            b["leads_by_channel"][canal_de_fuente(src_name)] += 1
            if l.get("STATUS_SEMANTIC_ID") == "S" or l.get("STATUS_ID") == "CONVERTED":
                b["converted"] += 1

        for d in deals:
            pipeline = pipelines.get(str(d.get("CATEGORY_ID")), "General")
            brand = marca_de_texto(pipeline)
            if not brand:
                continue  # embudos no de venta (Cobranza, Posventa...)
            b = by_brand[brand]
            b["deals"] += 1
            sem = d.get("STAGE_SEMANTIC_ID")
            if sem == "S":
                b["won"] += 1
                b["won_amount"] += float(d.get("OPPORTUNITY") or 0)
            elif sem == "F":
                b["lost"] += 1
            else:
                b["in_progress"] += 1

        out: dict[str, dict[str, Any]] = {}
        for brand, b in by_brand.items():
            out[brand] = {
                "leads": b["leads"],
                "leads_by_channel": dict(b["leads_by_channel"].most_common()),
                "converted": b["converted"],
                "conversion_rate": round(b["converted"] / b["leads"] * 100, 1) if b["leads"] else 0.0,
                "deals": b["deals"],
                "won": b["won"],
                "lost": b["lost"],
                "in_progress": b["in_progress"],
                "win_rate": round(b["won"] / (b["won"] + b["lost"]) * 100, 1) if (b["won"] + b["lost"]) else 0.0,
                "won_amount": round(b["won_amount"], 2),
                "avg_ticket_won": round(b["won_amount"] / b["won"], 2) if b["won"] else 0.0,
            }

        return {
            "source": "bitrix",
            "date_range": {"start": since, "end": datetime.now().strftime("%Y-%m-%d")},
            "total_leads": len(leads),
            "total_deals": len(deals),
            "by_brand": out,
        }
