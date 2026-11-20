# Traspaso de proyecto — Neon Grid (carátula Galaxy Watch 6)

Documento de continuación. Estado a fecha de este traspaso. Todo lo que aquí se
describe está verificado contra el reloj real o contra el binario de Watch Face
Studio 1.9.9, salvo lo marcado como **pendiente**.

Repositorio: <https://github.com/alejozd/neon-grid-watchface> (público, rama `main`).

---

## 1. Resumen en dos líneas

Hay una **carátula real, instalada y funcionando en el reloj** (formato WFF,
APK firmado, compilada sin Gradle). Y hay un **proyecto de Watch Face Studio
completo y verificado**: fondo, agujas, arcos-medidor, etiquetas, todos los
textos de datos, la ranura de complicación de evento, la hora mundial y las
zonas táctiles; renderizado y validado con el modo de prueba automático de WFS y
con el XML WFF que genera al compilar.

**Cerrado**: el diseño actual se queda como está. Se exploraron seis
distribuciones y tres rediseños más (sección 8) y no se adoptó ninguno; quedan
los bocetos y los scripts por si en el futuro se quiere retomar.

---

## 2. Carátula del reloj (WFF) — TERMINADA Y VERIFICADA

### Qué es
APK de recursos (sin código) en Watch Face Format v2, instalado y probado en un
**Galaxy Watch 6 / SM-R940, Wear OS 6, 480×480**.

### Paquetes y APK
| Variante | Paquete | APK |
|---|---|---|
| Neon (cian) | `com.relog.neongrid` | `build/NeonGrid-wearos5.apk` (SDK 34) |
| Neon, Wear OS 4 | `com.relog.neongrid` | `build/NeonGrid-wearos4.apk` (SDK 33) |
| Oro | `com.relog.neongrid.gold` | `build/NeonGrid-gold-wearos5.apk` |
| Hielo | `com.relog.neongrid.ice` | `build/NeonGrid-ice-wearos5.apk` |

Versión actual: **2.4** (versionCode **32**, instalado y activo en el reloj).
Firma: `build/keystore/cyber.jks` (alias `cyber`, pass `cyberwatch`; clave de
desarrollo, no para Play).

### Contenido de la esfera
Hora 12 h en cian (66 px, anclada a la derecha en x=326), AM/PM, segundero,
fecha 26 px (y=366), temperatura 30 px, condición, máx/mín, contador MSG,
ranura de evento (complicación), batería %, pulso, pasos + %, dos arcos-medidor
reales (batería 246→294, pasos 300→340), etiquetas de 13 px y la **hora mundial**
centrada bajo la fecha (y=400).

La hora mundial es **texto plano**: `BCN` en gris + la hora calculada
(ver 4.12) en cian, y **tocar la línea abre la app de reloj mundial**
(`WorldClockMainActivity`), que es la forma de consultar/añadir otras ciudades.

Se intentó convertirla en ranura de complicación (`slotId="3"`) para que el
usuario eligiera ciudad. **No funcionó y se revirtió** (ver 4.13): con
`DefaultProviderPolicy defaultSystemProvider="WORLD_CLOCK"` el sistema enlazaba
un proveedor que pintaba un marcador sin ciudad (`12:00p.m.`) en vez de la hora,
y al quitar la política el runtime se caía y el reloj volvía a la esfera de
fábrica. La función `world_clock_slot_block()` queda en el generador, sin usar,
como punto de partida para retomarlo.

El bloque del clima (temperatura y máx/mín) va dentro de un `<Condition>` sobre
`[WEATHER.IS_AVAILABLE]`; cuando el teléfono no ha enviado datos meteorológicos
el runtime devuelve 0 y la esfera mostraba "0° / 0°", ahora muestra un guion.

Manecillas: agujas `blade` (afiladas, con espina luminosa y muesca cerca de la
punta) y segundero `needle` con contrapeso magenta; la base queda escondida tras
el eje. La ranura de evento se subió: caja y=148..202 y las dos líneas más
juntas (título 0..24, texto violeta 22..52) — antes el morado caía demasiado
abajo.

