#!/usr/bin/env python3
"""
Valida el catálogo de modelos contra los anuncios reales de Meta Ads.

Muestra cuántos anuncios reales menciona cada modelo del catálogo, para
detectar entradas sin presencia (modelos que no se pautan en Paraguay) o
modelos pautados que faltan en el catálogo.

Uso:
    venv/bin/python3 scripts/validate_model_catalog.py [ruta_data_sources.json]
"""

from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.catalog.models_py import MODEL_CATALOG, detect_models_in_ads


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        candidates = sorted(glob.glob("output/raw/data_sources_*.json"))
        if not candidates:
            print("❌ No hay output/raw/data_sources_*.json. Corré main.py primero.")
            sys.exit(1)
        path = candidates[-1]

    print(f"Validando contra: {path}\n")
    data = json.load(open(path, encoding="utf-8"))
    ads = data.get("meta_ads", {}).get("ad_creatives", [])
    if not ads:
        print("❌ Ese archivo no tiene anuncios (ad_creatives).")
        sys.exit(1)

    by_brand = defaultdict(list)
    for ad in ads:
        by_brand[ad.get("account", "")].append(ad)

    total_with_ads = 0
    for brand in MODEL_CATALOG:
        brand_ads = by_brand.get(brand, [])
        detected = detect_models_in_ads(brand_ads, brand)
        print(f"== {brand} ({len(brand_ads)} anuncios)")
        for model in MODEL_CATALOG[brand]:
            n = len(detected.get(model, []))
            mark = "✅" if n else "  "
            print(f"  {mark} {model:<28} {n:>4} anuncios")
            if n:
                total_with_ads += 1
        print()

    print(f"Modelos con presencia real: {total_with_ads}")


if __name__ == "__main__":
    main()
