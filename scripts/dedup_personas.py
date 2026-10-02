#!/usr/bin/env python3
"""Dedup de personas de modelo: cuando un mismo modelo tiene varias personas,
queda la más nueva (regeneración con datos frescos) y las viejas van a _ARCHIVO."""
import re, shutil, sys
from pathlib import Path
from collections import defaultdict

PERSONAS = Path("/home/croman/Escritorio/BUYER PERSONA/output/personas")
ARCHIVO = Path("/home/croman/Escritorio/BUYER PERSONA/_ARCHIVO/personas-duplicadas")

def model_slug(name: str) -> str:
    m = re.match(r"Persona \d+ - Modelo (.+)\.md", name)
    return m.group(1) if m else None

grupos = defaultdict(list)
for f in sorted(PERSONAS.glob("Persona *.md")):
    slug = model_slug(f.name)
    if slug:
        grupos[slug].append(f)

ARCHIVO.mkdir(parents=True, exist_ok=True)
movidos, quedan_dup_num = [], set()

for slug, archivos in grupos.items():
    if len(archivos) < 2:
        continue
    # más nuevo por mtime gana
    archivos.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    ganador = archivos[0]
    for viejo in archivos[1:]:
        shutil.copy2(viejo, ARCHIVO / viejo.name)
        viejo.unlink()
        movidos.append((viejo.name, ganador.name))

# después del dedup, ver qué números siguen colisionando
por_num = defaultdict(list)
for f in PERSONAS.glob("Persona *.md"):
    num = f.name.split(" - ")[0]
    por_num[num].append(f.name)

print("=== DEDUP HECHO ===")
for viejo, ganador in movidos:
    print(f"  archivado: {viejo}  (quedó: {ganador})")
print(f"\nTotal archivados: {len(movidos)}")
print("\n=== COLISIONES RESTANTES (mismo número, modelos distintos) ===")
for num, nombres in sorted(por_num.items()):
    if len(nombres) > 1:
        print(f"  {num}: {nombres}")
