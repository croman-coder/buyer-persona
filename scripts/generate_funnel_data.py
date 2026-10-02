#!/usr/bin/env python3
"""
Genera datos de ejemplo para cada etapa del embudo de ventas.

Crea archivos CSV en data/embudo/ con datos realistas de:
- Formularios web (leads)
- Test drives solicitados
- Conversaciones de WhatsApp
- Cotizaciones
- Visitas al showroom
- Encuestas de satisfacción
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# Reutilizar marcas y modelos del generador principal
MARCAS_MODELOS = {
    "Santa Rosa": ["Santa Rosa SR5 SUV", "Santa Rosa Frontera Pickup", "Santa Rosa Urban Sedan"],
    "Jetour": ["Jetour Dashing", "Jetour X70 Plus", "Jetour X90", "Jetour i-DM", "Jetour Travler"],
    "GWM": ["GWM Haval H6", "GWM Poer", "GWM Tank 300", "GWM Haval Jolion", "GWM Cannon"],
    "JAC": ["JAC T8 Pickup", "JAC JS4 Sedan", "JAC e-JS4 EV"],
    "Renault": ["Renault Kwid", "Renault Sandero", "Renault Duster", "Renault Stepway"],
    "Mitsubishi": ["Mitsubishi L200", "Mitsubishi Outlander", "Mitsubishi ASX", "Mitsubishi Lancer"],
    "Zeekr": ["Zeekr 001", "Zeekr X", "Zeekr 009", "Zeekr 7X", "Zeekr Mix"],
    "Leapmotor": ["Leapmotor C10", "Leapmotor T03", "Leapmotor C11", "Leapmotor C01"],
    "JMEV": ["JMEV EV2", "JMEV EV3", "JMEV EV5", "JMEV EX5"],
    "Soueast": ["Soueast DX3", "Soueast DX7", "Soueast S70"],
}

CIUDADES = ["Asunción", "Ciudad del Este", "Encarnación", "San Lorenzo", "Luque",
            "Capiatá", "Lambaré", "Fernando de la Mora", "Pedro Juan Caballero", "Coronel Oviedo"]

VENDEDORES = ["Carlos Vega", "María Torres", "José Méndez", "Lucía Ríos", "Pedro Cardozo",
              "Sofía Aldana", "Diego Vera", "Valeria Sosa"]

FUENTES_LEAD = ["web", "meta", "google", "instagram", "whatsapp", "showroom"]

NOMBRES = ["Juan", "Ana", "Pedro", "María", "Carlos", "Lucía", "José", "Valeria",
           "Diego", "Sofía", "Martín", "Camila", "Fernando", "Paula", "Andrés",
           "Gabriel", "Micaela", "Roberto", "Laura", "Ricardo"]


def get_all_modelos():
    modelos = []
    for marca, lista in MARCAS_MODELOS.items():
        for modelo in lista:
            modelos.append(modelo)
    return modelos


def random_fecha(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def gen_formularios_web(output_dir, fecha_start, fecha_end):
    """Genera leads de formularios web."""
    path = output_dir / "formularios_web.csv"
    modelos = get_all_modelos()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "nombre", "email", "telefono", "vehiculo_interes", "mensaje", "fuente"
        ])
        writer.writeheader()

        for _ in range(random.randint(180, 250)):
            nombre = random.choice(NOMBRES)
            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "nombre": f"{nombre} {random.choice(NOMBRES)}",
                "email": f"{nombre.lower()}{random.randint(10,99)}@gmail.com",
                "telefono": f"09{random.randint(61,99)}{random.randint(100000,999999)}",
                "vehiculo_interes": random.choice(modelos),
                "mensaje": random.choice([
                    "Me interesa este vehículo, quiero más info",
                    "Quiero saber el precio y financiación",
                    "Disponible para test drive?",
                    "Tienen stock?",
                    "Quiero que me llamen",
                ]),
                "fuente": random.choices(FUENTES_LEAD, weights=[30, 25, 20, 15, 10], k=1)[0],
            })
    print(f"  ✅ {path.name}: leads web generados")


def gen_test_drives(output_dir, fecha_start, fecha_end):
    """Genera solicitudes de test drive."""
    path = output_dir / "test_drives.csv"
    modelos = get_all_modelos()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "nombre", "email", "telefono", "vehiculo",
            "ciudad", "fecha_preferida", "estado"
        ])
        writer.writeheader()

        for _ in range(random.randint(80, 120)):
            nombre = random.choice(NOMBRES)
            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "nombre": f"{nombre} {random.choice(NOMBRES)}",
                "email": f"{nombre.lower()}{random.randint(10,99)}@gmail.com",
                "telefono": f"09{random.randint(61,99)}{random.randint(100000,999999)}",
                "vehiculo": random.choice(modelos),
                "ciudad": random.choice(CIUDADES),
                "fecha_preferida": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "estado": random.choices(
                    ["pendiente", "confirmado", "completado", "cancelado"],
                    weights=[15, 25, 50, 10], k=1
                )[0],
            })
    print(f"  ✅ {path.name}: test drives generados")


def gen_whatsapp(output_dir, fecha_start, fecha_end):
    """Genera conversaciones de WhatsApp."""
    path = output_dir / "whatsapp_conversaciones.csv"
    modelos = get_all_modelos()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "telefono", "nombre", "vehiculo_interes",
            "mensajes_enviados", "mensajes_recibidos", "estado", "resultado"
        ])
        writer.writeheader()

        for _ in range(random.randint(150, 220)):
            nombre = random.choice(NOMBRES)
            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "telefono": f"09{random.randint(61,99)}{random.randint(100000,999999)}",
                "nombre": f"{nombre} {random.choice(NOMBRES)}",
                "vehiculo_interes": random.choice(modelos),
                "mensajes_enviados": random.randint(2, 25),
                "mensajes_recibidos": random.randint(1, 15),
                "estado": random.choices(["activo", "cerrado", "perdido"], weights=[40, 45, 15], k=1)[0],
                "resultado": random.choices(
                    ["en_conversacion", "cotizo", "visito_showroom", "compro", "sin_respuesta"],
                    weights=[25, 25, 20, 15, 15], k=1
                )[0],
            })
    print(f"  ✅ {path.name}: conversaciones WhatsApp generadas")


def gen_cotizaciones(output_dir, fecha_start, fecha_end):
    """Genera cotizaciones de vehículos."""
    path = output_dir / "cotizaciones.csv"
    modelos = get_all_modelos()

    precios_base = {
        "Zeekr": (40000, 75000), "Mitsubishi": (28000, 55000),
        "GWM": (25000, 48000), "Jetour": (22000, 42000),
        "JAC": (20000, 38000), "Santa Rosa": (18000, 35000),
        "Leapmotor": (18000, 35000), "Renault": (15000, 32000),
        "Soueast": (16000, 30000), "JMEV": (15000, 28000),
    }

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "cliente", "vehiculo", "precio_cotizado",
            "vendedor", "dias_para_cerrar", "resultado"
        ])
        writer.writeheader()

        for _ in range(random.randint(100, 160)):
            modelo = random.choice(modelos)
            marca = modelo.split()[0]
            mn, mx = precios_base.get(marca, (15000, 50000))
            precio = round(random.uniform(mn, mx), 2)

            resultado = random.choices(
                ["vendido", "perdido", "en_proceso"],
                weights=[30, 25, 45], k=1
            )[0]

            dias = random.randint(1, 60) if resultado != "en_proceso" else 0

            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "cliente": f"{random.choice(NOMBRES)} {random.choice(NOMBRES)}",
                "vehiculo": modelo,
                "precio_cotizado": precio,
                "vendedor": random.choice(VENDEDORES),
                "dias_para_cerrar": dias,
                "resultado": resultado,
            })
    print(f"  ✅ {path.name}: cotizaciones generadas")


def gen_showroom(output_dir, fecha_start, fecha_end):
    """Genera visitas al showroom."""
    path = output_dir / "visitas_showroom.csv"
    modelos = get_all_modelos()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "cliente", "vehiculo_interes", "vendedor",
            "tiempo_visita_min", "resultado"
        ])
        writer.writeheader()

        for _ in range(random.randint(70, 110)):
            resultado = random.choices(
                ["compro", "no_compro", "pendiente"],
                weights=[20, 40, 40], k=1
            )[0]

            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "cliente": f"{random.choice(NOMBRES)} {random.choice(NOMBRES)}",
                "vehiculo_interes": random.choice(modelos),
                "vendedor": random.choice(VENDEDORES),
                "tiempo_visita_min": random.randint(15, 120),
                "resultado": resultado,
            })
    print(f"  ✅ {path.name}: visitas showroom generadas")


def gen_encuestas(output_dir, fecha_start, fecha_end):
    """Genera encuestas de satisfacción."""
    path = output_dir / "encuestas_satisfaccion.csv"
    modelos = get_all_modelos()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "cliente", "vehiculo", "score", "recomendaria", "comentario"
        ])
        writer.writeheader()

        comentarios_positivos = [
            "Excelente servicio, muy conforme!",
            "El vehículo superó mis expectativas.",
            "Atención de primera, recomendado.",
            "Muy buena experiencia de compra.",
        ]
        comentarios_neutros = [
            "Correcto, sin problemas.",
            "Cumplió con lo prometido.",
            "Servicio normal.",
        ]
        comentarios_negativos = [
            "Demoró mucho la entrega.",
            "El precio era diferente al cotizado.",
            "Poca variedad de colores.",
        ]

        for _ in range(random.randint(40, 70)):
            score = random.choices(
                list(range(1, 11)),
                weights=[1, 1, 2, 2, 3, 5, 8, 15, 25, 38], k=1
            )[0]

            if score >= 9:
                comentario = random.choice(comentarios_positivos)
                recomendaria = "si"
            elif score >= 7:
                comentario = random.choice(comentarios_neutros)
                recomendaria = random.choice(["si", "no"])
            else:
                comentario = random.choice(comentarios_negativos)
                recomendaria = "no"

            writer.writerow({
                "fecha": random_fecha(fecha_start, fecha_end).strftime("%Y-%m-%d"),
                "cliente": f"{random.choice(NOMBRES)} {random.choice(NOMBRES)}",
                "vehiculo": random.choice(modelos),
                "score": score,
                "recomendaria": recomendaria,
                "comentario": comentario,
            })
    print(f"  ✅ {path.name}: encuestas generadas")


def main():
    output_dir = Path("data/embudo")
    output_dir.mkdir(parents=True, exist_ok=True)

    fecha_start = datetime(2025, 1, 1)
    fecha_end = datetime(2025, 7, 15)

    print("📊 Generando datos de embudo de ejemplo...\n")

    gen_formularios_web(output_dir, fecha_start, fecha_end)
    gen_test_drives(output_dir, fecha_start, fecha_end)
    gen_whatsapp(output_dir, fecha_start, fecha_end)
    gen_cotizaciones(output_dir, fecha_start, fecha_end)
    gen_showroom(output_dir, fecha_start, fecha_end)
    gen_encuestas(output_dir, fecha_start, fecha_end)

    print(f"\n✅ Todos los datos generados en {output_dir}/")
    print("\n💡 Para activar el embudo en el sistema:")
    print("   1. En config/settings.yaml → funnel → enabled: true")
    print("   2. Activar cada sub-fuente (web_forms, test_drives, etc.)")
    print("   3. Ejecutar: python main.py --demo")


if __name__ == "__main__":
    main()