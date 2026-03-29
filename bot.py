#!/usr/bin/env python3
"""
VibeVoice Telegram Bot
Un bot de Telegram que usa VibeVoice para generar audio en español.
Ahora con transcripción de voz usando Whisper.
"""

import os
import re
import torch
import logging
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update, Voice
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import whisper

# Importar VibeVoice
from vibevoice.modular.modeling_vibevoice_streaming_inference import VibeVoiceStreamingForConditionalGenerationInference
from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor

# Configuración
MODEL_PATH = "microsoft/VibeVoice-Realtime-0.5B"
OUTPUT_DIR = "/media/dennys/data-linux/projects/vibevoice-telegram/outputs"
VOICE_NAME = "sp-Spk0_woman"  # Voz en español

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variables globales para el modelo
model: Optional[VibeVoiceStreamingForConditionalGenerationInference] = None
processor: Optional[VibeVoiceStreamingProcessor] = None
whisper_model = None  # Modelo para transcripción
debug_mode = False


class VoiceManager:
    """Gestor de voces disponibles"""
    
    def __init__(self):
        self.voices_dir = Path(__file__).parent / "VibeVoice" / "demo" / "voices" / "streaming_model"
        self.available_voices = self._scan_voices()
    
    def _scan_voices(self) -> dict:
        """Escanea voces disponibles"""
        voices = {}
        if self.voices_dir.exists():
            for voice_file in self.voices_dir.glob("*.pt"):
                name = voice_file.stem
                voices[name] = str(voice_file)
        return voices
    
    def get_voice_path(self, voice_name: str = VOICE_NAME) -> str:
        """Obtiene la ruta de la voz"""
        # Buscar coincidencia
        for name, path in self.available_voices.items():
            if voice_name.lower() in name.lower():
                return path
        
        # Por defecto devolver una voz en español
        for name, path in self.available_voices.items():
            if name.startswith("sp-"):
                return path
        
        # Si no hay español, devolver la primera voz disponible
        return list(self.available_voices.values())[0] if self.available_voices else ""