### Toques verificados en el reloj (`dumpsys window` tras cada toque)
| Zona | Target | Abre |
|---|---|---|
| Temperatura | `com.samsung.android.watch.weather` | Clima |
| MSG | `com.whatsapp` | WhatsApp (lista de chats) |
| Batería | `BATTERY_STATUS` | Ajustes de batería |
| Pulso | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.heartrate.view.HeartRateActivity` | Pantalla de pulso con el botón **Medir** |
| Pasos | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.steps.view.StepsActivity` | Pantalla de pasos |
| Fecha | `com.samsung.android.calendar` | Calendario (día) |
| Hora mundial | `com.samsung.android.watch.worldclock/com.samsung.android.watch.worldclock.activity.WorldClockMainActivity` | App de reloj mundial (consultar otras ciudades) |

Notas: los atajos oficiales `HEALTH_HEART_RATE` y `CALENDAR` **no funcionan** en
este reloj y `WEATHER` abría Play Store. El formato `paquete/actividad` sí
funciona en `<Launch target="…">` y es imprescindible para pulso y pasos.
`HeartRateMeasureActivity` **inicia la medición sola**; `HeartRateActivity` abre
la pantalla con el botón Medir (es la elegida).

### Pipeline de compilación
```powershell
# 1. arte (escribe design/out/*)
python design\render.py --palette neon            # gold: --palette gold --suffix=-gold
# 2. XML + recursos del APK (watchface/)
python tools\gen_watchface.py --format 2 --palette neon --package com.relog.neongrid --label "Neon Grid" --device-utc-offset -5
# 3. APK firmado (aapt2 + zipalign + apksigner, sin Gradle ni internet)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -MinSdk 34 -VersionName "2.4"
# 4. instalar y probar
adb -s <serial> install -r build\NeonGrid-wearos5.apk
```
`--format 1` = WFF v1 (Wear OS 4); `--format 2` = v2 (Wear OS 5/6).

### Limitaciones conocidas
- Nunca se pudo verificar visualmente la capa **Always-On** (`screencap` sale
  negro en reposo y el AOD está desactivado en el reloj).
- Los arcos son medidores reales, pero la aguja de los segundos obliga a
  redibujar cada segundo (consumo normal, como cualquier esfera con segundero).

---

## 3. Proyecto de Watch Face Studio — COMPLETO Y VERIFICADO

### Qué hay
`wfs-project/NeonGrid.wfs` se abre en WFS 1.9.9 sin errores y **renderiza la
esfera entera** (verificado con el modo de prueba, ver 4.7). Capas, de abajo
arriba:

- Lienzo **450×450** circular.
- `bg` — el fondo (`neon_bg.png`).
- `gauge_battery`, `gauge_steps` — dos `progressBar` circulares reales: arco cian
  246→294 con `[BATT_PER]` y arco magenta 300→340 con `[SC_PER]`, pista de fondo
  al 20 % de opacidad. WFS los exporta como dos `<Arc>` con `<Transform
  target="endAngle">`, igual que la carátula WFF.
- Grupo `Hands` (analogClock) con `hour`, `minute`, `second` (28/26/30 × 450).
- Etiquetas rasterizadas `lbl_bat`, `lbl_bpm`, `lbl_pasos`, `lbl_msg`,
  `lbl_event` (los PNG de `design/out/labels`).
- Datos: `time` (HH:MM 12 h), `sec`, `ampm`, `date`, `temp`, `cond`, `tminmax`,
  `msg_v`, `bat_v`, `hr_v`, `steps_v`, `steps_pct`.
- `event_slot` — ranura de complicación `line`, caja 246,146,146,51, proveedor
  por defecto `NEXT_EVENT`, dos líneas: título (hora del evento, `#8FB6C9`,
  11 px) y texto (nombre, `#A24BFF`, 15 px). WFS la compila a
  `<ComplicationSlot supportedTypes="SHORT_TEXT">` con tres `<Compare>`
  (sin título, con icono, con título) y `<Default>`.
