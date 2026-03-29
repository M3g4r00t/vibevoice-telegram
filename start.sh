#!/bin/bash
# Iniciar VibeVoice Telegram Bot

cd /media/dennys/data-linux/projects/vibevoice-telegram

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

export PYTHONPATH="/media/dennys/data-linux/projects/vibevoice-telegram/VibeVoice:$PYTHONPATH"

echo "Iniciando VibeVoice Telegram Bot..."
./vibevoice_env/bin/python3 bot.py
