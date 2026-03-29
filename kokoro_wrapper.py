#!/usr/bin/env python3
"""Wrapper para Kokoro TTS que evita el error de externally-managed-environment"""
import subprocess
import sys
import os
import uuid

OUTPUT_DIR = "/media/dennys/data-linux/projects/vibevoice-telegram/outputs"
PYTHON_BIN = "/media/dennys/data-linux/projects/vibevoice-telegram/vibevoice_env/bin/python3"

def generate_speech(text: str, voice: str = "af_sarah", speed: float = 1.0) -> str:
    """Genera speech usando kokoro CLI"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_file = os.path.join(OUTPUT_DIR, f"kokoro_{uuid.uuid4().hex}.wav")
    
    # Forzar python3.12 que tiene torch
    cmd = [
        PYTHON_BIN, "-m", "kokoro", 
        "-t", text,
        "-m", voice,
        "-s", str(speed),
        "-o", output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Si hay error de environment, intentar con python3.12 y --break-system-packages
    if "externally-managed-environment" in result.stderr:
        # Ejecutar directamente el modulo kokoro
        cmd = [
            PYTHON_BIN, "-c",
            f"""
import os
os.environ['HF_HUB_DISABLE'] = '1'
from kokoro import KPipeline
import soundfile as sf
p = KPipeline('{voice[0]}')
a = p('{text}', voice='{voice}')
sf.write('{output_file}', a, 24000)
print('OK')
"""
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
    if result.returncode != 0 and "OK" not in result.stdout:
        # Print para debug
        print(f"stderr: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Kokoro error: {result.stderr[:200]}")
    
    return output_file

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hola mundo"
    output = generate_speech(text)
    print(f"Audio: {output}")