- Seis zonas táctiles invisibles (`drawEllipse` al 1 % de alfa) con `<Launch>` a
  los mismos destinos verificados en el reloj.

Capturas del render real de WFS: `build/wfs-render.png` (normal) y
`build/wfs-aod.png` (Always-On). El XML que genera WFS está en
`build/wfs-generated.xml`.

Valores por defecto del modo de prueba (los del propio WFS): 10:08:32, 25 °C,
despejado, batería 100 %, 3457 pasos (34 %), 89 ppm, 0 notificaciones, evento a
las 11:00.

### Cómo se genera
```powershell
python tools\repack_wfs.py       # empaquetado + sello  (usar este)
python tools\check_wfs.py        # invariantes del ZIP/modelo
tools\test_wfs.ps1               # modo de prueba de WFS: render + XML + resumen
```
`repack_wfs.py` importa `build_model()`, `hand_crop()` y `strings_xml()` de
`make_wfs_project.py` y escribe `wfs-project/NeonGrid.wfs`.
`make_wfs_project.py` por sí solo **no** añade el sello final, así que el archivo
bueno es el que produce `repack_wfs.py`.

El modelo se construye por *cirugía de plantillas*: los nodos `text` y
`progressBar` se clonan de `Weather_health_D_C.wfs`, la escena, el fondo, las
agujas y la zona táctil de `Minimal_classic_W_B.wfs`, y la ranura de
complicación de `Large_letters_D_C.wfs` (es la única de ejemplo con una
disposición de dos líneas). Después se reescriben geometría, fuente, colores,
expresiones y el grafo de ids (`reid_slot()` vuelve a enlazar `clipper` y los
`linkedElementId` de `categories.shortText/shortTitle/icon`).

### Referencias de coordenadas
`wfs-assets/SPEC.md` tiene la tabla completa de posiciones **a 480×480**.
`design/out/layout.json` es la fuente de verdad que usa el generador, y todo se
escala por **450/480 = 0.9375**.

---

## 4. Formato `.wfs`: todo lo descubierto (esto es lo valioso)

WFS **no puede importar** un proyecto WFF. El `.wfs` es un ZIP propio. Se
descubrió todo por ingeniería inversa contra los proyectos de ejemplo que trae
WFS instalado:

`C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio\tools\wfs_samples\*.wfs`

### 4.1 Estructura del ZIP
```
honeyface.json            <- PRIMERA entrada, el modelo del proyecto
latest_preview.png
res/                      <- entradas de carpeta (comprimidas en STORE)
res/drawable-nodpi/*.png  <- las capas
res/values/strings.xml
res/xml/watch_face*.xml
```
Python (`zipfile`) no escribe el flag UTF-8 (`0x0800`) que sí llevan los
originales; `tools/patch_wfs_flags.py` lo parchea en las cabeceras locales y
centrales. Es opcional, pero se dejó igual que el original.

### 4.2 El sello final (causa de "Invalid project file.")
WFS **no valida el ZIP**: mira los **últimos bytes del archivo**. La función
`getProjectFileType()` hace `endsWith("normal_watchface")` (o `normal_honeyface`;
`encrypt_*` si está cifrado). El archivo debe terminar exactamente con:

```
\x05\x00\x00\x00normal_watchface
```
`repack_wfs.py` copia esos 20 bytes del proyecto original y los añade al final.
**Sin esto, WFS dice "Invalid project file." aunque el ZIP sea perfecto.**

### 4.3 Tamaño de lienzo (causa de "Unsupported Project Size")
WFS 1.9.9 **solo acepta 450×450**. Los 12 proyectos de ejemplo son 450×450 y el
diálogo de compilación recomienda PNG de 450×450. Con 480×480 dice
"Unsupported Project Size (480 x 480)".
Deben coincidir **todos** estos sitios:
`settings.width/height`, grupo raíz `scene[0]`, nodo `analogClock`,
`res/xml/watch_face_shapes.xml`, la preview y las imágenes de las capas.

