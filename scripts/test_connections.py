#!/usr/bin/env python3
"""
Verifica las credenciales de Meta Ads y Google Ads SIN imprimir secretos.

Uso:
    venv/bin/python3 scripts/test_connections.py

Salida: OK / FAIL por cada conexión, con el motivo del error si falla.
Los tokens nunca se muestran (solo los últimos 4 caracteres para identificarlos).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_config


def mask(secret: str) -> str:
    """Muestra solo los últimos 4 caracteres de un secreto."""
    if not secret:
        return "(vacío)"
    return f"****{secret[-4:]}"


def test_meta(config: dict) -> bool:
    import requests

    cfg = config.get("meta_ads", {})
    token = cfg.get("access_token", "")
    version = cfg.get("api_version", "v21.0")

    if not token:
        print("  ❌ META_ADS_ACCESS_TOKEN vacío en .env")
        return False

    print(f"  Token: {mask(token)}")

    # 1. Validar token
    resp = requests.get(
        f"https://graph.facebook.com/{version}/me",
        params={"access_token": token},
        timeout=15,
    )
    if resp.status_code != 200:
        err = resp.json().get("error", {}).get("message", resp.text[:200])
        print(f"  ❌ Token inválido: {err}")
        return False
    print(f"  ✅ Token válido (usuario: {resp.json().get('name', resp.json().get('id', '?'))})")

    # 2. Validar acceso a cada cuenta del portfolio
    raw_accounts = cfg.get("ad_account_ids", "") or cfg.get("ad_account_id", "")
    ok = True
    for part in str(raw_accounts).split(","):
        part = part.strip()
        if not part:
            continue
        acc_id = part.split(":")[0].strip()
        label = part.split(":")[1].strip() if ":" in part else acc_id
        resp = requests.get(
            f"https://graph.facebook.com/{version}/{acc_id}",
            params={"access_token": token, "fields": "name,account_status,currency"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ {label}: '{data.get('name')}' ({data.get('currency')}, estado {data.get('account_status')})")
        else:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
            print(f"  ❌ {label} ({acc_id}): {err}")
            ok = False

    return ok


def test_google(config: dict) -> bool:
    cfg = config.get("google_ads", {})

    required = {
        "developer_token": cfg.get("developer_token", ""),
        "client_id": cfg.get("client_id", ""),
        "client_secret": cfg.get("client_secret", ""),
        "refresh_token": cfg.get("refresh_token", ""),
        "customer_id": cfg.get("customer_id", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"  ❌ Variables vacías en .env: {', '.join(missing)}")
        return False

    print(f"  Developer token: {mask(required['developer_token'])}")
    print(f"  Refresh token:   {mask(required['refresh_token'])}")

    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
    except ImportError:
        print("  ❌ Paquete google-ads no instalado (uv pip install google-ads)")
        return False

    credentials = {
        "developer_token": required["developer_token"],
        "client_id": required["client_id"],
        "client_secret": required["client_secret"],
        "refresh_token": required["refresh_token"],
        "use_proto_plus": True,
    }
    login_id = str(cfg.get("login_customer_id", "")).replace("-", "")
    if login_id:
        credentials["login_customer_id"] = login_id

    try:
        client = GoogleAdsClient.load_from_dict(credentials)
        service = client.get_service("GoogleAdsService")
        customer_id = str(required["customer_id"]).replace("-", "")
        query = "SELECT customer.descriptive_name, customer.currency_code FROM customer LIMIT 1"
        response = service.search(customer_id=customer_id, query=query)
        for row in response:
            print(f"  ✅ Cuenta: '{row.customer.descriptive_name}' ({row.customer.currency_code})")
        return True
    except GoogleAdsException as e:
        for error in e.failure.errors:
            print(f"  ❌ Google Ads API: {error.message}")
        return False
    except Exception as e:
        print(f"  ❌ Error de conexión/autenticación: {type(e).__name__}: {e}")
        return False


def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    if not (project_root / ".env").exists():
        print("❌ No existe .env — ejecutá primero:")
        print('   cp env.plantilla .env && chmod 600 .env && nano .env')
        sys.exit(1)

    config = load_config("config/settings.yaml")

    print("\n🔵 Meta Ads")
    meta_ok = test_meta(config)

    print("\n🔴 Google Ads")
    google_ok = test_google(config)

    print("\n" + "=" * 50)
    print(f"Meta Ads:   {'✅ CONECTADO' if meta_ok else '❌ FALLÓ'}")
    print(f"Google Ads: {'✅ CONECTADO' if google_ok else '❌ FALLÓ'}")
    print("=" * 50)

    if meta_ok or google_ok:
        print("\nSiguiente paso: habilitá las fuentes que dieron OK en config/settings.yaml")
        print("  google_ads.enabled: true  /  meta_ads.enabled: true")
        print("y corré:  venv/bin/python3 main.py")

    sys.exit(0 if (meta_ok and google_ok) else 1)


if __name__ == "__main__":
    main()
