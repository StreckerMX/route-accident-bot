# Route Accident Bot

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Google Maps Platform](https://img.shields.io/badge/Google%20Maps-Platform-4285F4?logo=googlemaps&logoColor=white)](https://developers.google.com/maps)
[![Telegram](https://img.shields.io/badge/Telegram-notifications-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

Analiza una ruta de Google Maps, detecta congestión severa, busca noticias del incidente y recomienda si conviene cambiar de ruta. Soporta alertas por Telegram.

> **¿Sin tarjeta de crédito?** Usa la versión gratuita: [route-accident-bot-free](https://github.com/StreckerMX/route-accident-bot-free)

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

Copia y pega en PowerShell (descarga/actualiza automáticamente desde GitHub):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; irm https://raw.githubusercontent.com/StreckerMX/route-accident-bot/main/Install-Remote.ps1 | iex
```

Se instala en `%LOCALAPPDATA%\RouteAccidentBot` y se abre la **interfaz gráfica** de configuración donde indicas:

1. API Keys de Google (Routes + Geocoding)
2. Enlace de Google Maps de tu ruta
3. Tipo de carretera: **cuota** o **libre**
4. Telegram *(opcional)*
5. Revisión automática cada 45 min *(opcional, checkbox)*

Vuelve a ejecutar el mismo comando cuando publique actualizaciones; conserva tu `.env` y configuración.

---

## Uso

Abre el acceso directo del escritorio **Route Accident Bot**, o ejecuta de nuevo el comando de instalación.

En la app: pega el enlace de Maps, elige **cuota/libre** y pulsa **Analizar ruta**. Opcionalmente activa **Revisar automáticamente cada 45 min**.

---

## Desinstalación

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; irm https://raw.githubusercontent.com/StreckerMX/route-accident-bot/main/Uninstall-RouteAccidentBot.ps1 | iex
```

Escribe `BORRAR` para confirmar. Cierra la aplicación antes.

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
  maps_link: "https://www.google.com/maps/dir/..."
  origin: "Tu origen"
  destination: "Tu destino"
  road_preference: "free"  # free | toll

monitor:
  periodic_enabled: false
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
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; irm https://raw.githubusercontent.com/StreckerMX/route-accident-bot/main/Install-Remote.ps1 | iex
```

Installs to `%LOCALAPPDATA%\RouteAccidentBot` and opens the setup GUI. Re-run to update without losing config.

## Run

Use the desktop shortcut or re-run the install command. Click **Analizar ruta** to analyze traffic. Optional automatic re-check every 45 minutes.

## Environment file (`.env`)

```env
GOOGLE_ROUTES_API_KEY=your_routes_api_key
GOOGLE_GEOCODING_API_KEY=your_geocoding_api_key
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## License

MIT