#!/usr/bin/env python3
"""Inspecciona los Excel de ventas en PC SRPY para identificar la base real."""
import re
import subprocess
import sys

ARCHIVOS = [
    "/home/croman/Escritorio/PC SRPY/Ventas + Origenes + ROI (1).xlsx",
    "/home/croman/Escritorio/PC SRPY/REPORTE SERGIO/Ventas + Origenes + ROI.xlsx",
]

for archivo in ARCHIVOS:
    print(f"\n{'='*70}\n{archivo}\n{'='*70}")
    # shared strings (los textos de las celdas)
    out = subprocess.run(
        ["unzip", "-p", archivo, "xl/sharedStrings.xml"],
        capture_output=True, text=True,
    ).stdout
    strings = re.findall(r"<t[^>]*>([^<]+)</t>", out)
    print("Primeros 50 textos:", strings[:50])
    print("Total textos únicos:", len(strings))
