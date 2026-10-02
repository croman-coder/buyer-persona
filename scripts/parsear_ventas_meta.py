#!/usr/bin/env python3
"""Parsea el xlsx de ventas sin openpyxl (solo stdlib) y da estadísticas."""
import re
import subprocess
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ARCHIVO = "/home/croman/Escritorio/PC SRPY/Ventas + Origenes + ROI (1).xlsx"

z = zipfile.ZipFile(ARCHIVO)

# 1) shared strings
strings = []
try:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", NS):
        texto = "".join(t.text or "" for t in si.iter("{%s}t" % NS["m"]))
        strings.append(texto.strip())
except KeyError:
    pass

# 2) mapear r:id -> archivo de hoja
wb_rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rel_map = {r.get("Id"): r.get("Target") for r in wb_rels}
wb = ET.fromstring(z.read("xl/workbook.xml"))
hojas = {}
for sh in wb.iter("{%s}sheet" % NS["m"]):
    rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    target = rel_map[rid]
    if not target.startswith("xl/"):
        target = "xl/" + target.lstrip("/")
    hojas[sh.get("name")] = target

def leer_hoja(path):
    """Devuelve lista de filas, cada fila = lista de valores (string compartido o literal)."""
    root = ET.fromstring(z.read(path))
    filas = []
    for row in root.iter("{%s}row" % NS["m"]):
        vals = {}
        for c in row.iter("{%s}c" % NS["m"]):
            ref = c.get("r")  # ej: B12
            col = re.match(r"[A-Z]+", ref).group()
            t = c.get("t")
            if t == "s":
                v = c.find("m:v", NS)
                val = strings[int(v.text)] if v is not None else ""
            elif t == "inlineStr":
                is_el = c.find("m:is", NS)
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"])) if is_el is not None else ""
            else:
                v = c.find("m:v", NS)
                val = v.text if v is not None else ""
            vals[col] = val.strip() if isinstance(val, str) else val
        filas.append(vals)
    return filas

# 3) analizar hoja META
nombre_hoja = sys_hoja = None
import sys
candidata = "META" if "META" in hojas else list(hojas)[0]
print(f"Hojas disponibles: {list(hojas)} → analizando '{candidata}'")
filas = leer_hoja(hojas[candidata])
print(f"Filas totales en '{candidata}': {len(filas)}")

# encabezados = primera fila
header = filas[0]
cols_orden = sorted(header.keys(), key=lambda c: (len(c), c))
print("\nEncabezados:")
for c in cols_orden:
    print(f"  {c}: {header[c][:60]!r}")

print("\nPrimera fila de datos:")
if len(filas) > 1:
    for c in cols_orden:
        print(f"  {header[c][:30]}: {filas[1].get(c, '')[:50]!r}")