### 4.4 `conditionalLine` obligatorio (causa de la ventana en blanco)
Cada nodo **debe** llevar su bloque `conditionalLine` con `activatedCondition`.
Si falta, el renderer de React revienta y la ventana queda en negro. El error
queda en el log:

```
%APPDATA%\WatchFaceStudio\dump\renderer.log
TypeError: Cannot read properties of undefined (reading 'activatedCondition')
    at useConditionState
```
**Ese log es la mejor herramienta de depuración**: cada fallo de apertura deja
traza allí. `main.log` casi no se escribe.

### 4.5 Agujas: franja alta y estrecha
WFS **estira la imagen al tamaño de la caja del nodo**. Las agujas del ejemplo
son **40×450** (alto del lienzo, ancho de la aguja) con la caja igual a la imagen
y pivote **50 %/50 %** (que cae en el centro del dial). Si se le pasa un cuadrado
450×450, la aguja se estira a una mancha enorme; si se le pasa el recorte del
`.xml` (18×128), aparece como una línea en el centro.

`hand_crop()` en `make_wfs_project.py` calcula ese recorte (alto completo, ancho
de la aguja + 6 px de margen) y escala a 450.

### 4.6 Rotación de las agujas: CONFIRMADO
El editor de WFS muestra las agujas a las 12 en punto (rotación 0) y en el
proyecto de ejemplo de Samsung también están guardadas con rotación 0. La
rotación por hora **se aplica al renderizar**: en la captura del modo de prueba
(`build/wfs-render.png`, hora 10:08:32) las agujas están a las 10:08 y el
segundero apunta a los 32 s. No hay nada que corregir en el nodo `analogClock`.

### 4.7 El modo de prueba de WFS (la herramienta que faltaba)
WFS 1.9.9 trae un modo headless **no documentado** que abre proyectos, los
renderiza y (opcionalmente) los compila sin tocar la interfaz:

```powershell
$env:ELECTRON_RUN_AS_NODE = $null      # si no, Electron arranca como Node
& "$env:LOCALAPPDATA\Programs\WatchFaceStudio\WatchFaceStudio.exe" `
    --test --wfs=<proyecto.wfs> --out=<carpeta> --user-data-dir=<perfil> [--build]
