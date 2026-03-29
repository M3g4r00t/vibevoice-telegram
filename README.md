# VibeVoice Telegram Bot 🤖🎙️

Un bot de Telegram que usa **VibeVoice** (Microsoft) para convertir texto en audio realista en español.

## Características

- 🎙️ Generación de audio a partir de texto usando IA
- 🇪🇸 Soporte para español
- 🚀 Integración con Telegram
- 🔊 Varias voces disponibles

## Requisitos

- Python 3.10+
- Token de bot de Telegram
- CUDA (recomendado) o CPU

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/vibevoice-telegram.git
cd vibevoice-telegram
```

2. Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Descargar voces adicionales (opcional):
```bash
cd VibeVoice/demo
bash download_experimental_voices.sh
```

## Configuración

1. Crear un bot en Telegram con @BotFather y obtener el token.

2. Crear archivo `.env`:
```bash
cp .env.example .env
```

3. Editar `.env` con tu token:
```
TELEGRAM_TOKEN=tu_token_aqui
```

## Uso rápido

Iniciar el bot (carga `.env`, ajusta `PYTHONPATH` y usa el venv):
```bash
bash start.sh
```

### Comandos del bot

- `/start`   – mensaje de bienvenida y defaults
- `/help`    – ayuda y recordatorio de comandos
- `/voices`  – lista voces disponibles
- `/voice <nombre>` – cambia la voz (motor activo)
- `/engine kokoro|vibevoice` – selecciona motor
- `/vvsteps <2-10>` – pasos de difusión (solo VibeVoice). Por defecto: 5 (versión original).
- `/debug on|off` – métricas de latencia (por defecto: off)

### Valores por defecto
- Motor: `vibevoice`
- Modelo: `microsoft/VibeVoice-Realtime-0.5B`
- Voz: `sp-Spk0_woman`
- Pasos de difusión: 5
- Debug: OFF

## Estructura del Proyecto

```
vibevoice-telegram/
├── VibeVoice/          # Código de VibeVoice (submódulo o clonado)
├── bot.py              # Código del bot de Telegram
├── requirements.txt    # Dependencias de Python
├── README.md           # Este archivo
└── .env                # Configuración (no commitear)
```

## Notas

- El modelo VibeVoice-Realtime-0.5B es primarily para inglés, pero puede generar español con resultados variables.
- Para mejor calidad en español, considera usar VibeVoice-TTS completo.
- Se requiere GPU para tiempo real decente.
- Si usas VibeVoice en CPU la latencia será alta.
- Si ves `Conflict: terminated by other getUpdates request`, asegúrate de correr solo una instancia del bot.

## Licencia

MIT License - Ver LICENSE para más detalles.

## Créditos

- [VibeVoice](https://github.com/microsoft/VibeVoice) por Microsoft
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
