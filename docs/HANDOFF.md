# Traspaso de proyecto — Neon Grid (carátula Galaxy Watch 6)

Documento de continuación. Estado a fecha de este traspaso. Todo lo que aquí se
describe está verificado contra el reloj real o contra el binario de Watch Face
Studio 1.9.9, salvo lo marcado como **pendiente**.

Repositorio: <https://github.com/alejozd/neon-grid-watchface> (público, rama `main`).

---

## 1. Resumen en dos líneas

Hay una **carátula real, instalada y funcionando en el reloj** (formato WFF,
APK firmado, compilada sin Gradle). Y hay un **proyecto de Watch Face Studio**
que se abre correctamente, pero que **solo contiene el fondo y las tres agujas**:
las capas de texto y datos todavía no se han generado.

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

Versión actual: **2.3**. Firma: `build/keystore/cyber.jks`
(alias `cyber`, pass `cyberwatch`; clave de desarrollo, no para Play).

### Contenido de la esfera
Hora 12 h en cian (66 px, anclada a la derecha en x=326), AM/PM, segundero,
fecha 26 px, temperatura 30 px, condición, máx/mín, contador MSG, ranura de
evento (complicación), batería %, pulso, pasos + %, dos arcos-medidor reales
(batería 246→294, pasos 300→340) y etiquetas de 13 px.

### Toques verificados en el reloj (`dumpsys window` tras cada toque)
| Zona | Target | Abre |
|---|---|---|
| Temperatura | `com.samsung.android.watch.weather` | Clima |
| MSG | `com.whatsapp` | WhatsApp (lista de chats) |
| Batería | `BATTERY_STATUS` | Ajustes de batería |
| Pulso | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.heartrate.view.HeartRateActivity` | Pantalla de pulso con el botón **Medir** |
| Pasos | `com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.steps.view.StepsActivity` | Pantalla de pasos |
| Fecha | `com.samsung.android.calendar` | Calendario (día) |

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
python tools\gen_watchface.py --format 2 --palette neon --package com.relog.neongrid --label "Neon Grid"
# 3. APK firmado (aapt2 + zipalign + apksigner, sin Gradle ni internet)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -MinSdk 34 -VersionName "2.3"
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

## 3. Proyecto de Watch Face Studio — ABIERTO, PERO INCOMPLETO

### Qué hay
`wfs-project/NeonGrid.wfs` se abre en WFS 1.9.9 sin errores. Contiene:

- Lienzo **450×450** circular.
- Capa `bg` con el fondo (`neon_bg.png`).
- Grupo `Hands` (analogClock) con `hour`, `minute`, `second` (28/26/30 × 450).

### Qué falta (siguiente paso del próximo chat)
**Todas las capas de texto y datos**: hora digital, segundos, AM/PM, fecha,
temperatura, condición, máx/mín, MSG, batería, pulso, pasos, ranura de evento y
las zonas táctiles. Por eso al abrir el proyecto solo se ven las agujas.

### Cómo se genera
```powershell
python tools\make_wfs_project.py     # modelo (honeyface.json)
python tools\repack_wfs.py           # empaquetado + sello  (usar este)
```
`repack_wfs.py` importa `build_model()` y `hand_crop()` de `make_wfs_project.py`
y escribe `wfs-project/NeonGrid.wfs`. `make_wfs_project.py` por sí solo **no**
añade el sello final, así que el archivo bueno es el que produce `repack_wfs.py`.

### Referencias de coordenadas
`wfs-assets/SPEC.md` tiene la tabla completa de posiciones **a 480×480**.
Para el proyecto de WFS hay que escalarlas por **450/480 = 0.9375**.

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

### 4.6 Rotación de las agujas en el editor
**PENDIENTE DE CONFIRMAR.** El editor de WFS muestra las agujas a las 12 en
punto (rotación 0) y en el proyecto de ejemplo de Samsung también están
guardadas con rotación 0. La hipótesis es que la rotación por hora se aplica al
pulsar **Play** o **Run on Device**. Prueba de 10 segundos:

> Abrir `wfs-project/NeonGrid.wfs`, pulsar ▶ (abajo a la izquierda) o mover el
> deslizador de la línea de tiempo 0–24 h, y ver si las agujas giran a las 10:08.

Si **no** giran con Play, el problema está en el nodo `analogClock` y hay que
comparar campo por campo con el del ejemplo `Minimal_classic_W_B.wfs`.

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
  puerto nuevo; el emparejamiento ya está hecho.

---

## 6. Siguiente paso concreto (para el próximo chat)

1. **Confirmar** si las agujas giran al pulsar Play (ver 4.6). Es el único
   cabo suelto del trabajo hecho hasta ahora.
2. **Añadir las capas de texto y datos** al generador del `.wfs`, clonando
   plantillas del ejemplo y usando las coordenadas de `wfs-assets/SPEC.md`
   escaladas ×0.9375:
   - `digitalClock` para HH:MM (12 h) y para los segundos.
   - `text` para AM/PM, temperatura, condición, máx/mín, valores de datos.
   - `date` para la fecha.
   - `complication` para la ranura de evento.
   - Rectángulos invisibles (`drawEllipse`/`image`) con enlace para los toques.
   - Pestaña **ALWAYS-ON** con la versión para AOD.
3. Publicar/comprobar con **Run on Device** y, si funciona, comparar con la
   carátula ya instalada.

Regla de trabajo que ha funcionado: **un cambio, una prueba, y leer
`renderer.log` ante cualquier fallo**. Los cuatro errores del `.wfs` se
resolvieron así, no a ciegas.

---

## 7. Estado del repositorio

```
watchface/      proyecto WFF (manifest, res/raw/watchface.xml, …)
design/         render.py (arte por código) + out/ (PNGs, layout.json, hands.json)
tools/          gen_watchface.py, export_wfs_assets.py,
                make_wfs_project.py, repack_wfs.py, patch_wfs_flags.py,
                make_variants.py, debug/
wfs-assets/     capas sueltas + SPEC.md (tabla de coordenadas y toques)
wfs-project/    NeonGrid.wfs  <- proyecto para abrir en WFS
docs/           HANDOFF.md (este archivo), WFF_RESEARCH.md, research/
build/          APKs firmados, keystore, capturas
build.ps1       compilación y firma offline
install.ps1     asistente de emparejamiento/instalación por adb
README.md       guía en español
```

La carátula del reloj está terminada y funcionando. El proyecto de WFS está
abierto y validado; le faltan las capas de datos.
