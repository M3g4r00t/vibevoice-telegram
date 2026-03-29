#!/usr/bin/env python3
"""Wrapper para Kokoro TTS"""
import subprocess
import sys
import os
import uuid
import argparse

OUTPUT_DIR = "/media/dennys/data-linux/projects/vibevoice-telegram/outputs"

def generate_speech(text: str, voice: str = "af_sarah", speed: float = 1.0) -> str:
    """Genera speech usando kokoro CLI"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_file = os.path.join(OUTPUT_DIR, f"kokoro_{uuid.uuid4().hex}.wav")
    
    cmd = [
        "kokoro",
        "-t", text,
        "-m", voice,
        "-s", str(speed),
        "-o", output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Kokoro error: {result.stderr}")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", required=True)
    parser.add_argument("-m", "--voice", default="af_sarah")
    parser.add_argument("-s", "--speed", type=float, default=1.0)
    args = parser.parse_args()
    
    output = generate_speech(args.text, args.voice, args.speed)
    print(f"Audio: {output}")