```

Deja en `<carpeta>`:

| Archivo | Qué es |
|---|---|
| `<proyecto>.preview.png` | render normal (450×450) |
| `<proyecto>.aod.png` | render Always-On + análisis de burn-in |
| `<proyecto>.xml` | el XML WFF que generaría al compilar |
| `testmode-summary.json` | `status` success/failed, `stage`, `message`, `durationMs` |

**Cuatro trampas, todas sufridas:**

1. `ELECTRON_RUN_AS_NODE=1` en el entorno (lo pone el harness) hace que el exe
   corra como Node y conteste `bad option: --wfs=...`. Hay que borrarla.
2. Compartir `%APPDATA%` con una instancia abierta hace que Chromium bloquee el
   perfil: el modo de prueba termina con el resumen vacío y `items: []`. Usar
   siempre `--user-data-dir` propio.
3. Necesita escribir en `%APPDATA%` y en su directorio de instalación; con el
   sandbox de archivos de DSH la app aborta al arrancar (`0x80000003`). Correr
   con `danger-full-access`.
4. `--build` compila el **AAB** (con `tools/common/key/debug.keystore`), no un
   APK instalable por adb.

Envoltorio listo para usar: `tools/test_wfs.ps1` (repack + prueba + resumen).

### 4.8 Expresiones y etiquetas de datos
Los textos se guardan como **segmentos**: `categories.text.properties.text.value`
es la plantilla editable (`([BATT_PER])%`) y `.expression` la lista de segmentos
`{"format":"expression"|"string", value, result, resultFormat}`.

Etiquetas que el motor entiende (sacadas de `app.asar`, ver
`tools/debug/debug_app_tags.py` y `debug_app_context.py`):

| Uso | Etiqueta |
|---|---|
| Hora / minutos / segundos | `[HOUR_1_12]`, `[HOUR_0_23]`, `[HOUR_1_12_Z]`, `[MIN]`, `[MIN_Z]`, `[SEC]`, `[SEC_Z]`, `[AMPM]`, `[IS_24H]` |
| Fecha | `[DAY_1_31]`, `[DAY_1_31_Z]`, `[DAY_WEEK_S]`, `[DAY_WEEK_F]`, `[MON_S]`, `[MON_F]`, `[MON_Z]`, `[YEAR]` |
| Batería / notificaciones | `[BATT_PER]`, `[BATT_IS_CHARGE]`, `[BATT_IS_LOW]`, `[UNREAD_NC]` |
| Salud | `[HR]`, `[HR_Z]`, `[SC]`, `[SC_GOAL]`, `[SC_PER]` |
| Clima | `[WTHR_TEM]`, `[WTHR_DAY_TEM_HIGH]`, `[WTHR_DAY_TEM_LOW]`, `[WTHR_COND]`, `[WTHR_COND_NAME]`, `[WTHR_UV_INDEX]`, `[WTHR_IS_AVAIL]` |

Hallazgos:

- `hourFormat` acepta `"12"`, `"24"` y `"SYNC_TO_DEVICE"`; `timeFormat` acepta
  `h`, `hm`, `hms`, `m`, `s`… pero **su plantilla automática no permite hora sin
  cero y minutos con cero a la vez**. Por eso la hora se hace con un nodo `text`
  de tres segmentos: `[HOUR_1_12]` + `":"` + `[MIN_Z]`.
- El operador **`||` no funciona** en el evaluador del editor (WFS sí lo usa en
  las condiciones que genera, pero es otro evaluador). Una cadena con `||` cae
  siempre al valor por defecto. La condición del clima se resuelve con un
  ternario anidado por código (15 comparaciones sueltas, sin operadores
  lógicos) y se ve correctamente: `DESPEJADO` con el clima de ejemplo.
- `[WTHR_COND_NAME]` no se usa: en este firmware renderiza vacío (mismo problema
  que `WEATHER.CONDITION_NAME` en WFF).
- `letterSpacing` se guarda como **porcentaje**: `em * 100`. WFS escribe
  `letterSpacing="0.02121"` a partir de 2.121.

### 4.9 Acciones `openApp`: sí aceptan paquete/actividad
WFS sólo ofrece 8 apps del sistema en el desplegable, pero el modelo guarda el
`customAppId` tal cual y `createAction` lo escribe en `<Launch target="…">`. Con
`type:"custom"` se puede poner `com.whatsapp` o
`com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.heartrate.view.HeartRateActivity`,
exactamente los destinos verificados en el reloj. El `stringResId` debe existir
en `stringResource` (el generador añade `ID_TAP_*` y escribe
`res/values/strings.xml`).

### 4.10 Las agujas heredadas del ejemplo vienen teñidas
El nodo `analogHandHour` de `Minimal_classic_W_B.wfs` trae `color` **negro**
(es la variante AOD): WFS exporta `<HourHand tintColor="#ff000000"/>` y la aguja
desaparece. Hay que forzar blanco (`#FFFFFFFF` = sin teñir) al clonar las tres.

### 4.11 Anatomía de un `complicationSlot`
El nodo más complejo del modelo. Lo que hay que respetar:

- `child` — los elementos "vivos" (los que se ven en el editor) y **el grafo de
  referencias**: `categories.shortText/shortTitle/icon.properties.linkedElementId`
  apuntan al `id` del hijo que pinta cada campo, y `clipper` apunta al hijo con
  `complicationField: "clipper"` (el marco). Si se regeneran ids hay que
  reenlazar las dos cosas (`reid_slot()` lo hace).
