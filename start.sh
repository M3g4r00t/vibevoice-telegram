#!/bin/bash
# Iniciar VibeVoice Telegram Bot

# Mata procesos que usan la GPU en modo compute (NVIDIA)
# Requiere: nvidia-smi

set -euo pipefail

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi no está instalado o no es una GPU NVIDIA." >&2
  exit 1
fi

# Obtiene los PIDs de procesos de cómputo (C) reportados por nvidia-smi
mapfile -t PIDS < <(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -E '^[0-9]+')

if [ ${#PIDS[@]} -eq 0 ]; then
  echo "No hay procesos de cómputo usando la GPU."
  exit 0
fi

echo "Matando PIDs: ${PIDS[*]}"
# Envía SIGTERM primero; si necesitas forzar, cambia a -9
kill "${PIDS[@]}" || true

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
