#Requires -Version 5.1
<#
.SYNOPSIS
    Instala dependencias en esta carpeta (desarrollo) y abre la GUI.
    Para usuarios finales usa Install-Remote.ps1 o el comando irm del README.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"
$RequirementsFile = Join-Path $ProjectRoot "RouteAccidentBot.Requirements.txt"
$EntryPoint = Join-Path $ProjectRoot "Start-RouteAccidentBot.py"

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

$pythonCmd = Get-PythonCmd
if (-not $pythonCmd) {
    Write-Host "Error: se requiere Python 3.10+" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $VenvPath "Scripts\python.exe"))) {
    & $pythonCmd -m venv $VenvPath
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip -q
& $venvPython -m pip install -r $RequirementsFile -q
& $venvPython $EntryPoint