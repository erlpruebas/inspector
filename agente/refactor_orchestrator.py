import re
import os
from pathlib import Path

file_path = Path("D:/inspector/agente/telegram_codex_orchestrator/orchestrator.py")
text = file_path.read_text(encoding="utf-8")

# 1. Add _evaluate_desktop_context method to Orchestrator class
# We'll inject it just before _run_codex_desktop_and_reply
eval_code = """
    def _evaluate_desktop_context(self, instruction: str) -> bool:
        \"\"\"
        Captures the screen and uses Gemini Vision to determine if the 
        currently open chat matches the instruction. Returns True if we should
        continue the current chat, False to start a new chat.
        \"\"\"
        try:
            from orchestrator_v2.desktop_codex_operator import capture_desktop_screenshot
            import google.generativeai as genai
            import json
            
            # Capture
            run_dir = self.settings.codex_workdir / ".system_generated" / "vision_prechecks"
            run_dir.mkdir(parents=True, exist_ok=True)
            import time
            screenshot_path = run_dir / f"precheck_{int(time.time())}.png"
            capture_desktop_screenshot(screenshot_path)
            
            api_key = self.settings.google_api_key
            if not api_key:
                return False
                
            genai.configure(api_key=api_key)
            import PIL.Image
            img = PIL.Image.open(screenshot_path)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"El usuario quiere: '{instruction}'. \\nMira la conversacion de Codex Desktop en la captura. ¿Trata sobre esto o es algo util continuarla? Responde SOLO con un JSON: {{\"should_continue\": true/false, \"topic\": \"...\"}}"
            response = model.generate_content([prompt, img])
            
            match = re.search(r"```json\s*(\{.*?\})\s*```", response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                self.memory.write("vision_precheck", f"Context: {data.get('topic')}\\nDecision: {data.get('should_continue')}", "system")
                return bool(data.get("should_continue", False))
                
            # Fallback
            if "true" in response.text.lower():
                return True
        except Exception as exc:
            self.memory.write("vision_precheck_error", str(exc), "system")
        return False

    def _run_codex_desktop_and_reply(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord) -> None:"""

text = text.replace("    def _run_codex_desktop_and_reply(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord) -> None:", eval_code)

# 2. Modify _run_codex_desktop_and_reply to use the new method
target = """            result = run_desktop_codex_operator(
                instruction,
                send=True,
                new_chat=not bool(thread_record.codex_thread_id),
                wait_seconds=self.settings.codex_timeout_seconds,
                debug_draft=False,
                pause_after_paste=False,
            )"""

replacement = """            # Vision Pre-Check
            should_continue = self._evaluate_desktop_context(instruction)
            is_new_chat = not should_continue

            result = run_desktop_codex_operator(
                instruction,
                send=True,
                new_chat=is_new_chat,
                wait_seconds=self.settings.codex_timeout_seconds,
                debug_draft=False,
                pause_after_paste=False,
            )"""
            
text = text.replace(target, replacement)

# 3. Handle the new vision result from Operator
target_finish = """            response = (
                f"Codex Desktop termino con estado: {result.status}\\n"
                f"Directorio de ejecucion: {result.run_dir}\\n"
                f"Captura final: {result.screenshot_path or 'sin captura'}"
            )
            self.memory.write("""

replacement_finish = """            # Procesar el JSON de vision_result si existe
            vision_narrative = ""
            if result.extracted_tokens_path and result.extracted_tokens_path.exists():
                import json
                try:
                    vision_data = json.loads(result.extracted_tokens_path.read_text(encoding="utf-8"))
                    vision_narrative = vision_data.get("narrative", "")
                except:
                    pass

            response = (
                f"Codex Desktop termino con estado: {result.status}\\n"
                f"Resumen Visual: {vision_narrative}\\n"
                f"Captura final: {result.screenshot_path or 'sin captura'}"
            )
            self.memory.write("""

text = text.replace(target_finish, replacement_finish)

file_path.write_text(text, encoding="utf-8")
print("Refactoring applied successfully.")
