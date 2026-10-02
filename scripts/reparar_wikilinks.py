#!/usr/bin/env python3
"""Reescribe wikilinks rotos por la renumeración de personas de modelo.

Busca en TODO el vault (Buyer Persona/ + output/personas/) cualquier link
[[Persona N - Modelo X]] donde N sea el número VIEJO del modelo X según la
tabla antes→después, y lo reemplaza por el número actual.
"""
import re
from pathlib import Path

raiz = Path("/home/croman/Escritorio/BUYER PERSONA")
arch_dir = raiz / "_ARCHIVO" / "personas-duplicadas"
act_dir = raiz / "output" / "personas"

# 1) Números ACTUALES por modelo
actual = {}
for f in act_dir.glob("Persona * - Modelo *.md"):
    n = int(f.name.split(" ")[1])
    modelo = f.name.split(" - Modelo ", 1)[1][:-3].strip()
    actual[modelo.casefold()] = (modelo, n)

# 2) Números VIEJOS por modelo (desde archivo)
viejos = {}
for f in arch_dir.glob("Persona * - Modelo *.md"):
    n = int(f.name.split(" ")[1])
    modelo = f.name.split(" - Modelo ", 1)[1][:-3].strip()
    cf = modelo.casefold()
    if cf in actual and actual[cf][1] != n:
        viejos[cf] = n

# 3) Escanear todos los .md del vault y reescribir links
patron = re.compile(r"\[\[(Persona (\d+) - Modelo ([^\]|#]+))([^\]]*)\]\]")

total_archivos = 0
total_links = 0
for md in raiz.rglob("*.md"):
    if "_ARCHIVO" in md.parts:
        continue
    texto = md.read_text(encoding="utf-8")
    original = texto

    def repl(m):
        global total_links
        etiqueta, num, modelo, resto = m.group(1), int(m.group(2)), m.group(3).strip(), m.group(4)
        cf = modelo.casefold()
        if cf in viejos and viejos[cf] == num:
            nuevo_num = actual[cf][1]
            nuevo_modelo = actual[cf][0]
            total_links += 1
            return f"[[Persona {nuevo_num} - Modelo {nuevo_modelo}{resto}]]"
        return m.group(0)

    texto = patron.sub(repl, texto)
    if texto != original:
        md.write_text(texto, encoding="utf-8")
        total_archivos += 1
        print(f"  ✏️  {md.relative_to(raiz)}")

print(f"\n{total_links} wikilinks corregidos en {total_archivos} archivos")
