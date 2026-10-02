#!/usr/bin/env python3
"""Verifica el acceso de la cuenta de servicio a Google Ads, GA4 y Search Console.

Desde el 9-sep-2026 Google no usa más el token de desarrollador: el acceso a la
API de Google Ads lo da el proyecto de Google Cloud dueño de la credencial.
Con una sola cuenta de servicio de solo lectura se leen las tres fuentes:

- Search Console: sitios a los que la cuenta de servicio fue agregada como usuario.
- GA4: propiedades donde tiene acceso de lector (necesita la Admin API activada).
- Google Ads: cuentas donde fue agregada como usuario (nivel Explorer o superior).

No imprime la clave ni ningún secreto: solo qué se ve y qué falta.

.env:
    GOOGLE_SA_KEY_FILE=/ruta/a/la/clave.json      (fuera del repo, permisos 600)

Uso: venv/bin/python3 scripts/verificar_google.py
"""
import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
SCOPES = ["https://www.googleapis.com/auth/adwords",
          "https://www.googleapis.com/auth/analytics.readonly",
          "https://www.googleapis.com/auth/webmasters.readonly"]


def search_console(s):
    r = s.get("https://www.googleapis.com/webmasters/v3/sites", timeout=60)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.json().get('error', {}).get('message', '')[:120]}"
    sitios = r.json().get("siteEntry", [])
    if not sitios:
        return False, "la cuenta de servicio no ve ningún sitio: agregarla en Search Console → Configuración → Usuarios y permisos"
    return True, "; ".join(f"{x['siteUrl']} ({x['permissionLevel']})" for x in sitios)


def ga4(s):
    r = s.get("https://analyticsadmin.googleapis.com/v1beta/accountSummaries", params={"pageSize": 200}, timeout=60)
    if r.status_code != 200:
        msg = r.json().get("error", {}).get("message", "")
        if "has not been used" in msg or "is disabled" in msg:
            return False, "activar «Google Analytics Admin API» y «Google Analytics Data API» en el proyecto"
        return False, f"HTTP {r.status_code}: {msg[:120]}"
    props = [(p["displayName"], p["property"].split("/")[-1])
             for a in r.json().get("accountSummaries", []) for p in a.get("propertySummaries", [])]
    if not props:
        return False, "no ve ninguna propiedad: agregarla como Lector en GA4 → Administrar → Gestión del acceso a la propiedad"
    return True, "; ".join(f"{n} ({i})" for n, i in props)


def google_ads(s):
    # La versión vigente de la API cambia varias veces por año: se prueba de la más nueva hacia atrás.
    for v in range(30, 17, -1):
        r = s.get(f"https://googleads.googleapis.com/v{v}/customers:listAccessibleCustomers", timeout=60)
        if r.status_code == 404:
            continue
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", "") if r.headers.get("content-type", "").startswith("application/json") else r.text
            if "has not been used" in msg or "is disabled" in msg:
                return False, "activar «Google Ads API» en el proyecto"
            return False, f"API v{v}, HTTP {r.status_code}: {msg[:160]} (¿nivel de acceso Explorer aprobado?)"
        cuentas = [c.split("/")[-1] for c in r.json().get("resourceNames", [])]
        if not cuentas:
            return False, f"API v{v}: no ve ninguna cuenta: agregarla como usuario de solo lectura en cada cuenta de Google Ads"
        return True, f"API v{v}: {len(cuentas)} cuenta(s): " + ", ".join(cuentas)
    return False, "no respondió ninguna versión de la API"


def main():
    clave = os.environ.get("GOOGLE_SA_KEY_FILE", "")
    if not clave or not os.path.isfile(clave):
        sys.exit("Falta GOOGLE_SA_KEY_FILE en .env (ruta a la clave JSON de la cuenta de servicio).")
    cred = service_account.Credentials.from_service_account_file(clave, scopes=SCOPES)
    print(f"Cuenta de servicio: {cred.service_account_email}\n")
    s = AuthorizedSession(cred)
    todo_ok = True
    for nombre, fn in (("Search Console", search_console), ("Google Analytics 4", ga4), ("Google Ads", google_ads)):
        try:
            ok, detalle = fn(s)
        except Exception as e:  # red, credencial inválida, etc.
            ok, detalle = False, f"{type(e).__name__}: {str(e)[:160]}"
        todo_ok &= ok
        print(f"{'✅' if ok else '❌'} {nombre}: {detalle}")
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
