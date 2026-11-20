# Verifica el proyecto .wfs de forma automatica con el modo de prueba de WFS.
#
# Watch Face Studio 1.9.9 trae un modo headless no documentado:
#     WatchFaceStudio.exe --test --wfs=<proyecto.wfs> --out=<carpeta>
# Abre el proyecto, lo renderiza, y deja en <carpeta>:
#     <proyecto>.preview.png     render normal
#     <proyecto>.aod.png         render Always-On (analiza el burn-in)
#     <proyecto>.xml             el XML WFF que generaria al compilar
#     testmode-summary.json      {"status":"success"|"failed","stage":...}
# (con --build ademas compila el AAB y lo deja en la misma carpeta).
#
# Requiere danger-full-access: la app escribe en %APPDATA% y aborta si el sandbox
# le corta el acceso a archivos. IMPORTANTE: hay que borrar ELECTRON_RUN_AS_NODE
# o Electron arranca como Node y responde "bad option: --wfs=...".
param(
    [string]$Project = "wfs-project\NeonGrid.wfs",
    [string]$OutDir = "build\wfs-test",
    [switch]$Build
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $env:LOCALAPPDATA "Programs\WatchFaceStudio\WatchFaceStudio.exe"
if (-not (Test-Path $exe)) { throw "no encuentro Watch Face Studio en $exe" }

$proj = if ([System.IO.Path]::IsPathRooted($Project)) { $Project } else { Join-Path $root $Project }
$out = if ([System.IO.Path]::IsPathRooted($OutDir)) { $OutDir } else { Join-Path $root $OutDir }
New-Item -ItemType Directory -Force -Path $out | Out-Null
Get-ChildItem $out -File -ErrorAction SilentlyContinue | Remove-Item -Force

$env:ELECTRON_RUN_AS_NODE = $null
# Perfil propio: si se comparte %APPDATA% con una instancia abierta, Chromium
# bloquea el perfil y el modo de prueba termina sin abrir el proyecto.
$profileDir = Join-Path $root ".wfs-test-profile"
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
$args_ = @("--test", "--wfs=$proj", "--out=$out", "--user-data-dir=$profileDir")
if ($Build) { $args_ += "--build" }

# WFS escribe el progreso del modo de prueba por stderr, asi que no se puede
# canalizar con 2>&1: PowerShell lo trataria como error terminante.
$outLog = Join-Path $out "wfs-console.out.log"
$errLog = Join-Path $out "wfs-console.err.log"
$proc = Start-Process -FilePath $exe -ArgumentList $args_ -Wait -PassThru `
    -RedirectStandardOutput $outLog -RedirectStandardError $errLog
Write-Host "WFS exit code: $($proc.ExitCode)"

$summary = Join-Path $out "testmode-summary.json"
if (-not (Test-Path $summary)) { throw "el modo de prueba no dejo resumen en $out" }
Get-Content $summary -Raw
Get-ChildItem $out -File | Select-Object Length, Name | Format-Table -AutoSize