- `complicationTypes.<tipo>.layouts.<layout>.elements` — plantillas por
  disposición; cada elemento lleva `complicationField`:
  `clipper`, `icon`, `shortText`, `shortTitle`. WFS elige una u otra según
  `<Expression>`/`<Compare>` (¿hay título?, ¿hay imagen monocroma?).
- `categories.complicationSlotPreview` — proveedor y disposición de la preview
  (`NEXT_EVENT` es un proveedor de texto corto válido).
- La plantilla útil es `Large_letters_D_C.wfs` → `Line Complication`: es la
  única con disposición de dos líneas (`shortTextTitle` = texto + título).
- Ojo con los elementos del ejemplo sin `complicationField`: si se mapean al
  texto principal, el XML sale con dos `<PartText>` idénticos superpuestos.

### 4.12 Hora mundial: los cuatro intentos y la causa real
Esto costó cuatro ciclos de instalación, así que queda escrito:

1. **`<Localization timezone="Europe/Madrid"/>`** (lo que emite WFS para una
   "world clock"): el runtime **lo ignora**. La esfera se pinta, pero la hora
   sale igual que la local. Probado también declarando formato WFF v3 en el
   manifest (por si era cosa de la versión): idéntico.
2. **`[TIMEZONE_OFFSET_DST]`**: no es una fuente de datos del runtime.
3. **`[DAY_1_31]`**: tampoco. Es el nombre **interno del editor**; en Watch Face
   Format el día del mes es **`[DAY]`** (`[DAY_Z]`, `[MONTH]`, `[DAY_OF_WEEK]`
   también son válidos). El runtime tiene 0 apariciones de `DAY_1_31`.
4. **Comillas sin escapar**: `expression="icuText("HH:mm", …)"` deja el XML mal
   formado; hay que escribir `&quot;` y `&amp;&amp;` como hace WFS.

Los tres fallos se manifiestan igual, y por eso se confunden: el proceso
`com.samsung.wear.watchface.runtime` muere al inicializar y el sistema vuelve a
la esfera de fábrica:

```
E WatchFaceService: WatchFace crashed during init
E WatchFaceService: java.lang.NullPointerException: Attempt to read from field
                    'java.util.ArrayList Z2.f.b' on a null object reference
                    in method 'java.util.ArrayList C2.b.F(Z2.f, java.lang.String)'
E WearServices: [ActiveWatchFaceFacade] WatchFaceId[...] has disappeared twice
                in 15000 milliseconds, reverting to the fallback watch face
```

**Antes de instalar**: `python tools\check_wff_tags.py` (comprueba que el XML
esté bien formado y que el runtime conozca todas las etiquetas) y
`python tools\check_wfs.py` para el `.wfs`.

**Lo que sí funciona**: `icuText("HH:mm", [UTC_TIMESTAMP] + desfase)`.
`icuText` formatea el instante en la zona **del reloj**, así que el desfase es
`España − reloj`. La regla de verano europea se calcula en la expresión con
`[MONTH]`, `[DAY]` y `[DAY_OF_WEEK]` (el día de la semana del 31 se deduce de
los de hoy), sin etiquetas exóticas. El desfase del reloj va como constante de
compilación: `--device-utc-offset` (por defecto `-5`).

En el proyecto de WFS no se puede usar la misma expresión: el editor solo
entiende `icuText` dentro de un nodo `date`, y un nodo de texto deja
`icuText(...)` **como texto literal** en el XML compilado (verificado). Por eso
el `.wfs` usa un nodo `date` con un desfase en horas calculado al empaquetar
(`spain_utc_offset()` en `make_wfs_project.py`), mientras que el APK lleva la
regla viva.

### 4.13 Cambiar la esfera activa por adb
No hay comando directo (`cmd wallpaper` solo tiene `set-dim-amount`), pero el
broadcast de Samsung **sí funciona**:

