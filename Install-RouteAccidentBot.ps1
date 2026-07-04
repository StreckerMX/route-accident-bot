#Requires -Version 5.1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"
$EnvFile = Join-Path $ProjectRoot ".env"
$ConfigFile = Join-Path $ProjectRoot "RouteAccidentBot.Settings.yaml"
$RequirementsFile = Join-Path $ProjectRoot "RouteAccidentBot.Requirements.txt"
$EntryPoint = Join-Path $ProjectRoot "Start-RouteAccidentBot.py"

function Write-Step([string]$Text) { Write-Host "`n$Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "  Listo: $Text" -ForegroundColor Green }
function Write-Err([string]$Text) { Write-Host "  Error: $Text" -ForegroundColor Red }

function Read-InputDefault {
    param([string]$Prompt, [string]$Default = "")
    if ($Default) {
        $raw = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
        return $raw.Trim()
    }
    return (Read-Host $Prompt).Trim()
}

function Read-Secret {
    param([string]$Prompt)
    $secure = Read-Host $Prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Read-YesNo {
    param([string]$Prompt, [bool]$DefaultYes = $false)
    $hint = if ($DefaultYes) { "S/n" } else { "s/N" }
    $answer = (Read-Host "$Prompt ($hint)").Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($answer)) { return $DefaultYes }
    return $answer -in @("s", "si", "sí", "y", "yes")
}

function Set-YamlValue {
    param(
        [string]$FilePath,
        [string]$KeyPath,
        [string]$Value,
        [bool]$Quoted = $true
    )
    $content = Get-Content $FilePath -Raw -Encoding UTF8
    $formatted = if ($Quoted) { "`"$Value`"" } else { $Value }
    $pattern = "(?m)^(\s*$([regex]::Escape($KeyPath)):\s*).*$"
    if ($content -match $pattern) {
        $content = [regex]::Replace($content, $pattern, "`${1}$formatted")
    }
    Set-Content $FilePath $content -Encoding UTF8 -NoNewline
}

function Write-TextFileUtf8NoBom {
    param([string]$Path, [string]$Content)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Test-Telegram {
    param([string]$Token, [string]$ChatId)
    $url = "https://api.telegram.org/bot$Token/sendMessage"
    $body = @{ chat_id = $ChatId; text = "Route Accident Bot: configuracion correcta." } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
    return $r.ok -eq $true
}

Clear-Host
Write-Host "`n  Route Accident Bot - Instalacion`n" -ForegroundColor Cyan
Set-Location $ProjectRoot

Write-Step "1/5  Verificando Python..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)" -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10))) {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}
if (-not $pythonCmd) {
    Write-Err "Se requiere Python 3.10 o superior."
    Write-Host "  Descarga: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Ok "Python detectado"

Write-Step "2/5  Preparando entorno..."
if (-not (Test-Path (Join-Path $VenvPath "Scripts\python.exe"))) {
    & $pythonCmd -m venv $VenvPath
}
$venvPython = Join-Path $VenvPath "Scripts\python.exe"
Write-Ok "Entorno listo"

Write-Step "3/5  Instalando dependencias..."
& $venvPython -m pip install --upgrade pip -q
& $venvPython -m pip install -r $RequirementsFile -q
Write-Ok "Dependencias instaladas"

Write-Step "4/5  Configuracion"
$reconfigure = $true
if ((Test-Path $EnvFile) -and -not (Read-YesNo "  Ya existe .env. Reconfigurar" $false)) {
    $reconfigure = $false
}

$routesKey = ""
$geocodingKey = ""
$enableTelegram = $false
$telegramToken = ""
$telegramChatId = ""

if ($reconfigure) {
    Write-Host ""
    Write-Host "  Necesitas dos API Keys en Google Cloud (Routes API y Geocoding API)." -ForegroundColor DarkGray
    Write-Host "  Puedes usar la misma clave si ambas APIs estan habilitadas en tu proyecto.`n" -ForegroundColor DarkGray

    $routesKey = Read-Secret "  API Key - Routes API"
    while ([string]::IsNullOrWhiteSpace($routesKey)) {
        $routesKey = Read-Secret "  API Key - Routes API"
    }

    $geocodingKey = Read-Secret "  API Key - Geocoding API (Enter = misma que Routes)"
    if ([string]::IsNullOrWhiteSpace($geocodingKey)) {
        $geocodingKey = $routesKey
    }

    $enableTelegram = Read-YesNo "  Activar Telegram" $false
    if ($enableTelegram) {
        $telegramToken = Read-Secret "  Token de Telegram"
        $telegramChatId = Read-InputDefault "  Chat ID de Telegram" ""
        while ([string]::IsNullOrWhiteSpace($telegramToken) -or [string]::IsNullOrWhiteSpace($telegramChatId)) {
            $telegramToken = Read-Secret "  Token de Telegram"
            $telegramChatId = Read-InputDefault "  Chat ID de Telegram" ""
        }
    }
}

Write-Host ""
$origin = Read-InputDefault "  Origen" "Ciudad de Mexico, CDMX"
$destination = Read-InputDefault "  Destino" "Toluca, Estado de Mexico"

Write-Step "5/5  Guardando configuracion..."
if ($reconfigure) {
    $envLines = @(
        "GOOGLE_ROUTES_API_KEY=$routesKey"
        "GOOGLE_GEOCODING_API_KEY=$geocodingKey"
        ""
        "TELEGRAM_BOT_TOKEN=$telegramToken"
        "TELEGRAM_CHAT_ID=$telegramChatId"
    )
    Write-TextFileUtf8NoBom -Path $EnvFile -Content ($envLines -join "`n")
    Write-Ok "Archivo .env"
}

Set-YamlValue $ConfigFile "  origin" $origin
Set-YamlValue $ConfigFile "  destination" $destination
Set-YamlValue $ConfigFile "  interval_minutes" "45" -Quoted $false
Set-YamlValue $ConfigFile "  jam_delay_threshold_minutes" "13" -Quoted $false

if ($reconfigure) {
    $content = Get-Content $ConfigFile -Raw -Encoding UTF8
    $flag = if ($enableTelegram) { "true" } else { "false" }
    $content = $content -replace '(?m)^(\s*enabled:\s*).*$', "`${1}$flag"
    Set-Content $ConfigFile $content -Encoding UTF8 -NoNewline
}
Write-Ok "RouteAccidentBot.Settings.yaml"

if ($reconfigure -and $enableTelegram) {
    try {
        if (Test-Telegram $telegramToken $telegramChatId) { Write-Ok "Telegram verificado" }
    } catch {
        Write-Host "  No se pudo verificar Telegram. Envia /start a tu bot e intenta de nuevo." -ForegroundColor Yellow
    }
}

Write-Host "`n  Instalacion completada.`n" -ForegroundColor Green
Write-Host "  Iniciar el bot:" -ForegroundColor Cyan
Write-Host "    .\Start-RouteAccidentBotGui.ps1   (interfaz grafica)" -ForegroundColor Yellow
Write-Host "    .\Start-RouteAccidentBot.ps1      (consola)`n" -ForegroundColor Yellow

if (Read-YesNo "  Iniciar ahora" $false) {
    & $venvPython $EntryPoint
}