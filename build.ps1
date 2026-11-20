# Builds the Watch Face Format APK (resource-only, no code) fully offline.
# Requires: Android SDK build-tools (aapt2, zipalign, apksigner) + JDK keytool.
param(
    [string]$Sdk = "$env:LOCALAPPDATA\Android\Sdk",
    [string]$BuildTools = "35.0.0",
    [string]$Platform = "android-35",
    [string]$Root = "C:\Proyectos\relog",
    [int]$VersionCode = 1,
    [string]$VersionName = "1.0",
    [int]$MinSdk = 30,
    [int]$TargetSdk = 34
)

$ErrorActionPreference = "Stop"
$bt = Join-Path $Sdk "build-tools\$BuildTools"
$aapt2 = Join-Path $bt "aapt2.exe"
$zipalign = Join-Path $bt "zipalign.exe"
$apksigner = Join-Path $bt "apksigner.bat"
$androidJar = Join-Path $Sdk "platforms\$Platform\android.jar"
$src = Join-Path $Root "watchface"
$out = Join-Path $Root "build"
$ks = Join-Path $out "keystore\cyber.jks"

foreach ($p in @($aapt2, $zipalign, $apksigner, $androidJar)) {
    if (-not (Test-Path $p)) { throw "Missing tool: $p" }
}
if (-not (Test-Path $ks)) { throw "Missing keystore: $ks" }

New-Item -ItemType Directory -Force -Path $out | Out-Null
$resZip = Join-Path $out "resources.zip"
$unsigned = Join-Path $out "watchface-unsigned.apk"
$aligned = Join-Path $out "watchface-aligned.apk"
$final = Join-Path $out "NeonGrid-$VersionName.apk"
foreach ($f in @($resZip, $unsigned, $aligned, $final)) { if (Test-Path $f) { Remove-Item $f -Force } }

Write-Host "[1/4] compiling resources..." -ForegroundColor Cyan
& $aapt2 compile --dir (Join-Path $src "res") -o $resZip
if ($LASTEXITCODE -ne 0) { throw "aapt2 compile failed" }

Write-Host "[2/4] linking APK..." -ForegroundColor Cyan
& $aapt2 link `
    -o $unsigned `
    -I $androidJar `
    --manifest (Join-Path $src "AndroidManifest.xml") `
    -R $resZip `
    --auto-add-overlay `
    --min-sdk-version $MinSdk `
    --target-sdk-version $TargetSdk `
    --version-code $VersionCode `
    --version-name $VersionName
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed" }

Write-Host "[3/4] aligning..." -ForegroundColor Cyan
& $zipalign -p -f 4 $unsigned $aligned
if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

Write-Host "[4/4] signing..." -ForegroundColor Cyan
& $apksigner sign `
    --ks $ks --ks-pass pass:cyberwatch --key-pass pass:cyberwatch --ks-key-alias cyber `
    --v1-signing-enabled true --v2-signing-enabled true `
    --out $final $aligned
if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

& $apksigner verify --print-certs $final | Select-Object -First 3
Write-Host "`nOK -> $final" -ForegroundColor Green
Write-Host ("size: {0:N1} KB" -f ((Get-Item $final).Length / 1KB))