```powershell
adb -s <serial> shell am broadcast `
  -a com.samsung.android.wearable.sysui.action.SET_ACTIVE_WATCH_FACE --ei favoriteId 44
```

El extra `favoriteId` es el id interno de su lista de favoritos (44 para
`com.relog.neongrid`; sale en el log `SecWatchFaceOrderRepository2` cada vez que
se abre el selector). Con `package`, `packageName`, `watchFaceId` o `component`
no hace nada. **No usar `input tap` a ciegas**: un toque acabó iniciando una
llamada.

---

## 5. Entorno y rutas

| Cosa | Ruta / valor |
|---|---|
| Proyecto | `C:\Proyectos\relog` |
| Python (con PIL y lxml) | `C:\Users\alejo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe` |
| adb | `C:\Users\alejo\AppData\Local\Android\Sdk\platform-tools\adb.exe` |
| Reloj (serial mDNS) | `adb-RFAX50JH1ZZ-9KG4PP._adb-tls-connect._tcp` (IP 192.168.1.11) |
| WFS 1.9.9 | `%LOCALAPPDATA%\Programs\WatchFaceStudio` |
| Proyectos de ejemplo WFS | `%LOCALAPPDATA%\Programs\WatchFaceStudio\tools\wfs_samples` |
| Logs de WFS | `%APPDATA%\WatchFaceStudio\dump\{main,renderer}.log` |
| Repositorio | <https://github.com/alejozd/neon-grid-watchface> |

Notas de entorno:
- El shell **no tiene salida a internet**, pero `gh` está autenticado como
  `alejozd` y **sí** funciona para crear repos y hacer push (con
  `danger-full-access` para escribir credenciales fuera del workspace).
- Los comandos `adb` necesitan `danger-full-access` (clave privada de adb fuera
  del workspace) y **cada llamada debe ser autocontenida**: el daemon de adb
  muere entre llamadas por el sandbox.
- El usuario **activa la depuración inalámbrica** cuando hace falta y pasa el
  puerto nuevo; el emparejamiento ya está hecho. **El puerto cambia** cada vez
  que se reactiva (y se cae al apagar la pantalla o salir del Wi-Fi): si `adb
  connect` responde `10061 connection refused`, hay que pedir el puerto nuevo.
  El comando de reconexión es `adb connect <ip>:<puerto>`.

---

## 6. Estado y trabajo opcional

**Nada pendiente por obligación**: la esfera está instalada y funcionando
(versionCode **32**), con la hora de Barcelona verificada, las manecillas nuevas,
el evento subido, el clima a prueba de falta de datos y el toque que abre el
reloj mundial. El proyecto de WFS también está completo y validado.

Si algún día se retoma, esto es lo que queda (todo opcional):

1. Probar el proyecto de WFS en el reloj con *Run on Device* (o `--build` para
   sacar el AAB) y comparar con la carátula WFF ya instalada.
2. Afinar el Always-On: la fecha sale en magenta sobre negro; para OLED conviene
   un gris tenue. WFS no tiene color por modo, así que habría que duplicar el
   nodo con `visibleOnAOD` complementario.
3. La hora mundial usa el desfase del reloj como constante de compilación
   (`--device-utc-offset`, `-5` por defecto). La regla de verano sí es dinámica;
   lo que no se puede es mover la esfera de país sin recompilar. Si se confirma
   que `[TIMEZONE_OFFSET]` (sin `_DST`) existe en el runtime, se sustituye.
4. Elegir ciudad **dentro** de la esfera (ranura de complicación): aparcado, ver
   4.13. La alternativa que sí funciona es el toque que abre la app.
5. Retomar cualquiera de las nueve propuestas visuales (sección 8).

Regla de trabajo que ha funcionado: **un cambio, una prueba**. Ahora la prueba es
barata: `python tools\repack_wfs.py` + `tools\test_wfs.ps1` y mirar
`build/wfs-test/NeonGrid.preview.png`, `NeonGrid.aod.png`,
`NeonGrid.xml` y `testmode-summary.json`. Ante un fallo de apertura,
`%APPDATA%\WatchFaceStudio\dump\renderer.log`; si la esfera desaparece sola en el
reloj, `adb logcat` (ver 4.12).

---

## 7. Estado del repositorio

```
watchface/      proyecto WFF (manifest, res/raw/watchface.xml, …)
design/         render.py (arte por código) + out/ (PNGs, layout.json, hands.json)
tools/          gen_watchface.py, export_wfs_assets.py,
                make_wfs_project.py, repack_wfs.py, patch_wfs_flags.py,
                check_wfs.py, test_wfs.ps1, make_variants.py, debug/
