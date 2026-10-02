"""
Conector de Datacar (datacarpy.com) — precios de lista del mercado 0km en Paraguay.

El sitio publica su catálogo desde Firestore con lectura pública (proyecto
``datacar2-0``). Se leen tres colecciones y se cruzan:

    brands (48)  →  models (294)  →  versions (796: precio USD, specs, concesionaria)

Uso: inteligencia competitiva **interna**. Por ley paraguaya no se puede hacer
publicidad comparativa nombrando marcas/modelos de la competencia: nada de
esto va a un copy público.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

PROJECT = "datacar2-0"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

# Cómo nombra Datacar a nuestras marcas -> etiqueta del portfolio
OUR_BRANDS = {
    "RENAULT": "Renault", "JETOUR": "Jetour", "GWM": "GWM", "JAC": "JAC",
    "MITSUBISHI": "Mitsubishi", "ZEEKR": "Zeekr", "LEAPMOTOR": "Leapmotor",
    "JMEV": "JMEV", "SOUEAST": "Soueast",
}

# Grupos concesionarios (competencia directa por casa)
DEALER_GROUP = {
    "garden": "Grupo Garden", "diesa": "Diesa", "toyotoshi": "Toyotoshi",
    "automaq": "Automaq", "nipon": "Nipon", "santa rosa": "Santa Rosa",
    "automotor": "Automotor", "tape ruvicha": "Tape Ruvicha", "rieder": "Rieder",
    "condor": "Condor", "cencar": "Cencar", "chacomer": "Chacomer",
}


def _val(x: dict) -> Any:
    """Convierte un valor tipado de Firestore REST a Python."""
    if "mapValue" in x:
        return {k: _val(v) for k, v in x["mapValue"].get("fields", {}).items()}
    if "arrayValue" in x:
        return [_val(i) for i in x["arrayValue"].get("values", [])]
    if "integerValue" in x:
        return int(x["integerValue"])
    if "doubleValue" in x:
        return float(x["doubleValue"])
    if "booleanValue" in x:
        return bool(x["booleanValue"])
    if "nullValue" in x:
        return None
    return next(iter(x.values()), None)


def _sin_acentos(s: str) -> str:
    b = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in b if not unicodedata.combining(c))


class DatacarConnector:
    """Descarga y cruza el catálogo público de Datacar."""

    def __init__(self, config: dict[str, Any]):
        self.api_key = str(config.get("api_key", "")).strip()
        if not self.api_key:
            raise ValueError("Datacar: api_key vacío (DATACAR_API_KEY en .env)")
        self.timeout = int(config.get("timeout", 30))

    def _collection(self, name: str) -> dict[str, dict]:
        docs: dict[str, dict] = {}
        token = ""
        while True:
            r = requests.get(
                f"{BASE}/{name}",
                params={"key": self.api_key, "pageSize": 300, "pageToken": token},
                timeout=self.timeout,
            )
            r.raise_for_status()
            body = r.json()
            for d in body.get("documents", []):
                doc_id = d["name"].split("/")[-1]
                docs[doc_id] = {k: _val(v) for k, v in d.get("fields", {}).items()}
            token = body.get("nextPageToken", "")
            if not token:
                break
        return docs

    def fetch_all(self) -> dict[str, Any]:
        brands = self._collection("brands")
        models = self._collection("models")
        versions = self._collection("versions")
        logger.info("Datacar: %d marcas, %d modelos, %d versiones", len(brands), len(models), len(versions))

        rows: list[dict[str, Any]] = []
        for vid, v in versions.items():
            m = models.get(str(v.get("modelId", "")), {})
            b = brands.get(str(m.get("brandId", "")), {})
            brand_name = str(b.get("name", m.get("brandId", ""))).strip()
            specs = v.get("specs") or {}
            price = v.get("price")
            try:
                price = int(float(price)) if price not in (None, "") else None
            except (TypeError, ValueError):
                price = None
            dealer = str(v.get("concesionaria", "")).strip()
            dealer_group = next(
                (g for k, g in DEALER_GROUP.items() if k in _sin_acentos(dealer)), dealer or "—"
            )
            rows.append({
                "version_id": vid,
                "brand": brand_name,
                "brand_upper": brand_name.upper(),
                "our_brand": OUR_BRANDS.get(brand_name.upper()),
                "model": str(m.get("name", "")).strip(),
                "model_id": str(v.get("modelId", "")),
                "version": str(v.get("name", "")).strip(),
                "price_usd": price,
                "promo": v.get("promocion") or "",
                "body": str(m.get("tipo_carroceria", "")).strip().upper(),
                "subsegment": str(m.get("subsegmento", "")).strip().upper(),
                "fuel": str(specs.get("combustible", "")).strip().upper(),
                "origin": str(m.get("origen", b.get("origen_marca", ""))).strip(),
                "dealer": dealer,
                "dealer_group": dealer_group,
                "motor": str(specs.get("motor", "")).strip(),
                "transmission": str(specs.get("transmision", "")).strip(),
                "traction": str(specs.get("traccion", "")).strip(),
                "airbags": str(specs.get("airbags", "")).strip(),
                "warranty": str(specs.get("garantia", "")).strip(),
                "seats": str(specs.get("plazas", "")).strip(),
                "url": str(v.get("url_auto", "")).strip(),
                "updated_at": str(v.get("updatedAt", ""))[:10],
            })

        rows = [r for r in rows if r["price_usd"]]
        rows.sort(key=lambda r: (r["subsegment"], r["price_usd"]))
        return {
            "source": "datacar",
            "fetched_at": datetime.now().strftime("%Y-%m-%d"),
            "counts": {"brands": len(brands), "models": len(models), "versions": len(rows)},
            "versions": rows,
        }
