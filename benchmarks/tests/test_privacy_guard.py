from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from benchmarks.privacy_guard import (
    PrivacyEntityStore,
    anonymize_text,
    apply_privacy_to_workdir,
    hydrate_text,
    verify_redacted_text,
)


class PrivacyGuardTests(unittest.TestCase):
    def test_stable_tokens_and_hydration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "entity_map.jsonl"
            store = PrivacyEntityStore(store_path)
            text = (
                "Emilio Rodriguez vive en Calle Mayor 4, Madrid. "
                "Email emilio@example.com y telefono +34 600 111 222."
            )

            first = anonymize_text(text, store, mode="redacted")
            second = anonymize_text(text, store, mode="redacted")

            self.assertIn("PERSON_", first.redacted_text)
            self.assertIn("EMAIL_", first.redacted_text)
            self.assertIn("PHONE_", first.redacted_text)
            self.assertEqual(first.redacted_text, second.redacted_text)

            hydrated = hydrate_text(first.redacted_text, store)
            self.assertIn("Emilio Rodriguez", hydrated)
            self.assertIn("emilio@example.com", hydrated)

    def test_mixed_keeps_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PrivacyEntityStore(Path(tmp) / "entity_map.jsonl")
            text = "Noelia Castro escribio a clinica centro desde noelia.castro@clinicacentro.es"

            result = anonymize_text(text, store, mode="mixed")

            self.assertIn("Noelia Castro [PERSON_", result.mixed_text)
            self.assertIn("@", result.original_text)
            self.assertIn("EMAIL_", result.mixed_text)
            self.assertIn("PERSON_", result.redacted_text)

    def test_apply_privacy_to_workdir_creates_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "results" / "run-1" / "work" / "engine" / "task-01"
            root.mkdir(parents=True, exist_ok=True)
            source = root / "contactos.csv"
            source.write_text(
                "Nombre,Email,Telefono\nAna Lopez,ana@example.com,600111222\n",
                encoding="utf-8",
            )

            result = apply_privacy_to_workdir(root, mode="redacted", store_path=Path(tmp) / "store.jsonl")

            self.assertTrue(result.verification_passed)
            self.assertIn("PERSON_", source.read_text(encoding="utf-8"))

            privacy_root = Path(tmp) / "results" / "run-1" / "privacy" / "engine" / "task-01"
            self.assertTrue((privacy_root / "original" / "contactos.csv").exists())
            self.assertTrue((privacy_root / "mixed" / "contactos.csv").exists())
            self.assertTrue((privacy_root / "redacted" / "contactos.csv").exists())
            self.assertTrue((privacy_root / "report.json").exists())

    def test_verifier_flags_residuals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PrivacyEntityStore(Path(tmp) / "entity_map.jsonl")
            text = "Contacto directo: Ana Lopez, ana@example.com, 600111222."
            result = verify_redacted_text(text, store)
            self.assertFalse(result.passed)
            self.assertGreater(result.entity_count, 0)


if __name__ == "__main__":
    unittest.main()

