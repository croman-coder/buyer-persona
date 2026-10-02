#!/usr/bin/env python3
"""
Genera datos de ventas de ejemplo para probar el sistema.

Crea ``data/sample_sales/ventas.csv`` con 500 registros realistas que
incluyen múltiples marcas de vehículos, canales de venta, ciudades y
perfiles demográficos diversos.

Marcas: Santa Rosa, Jetour, GWM, JAC, Renault, Mitsubishi, Zeekr,
Leapmotor, JMEV y Soueast.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# Catálogo de modelos por marca
PRODUCTOS = {
    "Santa Rosa": [
        "Santa Rosa SR5 SUV", "Santa Rosa Frontera Pickup", "Santa Rosa Urban Sedan",
        "Santa Rosa_delivery Van", "Santa Rosa Family Van",
    ],
    "Jetour": [
        "Jetour Dashing", "Jetour X70 Plus", "Jetour X90",
        "Jetour i-DM", "Jetour Travler",
    ],
    "GWM": [
        "GWM Haval H6", "GWM Poer", "GWM Tank 300",
        "GWM Haval Jolion", "GWM Cannon",
    ],
    "JAC": [
        "JAC T8 Pickup", "JAC JS4 Sedan", "JAC e-JS4 EV",
        "JAC Refine S4", "JAC iEV 7S EV",
    ],
    "Renault": [
        "Renault Kwid", "Renault Sandero", "Renault Duster",
        "Renault Stepway", "Renault Oroch Pickup",
    ],
    "Mitsubishi": [
        "Mitsubishi L200", "Mitsubishi Outlander", "Mitsubishi ASX",
        "Mitsubishi Lancer", "Mitsubishi Montero Sport",
    ],
    "Zeekr": [
        "Zeekr 001", "Zeekr X", "Zeekr 009",
        "Zeekr 7X", "Zeekr Mix",
    ],
    "Leapmotor": [
        "Leapmotor C10", "Leapmotor T03", "Leapmotor C11",
        "Leapmotor C01", "Leapmotor A12",
    ],
    "JMEV": [
        "JMEV EV2", "JMEV EV3", "JMEV EV5",
        "JMEV EX5", "JMEV U5",
    ],
    "Soueast": [
        "Soueast DX3", "Soueast DX7", "Soueast S70",
        "Soueast A5翼舞", "Soueast V Cross",
    ],
}

# Rango de precios por marca (en USD)
PRECIOS_MARCA = {
    "Santa Rosa": (18000, 35000),
    "Jetour": (22000, 42000),
    "GWM": (25000, 48000),
    "JAC": (20000, 38000),
    "Renault": (15000, 32000),
    "Mitsubishi": (28000, 55000),
    "Zeekr": (40000, 75000),
    "Leapmotor": (18000, 35000),
    "JMEV": (15000, 28000),
    "Soueast": (16000, 30000),
}

# Categorías / segmentos de vehículo
CATEGORIAS = ["SUV", "Sedan", "Pickup", "Hatchback", "Furgoneta", "Eléctrico"]

# Mapeo aproximado de categoría por modelo (para distribución realista)
def obtener_categoria(producto: str) -> str:
    p = producto.lower()
    if "ev" in p or "eléctrico" in p or "ielectric" in p or "zeekr" in p or "leapmotor" in p or "jmev" in p:
        return "Eléctrico"
    if "pickup" in p or "poer" in p or "cannon" in p or "l200" in p or "oroch" in p or "t8" in p or "frontera" in p:
        return "Pickup"
    if "suv" in p or "haval" in p or "dashing" in p or "x70" in p or "x90" in p or "dx3" in p or "dx7" in p or "tank" in p or "outlander" in p or "asx" in p or "duster" in p or "jolion" in p or "c10" in p or "c11" in p or "montero" in p or "travler" in p or "7x" in p or "a12" in p or "sr5" in p or "s4" in p:
        return "SUV"
    if "sedan" in p or "js4" in p or "lancer" in p or "s70" in p or "kwid" in p or "sandero" in p or "c01" in p or "urban" in p:
        return "Sedan"
    if "van" in p or "delivery" in p or "family" in p or "refine" in p or "009" in p or "mix" in p:
        return "Furgoneta"
    if "stepway" in p or "t03" in p or "a5" in p or "v cross" in p or "hatchback" in p or "iEV 7S".lower() in p:
        return "Hatchback"
    return random.choice(CATEGORIAS)


# Canales de venta
CANALES = ["Showroom", "Marketplace", "Venta Directa", "Instagram Shop", "WhatsApp Business"]

# Ciudades
CIUDADES = ["Asunción", "Ciudad del Este", "Encarnación", "San Lorenzo",
            "Luque", "Capiatá", "Lambaré", "Fernando de la Mora",
            "Pedro Juan Caballero", "Coronel Oviedo"]

# Géneros
GENEROS = ["Femenino", "Masculino", "No binario", "Prefiere no decir"]

# Configuración de perfiles demográficos por categoría (segmentos)
PERFIL_CATEGORIA = {
    "Eléctrico": {"edad_min": 28, "edad_max": 55, "genero_pref": None},
    "SUV": {"edad_min": 30, "edad_max": 60, "genero_pref": None},
    "Pickup": {"edad_min": 28, "edad_max": 65, "genero_pref": "Masculino"},
    "Sedan": {"edad_min": 25, "edad_max": 55, "genero_pref": None},
    "Hatchback": {"edad_min": 20, "edad_max": 45, "genero_pref": None},
    "Furgoneta": {"edad_min": 32, "edad_max": 60, "genero_pref": None},
}

NOMBRES_EMAIL = ["ana", "carlos", "maria", "jose", "lucia", "pedro", "sofia",
                 "diego", "valeria", "martin", "camila", "fernando", "julia",
                 "andres", "paula", "ricardo", "laura", "gabriel", "micaela", "roberto"]


def generar_email(nombre: str, idx: int) -> str:
    dominios = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]
    return f"{nombre}{random.randint(10, 99)}@{random.choice(dominios)}"


def generar_precio(marca: str) -> float:
    """Genera un precio realista según la marca."""
    mn, mx = PRECIOS_MARCA.get(marca, (15000, 50000))
    return round(random.uniform(mn, mx), 2)


def main():
    output_dir = Path("data/sample_sales")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ventas.csv"

    # Todas las marcas disponibles
    marcas = list(PRODUCTOS.keys())

    total_registros = 500
    fecha_inicio = datetime(2025, 1, 1)
    fecha_fin = datetime(2025, 7, 15)

    filas = []

    for i in range(total_registros):
        marca = random.choice(marcas)
        producto = random.choice(PRODUCTOS[marca])
        categoria = obtener_categoria(producto)
        perfil = PERFIL_CATEGORIA.get(categoria, {"edad_min": 25, "edad_max": 60, "genero_pref": None})

        # Generar edad según el perfil
        edad = random.randint(perfil["edad_min"], perfil["edad_max"])

        # Generar género (con sesgo si está definido)
        if perfil["genero_pref"]:
            genero = perfil["genero_pref"] if random.random() < 0.7 else random.choice(GENEROS)
        else:
            genero = random.choice(["Femenino", "Masculino"])

        ciudad = random.choice(CIUDADES)
        canal = random.choices(
            CANALES,
            weights=[35, 20, 25, 12, 8],  # Showroom más popular
            k=1,
        )[0]

        cantidad = 1  # Vehículos: normalmente 1 por transacción

        precio_unitario = generar_precio(marca)
        ingresos = round(precio_unitario * cantidad, 2)

        fecha = fecha_inicio + timedelta(
            seconds=random.randint(0, int((fecha_fin - fecha_inicio).total_seconds()))
        )

        email = generar_email(random.choice(NOMBRES_EMAIL), i)

        filas.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "producto": producto,
            "marca": marca,
            "categoria": categoria,
            "cantidad": cantidad,
            "ingresos": ingresos,
            "email_cliente": email,
            "edad_cliente": edad,
            "genero_cliente": genero,
            "ciudad_cliente": ciudad,
            "canal": canal,
        })

    # Ordenar por fecha
    filas.sort(key=lambda x: x["fecha"])

    # Escribir CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "producto", "marca", "categoria", "cantidad", "ingresos",
            "email_cliente", "edad_cliente", "genero_cliente", "ciudad_cliente", "canal"
        ])
        writer.writeheader()
        writer.writerows(filas)

    print(f"✅ Generados {len(filas)} registros en {output_path}")

    # Mostrar resumen
    from collections import Counter
    cat_counts = Counter(f["categoria"] for f in filas)
    canal_counts = Counter(f["canal"] for f in filas)
    marca_counts = Counter(f["producto"].split()[0] for f in filas)

    print("\n📊 Distribución por marca:")
    for marca, count in marca_counts.most_common():
        print(f"   {marca}: {count} ventas")

    print("\n📊 Distribución por categoría (segmento):")
    for cat, count in cat_counts.most_common():
        print(f"   {cat}: {count} ventas")

    print("\n📊 Distribución por canal:")
    for ch, count in canal_counts.most_common():
        print(f"   {ch}: {count} ventas")

    total_ingresos = sum(f["ingresos"] for f in filas)
    print(f"\n💰 Ingresos totales: ${total_ingresos:,.2f}")


if __name__ == "__main__":
    main()