#!/usr/bin/env python3
"""Análisis de ventas reales + ad creatives para informe competitivo."""
import pandas as pd
import json
import csv
from collections import Counter

# === 1. VENTAS REALES ===
df = pd.read_csv("/home/croman/Escritorio/BUYER PERSONA/data/sample_sales/ventas.csv")

print("=" * 60)
print("ANÁLISIS DE VENTAS REALES - SANTA ROSA AUTOMOTORES")
print("=" * 60)
print(f"\nTotal ventas: {len(df)}")
print(f"Ingresos totales: ${df['ingresos'].sum():,.0f}")
print(f"Ticket promedio: ${df['ingresos'].mean():,.0f}")
print(f"Edad media: {df['edad_cliente'].mean():.1f} | Mediana: {df['edad_cliente'].median():.0f} | Rango: {df['edad_cliente'].min()}-{df['edad_cliente'].max()}")

print("\n--- GÉNERO ---")
for g, c in df['genero_cliente'].value_counts().items():
    print(f"  {g}: {c} ({c/len(df)*100:.1f}%)")

print("\n--- TOP 15 CIUDADES ---")
for city, c in df['ciudad_cliente'].value_counts().head(15).items():
    print(f"  {city}: {c} ({c/len(df)*100:.1f}%)")

print("\n--- CANALES DE VENTA ---")
for ch, c in df['canal'].value_counts().items():
    print(f"  {ch}: {c} ({c/len(df)*100:.1f}%)")

print("\n--- POR MARCA ---")
marca = df.groupby('marca').agg(
    ventas=('cantidad', 'count'),
    ingresos=('ingresos', 'sum'),
    ticket=('ingresos', 'mean'),
    edad=('edad_cliente', 'mean')
).sort_values('ingresos', ascending=False)
print(f"{'Marca':<15} {'Vtas':>5} {'Ingresos':>12} {'Ticket':>10} {'Edad':>6}")
for idx, row in marca.iterrows():
    print(f"{idx:<15} {row['ventas']:>5} ${row['ingresos']:>10,.0f} ${row['ticket']:>8,.0f} {row['edad']:>5.1f}")

print("\n--- POR CATEGORÍA ---")
cat = df.groupby('categoria').agg(
    ventas=('cantidad', 'count'),
    ingresos=('ingresos', 'sum'),
    ticket=('ingresos', 'mean'),
    edad=('edad_cliente', 'mean')
).sort_values('ventas', ascending=False)
print(f"{'Categoría':<15} {'Vtas':>5} {'Ingresos':>12} {'Ticket':>10} {'Edad':>6}")
for idx, row in cat.iterrows():
    print(f"{idx:<15} {row['ventas']:>5} ${row['ingresos']:>10,.0f} ${row['ticket']:>8,.0f} {row['edad']:>5.1f}")

print("\n--- TOP 20 PRODUCTOS ---")
prod = df.groupby(['marca', 'producto']).agg(
    ventas=('cantidad', 'count'),
    ticket=('ingresos', 'mean')
).sort_values('ventas', ascending=False).head(20)
for idx, row in prod.iterrows():
    print(f"  {idx[0]:<12} {idx[1]:<30} {row['ventas']:>3} ventas  ${row['ticket']:>8,.0f}")

print("\n--- CANAL x MARCA ---")
ct = pd.crosstab(df['marca'], df['canal'], margins=True)
print(ct.to_string())

print("\n--- CATEGORÍA x GÉNERO ---")
ct2 = pd.crosstab(df['categoria'], df['genero_cliente'], margins=True)
print(ct2.to_string())

# === 2. AD CREATIVES ===
print("\n" + "=" * 60)
print("ANÁLISIS DE AD CREATIVES (ANUNCIOS PROPIOS)")
print("=" * 60)

with open("/home/croman/Escritorio/BUYER PERSONA/output/raw/ad_creatives.json", "r") as f:
    ads = json.load(f)

total_ads = 0
status_counts = Counter()
cta_counts = Counter()
brands = list(ads.keys())
print(f"\nMarcas con anuncios: {brands}")

for brand, brand_ads in ads.items():
    total_ads += len(brand_ads)
    for ad in brand_ads:
        status_counts[ad.get('status', 'UNKNOWN')] += 1
        cta_counts[ad.get('cta', 'UNKNOWN')] += 1

print(f"Total anuncios analizados: {total_ads}")
print(f"\nPor estado:")
for s, c in status_counts.most_common():
    print(f"  {s}: {c}")

print(f"\nPor CTA (call-to-action):")
for cta, c in cta_counts.most_common():
    print(f"  {cta}: {c}")

print(f"\nAnuncios por marca:")
for brand in brands:
    active = sum(1 for a in ads[brand] if a.get('status') == 'ACTIVE')
    paused = sum(1 for a in ads[brand] if a.get('status') == 'PAUSED')
    print(f"  {brand}: {len(ads[brand])} total ({active} activos, {paused} pausados)")

# Sample de creatividades exitosas
print("\n--- MUESTRA DE ANUNCIOS ACTIVOS (títulos y copy) ---")
count = 0
for brand, brand_ads in ads.items():
    for ad in brand_ads:
        if ad.get('status') == 'ACTIVE' and count < 15:
            print(f"\n  [{brand}] {ad.get('ad_name', '?')}")
            print(f"  Título: {ad.get('title', '?')}")
            body = ad.get('body', '?')[:200]
            print(f"  Copy: {body}...")
            print(f"  CTA: {ad.get('cta', '?')} | Imagen: {ad.get('has_image', False)}")
            count += 1

print("\n" + "=" * 60)
print("ANÁLISIS COMPLETO")
print("=" * 60)
