We are inside a dedicated model probe run directory.

Goal:
Investigate whether provider `groq` works for this intent:
comprobar desde esta maquina si Groq funciona para listar modelos, chat ligero, transcripcion STT y TTS; documentar errores exactos y configuracion recomendada

Inputs:
- If no model is specified, discover the most relevant current model for the stated intent.
- Find the official documentation yourself before using third-party sources.
- The provider API key is available only through environment variables:
  - `GROQ_API_KEY`
  - `PROVIDER_API_KEY`

Rules:
- Do not print or write the API key.
- Prefer official documentation and official API endpoints.
- Create small reproducible tests in this run directory.
- Execute the tests and record exact commands, timings, HTTP status, and observed errors.
- If a test fails, propose the most likely fixes and how to verify them.
- Keep artifacts local to this run directory.

Required final report:
1. Verdict: works / partially works / does not work.
2. What was tested.
3. Exact result of each test.
4. Recommended configuration.
5. Next fixes if blocked.