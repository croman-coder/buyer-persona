#!/usr/bin/env python3
"""Analiza las 3 hojas del xlsx para encontrar la de ventas con clientes."""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ARCHIVO = "/home/croman/Escritorio/PC SRPY/Ventas + Origenes + ROI (1).xlsx"

z = zipfile.ZipFile(ARCHIVO)

strings = []
try:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", NS):
        strings.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])).strip())
except KeyError:
    pass

wb_rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rel_map = {r.get("Id"): r.get("Target") for r in wb_rels}
wb = ET.fromstring(z.read("xl/workbook.xml"))
hojas = {}
for sh in wb.iter("{%s}sheet" % NS["m"]):
    rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    target = rel_map[rid]
    if not target.startswith("/"):
        target = "xl/" + target.lstrip("/")
    else:
        target = target.lstrip("/")
    hojas[sh.get("name")] = target

def leer_hoja(path, max_rows=5):
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
            elif t == "inlineStr":
                is_el = c.find("m:is", NS)
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"])) if is_el is not None else ""
            else:
                v = c.find("m:v", NS)
                val = v.text if v is not None else ""
            vals[col] = (val or "").strip()
        filas.append(vals)
        if len(filas) >= max_rows:
            break
    return filas

for nombre, path in hojas.items():
    print(f"\n{'='*70}\nHOJA '{nombre}' ({path})\n{'='*70}")
    filas = leer_hoja(path, max_rows=4)
    for i, f in enumerate(filas[:2]):
        cols = sorted(f.keys(), key=lambda c: (len(c), c))
        print(f"Fila {i+1}:")
        for c in cols[:25]:
            val = f[c]
            if val:
                print(f"  {c}: {val[:55]!r}")
