from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from python_repair import repair_python_syntax_if_requested


class TestPythonRepair(unittest.TestCase):
    def test_repairs_missing_colon_without_executing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            target = workdir / "programa_roto.py"
            target.write_text(
                "def calcular_cuadrado(numero):\n"
                "    return numero ** 2\n"
                "\n"
                "if calcular_cuadrado(5) > 10\n"
                "    print('Es mayor')\n",
                encoding="utf-8",
            )

            result = repair_python_syntax_if_requested(
                "Lee programa_roto.py, corrige el error de sintaxis y sobrescribe el archivo sin ejecutarlo",
                workdir,
            )

            self.assertIsNotNone(result)
            repaired = target.read_text(encoding="utf-8")
            self.assertIn("if calcular_cuadrado(5) > 10:\n", repaired)
            compile(repaired, str(target), "exec")

    def test_ignores_non_syntax_repair_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            target = workdir / "programa_roto.py"
            original = "if True\n    print('x')\n"
            target.write_text(original, encoding="utf-8")

            result = repair_python_syntax_if_requested("Resume programa_roto.py", workdir)

            self.assertIsNone(result)
            self.assertEqual(original, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
