import re
import json
from pathlib import Path

file_path = Path("D:/inspector/agente/orchestrator_v2/desktop_codex_operator.py")
text = file_path.read_text(encoding="utf-8")

target = """    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content([
            "Extrae todos los tokens de bot de Telegram que veas en esta imagen. Devuelve solo los tokens (numero:letras), uno por linea, sin markdown ni comillas.",
            img
        ])
        text = response.text
    except Exception as exc:
        print(f"Error en Gemini Vision: {exc}")
        return None
        
    token_pattern = re.compile(r"\\b\d{8,12}:[A-Za-z0-9_-]{30,}\\b")
    tokens = token_pattern.findall(text)
    if not tokens:
        return None
    payload = {f"LAB_BOT_{index}_TOKEN": token for index, token in enumerate(tokens[:4], start=1)}
    path = run_dir / "telegram_bot_tokens.private.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path"""

replacement = """    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        prompt = (
            "Analiza esta captura de pantalla de Codex Desktop. "
            "Devuelve un JSON estricto con la siguiente estructura:\\n"
            "{\\n"
            '  "narrative": "El resumen narrativo de la respuesta que ha dado el asistente.",\\n'
            '  "files": ["rutas/a/archivos.txt", "mencionadas/en/la/interfaz.py"]\\n'
            "}\\n"
            "Si no hay archivos mencionados, la lista de archivos debe estar vacía. "
            "Asegúrate de que la salida sea SÓLO JSON."
        )
        response = model.generate_content([prompt, img])
        response_text = response.text
    except Exception as exc:
        print(f"Error en Gemini Vision: {exc}")
        return None
        
    import re
    import json
    json_match = re.search(r"```json\\s*(\\{.*?\\})\\s*```", response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)
        
    try:
        data = json.loads(response_text)
    except Exception:
        data = {"narrative": response_text, "files": []}
        
    path = run_dir / "vision_result.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path"""

text = text.replace(target, replacement)
file_path.write_text(text, encoding="utf-8")
print("Refactoring operator applied successfully.")
