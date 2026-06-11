from __future__ import annotations

import sys
from pathlib import Path

# Add REPO_ROOT to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import load_settings
from intent import IntentInterpreter, ACTION_NEW_THREAD, ACTION_SWITCH_THREAD, ACTION_CODEX, ACTION_REMEMBER, ACTION_CREATE_ALARM

TEST_PHRASES = [
    # 1. Simple thread management
    "nuevo hilo facturas",
    "/nuevo_hilo facturas",
    "usar hilo facturas",
    "/usar_hilo facturas",
    "abre una conversación nueva",
    
    # 2. Combined thread + instruction commands (The ones causing issues!)
    "Abre un hilo nuevo sobre facturas y resume el archivo facturas.txt",
    "Crea una conversación nueva y haz un análisis del proyecto",
    "En el hilo facturas, calcula el IVA de facturas.txt",
    "abre una conversación sobre compras y descarga el presupuesto",
    
    # 3. Simple text commands for Codex
    "/codex dime la fecha de ayer",
    "dime la fecha de ayer",
    
    # 4. Remember facts vs instructions
    "recuerda que la contraseña del wifi es 1234",
    "recuerda analizar el archivo mañana",
    "guarda en memoria que el servidor usa el puerto 8080",
    "ten en cuenta borrar los archivos temporales de d:\\inspector",
    
    # 5. Alarms
    "Avisame dentro de dos minutos que encienda el ordenador",
    "Ponme una alarma mañana a las 9 para revisar el correo"
]

def run_tests():
    print("Cargando configuración...")
    settings = load_settings()
    print(f"Clave de API Google: {'Configurada' if settings.google_api_key else 'No configurada'}")
    print(f"Modelo Google Intent: {settings.google_model}")
    print(f"Google Intent Activado: {settings.google_intent_enabled}\n")
    
    interpreter = IntentInterpreter(settings)
    
    print(f"{'FRASE ORIGINAL':<75} | {'ACCIÓN':<20} | {'DETALLES':<50}")
    print("-" * 155)
    
    for phrase in TEST_PHRASES:
        try:
            intent = interpreter.interpret(phrase)
            args_str = str(intent.args)
            print(f"{phrase[:73]:<75} | {intent.action:<20} | {args_str[:48]:<50} (source: {intent.source})")
        except Exception as exc:
            print(f"{phrase[:73]:<75} | ERROR                | {str(exc)[:48]:<50}")

if __name__ == "__main__":
    run_tests()
