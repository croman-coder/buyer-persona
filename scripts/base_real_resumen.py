#!/usr/bin/env python3
"""Agrega la base real: contactos utilizables por marca, fechas, clientes únicos."""
import re
import zipfile
from collections import Counter
from datetime import datetime
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PATH = "/home/croman/Escritorio/BUYER PERSONA/ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx"

z = zipfile.ZipFile(PATH)
strings = []
root = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in root.iter(NS + "si"):
    strings.append("".join(t.text or "" for t in si.iter(NS + "t")).strip())

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

EPOCH = datetime(1899, 12, 30)

por_marca_total = Counter()
por_marca_contacto = Counter()
clientes_unicos = set()
emails_validos = 0
telefonos_validos = 0
fechas = []
ventas_reales = 0

for row in root_hoja.iter(NS + "row"):
    vals = {}
    for c in row.iter(NS + "c"):
        ref = c.get("r") or ""
        col = re.match(r"[A-Z]+", ref).group() if ref else ""
        vals[col] = celda_val(c).strip()
    marca = vals.get("B", "")
    if not marca or marca == "Marca":  # encabezado o vacío
        continue
    por_marca_total[marca] += 1

    cliente = vals.get("AB", "")
    email = vals.get("AC", "")
    tel = re.sub(r"[^0-9]", "", vals.get("AD", ""))
    tiene_email = "@" in email and "." in email.split("@")[-1]
    tiene_tel = len(tel) >= 9
    if tiene_email:
        emails_validos += 1
    if tiene_tel:
        telefonos_validos += 1
    if tiene_email or tiene_tel:
        por_marca_contacto[marca] += 1
    if cliente:
        clientes_unicos.add(cliente.upper())
    try:
        n_reales = float(vals.get("J", "0") or 0)
        if n_reales > 0:
            ventas_reales += 1
    except ValueError:
        pass
    f = vals.get("A", "")
    if f.replace(".", "").isdigit() and len(f) >= 5:
        fechas.append(EPOCH + __import__("datetime").timedelta(days=int(float(f))))

print(f"Registros totales: {sum(por_marca_total.values())}")
print(f"Ventas 'Reales' (>0): {ventas_reales}")
print(f"Clientes únicos: {len(clientes_unicos)}")
print(f"Con email válido: {emails_validos}")
print(f"Con teléfono válido: {telefonos_validos}")
if fechas:
    print(f"Rango fechas: {min(fechas):%d/%m/%Y} → {max(fechas):%d/%m/%Y}")

print("\nPor marca (total → con contacto utilizable):")
for marca, tot in por_marca_total.most_common():
    print(f"  {marca:<12} {tot:>6} → {por_marca_contacto.get(marca, 0):>6} ({100*por_marca_contacto.get(marca,0)/tot:.0f}%)")
