from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add REPO_ROOT to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator import Orchestrator
from codex_runner import CodexResult
from speech_io import SpeechResult

class TestOrchestratorIntegration(unittest.TestCase):
    @patch('orchestrator.load_settings')
    @patch('orchestrator.TelegramApi')
    def setUp(self, mock_telegram_class, mock_load_settings):
        # Setup settings using real Settings class
        from config import load_settings
        import dataclasses
        settings = load_settings()
        self.mock_settings = dataclasses.replace(
            settings,
            telegram_bot_token="fake_token",
            telegram_allowed_user_id=12345,
            codex_workdir=REPO_ROOT / "temp_test_workdir",
            google_api_key="fake_google_key",
            google_model="gemini-2.5-flash-lite",
            google_intent_enabled=True,
            google_intent_timeout_seconds=20,
            bypass_confirmation=True,
            drain_pending_on_start=False,
            codex_model="gpt-5.5",
            codex_sandbox="workspace-write",
            codex_approval="never",
            codex_timeout_seconds=1800,
            message_chunk_size=3500,
            memory_file=REPO_ROOT / "temp_test_memory" / "events.txt",
            memories_file=REPO_ROOT / "temp_test_memory" / "memories.txt",
            threads_file=REPO_ROOT / "temp_test_memory" / "threads.json",
            pending_tasks_file=REPO_ROOT / "temp_test_memory" / "pending_tasks.json",
            alarms_file=REPO_ROOT / "temp_test_memory" / "alarms.json",
            voice_settings_file=REPO_ROOT / "temp_test_memory" / "voice_settings.json",
            voice_runtime_dir=REPO_ROOT / "temp_test_memory" / "voice",
            codex_command=["codex"],
            codex_dirs_file=REPO_ROOT / "temp_test_memory" / "codex_dirs.json",
            codex_extra_dirs=[],
            lab_mode=False,
        )
        mock_load_settings.return_value = self.mock_settings
        
        # Instantiate orchestrator
        self.orch = Orchestrator()
        
        # Force synchronous execution of Codex tasks in tests
        def sync_start_confirmed_codex(chat_id, instruction, source, thread_record, pending_task):
            if self.orch._busy.acquire(blocking=False):
                try:
                    self.orch._run_codex_and_reply(chat_id, instruction, source, thread_record, pending_task)
                except Exception:
                    if self.orch._busy.locked():
                        self.orch._busy.release()
                    raise
        self.orch._start_confirmed_codex = sync_start_confirmed_codex
        
        # Force voice states to True for testing synthesizers and speak calls
        self.orch.voice_state.voz = True
        self.orch.voice_state.altavoz = True
        
        # Mock download_file
        self.orch.telegram.download_file = MagicMock(side_effect=lambda file_id, dest: dest.touch() or dest)
        self.orch.telegram.send_message = MagicMock()
        self.orch.telegram.send_audio = MagicMock()
        
        # Mock speech synthesis and play
        self.orch.speech.synthesize = MagicMock(return_value=SpeechResult(provider="fake_tts", path=Path("fake_path.wav"), detail="ok"))
        self.orch.speech.play = MagicMock()

    def tearDown(self):
        # Cleanup temp files
        import shutil
        temp_dir = REPO_ROOT / "temp_test_memory"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_workdir = REPO_ROOT / "temp_test_workdir"
        if temp_workdir.exists():
            shutil.rmtree(temp_workdir)

    @patch('orchestrator.urllib.request.urlopen')
    def test_document_download_and_caption_execution(self, mock_urlopen):
        # Mock Intent Classification to avoid calling actual Google API
        from intent import Intent, ACTION_CODEX
        self.orch.interpreter.interpret = MagicMock(return_value=Intent(
            ACTION_CODEX,
            {"instruction": "Analiza las ventas en el archivo ventas_2026.xlsx y haz recomendaciones"}
        ))

        # Mock Gemini response for summary
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "Este es el resumen narrativo de la ejecucion realizada."}]}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock Codex run to return a long response to trigger summarization
        long_response = (
            "Resultado del analisis de ventas:\n\n"
            "1. El primer trimestre mostro un crecimiento de 15% debido a la campana de primavera.\n\n"
            "2. El segundo trimestre tuvo una desviacion por los costes de distribucion elevados.\n\n"
            "3. En conclusion, se recomienda negociar tarifas con proveedores locales para reducir costes.\n\n"
            "Este texto es largo y tiene suficientes parrafos y caracteres para disparar el resumen narrativo de Gemini."
        )
        self.orch.codex.run = MagicMock(return_value=CodexResult(returncode=0, stdout=long_response, stderr="", thread_id="fake_thread_id"))

        # Create simulated message update containing a document and a caption instruction
        update = {
            "update_id": 1001,
            "message": {
                "message_id": 501,
                "chat": {"id": 12345},
                "from": {"id": 12345},
                "document": {
                    "file_name": "ventas_2026.xlsx",
                    "file_id": "doc_123_xyz",
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "file_size": 25000
                },
                "caption": "Analiza las ventas en el archivo ventas_2026.xlsx y haz recomendaciones"
            }
        }

        # Handle simulated update
        self.orch._handle_update(update)

        # 1. Assert file was downloaded to the inbox and exists in the active thread's workdir
        expected_download_path = Path(self.orch.threads.active().workdir) / "ventas_2026.xlsx"
        expected_inbox_path = Path(self.orch.settings.codex_workdir) / "inbox" / "ventas_2026.xlsx"
        self.assertTrue(expected_download_path.exists(), "El archivo Excel no fue descargado/copiado en el workdir")
        self.orch.telegram.download_file.assert_called_once_with("doc_123_xyz", expected_inbox_path)

        # 2. Assert Codex was called with the instruction
        self.orch.codex.run.assert_called_once_with(
            "Analiza las ventas en el archivo ventas_2026.xlsx y haz recomendaciones\n\n[System Note: The following files are available in your working directory (workspace): ventas_2026.xlsx]",
            thread_id=""
        )


        # 3. Assert Gemini summarizer was called for TTS
        # urllib.request.urlopen should have been called to fetch the Gemini summary
        mock_urlopen.assert_called()

        # 4. Assert speech synthesis was called and the last call was with the Gemini summary text
        self.assertTrue(self.orch.speech.synthesize.called)
        synthesize_args = self.orch.speech.synthesize.call_args[0]
        self.assertEqual(synthesize_args[0], "Este es el resumen narrativo de la ejecucion realizada.")

        # 5. Assert voice playback was called and audio sent by Telegram
        self.assertTrue(self.orch.speech.play.called)
        self.orch.speech.play.assert_called_with(Path("fake_path.wav"))
        self.assertTrue(self.orch.telegram.send_audio.called)
        self.orch.telegram.send_audio.assert_called_with(12345, Path("fake_path.wav"), caption="Voz: fake_tts")

        # 6. Assert telegram got the full text first, and then the voice summary text
        messages_sent = [call[0][1] for call in self.orch.telegram.send_message.call_args_list]
        self.assertIn("Archivo `ventas_2026.xlsx` aceptado y guardado en bandeja de entrada e hilo", messages_sent[0])
        self.assertIn("Recibido. Trabajo en el hilo", messages_sent[1])
        self.assertIn(long_response, messages_sent[2])
        self.assertIn("Resumen para voz:\nEste es el resumen narrativo de la ejecucion realizada.", messages_sent[3])

        print("\n\n>>> INTEGRATION TEST PASSED SUCCESSFULLY! <<<\n\n")

if __name__ == "__main__":
    unittest.main()
