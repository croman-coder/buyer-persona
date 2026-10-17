---
type: publicos
tags: [meta-ads, publicos, lista-de-clientes, uso-interno]
---
# 🎯 Públicos de compradores (listas de clientes)

> [!info] Qué es
> Listas de **compradores reales** del ERP subidas a Meta (mail y teléfono **cifrados**: Meta no los ve en claro) y su **público similar** en Paraguay: gente parecida a quien ya compró. Se arman con `scripts/publico_compradores.py`.
> Ningún dato de personas queda en este vault: solo cuántos, por qué se descartaron, de qué período y los IDs.

> [!warning] Reglas
> - Subir una lista necesita el OK de Croman. **Mitsubishi no se usa**: su base tiene los contactos de Nipon.
> - Se descartan las ventas a concesionarios, los mails de Santa Rosa y Nipon, los de relleno y todo mail o teléfono que aparezca en 3 ventas o más de la base (es de la empresa, de un vendedor o de relleno).
> - Usar el similar como **un conjunto aparte**, con su propio presupuesto, para compararlo con el público frío.
> - Desde mayo 2026 el ERP casi no trae mail ni teléfono: hasta que vuelvan esas columnas, la lista no suma compradores nuevos.

## Registro

### Jetour · 14-10-2026

| | |
|---|---|
| Cuenta | Jetour (`act_494721666377008`) |
| Compradores reales | **1012 personas** de 1040 ventas limpias (2227 ventas de la marca en la base) |
| Período de las compras | 2024-04-02 → 2026-08-07 · por año: 2024: 252, 2025: 510, 2026: 278 |
| Descartados (ventas) | venta sin ningún contacto limpio: 257 · teléfono repetido en 3 ventas o más: 254 · mail repetido en 3 ventas o más: 247 · mail de relleno: 100 · mail de Santa Rosa o de Nipon: 65 · venta a un concesionario: 52 |
| Cargados en Meta | 1037 filas · Meta las recibió: 1037 · inválidas: 0 |
| Lista de compradores | `120252322584340065` |
| Similar 1 % Paraguay | `120252322585290065` |
| Estado | Creados, **sin usar en ninguna campaña** todavía. Meta tarda unas horas en calcular el tamaño |

