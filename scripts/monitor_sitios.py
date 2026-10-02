#!/usr/bin/env python3
"""
Monitor de sitios web de Santa Rosa — verifica que todos estén online.
Silencioso si todo OK. Alerta si alguno cae.
"""
import requests
import sys
from datetime import datetime

SITIOS = [
    ("Santa Rosa", "https://santarosa.com.py"),
    ("GWM Paraguay", "https://www.gwm.com.py"),
    ("JAC Paraguay", "https://www.jac.com.py"),
    ("Mitsubishi PY", "https://mitsubishi.com.py"),
    ("Renault PY", "https://www.renault.com.py"),
    ("Leapmotor PY", "https://www.leapmotor.com.py"),
    ("Renew Subastas", "https://renewsubastas.com.py"),
    ("Jetour PY", "https://www.chery.com.py"),  # placeholder, jetour no tiene dominio estable
    ("PDI Dashboard", "https://pdi-santarosa.vercel.app"),
    ("CARBID", "https://renewsubastas.com.py"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

caidos = []
ok = []
ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for nombre, url in SITIOS:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code < 400:
            ok.append(f"✅ {nombre} ({resp.status_code}) — {url}")
        else:
            caidos.append(f"🔴 {nombre} (HTTP {resp.status_code}) — {url}")
    except requests.RequestException as e:
        caidos.append(f"🔴 {nombre} (ERROR) — {url} — {type(e).__name__}")

# Output: solo imprimir si hay caidos (silencioso si todo OK)
if caidos:
    print(f"🚨 ALERTA SITIOS WEB — {ahora}")
    print(f"{'='*50}")
    print(f"❌ {len(caidos)} sitio(s) con problemas:")
    print()
    for c in caidos:
        print(c)
    print()
    print(f"✅ {len(ok)} sitio(s) funcionando correctamente.")
    sys.exit(1)
else:
    # Silencioso: no imprimir nada si todo OK
    pass
