import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, "D:/inspector/agente")

from orchestrator_v2.desktop_codex_operator import run_desktop_codex_operator

def test_codex(prompt: str, new_chat: bool = True):
    print(f"Testing Codex Desktop with prompt: {prompt}")
    result = run_desktop_codex_operator(
        prompt,
        send=True,
        new_chat=new_chat,
        wait_seconds=60,
        debug_draft=False,
        pause_after_paste=False
    )
    
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")
    
    if result.extracted_tokens_path and result.extracted_tokens_path.exists():
        import json
        try:
            data = json.loads(result.extracted_tokens_path.read_text(encoding="utf-8"))
            print("--- Respuesta Extraida por Gemini Vision ---")
            print(data.get("narrative", ""))
            print("Archivos: ", data.get("files", []))
            print("--------------------------------------------")
        except Exception as e:
            print("Error parsing vision result:", e)
    else:
        print("No vision result extracted.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_codex(sys.argv[1])
    else:
        test_codex("Abre el navegador, busca en Google 'tiempo en Madrid', y dime la temperatura actual.")
