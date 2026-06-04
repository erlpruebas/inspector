import sys
from pathlib import Path
import os
import time

sys.path.insert(0, "D:/inspector/agente/telegram_codex_orchestrator")

from config import load_settings
from orchestrator import Orchestrator
from thread_store import ThreadRecord

def main():
    os.environ["TELEGRAM_TRANSPORT"] = "none" # Avoid polling conflicts
    settings = load_settings()
    if not settings.ready:
        print("Settings not ready (no bot token or chat id)")
        return
        
    orchestrator = Orchestrator()
    
    test_cases = [
        ("Test 1: Navegador basico", "Abre el navegador, busca 'tiempo en Madrid' y dime cual es la temperatura actual."),
        ("Test 2: Escritura local", "Crea un archivo llamado prueba_codex.txt en el escritorio con el texto 'Hola, esto es una prueba de escritura'."),
        ("Test 3: Lectura local", "Lee el archivo prueba_codex.txt del escritorio y dime que pone."),
        ("Test 4: Navegacion y Escritura", "Busca informacion sobre la poblacion de Tokio y guarda un pequeno resumen en un archivo llamado tokio.txt en el escritorio."),
        ("Test 5: App de SO", "Abre la aplicacion Calculadora, calcula 25 por 45 y dime el resultado final.")
    ]
    
    print(f"Target User ID: {settings.telegram_allowed_user_id}")
    
    for i, (title, instruction) in enumerate(test_cases, 1):
        thread_name = f"test_thread_{i}"
        thread_record = ThreadRecord(name=thread_name, title=title)
        
        print(f"\n--- Iniciando {title} ---")
        print(f"Instruction: {instruction}")
        
        try:
            # BLOQUEO: Evita el error 'release unlocked lock'
            orchestrator._busy.acquire()
            
            orchestrator._run_codex_desktop_and_reply(
                chat_id=settings.telegram_allowed_user_id,
                instruction=instruction,
                source="test_script",
                thread_record=thread_record
            )
            print(f"-> Prueba '{title}' enviada al operador.")
        except Exception as e:
            print(f"-> Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
        print("Esperando 10 segundos antes de la siguiente prueba...")
        time.sleep(10)
        
    print("\n--- Bateria de pruebas finalizada ---")

if __name__ == "__main__":
    main()
