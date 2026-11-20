# Neon Grid - assets para Watch Face Studio

Watch Face Studio **no puede importar** un proyecto WFF ya hecho (solo abre sus propios
`.wfs`), asi que aqui van las capas sueltas y la especificacion exacta para reconstruir la
esfera visualmente en WFS. Todo esta a **480x480 px**.

## Archivos

| Archivo | Uso en WFS | Tamano |
|---|---|---|
| `bg_480.png` | Fondo (capa de imagen, a pantalla completa) | 480x480 |
| `hand_hour_480.png` | Aguja horaria - **pivote en el centro (240,240)** | 480x480 |
| `hand_minute_480.png` | Aguja minutera - pivote en el centro | 480x480 |
| `hand_second_480.png` | Segundero - pivote en el centro | 480x480 |
| `lbl_*.png` | Etiquetas fijas ya rasterizadas (MSG, BPM, PASOS, BAT, EVENT) | recortadas |
| `preview_480.png` | Vista previa para el selector de esferas | 480x480 |

## Paleta

| Rol | Hex |
|---|---|
| Fondo / base | `#05080E` |
| Cian neon | `#22E7FF` |
| Magenta | `#FF2A6D` |
| Violeta | `#A24BFF` |
| Texto secundario | `#8FB6C9` |

Tipografia monoespaciada en negrita con letter-spacing amplio (0.02 - 0.14 EM).

## Posiciones (480x480, origen arriba-izquierda)

La hora va **anclada por la derecha en x=326**: asi la columna de segundos nunca choca,
tenga la hora uno o dos digitos.

| Elemento | Tipo en WFS | Anclaje | Tamano | Color |
|---|---|---|---|---|
| Fondo | Imagen | x=0, y=0 | 480x480 | - |
| Aguja horaria | Hand | centro (240,240) | largo 112 px | cian |
| Aguja minutera | Hand | centro (240,240) | largo 162 px | cian |
| Segundero | Hand | centro (240,240) | largo 178 px | magenta |
| Hora (12 h) | Texto | derecha en x=326, y=302 | 66 px | blanco |
| Segundos | Texto | izquierda x=350, y=290 | 20 px | cian |
| AM/PM | Texto | izquierda x=346, y=316 | 13 px | cian |
| Fecha | Texto | centrado, y=380 | 26 px | magenta |
| Temperatura | Complicacion Weather | centrado, y=78 | 30 px | cian |
| Condicion clima | Texto | centrado, y=114 | 18 px | `#8FB6C9` |
| Max / min del dia | Texto | centrado, y=142 | 16 px | `#8FB6C9` |
| Etiqueta MSG | Imagen `lbl_msg` | x=150, y=160 | 20x7 | - |
| Valor MSG | Texto / Notificaciones | izquierda x=132, y=188 | 30 px | magenta |
| Etiqueta EVENT | Imagen `lbl_event` | x=330, y=154 | 32x7 | - |
| Evento - titulo | Complicacion (Short/Long text) | caja 262..418 x 156..178 | 12-13 px | `#8FB6C9` |
| Evento - texto | Complicacion | caja 262..418 x 178..210 | 16 px | violeta |
| Etiqueta BAT | Imagen `lbl_bat` | x=72, y=204 | 19x7 | - |
| Valor BAT | Texto / Bateria | izquierda x=52, y=228 | 30 px | cian |
| Etiqueta BPM | Imagen `lbl_bpm` | x=76, y=274 | 20x7 | - |
| Valor BPM | Texto / Ritmo cardiaco | izquierda x=52, y=300 | 30 px | magenta |
| Etiqueta PASOS | Imagen `lbl_pasos` | x=368, y=220 | 32x7 | - |
| Valor PASOS | Texto / Pasos | derecha hasta x=404, y=244 | 24 px | cian |
| Meta de pasos | Texto / Pasos (%) | derecha hasta x=404, y=266 | 13 px | `#8FB6C9` |

> El anillo punteado interior que tenia la v1 se **elimino**: dejaba un hueco muerto entre
> el y el bisel. Ahora la esfera solo lleva el bisel + las marcas de los 60 minutos.

## Pasos sugeridos en WFS

