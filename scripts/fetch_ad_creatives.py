#!/usr/bin/env python3
"""
Lee el contenido real de los anuncios (copy, títulos, CTA) de cada cuenta
de Meta Ads configurada, para entender qué mensajes ya se están usando
y enriquecer el buyer persona con eso.

No modifica nada — solo lee y guarda un resumen en output/raw/ad_creatives.json
y lo imprime en pantalla.

Uso:
    venv/bin/python3 scripts/fetch_ad_creatives.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from src.config_loader import load_config
from src.connectors.meta_ads_connector import MetaAdsConnector


def fetch_ads_with_creative(access_token: str, account_id: str, api_version: str) -> list[dict]:
    """Trae todos los anuncios (activos y pausados) con su creatividad."""
    url = f"https://graph.facebook.com/{api_version}/{account_id}/ads"
    params = {
        "access_token": access_token,
        "fields": (
            "id,name,status,effective_status,adset{name,targeting},"
            "creative{id,name,title,body,object_story_spec,"
            "thumbnail_url,image_url,video_id,call_to_action_type,"
            "asset_feed_spec}"
        ),
        "limit": 100,
    }

    ads: list[dict] = []
    while url:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            err = resp.json().get("error", {}).get("message", resp.text[:300])
            print(f"  ⚠️  Error consultando anuncios: {err}")
            break

        data = resp.json()
        ads.extend(data.get("data", []))

        next_url = data.get("paging", {}).get("next")
        if next_url:
            url = next_url
            params = {}  # el next_url ya trae todos los params
            time.sleep(0.2)
        else:
            url = None

    return ads


def extract_copy(ad: dict) -> dict[str, Any]:
    """Extrae el texto/copy legible de un anuncio, sea cual sea su formato."""
    creative = ad.get("creative", {}) or {}
    story = creative.get("object_story_spec", {}) or {}

    body = creative.get("body", "")
    title = creative.get("title", "")
    cta = creative.get("call_to_action_type", "")
    image = creative.get("image_url") or creative.get("thumbnail_url") or ""

    # Formato link_data (imagen/carrusel estático)
    link_data = story.get("link_data", {})
    if link_data:
        body = body or link_data.get("message", "")
        title = title or link_data.get("name", "") or link_data.get("link", "")
        cta = cta or (link_data.get("call_to_action", {}) or {}).get("type", "")
        if link_data.get("child_attachments"):
            # Carrusel: juntar los mensajes de cada tarjeta
            cards = [c.get("name", "") for c in link_data["child_attachments"] if c.get("name")]
            if cards:
                title = title or " | ".join(cards)

    # Formato video_data
    video_data = story.get("video_data", {})
    if video_data:
        body = body or video_data.get("message", "")
        title = title or video_data.get("title", "")
        cta = cta or (video_data.get("call_to_action", {}) or {}).get("type", "")

    # Formato asset_feed_spec (anuncios dinámicos/Advantage+)
    afs = creative.get("asset_feed_spec", {}) or {}
    if afs and not body:
        bodies = afs.get("bodies", [])
        titles = afs.get("titles", [])
        if bodies:
            body = " / ".join(b.get("text", "") for b in bodies if b.get("text"))
        if titles:
            title = " / ".join(t.get("text", "") for t in titles if t.get("text"))

    return {
        "ad_name": ad.get("name", ""),
        "status": ad.get("effective_status", ad.get("status", "")),
        "adset_name": (ad.get("adset") or {}).get("name", ""),
        "targeting": (ad.get("adset") or {}).get("targeting", {}),
        "title": title,
        "body": body,
        "cta": cta,
        "has_image": bool(image),
    }


def main():
    config = load_config("config/settings.yaml")
    meta_cfg = config.get("meta_ads", {})

    token = meta_cfg.get("access_token", "")
    api_version = meta_cfg.get("api_version", "v21.0")
    raw_accounts = meta_cfg.get("ad_account_ids", "") or meta_cfg.get("ad_account_id", "")

    if not token:
        print("❌ META_ADS_ACCESS_TOKEN vacío en .env")
        sys.exit(1)

    accounts = MetaAdsConnector._parse_accounts(raw_accounts)
    if not accounts:
        print("❌ No hay cuentas configuradas en META_ADS_AD_ACCOUNT_IDS")
        sys.exit(1)

    all_results: dict[str, list[dict]] = {}

    for account in accounts:
        acc_id, label = account["id"], account["label"]
        print(f"\n{'=' * 70}")
        print(f"📢 {label} ({acc_id})")
        print("=" * 70)

        ads = fetch_ads_with_creative(token, acc_id, api_version)
        parsed = [extract_copy(ad) for ad in ads]
        all_results[label] = parsed

        if not parsed:
            print("  (sin anuncios)")
            continue

        for ad in parsed:
            print(f"\n  📌 {ad['ad_name']}  [{ad['status']}]")
            print(f"     Adset: {ad['adset_name']}")
            if ad["title"]:
                print(f"     Título: {ad['title']}")
            if ad["body"]:
                print(f"     Copy: {ad['body'][:300]}")
            if ad["cta"]:
                print(f"     CTA: {ad['cta']}")

    out_path = Path("output/raw/ad_creatives.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    total = sum(len(v) for v in all_results.values())
    print(f"\n\n💾 {total} anuncios guardados en {out_path}")


if __name__ == "__main__":
    main()
