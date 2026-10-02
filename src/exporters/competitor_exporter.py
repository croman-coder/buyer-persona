"""
Nota de Obsidian con los precios de lista del mercado 0km (Datacar).

Genera ``Competencia/💰 Precios Mercado 0km (Datacar).md``: nuestros modelos
contra su competencia directa, el mercado completo por subsegmento y los
cambios de precio desde el snapshot anterior. Uso interno.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

NOTE_NAME = "💰 Precios Mercado 0km (Datacar).md"


def _usd(v: float | int | None) -> str:
    return f"{v:,.0f}" if v else "—"


def export(analysis: dict[str, Any], data: dict[str, Any], changes: list[dict], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / NOTE_NAME
    by_model = analysis["by_model"]
    by_sub = analysis["by_subsegment"]
    counts = data.get("counts", {})

    L: list[str] = [
        "---",
        "tipo: precios-competencia",
        f"fuente: datacarpy.com (Firestore público)",
        f"actualizado: {data.get('fetched_at', datetime.now().strftime('%Y-%m-%d'))}",
        f"versiones: {counts.get('versions', 0)}",
        "tags:",
        "  - competencia",
        "  - precios",
        "  - uso-interno",
        "---",
        "",
        "# 💰 Precios Mercado 0km — Datacar",
        "",
        f"> Precios de lista **USD** publicados por cada concesionaria en [datacarpy.com](https://www.datacarpy.com/catalogo). "
        f"{counts.get('brands', 0)} marcas · {counts.get('models', 0)} modelos · {counts.get('versions', 0)} versiones con precio. "
        f"Se actualiza con el pipeline diario.",
        "",
        "> [!danger] Solo uso interno",
        "> Por ley paraguaya no se puede nombrar marcas ni modelos de la competencia en publicidad. "
        "Esto sirve para fijar precio, argumentar en el salón y decidir pauta — nunca para un copy público.",
        "",
        "Relacionado: [[⚔️ Benchmark Competitivo]] · [[⚔️ Battle Cards Modelo vs Modelo]] · [[Buyer Personas MOC]]",
        "",
    ]

    # --- 1. Nuestros modelos vs competencia directa ---
    L += ["## 1. Nuestros modelos vs competencia directa", "",
          "Competencia directa = mismo subsegmento y precio dentro de ±25% de nuestra mediana. "
          "**Δ** es cuánto más caro (+) o más barato (−) es el competidor respecto a nosotros.", ""]

    by_brand: dict[str, list[str]] = {}
    for name, m in by_model.items():
        by_brand.setdefault(m["brand"], []).append(name)

    for brand in sorted(by_brand):
        L.append(f"### {brand}")
        L.append("")
        for name in sorted(by_brand[brand], key=lambda n: by_model[n]["price_median"]):
            m = by_model[name]
            ours = " · ".join(f"{v['version']} {_usd(v['price_usd'])}" for v in m["our_versions"][:4])
            L.append(f"#### {name} — {m['subsegment']} · USD {_usd(m['price_min'])}"
                     + (f"–{_usd(m['price_max'])}" if m['price_max'] != m['price_min'] else "")
                     + f" · {m['rank_in_subsegment']}")
            L.append(f"Nuestras versiones: {ours}")
            L.append("")
            if m["competitors"]:
                L.append("| Competidor | Versión | Precio | Δ | Combustible | Casa |")
                L.append("|---|---|--:|--:|---|---|")
                for c in m["competitors"]:
                    L.append(f"| **{c['brand']} {c['model']}** | {c['version']} | {_usd(c['price_usd'])} "
                             f"| {c['delta_pct']:+.1f}% | {c['fuel'] or '—'} | {c['dealer_group']} |")
            else:
                L.append("_Sin competidores externos en la banda de precio._")
            if m["internal_overlap"]:
                L.append("")
                L.append("Solapamiento interno (mismas casa y banda): "
                         + ", ".join(f"{c['brand']} {c['model']} {_usd(c['price_usd'])} ({c['delta_pct']:+.0f}%)"
                                     for c in m["internal_overlap"]))
            L.append("")

    # --- 2. Cambios de precio ---
    L += ["## 2. Cambios de precio desde el snapshot anterior", ""]
    if changes:
        L.append("| Marca | Modelo | Versión | Antes | Ahora | Δ | Casa |")
        L.append("|---|---|---|--:|--:|--:|---|")
        for c in changes[:40]:
            L.append(f"| {c['brand']} | {c['model']} | {c['version']} | {_usd(c['old_price'])} "
                     f"| {_usd(c['price_usd'])} | {c['delta_pct']:+.1f}% | {c['dealer_group']} |")
    else:
        L.append("_Sin cambios (o primer snapshot)._")
    L.append("")

    # --- 3. Mercado completo por subsegmento ---
    L += ["## 3. Mercado completo por subsegmento", "",
          "Ordenado por precio. Nuestras marcas en **negrita**.", ""]
    for sub in sorted(by_sub, key=lambda s: (s == "SIN SEGMENTO", s)):
        rows = by_sub[sub]
        L.append(f"### {sub} ({len(rows)} versiones)")
        L.append("")
        L.append("| Marca | Modelo | Versión | Precio | Combustible | Casa |")
        L.append("|---|---|---|--:|---|---|")
        for r in rows:
            b = f"**{r['brand']}**" if r.get("our_brand") else r["brand"]
            L.append(f"| {b} | {r['model']} | {r['version']} | {_usd(r['price_usd'])} | {r['fuel'] or '—'} | {r['dealer_group']} |")
        L.append("")

    path.write_text("\n".join(L), encoding="utf-8")
    logger.info("Precios competencia exportados: %s", path.name)
    return path
