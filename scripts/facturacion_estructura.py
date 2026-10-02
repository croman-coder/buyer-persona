#!/usr/bin/env python3
"""Parsea la hoja Datos de FacturacionUnidades: detecta encabezado, cuenta registros, fechas, contacto."""
import re
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PATH = "/home/croman/Escritorio/BUYER PERSONA/ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx"

z = zipfile.ZipFile(PATH)
strings = []
root = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in root.iter(NS + "si"):
    strings.append("".join(t.text or "" for t in si.iter(NS + "t")).strip())

# la hoja 'Datos' es la primera -> encontrar su target
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rel_map = {r.get("Id"): r.get("Target") for r in rels}
wb = ET.fromstring(z.read("xl/workbook.xml"))
target = None
for sh in wb.iter(NS + "sheet"):
    if sh.get("name") == "Datos":
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = (rel_map.get(rid) or "").lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target

root_hoja = ET.fromstring(z.read(target))

def celda_val(c):
    t = c.get("t")
    if t == "s":
        v = c.find(NS + "v")
        return strings[int(v.text)] if v is not None and v.text else ""
    v = c.find(NS + "v")
    return (v.text or "") if v is not None else ""

filas_datos = []
header = {}
for i, row in enumerate(root_hoja.iter(NS + "row"), start=1):
    vals = {}
    for c in row.iter(NS + "c"):
        ref = c.get("r") or ""
        col = re.match(r"[A-Z]+", ref).group() if ref else ""
        vals[col] = celda_val(c).strip()
    if i <= 6:
        no_vacios = {k: v[:40] for k, v in sorted(vals.items(), key=lambda kv: (len(kv[0]), kv[0]))[:14] if v}
        print(f"Fila {i}: {no_vacios}")
    # detectar fila de encabezados: contiene 'Marca' y 'Modelo' o similar
    joined = " | ".join(vals.values()).upper()
    if not header and ("MODELO" in joined and ("MARCA" in joined or "CHASIS" in joined)):
        header = dict(vals)
        header_row = i
        continue
    if header:
        filas_datos.append(vals)

print(f"\nFila de encabezado: {header_row}")
cols = sorted(header.keys(), key=lambda c: (len(c), c))
print(f"Columnas ({len(cols)}):")
for c in cols:
    print(f"  {c}: {header[c][:45]!r}")
print(f"\nRegistros debajo del encabezado: {len(filas_datos)}")