wfs-assets/     capas sueltas + SPEC.md (tabla de coordenadas y toques)
wfs-project/    NeonGrid.wfs  <- proyecto para abrir en WFS
docs/           HANDOFF.md (este archivo), WFF_RESEARCH.md, research/
build/          APKs firmados, keystore, capturas, wfs-render.png, wfs-aod.png,
                wfs-generated.xml
build.ps1       compilación y firma offline
install.ps1     asistente de emparejamiento/instalación por adb
README.md       guía en español
```

Herramientas de investigación en `tools/debug/` (leen directamente `app.asar` y
los proyectos de ejemplo, son la fuente de todo lo de la sección 4):

| Script | Para qué |
|---|---|
| `debug_dump_nodes.py <ejemplo.wfs>` | árbol de nodos con geometría |
| `debug_node_json.py <ejemplo.wfs> --name X` | JSON completo de un nodo |
| `debug_node_props.py <ejemplo.wfs> --type text` | propiedades planas, fácil de comparar |
| `debug_tags.py tags\|actions\|texts` | inventario de etiquetas y acciones de los 12 ejemplos |
| `debug_app_tags.py WTHR` | busca nombres de etiqueta dentro de `app.asar` |
| `debug_app_context.py <texto> [radio]` | imprime el código alrededor de un literal |
| `mock_world_clock.py` | montajes de dónde poner la hora mundial (eligió la opción B) |
| `mock_layouts.py` | tres redistribuciones de la esfera actual |
| `mock_concepts.py` | consola, tarjetas y arcade (tipografía grande) |
| `mock_redesign.py` | sunset, pixel y papel (paleta y formas nuevas) |

### 8. Exploraciones de diseño (cerradas, ninguna adoptada)

Entre el 20 y el 21/11 se propusieron **nueve** variantes, todas solo como
imagen (`build/mock-*.png`) y sin tocar la esfera:

1. Tres redistribuciones de la información actual (cápsula inferior, anillos con
   insignias, rail lateral). → descartadas por «parecerse demasiado a lo que hay».
2. Tres con tipografía grande y estética de juego (consola radar con agujas,
   tarjetas digitales con esquinas cortadas, arcade con barras segmentadas).
   → descartadas.
3. Tres rediseños totales: **sunset** (degradado cálido, sol rayado, pastillas),
   **pixel** (8 bits, verde ácido, corazones) y **papel** (fondo claro, tinta
   fina, acentos azul/naranja). → descartadas.

**Conclusión**: el diseño actual (cian/magenta sobre negro, rejilla, arcos y
manecillas `blade`) se queda. Los scripts quedan en `tools/debug/` y las capturas
en `build/`, así que retomar cualquiera es cuestión de abrir el script y
desarrollarlo de verdad en `design/render.py`.

La carátula del reloj está terminada y funcionando en el reloj, con la hora de
Barcelona, las manecillas nuevas, el evento más arriba y el clima a prueba de
falta de datos. El proyecto de WFS renderiza la esfera entera y compila a WFF.
**Proyecto cerrado**: no queda trabajo pendiente salvo lo opcional de la
sección 6 y probar el proyecto de WFS con *Run on Device*.
