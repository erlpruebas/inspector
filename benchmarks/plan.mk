Sí. Usaría estos 40 minutos de GPT-5.5 **solo para fijar arquitectura y criterios**, y luego pasaría la ejecución pesada a 5.4-mini. Con 20% de ventana restante no conviene empezar una implementación larga ahora: mejor dejamos el mapa perfecto y evitamos quedarnos a medias.

Primero, una precisión: un plan de 20 €/mes suele ser **Plus**, no Pro. Pero para la estrategia da igual: tomo como verdad operativa lo que me dices, que tenemos una ventana de 5 horas, queda 20%, y resetea en 40 minutos.

**Lo Que Dice La Comunidad**
Las mejores soluciones no usan solo LLM. La línea dominante es **híbrida**:

- **Reglas y detectores deterministas** para emails, teléfonos, DNI/NIF, IBAN, URLs, matrículas, fechas, importes, códigos.
- **NER / PII analyzer** para nombres, organizaciones, ubicaciones y entidades menos regulares.
- **Modelo local** para casos semánticos difíciles: “mi jefe”, “el cliente de Vigo”, “la hija de Antonio”, referencias indirectas.
- **Mapa local persistente** para poder reidentificar internamente sin mandar datos reales fuera.

Esto encaja con Microsoft Presidio, que separa análisis PII y anonimización con operadores configurables. Presidio permite detección personalizable y anonimización/deanonimización. Google Sensitive Data Protection plantea transformaciones como masking, tokenization y surrogate tokens, y NIST insiste en que desidentificar no es binario: hay que medir riesgo de reidentificación.  
Fuentes: [Microsoft Presidio](https://microsoft.github.io/presidio/), [Presidio anonymizer](https://microsoft.github.io/presidio/anonymizer/), [Google de-identification](https://cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data), [Google transformations](https://cloud.google.com/sensitive-data-protection/docs/transformations-reference), [NIST IR 8053](https://csrc.nist.gov/pubs/ir/8053/final), [NIST SP 800-122](https://www.nist.gov/publications/guide-protecting-confidentiality-personally-identifiable-information-pii).

**Decisión De Arquitectura**
Yo implementaría un sistema llamado, por ejemplo, `privacy_guard`, con tres salidas por documento:

```text
original/
  contrato_001.txt

mixed/
  contrato_001.mixed.txt
  "Emilio Rodriguez [PERSON_0015] vive en Calle Mayor 4 [ADDRESS_0007]"

redacted/
  contrato_001.redacted.txt
  "PERSON_0015 vive en ADDRESS_0007"

maps/
  entity_map.sqlite o entity_map.jsonl cifrado
```

Elegiría **corchetes** para la copia mixta: `Emilio Rodriguez [PERSON_0015]`. Es más fácil de parsear, menos ambiguo que la barra, y los modelos suelen respetar bien tokens delimitados.

La sustitución debe ser **global y estable**. Si `Javier Martinez Lopez` es `PERSON_0015`, lo es en todos los documentos, todas las tareas y todos los días. Su teléfono será otro token estable, por ejemplo `PHONE_0025`. No mezclaría entidad persona y teléfono en el mismo ID salvo que creemos relaciones en el mapa.

**Pipeline De Anonimización**
1. **Ingesta local**
   - TXT, MD, CSV, JSONL inicialmente.
   - PDF/DOCX después, con extractores separados.

2. **Detección determinista**
   - email
   - teléfono
   - DNI/NIE/NIF
   - IBAN
   - URLs
   - direcciones probables
   - matrículas/códigos
   - fechas sensibles si aplica

3. **Detección NER local**
   - usar Presidio si instala bien en Windows.
   - si Presidio pesa demasiado, fallback con reglas + spaCy/stanza más adelante.
   - Mini Nano como segunda opinión semántica, no como fuente única.

4. **Resolución de entidades**
   - normalizar: mayúsculas/minúsculas, acentos, espacios.
   - agrupar variantes: `J. Martinez`, `Javier Martinez`, `Javier Martinez Lopez`.
   - mantener mapa global.

5. **Anonimización**
   - `PERSON_0001`, `ORG_0001`, `EMAIL_0001`, `PHONE_0001`, `ADDRESS_0001`, `ID_0001`, `BANK_0001`.
   - modo reversible local mediante mapa.
   - modo irreversible si se borra el mapa.

6. **Verificación**
   - escaneo posterior del redacted.
   - si queda un email/DNI/teléfono detectable, falla.
   - Mini Nano puede revisar: “lista posibles datos personales que aún veas”.

**Papel De Mini Nano**
Mini Nano no debe ser el guardia único. Lo usaría así:

- **Detector semántico local**: “¿ves personas, empresas, direcciones o relaciones sensibles que las reglas no hayan marcado?”
- **Validador local**: revisar el archivo redacted antes de mandarlo a APIs externas.
- **Clasificador de sensibilidad**: decidir si el documento puede ir descubierto, ofuscado o no debe salir.
- **Extractor pequeño**: tareas cortas con contexto acotado.

No lo usaría para documentos enormes de una vez, porque ya vimos `524` y latencias altas. Lo usaremos por chunks.

**Flujo Para Usuario**
Cuando entre una tarea/documento:

```text
Modo descubierto:
  documento original -> modelo externo

Modo privado:
  original -> privacy_guard local
  redacted -> modelo externo
  respuesta externa -> opcional rehidratacion local
```

Ejemplo:

```text
Usuario: "Resume el contrato de Emilio Rodriguez"
Privado:
  "Resume el contrato de PERSON_0015"
Modelo externo responde:
  "PERSON_0015 debe aportar ID_0003..."
Sistema local muestra:
  "Emilio Rodriguez debe aportar DNI..."
```

Esto nos da soberanía: lo sensible no sale salvo que el usuario elija modo descubierto.

**Laboratorio De Benchmark**
No correría “todo contra todo” de golpe. Haría una campaña escalonada y persistente:

1. **Healthcheck cada ciclo**
   - Codex
   - Gemini
   - Groq
   - OpenRouter
   - Mini Nano

2. **Canaria pequeña**
   - 6 tareas: una por tipo/profesión.
   - todos los motores.
   - objetivo: detectar proveedores rotos.

3. **Batería base**
   - 30 tareas actuales.
   - sin Codex 5.5 salvo muestra pequeña.
   - Mini Nano solo tareas cortas/redacted.

4. **Batería privada**
   - mismas tareas, pero con documentos anonimizados.
   - comparar pérdida de calidad por ofuscación.

5. **Batería de seis profesiones**
   - tareas naturales.
   - medir por dimensiones, no por niveles:
     - contexto
     - herramientas
     - riesgo
     - formato
     - razonamiento
     - frescura
     - tolerancia al error

**Política De Límites**
Para no quemar Codex:

- Codex 5.5: solo arquitectura, revisión final, y una muestra premium.
- Codex 5.4-mini: implementación y benchmark limitado.
- Gemini Flash-Lite: grading y clasificación.
- Groq: router barato hasta que rate-limit lo pare.
- OpenRouter DeepSeek: cuando tenga crédito, canarias primero.
- Mini Nano: sin coste API, pero lento; correr en paralelo lógico, no bloquear todo.

Scheduler:

```text
cooldown normal: 2 horas
524 Mini Nano: cooldown 30-60 min
429 Groq: cooldown 2 horas
402 OpenRouter: desactivar proveedor hasta credito
Codex 5.5: cupo manual, no automatico masivo
```

**Plan De Implementación**
Fase 1: privacidad local mínima  
Crear `benchmarks/privacy_guard/` con detector regex, mapa global, tres salidas y tests sintéticos.

Fase 2: Mini Nano en privacidad  
Añadir modo `--semantic-review mini-nano`, por chunks, con timeout y fallback.

Fase 3: integración con benchmark  
Añadir opción `--privacy-mode redacted|clear`, preparar workdir con archivos anonimizados y guardar mapping local fuera del contexto enviado.

Fase 4: benchmark privado vs descubierto  
Correr mismas tareas con y sin ofuscación. Medir pérdida de calidad, filtraciones y latencia.

Fase 5: informe HTML  
Actualizar informe con:
- mejor modelo por tarea
- mejor modelo por dimensión
- coste/calidad
- privacidad/calidad
- cuándo merece descubrir datos
- cuándo basta anonimizar
- cuándo usar Mini Nano local

**Criterio De Éxito**
No diría que está listo hasta que cumpla esto:

- 95%+ de emails/teléfonos/DNI/IBAN detectados en tests sintéticos.
- mapa global estable entre documentos.
- cero PII obvia en archivo redacted tras verificación.
- Mini Nano ayuda a detectar entidades no capturadas por reglas.
- benchmark puede correr en modo privado sin romper tareas.
- informe compara calidad entre original y redacted.

Mi recomendación final: ahora, con GPT-5.5 y poca ventana, **no implementamos**. Dejamos este plan como contrato de trabajo. Cuando resetee la ventana, pasamos a 5.4-mini para construir fase 1 y fase 2, y reservamos 5.5 para revisar el diseño y el informe final.


Sí. Ya está pensado. Te lo dejo como **plan operativo para que 5.4-mini implemente casi sin decidir**, solo siguiendo pasos. La idea madre es esta: **privacidad local primero, modelos externos después**. Mini Nano no sustituye al anonimizado algorítmico; lo refuerza.

**Objetivo Final**
Construir dos capacidades:

1. **Privacy Guard local**
   - Detecta datos sensibles.
   - Crea tres versiones:
     - `original`: documento intacto.
     - `mixed`: `Emilio Rodriguez [PERSON_0015]`.
     - `redacted`: `PERSON_0015`.
   - Mantiene un mapa global estable.
   - Permite rehidratar respuestas si procede.

2. **Benchmark completo con modo privado**
   - Ejecutar tareas descubiertas y anonimizadas.
   - Comparar calidad, coste, latencia, fallos y pérdida de información.
   - Añadir Mini Nano como motor auxiliar y como evaluador local de privacidad.

Fuentes de criterio: Microsoft Presidio para PII/anonymizer, Google Sensitive Data Protection para transformaciones/tokenización, NIST para riesgo de reidentificación.  
Referencias: [Presidio](https://microsoft.github.io/presidio/), [Presidio anonymizer](https://microsoft.github.io/presidio/anonymizer/), [Google de-identification](https://cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data), [Google transformations](https://cloud.google.com/sensitive-data-protection/docs/transformations-reference), [NIST IR 8053](https://csrc.nist.gov/pubs/ir/8053/final), [NIST SP 800-122](https://www.nist.gov/publications/guide-protecting-confidentiality-personally-identifiable-information-pii).

**Decisión De Diseño**
Usaremos **pseudonimización reversible local**, no anonimización irreversible pura.

Razón: para trabajar con asistentes necesitamos que el modelo externo pueda razonar con continuidad:

```text
PERSON_0015 escribe a ORG_0003 sobre CONTRACT_0002
```

Y luego nosotros, localmente, podemos volver a mostrar:

```text
Javier Martinez Lopez escribe a Clinica Centro sobre el contrato de mantenimiento
```

Esto es más útil que borrar todo con `***`.

**Formato De Tokens**
Usar tokens en mayúsculas con tipo e ID:

```text
PERSON_0001
ORG_0001
EMAIL_0001
PHONE_0001
ADDRESS_0001
ID_NUMBER_0001
BANK_0001
DATE_0001
URL_0001
LICENSE_PLATE_0001
CONTRACT_0001
CASE_0001
```

Para copia mixta:

```text
Emilio Rodriguez [PERSON_0001]
Calle Mayor 4, Madrid [ADDRESS_0001]
emilio@email.com [EMAIL_0001]
```

El corchete es mejor que la barra porque es menos ambiguo, se parsea fácil y los modelos lo respetan bien.

**Mapa Global**
Crear un almacén local:

```text
benchmarks/privacy_guard_store/entity_map.jsonl
benchmarks/privacy_guard_store/entity_map.sqlite
```

Para empezar, JSONL es suficiente. SQLite después si crece.

Registro mínimo:

```json
{
  "entity_id": "PERSON_0001",
  "entity_type": "PERSON",
  "canonical_value": "Javier Martinez Lopez",
  "normalized_value": "javier martinez lopez",
  "aliases": ["Javier Martinez", "J. Martinez"],
  "first_seen": "2026-05-19T16:00:00Z",
  "last_seen": "2026-05-19T16:00:00Z",
  "source": "regex|presidio|mini_nano|manual",
  "confidence": 0.92
}
```

Regla dura: si el mismo dato vuelve a aparecer, recibe el mismo token.

**Arquitectura De Carpetas**
Crear:

```text
benchmarks/privacy_guard/
  __init__.py
  detectors.py
  entity_store.py
  anonymizer.py
  verifier.py
  mini_nano_review.py
  cli.py
  README.md

benchmarks/privacy_guard_samples/
  input/
  original/
  mixed/
  redacted/
  maps/
  reports/

benchmarks/tests/
  test_privacy_guard.py
```

**Fase 1: Detector Algorítmico**
Implementar primero sin dependencias pesadas.

Detectores por regex:

- email
- teléfono español e internacional
- DNI/NIE/NIF
- IBAN
- URL
- IP
- matrícula española aproximada
- importes si se decide sensible
- fechas si el modo lo pide
- códigos de contrato/expediente
- direcciones simples: `Calle`, `Avda`, `Avenida`, `Plaza`, `Paseo`, número, ciudad

Salida de detector:

```json
{
  "start": 10,
  "end": 25,
  "text": "600 100 031",
  "entity_type": "PHONE",
  "confidence": 0.99,
  "detector": "regex_phone"
}
```

Importante: reemplazar spans de derecha a izquierda para no romper offsets.

**Fase 2: Nombres Y Organizaciones**
Primera versión:

- diccionario dinámico desde contactos CSV.
- heurística de nombres propios:
  - 2-4 palabras con inicial mayúscula.
  - evitar meses, ciudades comunes, títulos.
- organizaciones:
  - sufijos `SL`, `S.L.`, `SA`, `S.A.`, `Ltd`, `Inc`, `Clinic`, `Clinica`, `Legal`, `Health`, etc.
  - nombres que aparecen como empresas en contactos.

Después, si merece, añadir Presidio como detector opcional:

```powershell
pip install presidio-analyzer presidio-anonymizer spacy
python -m spacy download es_core_news_md
```

Pero no bloquear la v1 si Presidio da guerra en Windows.

**Fase 3: Mini Nano Como Revisor Local**
Mini Nano no modifica directamente el texto. Hace propuestas.

Prompt por chunk:

```text
Eres un revisor local de privacidad. No reescribas el documento.
Devuelve SOLO JSON con posibles entidades sensibles no marcadas.

Tipos permitidos:
PERSON, ORG, EMAIL, PHONE, ADDRESS, ID_NUMBER, BANK, DATE, CASE, CONTRACT, OTHER_SECRET.

Texto:
<<<
...
>>>

JSON:
[
  {"text":"...", "entity_type":"PERSON", "reason":"...", "confidence":0.0}
]
```

Reglas:

- chunk pequeño, 1.500-3.000 caracteres.
- timeout alto.
- si falla, se continúa sin Mini Nano.
- solo se aceptan entidades con `confidence >= 0.75`.
- validar que el texto propuesto existe literalmente en el chunk.

**Fase 4: Tres Salidas**
CLI objetivo:

```powershell
python .\benchmarks\privacy_guard\cli.py anonymize `
  --input .\benchmarks\privacy_guard_samples\input\contrato_001.txt `
  --out-dir .\benchmarks\privacy_guard_samples `
  --mode hybrid `
  --global-map .\benchmarks\privacy_guard_store\entity_map.jsonl
```

Debe generar:

```text
original/contrato_001.txt
mixed/contrato_001.mixed.txt
redacted/contrato_001.redacted.txt
maps/contrato_001.privacy_report.json
```

Reporte:

```json
{
  "input": "...",
  "entities_found": 24,
  "by_type": {"PERSON": 4, "EMAIL": 3},
  "redaction_passed": true,
  "residual_findings": [],
  "mini_nano_used": true,
  "mini_nano_seconds": 42.1
}
```

**Fase 5: Verificador**
Después de anonimizar, volver a escanear `redacted`.

Falla si quedan:

- emails
- teléfonos
- DNI/NIE
- IBAN
- URLs sensibles
- nombres detectados por mapa previo
- valores exactos ya conocidos en el mapa

Mini Nano puede hacer una revisión secundaria:

```text
Busca posibles datos personales residuales. Devuelve JSON. No expliques.
```

Pero el verificador principal debe ser algorítmico.

**Fase 6: Rehidratación**
Necesitamos convertir respuestas de modelos externos:

```text
PERSON_0001 debe enviar ID_NUMBER_0001 antes del DATE_0002.
```

a:

```text
Javier Martinez Lopez debe enviar DNI 12345678Z antes del 14 de mayo.
```

CLI:

```powershell
python .\benchmarks\privacy_guard\cli.py hydrate `
  --input respuesta_redacted.md `
  --map benchmarks\privacy_guard_store\entity_map.jsonl `
  --output respuesta_hidratada.md
```

Esto debe ser opcional. Para informes internos, puede bastar respuesta pseudonimizada.

**Integración En Benchmark**
Añadir a `benchmark_scheduler.py`:

```text
--privacy-mode clear|redacted|mixed
--privacy-map benchmarks/privacy_guard_store/entity_map.jsonl
--privacy-review none|mini_nano
```

Comportamiento:

- `clear`: como ahora.
- `redacted`: antes de ejecutar motor, anonimiza assets del workdir.
- `mixed`: solo para auditoría humana, no enviar a modelos externos salvo decisión explícita.

En `prepare_workdir`, después de copiar assets:

```text
si privacy-mode redacted:
  crear copia redacted de cada asset textual
  sustituir el asset que verá el modelo por la versión redacted
  guardar original fuera del contexto enviado
```

No enviar mapas a modelos externos.

**Benchmark De Privacidad**
Crear suite nueva:

```text
benchmarks/tasks/privacy_tasks.json
```

Tareas:

1. contrato con persona, DNI, dirección, email, teléfono.
2. hilo de emails con varias personas.
3. CSV de clientes.
4. nota de voz transcrita con datos difusos.
5. documento legal con fechas, importes y empresas.
6. mezcla multiarchivo.

Cada tarea debe tener expected keys en versión redacted:

```json
"expected_keys": ["PERSON_0001", "ID_NUMBER_0001", "ADDRESS_0001"]
```

Y expected privacy:

```json
"forbidden_patterns": ["@", "\\b\\d{8}[A-Z]\\b", "\\+34"]
```

**Benchmark Completo De Modelos**
No correr todo brutalmente de golpe. Plan prudente:

Primero healthcheck:

```powershell
python .\benchmarks\provider_health.py --live
```

Canaria:

```powershell
python .\benchmarks\benchmark_scheduler.py `
  --tasks-file .\benchmarks\tasks\assistant_tasks.json `
  --engine-matrix .\benchmarks\engine_matrix_ready.json `
  --task test-01 --task test-02 --task test-05 `
  --once --heuristic-only
```

Luego privacidad:

```powershell
python .\benchmarks\benchmark_scheduler.py `
  --tasks-file .\benchmarks\tasks\privacy_tasks.json `
  --engine gemini_api:gemini-2.5-flash-lite `
  --engine openrouter:deepseek/deepseek-v3.2 `
  --engine vikingnano:gemini-nano-local `
  --privacy-mode redacted `
  --once --heuristic-only
```

Después batería grande en ciclos:

```powershell
python .\benchmarks\benchmark_scheduler.py `
  --tasks-file .\benchmarks\tasks\assistant_tasks.json `
  --engine-matrix .\benchmarks\engine_matrix_ready.json `
  --cooldown-seconds 7200 `
  --cycle-sleep-seconds 7200
```

Codex 5.5 no debe entrar en la matriz completa al principio. Solo muestra premium.

**Política De Modelos**
- `codex:gpt-5.4-mini`: implementación y tareas agenticas estándar.
- `codex:gpt-5.5`: revisión premium, tareas complejas, informe final.
- `gemini_api:gemini-2.5-flash-lite`: juez barato, router, resumen.
- `groq:llama-3.1-8b-instant`: router barato si no rate-limita.
- `openrouter:deepseek/deepseek-v3.2`: candidato fuerte coste/calidad.
- `vikingnano:gemini-nano-local`: privacidad local, extracción corta, validación semántica.
- `opencode:*`: comparación agentica cuando el proveedor esté estable.

**Criterios De Medición**
Para cada ejecución guardar:

```json
{
  "engine": "...",
  "task_id": "...",
  "privacy_mode": "clear|redacted",
  "score": 0-10,
  "expected_keys_passed": true,
  "latency_seconds": 0,
  "cost": 0,
  "technical_status": "ok|timeout|rate_limit|fail",
  "privacy_leak_count": 0,
  "quality_loss_vs_clear": 0
}
```

Insights que queremos sacar:

- modelo mínimo suficiente por tipo de tarea.
- pérdida de calidad por anonimización.
- tareas donde anonimizar rompe demasiado contexto.
- tareas donde Mini Nano basta.
- cuándo escalar a 5.4-mini o 5.5.
- cuándo se puede mandar redacted a OpenRouter/Gemini sin riesgo alto.

**Informe Final HTML**
Crear/actualizar:

```text
benchmarks/results/privacy_model_strategy_report.html
```

Debe incluir:

- matriz modelo x tarea.
- gráfico calidad/coste.
- gráfico calidad/privacidad.
- tabla de fallos técnicos.
- recomendación de routing.
- política de privacidad:
  - descubierto
  - redacted
  - local-only
- conclusiones por profesión.
- conclusiones por dimensión de tarea.

**Reglas De Routing Futuras**
Propuesta inicial:

```text
Si documento contiene PII alta:
  privacy_guard redacted
  Mini Nano verifica
  enviar redacted a modelo externo

Si tarea es simple y local:
  Mini Nano directo

Si tarea necesita archivos/código:
  Codex 5.4-mini

Si tarea es crítica o score < 8:
  Codex 5.5

Si tarea es resumen o clasificación:
  Gemini Flash-Lite o Groq

Si OpenRouter DeepSeek da buen score/coste:
  usar como worker principal no agentico o vía OpenCode
```

**Orden Exacto Para 5.4-mini**
1. Crear `benchmarks/privacy_guard/`.
2. Implementar `detectors.py`.
3. Implementar `entity_store.py`.
4. Implementar `anonymizer.py`.
5. Implementar `verifier.py`.
6. Implementar `cli.py`.
7. Crear 6 documentos sintéticos.
8. Crear tests unitarios.
9. Añadir Mini Nano review.
10. Añadir `--privacy-mode` al scheduler.
11. Crear `privacy_tasks.json`.
12. Correr smoke tests locales.
13. Correr canaria con Mini Nano/Gemini/OpenRouter.
14. Generar informe HTML.

**Criterio De Parada**
No seguir a benchmark grande hasta que:

- los tests de privacidad pasan.
- `redacted` no contiene email/teléfono/DNI/IBAN.
- el mapa global reutiliza IDs correctamente.
- Mini Nano falla de forma no bloqueante.
- una tarea benchmark funciona en modo `redacted`.

Esta es la hoja de ruta buena. Ahora 5.4-mini puede ejecutar por fases sin tener que rediseñar nada, y nosotros reservamos 5.5 para revisar puntos delicados: detección semántica, routing y el informe estratégico.