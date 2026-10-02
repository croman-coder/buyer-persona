#!/usr/bin/env python3
"""
Verifica el estado y la expiración de los tokens de Meta Ads y Google Ads.

Diseñado para correr desde cron (semanal) y alertar ANTES de que un token
caduque, para que el pipeline no se caiga de golpe.

Uso:
    venv/bin/python3 scripts/check_tokens.py
    venv/bin/python3 scripts/check_tokens.py --warn-days 14

Salida: estado de cada plataforma + días hasta expirar.
Notifica (vía Telegram/Webhook/Email) si algún token está crítico.

Exit codes:
    0 = todos los tokens OK
    1 = algún token expira dentro de --warn-days o ya está vencido
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from src.config_loader import load_config


def mask(secret: str) -> str:
    if not secret:
        return "(vacío)"
    return f"****{secret[-4:]}"


def _send_notification(message: str) -> None:
    """Envía alerta por los canales configurados en .env (si hay)."""
    # Telegram
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if token and chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": message},
                timeout=10,
            )
        except requests.RequestException:
            pass

    # Webhook
    webhook = os.getenv("WEBHOOK_URL", "")
    if webhook:
        try:
            requests.post(
                webhook,
                json={"text": message},
                timeout=10,
            )
        except requests.RequestException:
            pass

    # Email
    email = os.getenv("ALERT_EMAIL", "")
    if email and shutil_which("mail"):
        try:
            subprocess_mail(email, message)
        except Exception:
            pass


def shutil_which(cmd: str) -> str | None:
    import shutil

    return shutil.which(cmd)


def subprocess_mail(to: str, body: str) -> None:
    import subprocess

    subprocess.run(
        ["mail", "-s", "⚠️ Buyer Persona: token por expirar", to],
        input=body,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Meta Ads
# ---------------------------------------------------------------------------

def check_meta(config: dict, warn_days: int) -> tuple[bool, str]:
    """
    Devuelve (ok, reporte).
    ok=False si el token está vencido o expira dentro de warn_days.
    """
    cfg = config.get("meta_ads", {})
    token = cfg.get("access_token", "")
    version = cfg.get("api_version", "v21.0")

    lines: list[str] = ["🔵 Meta Ads"]

    if not token:
        lines.append("  ❌ META_ADS_ACCESS_TOKEN vacío en .env")
        return False, "\n".join(lines)

    lines.append(f"  Token: {mask(token)}")

    # /debug_token devuelve expires_at para tokens de usuario
    app_id = cfg.get("app_id", "")
    app_secret = cfg.get("app_secret", "")

    try:
        # Método 1: debug_token (requiere app access token)
        if app_id and app_secret:
            # App access token
            app_token_resp = requests.get(
                f"https://graph.facebook.com/{version}/oauth/access_token",
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "grant_type": "client_credentials",
                },
                timeout=15,
            )
            app_token_resp.raise_for_status()
            app_token = app_token_resp.json().get("access_token", "")

            debug_resp = requests.get(
                f"https://graph.facebook.com/{version}/debug_token",
                params={
                    "input_token": token,
                    "access_token": app_token or f"{app_id}|{app_secret}",
                },
                timeout=15,
            )
            debug_resp.raise_for_status()
            data = debug_resp.json().get("data", {})

            if not data.get("is_valid", False):
                err = data.get("error", {}).get("message", "token inválido")
                lines.append(f"  ❌ Token inválido: {err}")
                return False, "\n".join(lines)

            lines.append("  ✅ Token válido")

            expires_at = data.get("expires_at", 0)
            if expires_at == 0:
                lines.append("  ♾️  Token sin expiración (long-lived o del sistema)")
                return True, "\n".join(lines)

            expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            remaining = (expiry - datetime.now(timezone.utc)).days
            lines.append(f"  ⏰ Expira el {expiry.strftime('%Y-%m-%d')} ({remaining} días)")

            if remaining < 0:
                lines.append("  🚨 YA ESTÁ VENCIDO — regenerar en Facebook YA")
                return False, "\n".join(lines)
            if remaining < warn_days:
                lines.append(f"  ⚠️  Renovar pronto (menos de {warn_days} días)")
                return False, "\n".join(lines)
            return True, "\n".join(lines)

        # Método 2: sin app_id/secret, solo validar que el token funciona
        resp = requests.get(
            f"https://graph.facebook.com/{version}/me",
            params={"access_token": token},
            timeout=15,
        )
        if resp.status_code == 200:
            who = resp.json().get("name", resp.json().get("id", "?"))
            lines.append(f"  ✅ Token funcional (usuario: {who})")
            lines.append("  ℹ️  No se puede calcular expiración sin app_id/app_secret")
            return True, "\n".join(lines)

        err = resp.json().get("error", {}).get("message", resp.text[:200])
        lines.append(f"  ❌ Token inválido: {err}")
        return False, "\n".join(lines)

    except requests.RequestException as e:
        lines.append(f"  ❌ Error de conexión: {e}")
        return False, "\n".join(lines)


# ---------------------------------------------------------------------------
# Google Ads
# ---------------------------------------------------------------------------

def check_google(config: dict, warn_days: int) -> tuple[bool, str]:
    """
    Google Ads usa refresh tokens que no expiran solos, pero validamos
    que la conexión funcione.
    """
    cfg = config.get("google_ads", {})
    lines: list[str] = ["🔴 Google Ads"]

    required = {
        "developer_token": cfg.get("developer_token", ""),
        "client_id": cfg.get("client_id", ""),
        "client_secret": cfg.get("client_secret", ""),
        "refresh_token": cfg.get("refresh_token", ""),
        "customer_id": cfg.get("customer_id", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        lines.append(f"  ⚠️  Variables vacías en .env: {', '.join(missing)}")
        return False, "\n".join(lines)

    lines.append(f"  Developer token: {mask(required['developer_token'])}")
    lines.append(f"  Refresh token:   {mask(required['refresh_token'])}")

    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
    except ImportError:
        lines.append("  ⚠️  Paquete google-ads no instalado (no se puede validar)")
        return False, "\n".join(lines)

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
        query = "SELECT customer.descriptive_name FROM customer LIMIT 1"
        response = service.search(customer_id=customer_id, query=query)
        for row in response:
            lines.append(f"  ✅ Cuenta: '{row.customer.descriptive_name}'")
            break
        else:
            lines.append("  ✅ Conexión OK (sin cuenta descriptiva)")
        lines.append("  ♾️  Refresh token: sin expiración (es auto-renovable)")
        return True, "\n".join(lines)
    except GoogleAdsException as e:
        for error in e.failure.errors:
            lines.append(f"  ❌ Google Ads API: {error.message}")
        return False, "\n".join(lines)
    except Exception as e:
        lines.append(f"  ❌ {type(e).__name__}: {e}")
        return False, "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica tokens de las APIs.")
    parser.add_argument(
        "--warn-days",
        type=int,
        default=14,
        help="Avisar si un token expira en menos de N días (default: 14)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    if not (project_root / ".env").exists():
        print("⚠️  No existe .env — algunos chequeos se omitirán")

    config = load_config("config/settings.yaml")

    print("=" * 60)
    meta_ok, meta_report = check_meta(config, args.warn_days)
    print(meta_report)

    print()
    google_ok, google_report = check_google(config, args.warn_days)
    print(google_report)
    print("=" * 60)

    all_ok = meta_ok and google_ok
    if all_ok:
        print("\n✅ Todos los tokens están OK.\n")
        sys.exit(0)
    else:
        print("\n⚠️  Hay tokens que requieren atención.\n")
        # Enviar notificación
        report = f"⚠️ Buyer Persona — revisión de tokens\n\n{meta_report}\n\n{google_report}"
        _send_notification(report)
        sys.exit(1)


if __name__ == "__main__":
    main()