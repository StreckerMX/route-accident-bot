#Requires -Version 5.1
<#
.SYNOPSIS
    Inicia la interfaz grafica de Route Accident Bot.
.EXAMPLE
    .\Start-RouteAccidentBotGui.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$EntryPoint = Join-Path $ProjectRoot "Start-RouteAccidentBotGui.py"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Error: no se encontro el entorno virtual." -ForegroundColor Red
    Write-Host "Ejecuta primero: .\Install-RouteAccidentBot.ps1" -ForegroundColor Yellow
    exit 1
}

& $VenvPython $EntryPoint