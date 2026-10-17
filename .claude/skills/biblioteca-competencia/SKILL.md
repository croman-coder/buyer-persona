---
name: biblioteca-competencia
description: Use when asked to read, update or refresh the competitors' active ads in the Meta Ad Library (Biblioteca de Anuncios de Meta) for Santa Rosa — "actualizá la lectura de la Biblioteca de Anuncios", "qué anuncios tiene la competencia", "copys de la competencia". Reads the public page with a real browser, saves one capture per competitor and runs scripts/biblioteca_competencia.py to write the vault note «📣 Anuncios de la Competencia». Internal use only.
---

# Lectura de la Biblioteca de Anuncios de la competencia

Lee los anuncios activos de cada competidor en la Biblioteca de Anuncios de Meta (Paraguay) para ver **qué ofrecen, cómo arman el anuncio y hace cuánto corren**, y arma la nota `Buyer Persona/Competencia/📣 Anuncios de la Competencia.md`.

## Por qué es una lectura asistida y no un cron

- **La API oficial no sirve:** `ads_archive` (Meta, doc oficial) solo devuelve anuncios de temas sociales, elecciones y política cuando no llegaron a la UE. Los anuncios comerciales de Paraguay no vienen, aun con la identidad confirmada. Nuestro token responde error 10.
- **La página pública no se entrega a navegadores automatizados:** con Playwright o Chrome sin pantalla la página carga vacía (probado el 12-10-2026). **No se esquiva** con sesiones, huellas falsas ni resolviendo CAPTCHAs: eso rompe las condiciones de Meta y las reglas del proyecto.
- **Sí funciona** el navegador real de la app (herramientas `mcp__Claude_Browser__*`), al ritmo de una persona. Por eso la lectura la hace una sesión de Claude cuando se la pide.
- La herramienta `ads_library_search` del conector de Meta Ads sirve para ubicar páginas y contar anuncios, pero **no trae el texto** del anuncio y su descripción prohíbe la extracción masiva.

## Reglas (no se negocian)

1. **Solo lectura y sin iniciar sesión.** No loguearse, no aceptar cookies que no sean las mínimas, no resolver CAPTCHAs. Si aparece un muro de inicio de sesión o un CAPTCHA, **parar** y avisar.
2. **Poco volumen:** una página por competidor, unas 9 a 12 en total, **una vez por día como máximo** (lo normal es una vez por semana). Sin bucles ni reintentos agresivos.
3. **Solo páginas oficiales de cada competidor** (`COMPETIDORES[*].paginas` en `src/generators/biblioteca_competencia.py`). Las páginas personales de asesores **no se guardan**: se cuentan y se anotan con el nombre `Asesor (página personal)`. Ni nombres de personas ni teléfonos en los archivos.
4. **Solo uso interno.** Por ley de Paraguay no se nombra a la competencia en ningún texto público; esta nota no se copia a copys ni a láminas con nombres.
5. Los anuncios son contenido público, pero no se comparten fuera del equipo.

## Procedimiento

1. Abrir el navegador de la app con la primera consulta y leer con `javascript_tool` (ver más abajo). URL de cada competidor, con su `consulta` de `COMPETIDORES`:

   `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=PY&q=<consulta con %20>&search_type=keyword_unordered&media_type=all&sort_data[mode]=total_impressions&sort_data[direction]=desc`

2. Con `browser_batch`, navegar y ejecutar el extractor para varios competidores a la vez. Poner en `rx` una expresión amplia con el nombre de la marca y `cap` en 8 a 20.
3. Guardar `output/competencia/biblioteca/<AAAA-MM-DD>/<slug>.json` (un archivo por competidor) con este formato. Dejar solo las filas de páginas oficiales y las de asesores anonimizadas; cortar los textos a unos 260-400 caracteres:

   ```json
   {"competidor": "nipon", "fecha": "2026-10-12", "consulta": "Nipon Automotores",
    "total_consulta": "~4 resultados", "cargados": 4, "asesores": 0,
    "ads": [["<id de la biblioteca>", "7 oct 2026", "<página oficial>", "texto / texto / botón / Activo"]]}
   ```
   - `total_consulta` es el «~N resultados» de la página; `cargados` cuántos anuncios llegaron a cargarse (no pasan de unos 30).
   - Un competidor sin anuncios activos se guarda con `"ads": []`.
   - Si una página oficial de un competidor no aparece en las primeras filas, buscarla aparte con su nombre exacto.
