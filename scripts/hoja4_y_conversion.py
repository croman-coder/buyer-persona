#!/usr/bin/env python3
"""Lee Hoja4 completa + cuenta filas de CONVERSION con rango de fechas."""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ARCHIVO = "/home/croman/Escritorio/PC SRPY/Ventas + Origenes + ROI (1).xlsx"
z = zipfile.ZipFile(ARCHIVO)

strings = []
root = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in root.findall("m:si", NS):
    strings.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])).strip())

def leer_hoja(path):
    root = ET.fromstring(z.read(path))
    filas = []
    for row in root.iter("{%s}row" % NS["m"]):
        vals = {}
        for c in row.iter("{%s}c" % NS["m"]):
            ref = c.get("r") or ""
            col = re.match(r"[A-Z]+", ref).group() if ref else ""
            t = c.get("t")
            if t == "s":
                v = c.find("m:v", NS)
                val = strings[int(v.text)] if v is not None and v.text else ""
            else:
                v = c.find("m:v", NS)
                val = v.text if v is not None else ""
            vals[col] = (val or "").strip()
        if any(vals.values()):
            filas.append(vals)
    return filas

# --- Hoja4 completa ---
print("="*70)
print("HOJA4 COMPLETA")
print("="*70)
filas = leer_hoja("xl/worksheets/sheet1.xml")
print(f"Total filas: {len(filas)}")
for i, f in enumerate(filas[:15]):
    cols = sorted(f.keys(), key=lambda c: (len(c), c))
    datos = {c: f[c][:45] for c in cols if f[c]}
    print(f"Fila {i+1}: {datos}")

# --- CONVERSION: rango temporal y columnas Z+ ---
print()
print("="*70)
print("CONVERSION — estadística")
print("="*70)
conv = leer_hoja("xl/worksheets/sheet2.xml")
print(f"Total filas con datos: {len(conv)}")
header = conv[0]
cols = sorted(header.keys(), key=lambda c: (len(c), c))
print(f"Columnas ({len(cols)}): {[header[c] for c in cols]}")
meses = {}
anios = {}
for f in conv[1:]:
    y = f.get("X", "")
    m = f.get("Y", "")
    if y:
        anios[y] = anios.get(y, 0) + 1
    if m:
        meses[m] = meses.get(m, 0) + 1
print("Por año:", dict(sorted(anios.items())))
print("Por mes:", meses)
