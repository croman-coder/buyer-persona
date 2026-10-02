#!/usr/bin/env python3
"""Chequea que cada ref [[Persona N - Modelo X]] del MOC exista como archivo."""
import re
from pathlib import Path

raiz = Path("/home/croman/Escritorio/BUYER PERSONA/output/personas")
existentes = {f.stem for f in raiz.glob("Persona *.md")}

texto = (raiz / " Buyer Personas MOC.md").read_text(encoding="utf-8")
refs = re.findall(r"\[\[(Persona \d+ - Modelo [^\]|#]+)", texto)

rotos = [r for r in refs if r not in existentes]
print(f"refs de modelo en MOC: {len(refs)} | rotas: {len(rotos)}")
for r in sorted(set(rotos)):
    print("ROTO:", r)
