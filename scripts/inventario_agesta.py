#!/usr/bin/env python3
"""Inventario de los 3 xlsx de ENCUESTA AGESTA: hojas, filas y columnas clave."""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

ARCHIVOS = [
    "/home/croman/Escritorio/BUYER PERSONA/ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx",
    "/home/croman/Escritorio/BUYER PERSONA/ENCUESTA AGESTA/2026 S07 RESULT ENC(M bruto) (1).xlsx",
    "/home/croman/Escritorio/BUYER PERSONA/ENCUESTA AGESTA/Grilla Enc Stream S29 2025 Release II vtas (1).xlsx",
]

def inventario(path):
    print(f"\n{'='*72}\n{path.split('/')[-1]}\n{'='*72}")
    z = zipfile.ZipFile(path)
    # shared strings
    strings = []
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.iter(NS + "si"):
            strings.append("".join(t.text or "" for t in si.iter(NS + "t")).strip())
    except KeyError:
        pass
    # mapa de hojas
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.get("Id"): r.get("Target") for r in rels}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    for sh in wb.iter(NS + "sheet"):
        nombre = sh.get("name")
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id") or ""
        target = (rel_map.get(rid) or "").lstrip("/")
        if target and not target.startswith("xl/"):
            target = "xl/" + target
        try:
            root_hoja = ET.fromstring(z.read(target))
        except KeyError:
            print(f"  Hoja '{nombre}': no se pudo leer ({target})")
            continue
        n_filas = sum(1 for _ in root_hoja.iter(NS + "row"))
        # encabezados: primera fila con celdas
        header, fila2 = [], {}
        for row in root_hoja.iter(NS + "row"):
            vals = {}
            for c in row.iter(NS + "c"):
                ref = c.get("r") or ""
                col = re.match(r"[A-Z]+", ref).group() if ref else ""
                t = c.get("t")
                if t == "s":
                    v = c.find(NS + "v")
                    val = strings[int(v.text)] if v is not None and v.text else ""
                elif t == "inlineStr":
                    is_el = c.find(NS + "is")
                    val = "".join(x.text or "" for x in is_el.iter(NS + "t")) if is_el is not None else ""
                else:
                    v = c.find(NS + "v")
                    val = v.text if v is not None else ""
                vals[col] = (val or "").strip()
            if any(vals.values()):
                if not header:
                    header = vals
                else:
                    fila2 = vals
                    break
        cols = sorted(header.keys(), key=lambda c: (len(c), c))
        print(f"  Hoja '{nombre}' — {n_filas} filas")
        print(f"    Encabezados ({len(cols)}): {[header[c][:28] for c in cols[:22]]}")
        if cols:
            resto = [header[c][:20] for c in cols[22:44]]
            if resto:
                print(f"    Continuación: {resto}")
        if fila2:
            muestra = {c: fila2[c][:25] for c in sorted(fila2.keys(), key=lambda c: (len(c), c))[:10] if fila2[c]}
            print(f"    Fila 2 muestra: {muestra}")

for a in ARCHIVOS:
    inventario(a)