async def load_model():
    """Carga el modelo VibeVoice y Whisper"""
    global model, processor, whisper_model
    
    logger.info(f"Cargando modelo VibeVoice desde {MODEL_PATH}...")
    
    # Determinar dispositivo
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    logger.info(f"Usando dispositivo: {device}")
    
    # Cargar processor
    processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_PATH)
    
    # Cargar modelo
    if device == "cuda":
        # Usa sdpa por compatibilidad; flash-attn no es obligatorio
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map="cuda",
            attn_implementation="sdpa"
        )
    elif device == "mps":
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float32,
            attn_implementation="sdpa"
        )
        model.to("mps")
    else:
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float32,
            device_map="cpu",
            attn_implementation="sdpa"
        )
    
    model.eval()
    model.set_ddpm_inference_steps(num_steps=5)
    
    logger.info("Modelo VibeVoice cargado correctamente")
    
    # Cargar modelo Whisper para transcripción
    logger.info("Cargando modelo Whisper para transcripción...")
    whisper_device = "cuda" if torch.cuda.is_available() else "cpu"
    whisper_model = whisper.load_model("medium", device=whisper_device)
    logger.info(f"Modelo Whisper cargado en {whisper_device}")


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio a texto usando Whisper"""
    global whisper_model
    
    if whisper_model is None:
        raise RuntimeError("Modelo Whisper no cargado")
    
    # Transcribir
    result = whisper_model.transcribe(audio_path, language="es")
    return result["text"].strip()


def generate_audio(text: str, voice_name: str = VOICE_NAME) -> str:
    """Genera audio a partir de texto"""
    global model, processor
    
    if model is None or processor is None:
        raise RuntimeError("Modelo no cargado")
    
    # Limpiar texto
    text = text.replace("'", "'").replace('"', '"').replace('"', '"')
    
    # Obtener voz
    voice_manager = VoiceManager()
    voice_path = voice_manager.get_voice_path(voice_name)
    voice_sample = torch.load(voice_path, map_location="cuda" if torch.cuda.is_available() else "cpu", weights_only=False)
    
    # Procesar entrada
    inputs = processor.process_input_with_cached_prompt(
        text=text,
        cached_prompt=voice_sample,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    
    # Mover a dispositivo
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for k, v in inputs.items():
        if torch.is_tensor(v):
            inputs[k] = v.to(device)
    
    # Generar audio
    outputs = model.generate(
        **inputs,
        max_new_tokens=None,
        cfg_scale=1.5,
        tokenizer=processor.tokenizer,
        generation_config={'do_sample': False},
        verbose=False,
        all_prefilled_outputs=voice_sample
    )
    
    # Guardar audio
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"vibevoice_{hash(text)}.wav")
    processor.save_audio(outputs.speech_outputs[0], output_path=output_path)
    
    return output_path


# Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    await update.message.reply_text(
        "🎙️ ¡Hola! Soy el bot de VibeVoice.\n\n"
        "Puedo hacer dos cosas:\n"
        "• 📝→🎤 Envíame texto y lo convertiré en audio\n"
        "• 🎤→📝 Envíame un mensaje de voz y lo transcribiré\n\n"
        "Comandos disponibles:\n"
        "/start - Ver este mensaje\n"
        "/voices - Ver voces disponibles\n"
        "/help - Ayuda"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    await update.message.reply_text(
        "📖 *Cómo usarme:*\n\n"
        "*Texto a voz (TTS):*\n"
        "1. Envíame cualquier texto\n"
        "2. Yo lo convertiré en audio\n\n"
        "*Voz a texto (Transcripción):*\n"
        "1. Envíame un mensaje de voz\n"
        "2. Yo lo transcribiré a texto\n\n"
        "Puedes usar /voices para ver las voces disponibles.\n"
        "Activa métricas con /debug on (por defecto está off).",
        parse_mode="Markdown"
    )


async def voices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /voices"""
    voice_manager = VoiceManager()
    voices_list = "\n".join([f"• <code>{v}</code>" for v in sorted(voice_manager.available_voices.keys())])

    await update.message.reply_text(
        "🎭 <b>Voces disponibles:</b>\n\n" + voices_list,
        parse_mode=ParseMode.HTML
    )


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa/desactiva modo debug (muestra latencia)."""
    global debug_mode
    if not context.args:
        estado = "on" if debug_mode else "off"
        await update.message.reply_text(f"Modo debug está {estado}. Usa /debug on|off")
        return
    arg = context.args[0].lower()
    if arg not in ("on", "off"):
        await update.message.reply_text("Usa /debug on o /debug off")
        return
    debug_mode = (arg == "on")
    await update.message.reply_text(f"✅ Debug {arg}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto"""
    text = update.message.text
    
    # Ignorar comandos
    if text.startswith('/'):
        return
    
    # Enviar mensaje de "escribiendo"
    await update.message.chat.send_action("upload_voice")
    
    try:
        t0 = time.time()
        # Generar audio
        audio_path = generate_audio(text)
        
        # Enviar audio
        with open(audio_path, 'rb') as audio_file:
            await update.message.reply_voice(audio_file)
        
        # Limpiar archivo temporal
        os.remove(audio_path)
        
        if debug_mode:
            dt = time.time() - t0
            await update.message.reply_text(f"⏱️ Latencia: {dt:.2f}s")
        
    except Exception as e:
        logger.error(f"Error generando audio: {e}")
        await update.message.reply_text(
            f"❌ Error al generar audio: {str(e)}"
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de voz - los transcribe a texto"""
    voice = update.message.voice
    
    if not voice:
        return
    
    # Enviar mensaje de "escribiendo"
    await update.message.chat.send_action("typing")
    
    try:
        t0 = time.time()
        
        # Descargar el archivo de voz
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
            await voice_file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Transcribir
            transcription = transcribe_audio(tmp_path)
            
            if debug_mode:
                dt = time.time() - t0
                await update.message.reply_text(
                    f"📝 *Transcripción:*\n\n{transcription}\n\n⏱️ Tiempo: {dt:.2f}s",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"📝 *Transcripción:*\n\n{transcription}",
                    parse_mode="Markdown"
                )
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
    except Exception as e:
        logger.error(f"Error transcribiendo audio: {e}")
        await update.message.reply_text(
            f"❌ Error al transcribir: {str(e)}"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores"""
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Ha ocurrido un error. Por favor intenta de nuevo."
        )


def main():
    """Inicia el bot"""
    # Token de Telegram (configurable via variable de entorno)
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
    
    if not TELEGRAM_TOKEN:
        logger.error("No se ha configurado TELEGRAM_TOKEN")
        print("Error: Configura TELEGRAM_TOKEN")
        return
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voices", voices_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_error_handler(error_handler)
    
    # Cargar modelo al iniciar
    print("Cargando modelo VibeVoice...")
    asyncio.run(load_model())
    
    # Iniciar bot
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
