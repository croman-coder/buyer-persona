#!/usr/bin/env python3
"""Verificación post-dedup: numeración única y contigua en personas raíz,
dedup de Marketing por canal+modelo, y conteo final."""
import re, shutil
from pathlib import Path
from collections import defaultdict

PERSONAS = Path("/home/croman/Escritorio/BUYER PERSONA/output/personas")
MKT = PERSONAS / "Marketing"
ARCHIVO = Path("/home/croman/Escritorio/BUYER PERSONA/_ARCHIVO/personas-duplicadas")

# ── 1. Numeración en raíz ──
por_num = defaultdict(list)
for f in PERSONAS.glob("Persona *.md"):
    m = re.match(r"Persona (\d+) - ", f.name)
    if m:
        por_num[int(m.group(1))].append(f.name)

nums = sorted(por_num)
dupes = {n: v for n, v in por_num.items() if len(v) > 1}
faltantes = [n for n in range(1, max(nums) + 1) if n not in por_num]
print(f"Raíz: {len(nums)} números únicos | rango 1-{max(nums)}")
print(f"Duplicados: {dupes or 'ninguno'}")
print(f"Faltantes: {faltantes or 'ninguno'}")

# ── 2. Dedup Marketing por canal + modelo ──
grupos_mkt = defaultdict(list)
for f in MKT.glob("*.md"):
    m = re.match(r"(Email|Google Ads|Meta Ads|WhatsApp) - Persona \d+ - Modelo (.+)\.md", f.name)
    if m:
        grupos_mkt[(m.group(1), m.group(2))].append(f)

movidos = 0
for (canal, slug), archivos in sorted(grupos_mkt.items()):
    if len(archivos) < 2:
        continue
    archivos.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    for viejo in archivos[1:]:
        shutil.copy2(viejo, ARCHIVO / viejo.name)
        viejo.unlink()
        movidos += 1

print(f"\nMarketing: {movidos} duplicados archivados")

# ── 3. Conteo final ──
raiz = len(list(PERSONAS.glob("Persona *.md")))
mkt_total = len(list(MKT.glob("*.md")))
print(f"\nFinal: {raiz} personas raíz | {mkt_total} archivos Marketing ({mkt_total // 4} personas × 4 canales)")