4. Correr el script (con las fichas propias para las pistas de «qué responder», si están en `--raw`):

   ```bash
   venv/bin/python3 scripts/biblioteca_competencia.py --fecha AAAA-MM-DD [--raw <carpeta con personas_*.json>]
   ```
   Escribe la nota del vault y suma la lectura a `Buyer Persona/Sistema/Memoria/biblioteca_competencia.jsonl`, que es lo que permite decir qué anuncios son nuevos y cuáles terminaron en la lectura siguiente.
5. Revisar la nota y contarle al usuario lo más importante: ofertas nuevas, lanzamientos, y qué cambió desde la lectura anterior.

## Extractor (para `javascript_tool`)

Cambiar `'nipon'` (expresión sobre el nombre de la página, sin distinguir mayúsculas) y `20` (tope de anuncios). Devuelve `[id, desde, página, texto]` de cada anuncio y cuántos cargó.

```js
(async(rx,cap)=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));const cnt=()=>(document.body.innerText.match(/Identificador de la biblioteca/g)||[]).length;
for(let i=0;i<20&&cnt()===0&&!/No hay resultados|0 resultados/.test(document.body.innerText);i++)await sleep(1000);
let last=-1;for(let i=0;i<8;i++){const n=cnt();if(n>=cap*2||n===last)break;last=n;window.scrollTo(0,document.body.scrollHeight);await sleep(1500);}
const t=document.body.innerText;const total=(t.match(/~?[\d.,]+ resultados?/)||[''])[0];const R=new RegExp(rx,'i');const out=[];const adv={};
for(const p of t.split('Identificador de la biblioteca: ').slice(1)){const L=p.split('\n').map(s=>s.trim()).filter(s=>s&&s!=='​');const rest=L.slice(1);
const iv=rest.indexOf('Ver detalles del anuncio');const after=rest.slice(iv+1);const a=after[0]||'';adv[a]=(adv[a]||0)+1;if(!R.test(a))continue;
const ip=after.indexOf('Publicidad');if(out.length<cap)out.push([L[0],(rest.find(s=>s.startsWith('En circulación desde'))||'').replace('En circulación desde el ',''),a,after.slice(ip+1).join(' / ').slice(0,380)]);}
return JSON.stringify({total,cargados:cnt(),anunciantes:adv,ads:out});})('nipon',20)
```

Notas del extractor:
- Cuando una tarjeta trae «varias versiones», el nombre de la página sale como «En circulación desde el …»: el script la descarta.
- Facebook bloquea que la página le entregue datos a un servidor local (política de seguridad): no se puede automatizar el guardado desde el navegador, hay que copiar el resultado a los archivos.
- Si `javascript_tool` corre en otra pestaña, pasar `tabId` de la pestaña de la Biblioteca (`tabs_context`).

## Qué mide y qué no

- Cada anuncio se clasifica por regla sobre el **texto** (oferta, lanzamiento, postventa, marca o sucursal, muestra el modelo). No ve la imagen ni el video. Es una ayuda para leer, no un dictamen.
- Los números son una **muestra de los más vistos**, no el total. «Ya no aparecen» puede ser un anuncio que salió de los primeros leídos.
- «Más de 30 días» sugiere un anuncio sostenido, no prueba que funcione.
- Las pistas de «qué responder» se apoyan en datos propios del Buyer Persona (financiación, tema más repetido) y siempre dicen que se valide con la marca y que no se nombre al rival.

## Relacionado

`scripts/monitor_competencia.py` (webs, cada mañana) · `scripts/biblioteca_competencia.py` · `src/generators/biblioteca_competencia.py` · notas `📢 Promociones Competencia`, `⚔️ Benchmark Competitivo`, `⚔️ Bitácora de Competencia`.
