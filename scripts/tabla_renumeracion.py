#!/usr/bin/env python3
"""Tabla antes→después de números de personas de modelo (dedup del 25/08)."""
from pathlib import Path

raiz = Path("/home/croman/Escritorio/BUYER PERSONA")
arch_dir = raiz / "_ARCHIVO" / "personas-duplicadas"
act_dir = raiz / "output" / "personas"

def numero(path, nombre_modelo):
    for f in path.glob("Persona * - Modelo *.md"):
        if f.name.endswith(f" - Modelo {nombre_modelo}.md"):
            return f.name.split(" ")[1]
    return "-"

cambios = []
for f in sorted(arch_dir.glob("Persona * - Modelo *.md")):
    modelo = f.name.split(" - Modelo ", 1)[1][:-3]
    viejo = f.name.split(" ")[1]
    nuevo = numero(act_dir, modelo)
    marca = "igual" if viejo == nuevo else "CAMBIO"
    cambios.append((modelo, viejo, nuevo, marca))

print(f"{'Modelo':<22} {'antes':>5} {'ahora':>6}  estado")
for modelo, viejo, nuevo, marca in cambios:
    print(f"{modelo:<22} {viejo:>5} {nuevo:>6}  {marca}")
