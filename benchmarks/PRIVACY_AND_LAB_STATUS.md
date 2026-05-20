# Privacy And Lab Status

Estado vivo del laboratorio de privacidad, anonimización y benchmark.

## Lo que ya está implementado

- `benchmarks/privacy_guard/`
  - `detectors.py`
  - `entity_store.py`
  - `anonymizer.py`
  - `verifier.py`
  - `mini_nano_review.py`
  - `cli.py`
- Integración de privacidad en:
  - `benchmarks/benchmark_scheduler.py`
  - `benchmarks/multi_runner.py`
  - `benchmarks/benchmark_main.py`
- Exclusión de carpetas `privacy/` en los contextos de workspace para no filtrar artefactos anonimizados a los modelos.
- `benchmarks/tasks/privacy_tasks.json`
- Tests unitarios:
  - `benchmarks/tests/test_privacy_guard.py`

## Decisiones actuales

- El mapa de entidades es global y coherente entre documentos.
- La copia mixta usa formato:
  - `Texto original [TOKEN_0001]`
- La copia redacted usa solo token:
  - `TOKEN_0001`
- El almacenamiento del mapa vive fuera del contexto que ve el modelo.
- Mini Nano se usa como revisor semántico opcional, no como única defensa.
- La parte algorítmica sigue siendo la primera capa.

## Resultado de las pruebas

### Anonimización local

- `python -m unittest benchmarks.tests.test_privacy_guard`
  - OK
- `python benchmarks/privacy_guard/cli.py --help`
  - OK
- `python benchmarks/privacy_guard/cli.py anonymize ...`
  - OK

### Smoke tests de benchmark privado

- `groq:llama-3.1-8b-instant`
  - OK en `privacy-02`
  - tiempo total aproximado: 0.65 s
- `openrouter:deepseek/deepseek-v3.2`
  - OK en `privacy-01`
  - tiempo total aproximado: 11.1 s
  - coste aproximado: `0.0001134756`
- `codex:gpt-5.4-mini`
  - OK en el run multiusuario privado
  - tiempo aproximado: 63 s por tarea en el corte actual
- `gemini_api:gemini-2.5-flash-lite`
  - OK en el run multiusuario privado
  - más lento que Groq, más ágil que Codex
- `vikingnano:gemini-nano-local`
  - disponible de forma intermitente / sensible a timeout

### Salud de proveedores

- `provider_health.py --live`
  - `codex`: OK
  - `groq`: OK
  - `openrouter`: OK
  - `gemini_api`: OK
  - `vikingnano`: timeout
  - `lmstudio`: fail local en esta máquina

## Cambios recientes útiles

- Se ajustó `openrouter` para pedir menos tokens de salida por defecto:
  - `BENCH_OPENROUTER_MAX_TOKENS=384`
- La CLI de `privacy_guard` ya funciona como script directo y como módulo.
- La detección de organizaciones se corrigió para no comerse nombres de persona ni correos.
- El orquestador multiusuario ya corre con 4 carriles paralelos y carpetas separadas.
- Se generó un informe HTML vivo en:
  - [lab_report.html](d:/inspector/benchmarks/results/20260519_180015_234962/lab_report.html)
- El reporte actual queda reflejado también en:
  - [latest_lab_report.html](d:/inspector/benchmarks/results/latest_lab_report.html)

## Comandos útiles

### Ver salud de proveedores

```powershell
python .\benchmarks\provider_health.py --live
```

### Probar anonimización local

```powershell
python .\benchmarks\privacy_guard\cli.py anonymize --input .\ruta\archivo.txt --out-dir .\salida --mode redacted
```

### Correr una tarea privada con Groq

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\privacy_tasks.json --engine groq:llama-3.1-8b-instant --task privacy-02 --privacy-mode redacted --privacy-review none --once --no-grade
```

### Correr una tarea privada con OpenRouter

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\privacy_tasks.json --engine openrouter:deepseek/deepseek-v3.2 --task privacy-01 --privacy-mode redacted --privacy-review none --once --no-grade
```

### Correr el orquestador de cuatro usuarios

```powershell
python .\benchmarks\multi_user_orchestrator.py --tasks-file .\benchmarks\tasks\privacy_tasks.json --task privacy-01 --task privacy-02 --task privacy-03 --task privacy-04 --users 4 --engine groq:llama-3.1-8b-instant --engine openrouter:deepseek/deepseek-v3.2 --engine gemini_api:gemini-2.5-flash-lite --engine codex:gpt-5.4-mini --privacy-mode redacted --privacy-review none --no-grade
```

## Lectura práctica

- Para extracción, limpieza y tareas cortas, Groq está funcionando muy bien en latencia.
- OpenRouter DeepSeek ya es usable de verdad dentro del laboratorio, pero conviene mantener un techo de salida más bajo.
- Codex 5.4 mini ya está validado en el modo privado y sirve como agente serio, aunque es el más lento del grupo.
- Gemini Flash-Lite queda muy bien como validación barata y apoyo.
- Mini Nano sigue siendo útil como apoyo local, pero no todavía como motor principal de benchmark largo.
- La arquitectura privada es viable y no filtra el material anonimizando al contexto del modelo.

## Siguiente paso recomendado

1. Ampliar `privacy_tasks.json` con más casos sintéticos.
2. Correr una batería pequeña en `groq`, `openrouter` y `gemini_api`.
3. Añadir revisión con Mini Nano por chunks pequeños.
4. Generar el informe HTML final con comparación:
   - calidad
   - coste
   - latencia
   - pérdida por anonimización
   - fallos técnicos

## Estado a día de hoy

La pieza funcional final del sistema de anonimización ya está en sitio y el orquestador multiusuario también. Lo que queda por seguir refinando es la capa de conclusiones finas, sobre todo para Mini Nano y para ampliar el banco sintético con más profesiones, pero la base ya sirve para empezar pruebas reales sin mezclar datos ni carriles.
