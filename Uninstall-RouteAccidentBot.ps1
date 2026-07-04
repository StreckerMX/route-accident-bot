#Requires -Version 5.1
<#
.SYNOPSIS
    Elimina por completo Route Accident Bot y todos sus archivos.
.DESCRIPTION
    Borra el entorno virtual, configuracion, claves (.env) y el resto del proyecto.
    La carpeta del repositorio se eliminara al finalizar este script.
.EXAMPLE
    .\Uninstall-RouteAccidentBot.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$ConfirmWord = "BORRAR"

function Read-YesNo {
    param([string]$Prompt, [bool]$DefaultYes = $false)
    $hint = if ($DefaultYes) { "S/n" } else { "s/N" }
    $answer = (Read-Host "$Prompt ($hint)").Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($answer)) { return $DefaultYes }
    return $answer -in @("s", "si", "sí", "y", "yes")
}

Clear-Host
Write-Host ""
Write-Host "  Route Accident Bot - Desinstalacion completa" -ForegroundColor Red
Write-Host ""
Write-Host "  Se eliminara TODO en:" -ForegroundColor Yellow
Write-Host "    $ProjectRoot" -ForegroundColor White
Write-Host ""
Write-Host "  Incluye: codigo, venv, .env, configuracion y datos locales." -ForegroundColor Yellow
Write-Host "  Cierra el bot (consola o interfaz grafica) antes de continuar." -ForegroundColor Yellow
Write-Host ""

if (-not (Read-YesNo "  Continuar con la desinstalacion" $false)) {
    Write-Host "`n  Cancelado. No se borro nada.`n" -ForegroundColor Green
    exit 0
}

$typed = (Read-Host "  Escribe $ConfirmWord para confirmar").Trim()
if ($typed -ne $ConfirmWord) {
    Write-Host "`n  Confirmacion incorrecta. No se borro nada.`n" -ForegroundColor Green
    exit 0
}

Write-Host "`n  Eliminando archivos..." -ForegroundColor Cyan

$scriptPath = $PSCommandPath
$failed = [System.Collections.Generic.List[string]]::new()

Get-ChildItem -LiteralPath $ProjectRoot -Force | ForEach-Object {
    if ($_.FullName -eq $scriptPath) {
        return
    }
    try {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop
        Write-Host "  Eliminado: $($_.Name)" -ForegroundColor DarkGray
    } catch {
        $failed.Add($_.Name)
        Write-Host "  No se pudo eliminar: $($_.Name)" -ForegroundColor Yellow
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "  Algunos elementos siguen en uso. Cierra Python/terminal y ejecuta de nuevo," -ForegroundColor Yellow
    Write-Host "  o borra manualmente la carpeta:" -ForegroundColor Yellow
    Write-Host "    $ProjectRoot`n" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "  Programando eliminacion de la carpeta del proyecto..." -ForegroundColor Cyan

$deleteCmd = "timeout /t 2 /nobreak >nul & rmdir /s /q `"$ProjectRoot`""
Start-Process -FilePath "cmd.exe" -ArgumentList "/c $deleteCmd" -WindowStyle Hidden | Out-Null

Write-Host "  Desinstalacion completada. La carpeta desaparecera en unos segundos.`n" -ForegroundColor Green
exit 0