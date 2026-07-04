#Requires -Version 5.1
<#
.SYNOPSIS
    Instala o actualiza Route Accident Bot desde GitHub y abre la interfaz grafica.
.EXAMPLE
    irm https://raw.githubusercontent.com/StreckerMX/route-accident-bot/main/Install-Remote.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$RepoOwner = "StreckerMX"
$RepoName = "route-accident-bot"
$InstallDir = Join-Path $env:LOCALAPPDATA "RouteAccidentBot"
$ZipUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/main.zip"
$RequirementsFile = "RouteAccidentBot.Requirements.txt"
$SettingsFile = "RouteAccidentBot.Settings.yaml"
$EntryPoint = "Start-RouteAccidentBot.py"

function Write-Step([string]$Text) { Write-Host "`n$Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "  $Text" -ForegroundColor Green }

function Get-PythonCmd {
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)" -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10))) {
                return $cmd
            }
        } catch {}
    }
    return $null
}

function Backup-UserData([string]$TargetDir) {
    $backup = @{}
    $envFile = Join-Path $TargetDir ".env"
    $settingsFile = Join-Path $TargetDir $SettingsFile
    if (Test-Path $envFile) { $backup[".env"] = Get-Content $envFile -Raw -Encoding UTF8 }
    if (Test-Path $settingsFile) { $backup[$SettingsFile] = Get-Content $settingsFile -Raw -Encoding UTF8 }
    return $backup
}

function Restore-UserData([string]$TargetDir, [hashtable]$Backup) {
    foreach ($key in $Backup.Keys) {
        $path = Join-Path $TargetDir $key
        Set-Content -Path $path -Value $Backup[$key] -Encoding UTF8 -NoNewline
    }
}

function Update-FromZip([string]$TargetDir) {
    $tempRoot = Join-Path $env:TEMP "rab-install-$([guid]::NewGuid().ToString('N'))"
    $zipPath = Join-Path $tempRoot "repo.zip"
    $extractDir = Join-Path $tempRoot "extract"
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    Write-Host "  Descargando ultima version..." -ForegroundColor DarkGray
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $sourceDir = Get-ChildItem $extractDir -Directory | Select-Object -First 1
    if (-not $sourceDir) { throw "No se pudo extraer el repositorio." }

    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }

    $backup = Backup-UserData $TargetDir
    $venvPath = Join-Path $TargetDir "venv"

    Get-ChildItem -LiteralPath $TargetDir -Force | Where-Object {
        $_.Name -notin @("venv", ".env", $SettingsFile)
    } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Copy-Item -Path (Join-Path $sourceDir.FullName "*") -Destination $TargetDir -Recurse -Force
    Restore-UserData $TargetDir $backup

    if (Test-Path $venvPath) {
        Write-Ok "Entorno virtual conservado"
    }

    Remove-Item $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

function Update-FromGit([string]$TargetDir) {
    if (-not (Test-Path (Join-Path $TargetDir ".git"))) {
        throw "No es un repositorio git."
    }
    git -C $TargetDir pull --ff-only
}

Clear-Host
Write-Host "`n  Route Accident Bot - Instalacion remota`n" -ForegroundColor Cyan

Write-Step "1/4  Verificando Python..."
$pythonCmd = Get-PythonCmd
if (-not $pythonCmd) {
    Write-Host "  Se requiere Python 3.10 o superior." -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Ok "Python listo"

Write-Step "2/4  Actualizando aplicacion en $InstallDir"
$updatedWithGit = $false
if ((Get-Command git -ErrorAction SilentlyContinue) -and (Test-Path (Join-Path $InstallDir ".git"))) {
    try {
        Update-FromGit $InstallDir
        $updatedWithGit = $true
        Write-Ok "Codigo actualizado con git pull"
    } catch {
        Write-Host "  git pull fallo, usando descarga ZIP..." -ForegroundColor Yellow
    }
}
if (-not $updatedWithGit) {
    Update-FromZip $InstallDir
    Write-Ok "Codigo actualizado desde GitHub"
}

Write-Step "3/4  Preparando entorno..."
$venvPath = Join-Path $InstallDir "venv"
if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
    & $pythonCmd -m venv $venvPath
}
$venvPython = Join-Path $venvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip -q
& $venvPython -m pip install -r (Join-Path $InstallDir $RequirementsFile) -q
Write-Ok "Dependencias listas"

Write-Step "4/4  Abriendo interfaz grafica..."
$launcher = Join-Path $InstallDir $EntryPoint
if (-not (Test-Path $launcher)) {
    throw "No se encontro $EntryPoint en $InstallDir"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Route Accident Bot.lnk"
try {
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = (Join-Path $InstallDir "Start-RouteAccidentBot.ps1")
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Save()
    Write-Ok "Acceso directo en escritorio"
} catch {
    Write-Host "  No se pudo crear acceso directo (opcional)." -ForegroundColor DarkGray
}

Write-Host "`n  Listo. Se abrira la aplicacion.`n" -ForegroundColor Green
Set-Location $InstallDir
& $venvPython $launcher