1. *New Project* -> dispositivo **Galaxy Watch 6** -> lienzo 480x480.
2. Importa `bg_480.png` como capa de imagen a pantalla completa.
3. Anade tres **Hand** con las imagenes de agujas (sin desplazar el pivote).
4. Anade los textos de hora, segundos, AM/PM y fecha con los anclajes de la tabla.
5. Coloca las etiquetas PNG y encima de cada una su dato: **Heart rate**, **Steps**
   (valor + porcentaje de meta), **Battery level**, **Notifications**, **Weather**
   (temperatura actual y maxima/minima).
6. La **complicacion de eventos** ocupa la caja de la derecha con dos lineas
   (titulo = hora del evento, texto = nombre). Acepta *Short text* y *Long text*.
7. Configura el **Always On**: fondo negro, agujas y hora en gris claro.
8. *Build* -> instala por Wi-Fi al reloj o exporta el APK/AAB.

## Notas

- El `%` de la bateria se escribe como texto fijo tras el valor.
- Si vas a publicar en Play, WFS genera un AAB firmado con tu clave; los APK de este
  repositorio estan firmados con una clave local de desarrollo.

## Condicion del clima (texto bajo la temperatura)

En el APK se resuelve con un `<Condition>` sobre `[WEATHER.CONDITION]` (entero). Mapeo:

| Valor | Condicion | Etiqueta |
|---|---|---|
| 1, 8 | CLEAR / SUNNY | DESPEJADO |
| 2, 14 | CLOUDY / PARTLY_CLOUDY | NUBLADO |
| 4, 6, 12 | HEAVY_RAIN / RAIN / LIGHT_RAIN | LLUVIA |
| 5, 7, 11 | HEAVY_SNOW / SNOW / LIGHT_SNOW | NIEVE |
| 3, 13 | FOG / MIST | NIEBLA |
| 9 | THUNDERSTORM | TORMENTA |
| 10 | SLEET | AGUANIEVE |
| 15 | WINDY | VIENTO |
| 0 / sin datos | UNKNOWN_VALUE | - |
## Medidores (arcos de la izquierda)

Los dos arcos **miden de verdad** (antes eran adorno):

| Arco | Zona | Rango de angulos | Expresion |
|---|---|---|---|
| Bateria | izquierda (7:30 a 10:00) | 246 -> 294 | `246 + 0.48 * [BATTERY_PERCENT]` |
| Meta de pasos | arriba-izquierda (10:00 a 11:20) | 300 -> 340 | `300 + 0.40 * [STEP_PERCENT]` |

Centro del circulo (240,240), diametro 410, grosor 4 px, cap ROUND.
Cada medidor lleva una pista de fondo al 20 % de alfa (`#33RRGGBB`) y el relleno a color
pleno. En WFS esto se hace con un arco y una expresion sobre su angulo final
(propiedad **End angle** = expresion).
## Toques (zonas interactivas)

Cada dato tiene una zona tactil invisible (`PartDraw` casi transparente + `<Launch target="..."/>`)
del tamano justo del numero, no todo el ancho del texto. Destinos **verificados en el reloj**:

| Dato | Zona (x,y,w,h) | Target | Abre |
|---|---|---|---|
| Temperatura | 196,52,90,54 | `com.samsung.android.watch.weather` | Clima |
| MSG | 124,160,70,56 | `com.whatsapp` | WhatsApp (lista de chats) |
| Bateria | 44,206,84,52 | `BATTERY_STATUS` | Ajustes de bateria |
| BPM | 60,272,76,52 | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.heartrate.view.measure.HeartRateMeasureActivity` | Medidor de pulso |
| Pasos | 326,228,84,52 | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.steps.view.StepsActivity` | Pantalla de pasos |
| Fecha | 146,352,190,46 | `com.samsung.android.calendar` | Calendario (dia) |
| Evento | ranura de complicacion | (lo gestiona el proveedor) | App del calendario |

Aprendizajes (probados uno por uno):

- Los atajos del sistema `HEALTH_HEART_RATE` y `CALENDAR` **no abren nada** en este reloj;
  `WEATHER` incluso lanza Play Store. `BATTERY_STATUS` y `MESSAGE` son los unicos utiles.
- Un **nombre de paquete** abre la app (`com.whatsapp`, `com.samsung.android.calendar`).
- El formato **`paquete/actividad`** funciona y permite abrir una pantalla concreta
  (imprescindible para el medidor de pulso y para la pantalla de pasos).
- `HeartRateActivity` no es lanzable directamente; hay que usar `HeartRateMeasureActivity`.