#Requires -Version 5.1
<#
.SYNOPSIS
    Inicia el monitor de trafico Route Accident Bot.
.EXAMPLE
    .\Start-RouteAccidentBot.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$EntryPoint = Join-Path $ProjectRoot "Start-RouteAccidentBot.py"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Error: no se encontro el entorno virtual." -ForegroundColor Red
    Write-Host "Ejecuta primero: .\Install-RouteAccidentBot.ps1" -ForegroundColor Yellow
    exit 1
}

& $VenvPython $EntryPoint
