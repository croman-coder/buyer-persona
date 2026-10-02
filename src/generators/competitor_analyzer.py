"""
Cruce de precios Datacar contra nuestro catálogo.

Para cada modelo del portfolio ubica sus versiones en Datacar (precio de
lista real publicado por la concesionaria) y arma la competencia directa:
versiones de otras marcas en el mismo subsegmento (B-SUV, D-PICKUP...) dentro
de una banda de precio. Solo uso interno — ver nota legal en el conector.
"""

from __future__ import annotations

import json
import logging
import re
import statistics
from pathlib import Path
from typing import Any

from src.catalog.models_py import MODEL_CATALOG

logger = logging.getLogger(__name__)


def match_our_model(row: dict[str, Any]) -> str | None:
    """Nombre de catálogo para una fila de Datacar de una marca nuestra."""
    brand = row.get("our_brand")
    if not brand:
        return None
    text = f"{brand} {row.get('model', '')} {row.get('version', '')}".lower()
    for name, pat in MODEL_CATALOG.get(brand, {}).items():
        if re.search(pat, f"{brand} {row.get('model', '')}".lower(), re.I):
            return name
    for name, pat in MODEL_CATALOG.get(brand, {}).items():
        if re.search(pat, text, re.I):
            return name
    return f"{brand} {str(row.get('model', '')).strip().title()}"


def analyze(rows: list[dict[str, Any]], price_band: float = 0.25) -> dict[str, Any]:
    """
    Returns:
        {
          "by_model": { "Renault Kwid": {subsegment, our_versions:[...], price_min, price_max,
                                          price_median, competitors:[...] } },
          "by_subsegment": { "B-SUV": [rows ordenadas por precio] },
        }
    """
    by_sub: dict[str, list[dict]] = {}
    for r in rows:
        by_sub.setdefault(r.get("subsegment") or "SIN SEGMENTO", []).append(r)
    for lst in by_sub.values():
        lst.sort(key=lambda r: r["price_usd"])

    ours: dict[str, list[dict]] = {}
    for r in rows:
        name = match_our_model(r)
        if name:
            ours.setdefault(name, []).append(r)

    by_model: dict[str, dict[str, Any]] = {}
    for name, versions in ours.items():
        prices = [v["price_usd"] for v in versions]
        median = statistics.median(prices)
        sub = versions[0].get("subsegment") or "SIN SEGMENTO"
        lo, hi = median * (1 - price_band), median * (1 + price_band)
        brand = versions[0]["our_brand"]
        in_band = [
            r for r in by_sub.get(sub, [])
            if r.get("our_brand") != brand and lo <= r["price_usd"] <= hi
        ]

        def _closest_per_model(rows_: list[dict]) -> list[dict]:
            # una fila por modelo: la versión más cercana en precio (copia, no mutar la original)
            best: dict[str, dict] = {}
            for c in rows_:
                key = f"{c['brand']} {c['model']}"
                if key not in best or abs(c["price_usd"] - median) < abs(best[key]["price_usd"] - median):
                    best[key] = dict(c)
            out = sorted(best.values(), key=lambda r: abs(r["price_usd"] - median))
            for c in out:
                c["delta_usd"] = c["price_usd"] - median
                c["delta_pct"] = round(c["delta_usd"] / median * 100, 1)
            return out

        external = _closest_per_model([r for r in in_band if not r.get("our_brand")])
        internal = _closest_per_model([r for r in in_band if r.get("our_brand")])

        by_model[name] = {
            "brand": brand,
            "subsegment": sub,
            "our_versions": sorted(versions, key=lambda v: v["price_usd"]),
            "price_min": min(prices),
            "price_max": max(prices),
            "price_median": median,
            "rank_in_subsegment": _rank(median, by_sub.get(sub, [])),
            "competitors": external[:8],
            "internal_overlap": internal[:5],
        }

    return {"by_model": by_model, "by_subsegment": by_sub}


def _rank(price: float, rows: list[dict]) -> str:
    """Posición de precio dentro del subsegmento: 'más barato', 'medio', 'más caro'."""
    if not rows:
        return "—"
    prices = sorted(r["price_usd"] for r in rows)
    below = sum(1 for p in prices if p < price)
    pct = below / len(prices)
    if pct < 0.33:
        return "tercio más barato"
    if pct < 0.66:
        return "tercio medio"
    return "tercio más caro"


def price_changes(current: list[dict], previous_path: Path) -> list[dict]:
    """Compara contra el snapshot anterior: versiones que cambiaron de precio."""
    if not previous_path.exists():
        return []
    try:
        prev = {r["version_id"]: r for r in json.load(open(previous_path, encoding="utf-8")).get("versions", [])}
    except Exception:
        return []
    changes = []
    for r in current:
        p = prev.get(r["version_id"])
        if p and p.get("price_usd") and p["price_usd"] != r["price_usd"]:
            changes.append({
                **r,
                "old_price": p["price_usd"],
                "delta_usd": r["price_usd"] - p["price_usd"],
                "delta_pct": round((r["price_usd"] - p["price_usd"]) / p["price_usd"] * 100, 1),
            })
    changes.sort(key=lambda c: abs(c["delta_pct"]), reverse=True)
    return changes
