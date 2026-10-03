#!/usr/bin/env python3
"""Corre el cruce de ventas con leads de Meta sin esperar al pipeline de las 06:00.

Lee los leads de formulario de los últimos 90 días (claves cifradas, ver
src/generators/ventas_meta.py), el gasto por campaña de todas las cuentas y las
ventas del ERP; escribe output/raw/ventas_meta_<fecha>.json y la nota
«Sistema/💰 Ventas que vinieron de Meta». Solo totales: ningún nombre, teléfono ni
mail sale de la memoria.

Uso: venv/bin/python3 scripts/cruce_ventas_meta.py
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.config_loader import load_config  # noqa: E402
from src.connectors.meta_ads_connector import MetaAdsConnector  # noqa: E402
from src.connectors.sales_connector import SalesConnector  # noqa: E402
from src.generators.ventas_meta import cruzar, nota  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")


def leer_fuentes(config: dict) -> tuple[list, list, list]:
    """(claves de ventas, claves de leads, gasto por campaña)."""
    sales_cfg = {**config.get("sales", {}), "file_path": config["paths"]["sales_history"]}
    ventas = SalesConnector(sales_cfg)
    ventas._load_dataframe()
    meta = MetaAdsConnector(config["meta_ads"])
    meta._collect_leads_from_pages({"leads_by_brand": {}}, days_back=int(config["meta_ads"].get("days_back", 90)))
    desde, hasta = meta._get_date_range()
    campanas = []
    for cuenta in meta.ad_accounts:
        meta.ad_account_id = cuenta["id"]
        try:
            filas = meta._fetch_campaign_insights(desde, hasta)
        except Exception as exc:  # una cuenta caída no frena el resto
            print(f"  cuenta {cuenta['id']}: {exc}")
            continue
        for f in filas:
            f["account"] = cuenta["label"]
        campanas += filas
    return ventas.claves_ventas, meta.claves_leads, campanas


def main() -> None:
    config = load_config("config/settings.yaml")
    ventas, leads, campanas = leer_fuentes(config)
    print(f"ventas del ERP: {len(ventas)} · leads de Meta: {len(leads)} · campañas con gasto: {len(campanas)}")
    r = cruzar(ventas, leads, campanas)
    ventas.clear()
    leads.clear()
    if not r:
        sys.exit("Sin datos para cruzar.")
    salida = ROOT / "output" / "raw" / f"ventas_meta_{datetime.now():%Y%m%d_%H%M%S}.json"
    salida.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    vault = config["paths"].get("obsidian_vault", "")
    if vault:
        (ROOT / vault / "Sistema" / "💰 Ventas que vinieron de Meta.md").write_text(nota(r), encoding="utf-8")
    print(f"ventas evaluadas: {r['ventas_evaluadas']} ({r['ventas_desde']} → {r['ventas_hasta']}) · "
          f"leads del {r['ventana_leads']['desde']} al {r['ventana_leads']['hasta']}")
    for marca, m in r["por_marca"].items():
        print(f"  {marca:11s} {m['con_meta']:4d} de {m['ventas']:4d} con lead de Meta "
              f"(teléfono/mail {m['por_contacto']}, nombre {m['por_nombre']}, ambiguas {m['ambiguas']}) · origen {m['origen']}")
    print(f"días del lead a la venta: {r['dias']} · entre marcas: {r['entre_marcas'][:5]}")
    print("guardado en", salida.relative_to(ROOT))


if __name__ == "__main__":
    main()
