# Route Accident Bot

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Google Maps Platform](https://img.shields.io/badge/Google%20Maps-Platform-4285F4?logo=googlemaps&logoColor=white)](https://developers.google.com/maps)
[![Telegram](https://img.shields.io/badge/Telegram-notifications-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

Monitorea una ruta de Google Maps, detecta congestión severa, busca noticias del incidente y recomienda si conviene cambiar de ruta. Soporta alertas por Telegram.

[English version](#english)

---

## Requisitos

- Windows con **Python 3.10+**
- Cuenta en [Google Cloud](https://console.cloud.google.com/)
- Dos API Keys (o una misma clave con ambas APIs habilitadas):
  - [Routes API](https://console.cloud.google.com/apis/library/routes.googleapis.com)
  - [Geocoding API](https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com)
- *(Opcional)* Bot de Telegram

---

## Instalación (Windows)

Copia y pega en PowerShell:

```powershell
git clone https://github.com/StreckerMX/route-accident-bot.git; cd route-accident-bot; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\Install-RouteAccidentBot.ps1
```

El instalador solicitará:

1. **API Key — Routes API**
2. **API Key — Geocoding API** (puedes usar la misma clave)
3. Origen y destino de tu ruta
4. Telegram *(opcional)*

---

## Uso

```powershell
.\Start-RouteAccidentBot.ps1
```

Presiona `Ctrl+C` para detener el monitoreo.

**Configuración por defecto:**
- Revisión cada **45 minutos**
- Alerta solo si el retraso supera **13 minutos**

---

## Configuración manual

### Archivo `.env`

```env
GOOGLE_ROUTES_API_KEY=tu_clave_routes_api
GOOGLE_GEOCODING_API_KEY=tu_clave_geocoding_api

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

### Archivo `RouteAccidentBot.Settings.yaml`

```yaml
route:
  origin: "Tu origen"
  destination: "Tu destino"

monitor:
  interval_minutes: 45
  jam_delay_threshold_minutes: 13

telegram:
  enabled: false
  notify_on_alert: true
```

---

## Obtener las API Keys de Google

1. Entra a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea o selecciona un proyecto
3. Habilita **Routes API** y **Geocoding API**
4. Ve a **Credenciales → Crear credenciales → Clave de API**
5. Restringe cada clave a su API correspondiente

---

## Telegram (opcional)

1. Crea un bot con [@BotFather](https://t.me/BotFather) → `/newbot`
2. Obtén tu Chat ID con [@userinfobot](https://t.me/userinfobot)
3. Envía `/start` a tu bot
4. Agrega token y Chat ID en `.env`
5. Activa en `RouteAccidentBot.Settings.yaml`:

```yaml
telegram:
  enabled: true
```

---

## Solución de problemas

| Problema | Qué hacer |
|----------|-----------|
| Error con API Key | Verifica que Routes API y Geocoding API estén habilitadas |
| `403 PERMISSION_DENIED` | Revisa que cada clave tenga acceso a su API |
| No llegan mensajes de Telegram | Envía `/start` a tu bot antes de usarlo |
| Sin rutas disponibles | Revisa origen y destino en `RouteAccidentBot.Settings.yaml` |

---

## Licencia

MIT

---

# English

Traffic route monitor for Google Maps with news investigation, route recommendations, and optional Telegram alerts.

## Requirements

- Windows with **Python 3.10+**
- [Google Cloud](https://console.cloud.google.com/) account
- Two API keys (or one key with both APIs enabled):
  - Routes API
  - Geocoding API
- *(Optional)* Telegram bot

## Install (Windows)

```powershell
git clone https://github.com/StreckerMX/route-accident-bot.git; cd route-accident-bot; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\Install-RouteAccidentBot.ps1
```

## Run

```powershell
.\Start-RouteAccidentBot.ps1
```

**Defaults:** check every **45 minutes**, alert when delay exceeds **13 minutes**.

## Environment file (`.env`)

```env
GOOGLE_ROUTES_API_KEY=your_routes_api_key
GOOGLE_GEOCODING_API_KEY=your_geocoding_api_key
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## License

MIT