#Requires -Version 5.1
<#
.SYNOPSIS
    Instalador interactivo de Route Accident Bot.
.EXAMPLE
    .\Install-RouteAccidentBot.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExampleFile = Join-Path $ProjectRoot "RouteAccidentBot.env.example"
$ConfigFile = Join-Path $ProjectRoot "RouteAccidentBot.Settings.yaml"
$RequirementsFile = Join-Path $ProjectRoot "RouteAccidentBot.Requirements.txt"
$EntryPoint = Join-Path $ProjectRoot "Start-RouteAccidentBot.py"
$StartScript = Join-Path $ProjectRoot "Start-RouteAccidentBot.ps1"

function Write-StepTitle([string]$Text) { Write-Host "`n=== $Text ===" -ForegroundColor Cyan }
function Write-Success([string]$Text) { Write-Host "  [OK] $Text" -ForegroundColor Green }
function Write-Notice([string]$Text) { Write-Host "  [!] $Text" -ForegroundColor Yellow }
function Write-Failure([string]$Text) { Write-Host "  [X] $Text" -ForegroundColor Red }

function Read-InputWithDefault {
    param([string]$Prompt, [string]$Default = "")
    if ($Default) {
        $raw = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
        return $raw.Trim()
    }
    return (Read-Host $Prompt).Trim()
}

function Read-SecretPlain {
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

function Update-YamlField {
    param([string]$FilePath, [string]$KeyPath, [string]$Value)
    $content = Get-Content $FilePath -Raw -Encoding UTF8
    $pattern = "(?m)^(\s*$([regex]::Escape($KeyPath)):\s*).*$"
    if ($content -match $pattern) {
        $content = [regex]::Replace($content, $pattern, "`${1}`"$Value`"")
    }
    Set-Content $FilePath $content -Encoding UTF8 -NoNewline
}

function Send-TelegramTestMessage {
    param([string]$Token, [string]$ChatId)
    $url = "https://api.telegram.org/bot$Token/sendMessage"
    $body = @{ chat_id = $ChatId; text = "Route Accident Bot: mensaje de prueba. Telegram configurado correctamente." } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
    return $response.ok -eq $true
}

Clear-Host
Write-Host "`n  Route Accident Bot`n  Instalador interactivo`n  --------------------`n" -ForegroundColor Cyan
Set-Location $ProjectRoot

if ($PSVersionTable.PSEdition -eq "Core") {
    Write-Notice "Detectado PowerShell 7+. Si Windows Security bloquea pip, usa Windows PowerShell 5.1 o continua: este instalador usa 'python -m pip' para evitar ese bloqueo."
}

Write-StepTitle "Paso 1: Verificar Python"
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $versionText = & $cmd --version 2>&1
        if ($versionText -match "Python (\d+)\.(\d+)" -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10))) {
            $pythonCmd = $cmd
            Write-Success "Encontrado: $versionText"
            break
        }
    } catch {}
}
if (-not $pythonCmd) { Write-Failure "Se requiere Python 3.10+."; exit 1 }

Write-StepTitle "Paso 2: Entorno virtual"
if (-not (Test-Path (Join-Path $VenvPath "Scripts\python.exe"))) {
    & $pythonCmd -m venv $VenvPath
    Write-Success "Entorno virtual creado"
} else { Write-Success "Entorno virtual ya existe" }

$venvPython = Join-Path $VenvPath "Scripts\python.exe"

Write-StepTitle "Paso 3: Instalar dependencias"
Write-Host "  Usando 'python -m pip' (evita bloqueo de Windows Security sobre pip.exe)" -ForegroundColor DarkGray
& $venvPython -m pip install --upgrade pip -q
& $venvPython -m pip install -r $RequirementsFile -q
Write-Success "Dependencias instaladas"

Write-StepTitle "Paso 4: Configuracion del bot"
$skipEnv = (Test-Path $EnvFile) -and -not (Read-YesNo "Ya existe .env. Deseas reconfigurarlo?" $false)
$enableTelegram = $false
$telegramToken = ""
$telegramChatId = ""

if (-not $skipEnv) {
    $googleKey = Read-SecretPlain "API Key de Google Maps"
    while ([string]::IsNullOrWhiteSpace($googleKey)) { $googleKey = Read-SecretPlain "API Key de Google Maps" }
    $enableTelegram = Read-YesNo "Activar notificaciones por Telegram?" $false
    if ($enableTelegram) {
        Write-Host "  Usa @BotFather y @userinfobot. Envia /start a tu bot." -ForegroundColor DarkGray
        $telegramToken = Read-SecretPlain "Token del bot de Telegram"
        $telegramChatId = Read-InputWithDefault "Chat ID de Telegram" ""
    }
}

$origin = Read-InputWithDefault "Origen de la ruta" "Ciudad de Mexico, CDMX"
$destination = Read-InputWithDefault "Destino de la ruta" "Toluca, Estado de Mexico"
$interval = Read-InputWithDefault "Intervalo de revision (minutos)" "5"

Write-StepTitle "Paso 5: Guardar configuracion"
if (-not $skipEnv) {
    @("GOOGLE_MAPS_API_KEY=$googleKey", "", "TELEGRAM_BOT_TOKEN=$telegramToken", "TELEGRAM_CHAT_ID=$telegramChatId") -join "`n" | Set-Content $EnvFile -Encoding UTF8
    Write-Success "Archivo .env creado"
}
Update-YamlField $ConfigFile "  origin" $origin
Update-YamlField $ConfigFile "  destination" $destination
Update-YamlField $ConfigFile "  interval_minutes" $interval
$content = Get-Content $ConfigFile -Raw -Encoding UTF8
if (-not $skipEnv) { $content = $content -replace '(?m)^(\s*enabled:\s*).*$', "`${1}$(if ($enableTelegram) { 'true' } else { 'false' })" }
Set-Content $ConfigFile $content -Encoding UTF8 -NoNewline
Write-Success "RouteAccidentBot.Settings.yaml actualizado"

if (-not $skipEnv -and $enableTelegram) {
    Write-StepTitle "Paso 6: Probar Telegram"
    try {
        if (Send-TelegramTestMessage $telegramToken $telegramChatId) { Write-Success "Mensaje de prueba enviado" }
        else { Write-Notice "No se pudo confirmar el envio" }
    } catch { Write-Notice "Error: $($_.Exception.Message)" }
}

Write-StepTitle "Instalacion completada"
Write-Host "`n  Para iniciar el bot:`n" -ForegroundColor Cyan
Write-Host "    .\Start-RouteAccidentBot.ps1" -ForegroundColor Yellow
Write-Host ""
if (Read-YesNo "Deseas iniciar el bot ahora?" $false) { & $venvPython $EntryPoint }
