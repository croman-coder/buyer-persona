---
tipo: proyecto-operativo
estado: sin empezar
disparador: Valentina (Marketing) pidio unidades 18-25 por marca el 2026-08-21
responsable: Croman
tags: [crm, datos, edad, buyer-persona, proceso]
actualizado: 2026-08-21
---

# Capturar la edad del comprador

## El problema, en una linea

Marketing pide segmentar ventas por edad y **no se puede**: el dato no existe en ningun sistema.

## Lo que se verifico el 2026-08-21

| Fuente | Tiene edad? | Detalle |
| --- | --- | --- |
| ERP (`FacturacionUnidades-7343.xlsx`) | **No** | 29 columnas, ninguna de edad, nacimiento o cedula. Cero RUC y cero fechas de nacimiento en las 12.254 cadenas del archivo |
| Encuesta AGESTA | **No** | Tiene sexo derivado del nombre. Lo que parecia edad era *antiguedad* de la relacion |
| CRM Bitrix | **El campo existe, vacio** | ver abajo |

## El hallazgo que cambia el enfoque

Bitrix **ya tiene** el campo. Es `BIRTHDATE`, estandar en contactos, titulo "Fecha de nacimiento". No hay que crear nada.

```
contactos en el CRM:              50.334
con fecha de nacimiento cargada:       4
```

Cuatro. De cincuenta mil. Y los cuatro se cargaron a mano: tres por telefono (`SOURCE_ID: CALL`) y uno por web, entre febrero y junio de 2026.

**Esto no es un problema tecnico. La herramienta esta, nadie la usa.**

## Donde entran los datos hoy

El formulario de captura (`LANDING EXPO FORM`) pide nombre, email, telefono, marca, modelo, comentario y asesor. A Bitrix le manda cuatro campos: `NAME`, `LAST_NAME`, `PHONE`, `EMAIL`. La fecha de nacimiento no viaja porque no se pide.

## Donde conviene pedirla — y donde no

> [!warning] En el formulario de lead, NO
> Sumar un campo mas al formulario de captura baja la conversion, y la mayoria
> de los leads nunca compra. Se estaria pagando con leads perdidos un dato que
> solo importa de los que si compran.

**El momento correcto es la venta**, por dos razones: el vendedor ya esta pidiendo la cedula para la factura, asi que sumar la fecha no agrega friccion real; y a esa altura la persona ya decidio, no se va a caer por un campo mas.

Dos puntos concretos, en orden de facilidad:

1. **Al cerrar el negocio en Bitrix.** El campo existe; falta que sea visible y obligatorio en la ficha de contacto. Es configuracion de formulario en Bitrix, no desarrollo.
2. **En la entrega del PDI.** El circuito de preentrega ya recoge datos del cliente. Si la venta no lo capturo, es la segunda oportunidad antes de que la persona se vaya con el auto.

## Como medir si esta funcionando

La misma consulta que dio 4 hoy:

```
crm.contact.list?filter[>BIRTHDATE]=1900-01-01
```

Revisarla al mes. Si sigue en un digito, el proceso no prendio y hay que
entender por que antes de insistir.

## Cuando esto rinda

Recien con seis meses a un año de datos se puede responder lo que pidio
Valentina con numeros medidos en vez de estimados. Mientras tanto, lo que hay
es [[Unidades por marca y rango etario]] — que cruza ventas reales con alcance
de Meta y **es una estimacion, no una medicion**.

## Lo que falta decidir

- [ ] Quien configura el campo como obligatorio en Bitrix
- [ ] Como se le comunica a los vendedores, y quien
- [ ] Si se pide tambien en la entrega del PDI o solo en la venta
- [ ] Si vale la pena recuperar la edad de clientes viejos (la encuesta AGESTA
      podria preguntarla, ya tiene el canal armado)

Relacionado: [[Unidades por marca y rango etario]] · [[Ventas Reales - abril 2024 a abril 2026]] · [[Embudo Bitrix - ultimos 90 dias]]
