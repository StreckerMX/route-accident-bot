#Requires -Version 5.1
<#
.SYNOPSIS
    Elimina Route Accident Bot y todos sus archivos.
#>

$ErrorActionPreference = "Stop"
$ConfirmWord = "BORRAR"
$LocalAppDir = Join-Path $env:LOCALAPPDATA "RouteAccidentBot"

function Read-YesNo {
    param([string]$Prompt, [bool]$DefaultYes = $false)
    $hint = if ($DefaultYes) { "S/n" } else { "s/N" }
    $answer = (Read-Host "$Prompt ($hint)").Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($answer)) { return $DefaultYes }
    return $answer -in @("s", "si", "sí", "y", "yes")
}

function Remove-ProjectDir([string]$ProjectRoot) {
    $scriptPath = $PSCommandPath
    $failed = [System.Collections.Generic.List[string]]::new()

    Get-ChildItem -LiteralPath $ProjectRoot -Force | ForEach-Object {
        if ($_.FullName -eq $scriptPath) { return }
        try {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop
        } catch {
            $failed.Add($_.Name)
        }
    }

    if ($failed.Count -gt 0) {
        Write-Host "  No se pudo eliminar todo en $ProjectRoot" -ForegroundColor Yellow
        return $false
    }

    if ($ProjectRoot -eq $PSScriptRoot) {
        $deleteCmd = "timeout /t 2 /nobreak >nul & rmdir /s /q `"$ProjectRoot`""
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c $deleteCmd" -WindowStyle Hidden | Out-Null
    } else {
        Remove-Item -LiteralPath $ProjectRoot -Recurse -Force
    }
    return $true
}

Clear-Host
Write-Host "`n  Route Accident Bot - Desinstalacion`n" -ForegroundColor Red

$targets = @()
if (Test-Path $LocalAppDir) { $targets += $LocalAppDir }
if ((Test-Path $PSScriptRoot) -and ($PSScriptRoot -notin $targets)) { $targets += $PSScriptRoot }

if ($targets.Count -eq 0) {
    Write-Host "  No se encontro ninguna instalacion.`n" -ForegroundColor Yellow
    exit 0
}

Write-Host "  Se eliminara:" -ForegroundColor Yellow
$targets | ForEach-Object { Write-Host "    $_" -ForegroundColor White }
Write-Host "`n  Cierra la aplicacion antes de continuar." -ForegroundColor Yellow

if (-not (Read-YesNo "  Continuar" $false)) { exit 0 }
if ((Read-Host "  Escribe $ConfirmWord para confirmar").Trim() -ne $ConfirmWord) { exit 0 }

foreach ($dir in $targets) {
    Write-Host "`n  Eliminando $dir ..." -ForegroundColor Cyan
    if (Remove-ProjectDir $dir) {
        Write-Host "  Listo." -ForegroundColor Green
    }
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcut = Join-Path $desktop "Route Accident Bot.lnk"
if (Test-Path $shortcut) { Remove-Item $shortcut -Force }

Write-Host "`n  Desinstalacion completada.`n" -ForegroundColor Green