# ============================================================
#  Instalador de "Neon Grid" para Galaxy Watch 6 (Wear OS)
#  Ejecutar en el PC:   powershell -ExecutionPolicy Bypass -File .\install.ps1
#  Requisitos: Android SDK platform-tools (adb) y el reloj en la misma red Wi-Fi.
# ============================================================
$ErrorActionPreference = "Stop"

function Find-Adb {
    $cands = @(
        (Get-Command adb.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "$env:ProgramFiles\Android\platform-tools\adb.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }
    if (-not $cands) { throw "No encuentro adb.exe. Instala Android SDK Platform-Tools." }
    return $cands[0]
}

$adb = Find-Adb
Write-Host "adb: $adb" -ForegroundColor DarkGray

Write-Host ""
Write-Host "=== PASO 1: emparejar (solo la primera vez) ===" -ForegroundColor Cyan
Write-Host "En el reloj: Ajustes -> Opciones de desarrollador -> Depuración inalámbrica"
Write-Host "  -> 'Emparejar dispositivo con código'. Deja esa pantalla ABIERTA."
$pairAddr = Read-Host "IP:puerto de la pantalla de EMPAREJAMIENTO (ej. 192.168.1.11:41234)"
$pairCode = Read-Host "Código de 6 dígitos"

& $adb kill-server | Out-Null
Write-Host "Emparejando $pairAddr ..." -ForegroundColor Yellow
& $adb pair $pairAddr $pairCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "El emparejamiento falló. Vuelve a abrir la pantalla de emparejamiento (el puerto y el código cambian) y reintenta." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== PASO 2: conectar ===" -ForegroundColor Cyan
Write-Host "Ahora mira la pantalla principal de 'Depuración inalámbrica' (IP:puerto, suele ser 5555)."
$connAddr = Read-Host "IP:puerto de CONEXIÓN"
& $adb connect $connAddr

Start-Sleep -Seconds 2
$devices = & $adb devices | Select-String "device$"
if (-not $devices) {
    Write-Host "El reloj no aparece conectado. Revisa que la depuración inalámbrica siga activa y que el PC esté en la misma Wi-Fi." -ForegroundColor Red
    & $adb devices
    exit 1
}

$serial = ($devices[0] -split "\s+")[0]
Write-Host "Conectado a $serial" -ForegroundColor Green

Write-Host ""
Write-Host "=== PASO 3: elegir variante e instalar ===" -ForegroundColor Cyan
$api = (& $adb -s $serial shell getprop ro.build.version.sdk).Trim()
Write-Host "API del reloj: $api"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$apk = if ([int]$api -ge 34) {
    Join-Path $here "build\NeonGrid-wearos5.apk"   # WFF v2: clima nativo
} else {
    Join-Path $here "build\NeonGrid-wearos4.apk"   # WFF v1: sin clima
}
if (-not (Test-Path $apk)) { throw "No encuentro el APK: $apk" }
Write-Host "Instalando $apk ..." -ForegroundColor Yellow
& $adb -s $serial install -r $apk
if ($LASTEXITCODE -ne 0) { throw "adb install falló" }

Write-Host ""
Write-Host "=== LISTO ===" -ForegroundColor Green
Write-Host "Para activarla en el reloj:"
Write-Host "  1) Manten pulsada la esfera actual."
Write-Host "  2) Desliza el carrusel HASTA EL FINAL y toca el mosaico 'Anadir caratula de reloj'."
Write-Host "  3) Baja por la lista hasta la seccion 'Descargados' y elige 'Neon Grid'."
Write-Host ""
Write-Host "Para el hueco EVENT: manten pulsada la esfera -> Editar -> toca EVENT -> Calendario."
Write-Host "Desinstalar:  $adb -s $serial uninstall com.relog.neongrid"
