# Investigación profunda y plan ejecutivo de IA ofimática

## Contexto

Se ha realizado una investigación sobre el estado actual de herramientas de inteligencia artificial para ofimática y agentes CLI, cruzando los hallazgos con datos locales de OpenRouter/Gemini disponibles en el entorno de trabajo. Las fuentes web consultadas (sider.ai, estrategIA, HIX AI, Luis Ampuero) abarcan lanzamientos hasta mayo de 2025.

## Estado actual de herramientas de IA para ofimática

Según la guía de Sider AI (sep 2025), las principales herramientas de investigación profunda incluyen ChatGPT, Gemini, Claude y Grok, todas con capacidades de búsqueda avanzada y generación de informes. Perplexity Deep Research y xAI DeepSearch también han emergido como alternativas sólidas (estrategIA, mar 2025). La función "Deep Research" de Google, lanzada en diciembre de 2024, es pionera. HIX AI ofrece un agente gratuito especializado en investigación. Luis Ampuero (mayo 2025) advierte sobre la erosión del pensamiento crítico y sesgos ocultos, recomendando un equilibrio.

En ofimática, estas herramientas permiten automatizar la redacción de correos, generación de informes, análisis de datos (CSV), resúmenes de hilos de correo y transcripción de notas de voz. Los agentes CLI (Command Line Interface) complementan esta automatización al ejecutar tareas repetitivas como filtrado de contactos, extracción de información y recordatorios.

## Análisis de agentes CLI y formato local

Los datos locales (asistant_synthetic/) contienen:

- **`notas_voz.jsonl`**: 20 transcripciones de notas de voz con tareas pendientes (llamadas, envíos, preparación de informes). VN-014 menciona explícitamente "Preparar comparativa OpenRouter contra Gemini para tareas de ofimática".
- **`emails_hilos.md`**: 6 hilos de correo con fechas, asuntos y cuerpos. Incluyen solicitudes de demo, descuentos, contratos, reuniones, formatos de informes y propuestas pendientes.
- **`contactos_50.csv`**: 50 contactos con datos de nombre, email, ciudad, empresa, rol, tipo (cliente, proveedor, etc.) y prioridad (alta, media, baja). Varios contactos aparecen recurrentemente en notas y correos (Noelia Castro, Luis Martin, Ana Lopez, etc.).

Un agente CLI podría integrar estas fuentes para: priorizar contactos de alta prioridad en Madrid, enviar recordatorios automáticos basados en fechas de los correos, generar informes en PDF con resumen ejecutivo (como solicita Ana Lopez en E-005), o comparar costes de OpenRouter vs Gemini.

## Cruce con datos locales sobre OpenRouter/Gemini

La nota VN-014 indica la necesidad de una comparativa. OpenRouter ofrece acceso a múltiples modelos (incluyendo Gemini) con precios por token y sin suscripción fija, ideal para prototipos. Gemini (de Google) destaca en análisis multimodal y razonamiento. Los costes típicos: Gemini 1.5 Pro ~$0.0035 por 1k tokens de entrada; OpenRouter puede ser más barato si se usa modelos de código abierto (DeepSeek, Llama). Para tareas ofimáticas (resumir correos, clasificar contactos, generar respuestas), Gemini ofrece rapidez y precisión en español, mientras que OpenRouter permite flexibilidad de modelos.

Los contactos de alta prioridad (Ruben Ortega, Ana Lopez, etc.) podrían beneficiarse de un agente que programe recordatorios y envíe informes automáticos. Los hilos de correo muestran plazos concretos (demo el 14 mayo, revisión contrato antes del 12, etc.) que un agente podría monitorizar.

## Recomendación ejecutiva

**Estrategia: Integrar Gemini para tareas de ofimática (generación de informes, resúmenes, respuestas) y OpenRouter para consultas de investigación profunda y experimentación con modelos alternativos, todo orquestado mediante un agente CLI.**

1. **Fase inmediata (1-2 semanas)**: Desplegar un agente CLI que lea `notas_voz.jsonl` y `emails_hilos.md` para extraer tareas y fechas, y que genere recordatorios automáticos. Usar Gemini (vía API) para resumir hilos y redactar respuestas sugeridas. Coste estimado: $5-10 en tokens.

2. **Fase de consolidación (3-4 semanas)**: Ampliar el agente para procesar `contactos_50.csv` y generar listas segmentadas (ej. contactos de alta prioridad en Madrid). Implementar integración con OpenRouter para investigaciones profundas (consultas a múltiples modelos) y comparativa de costes.

3. **Fase de optimización (5-6 semanas)**: Validar la calidad de los informes generados con el feedback de los contactos (ej. formato PDF + resumen ejecutivo de Ana Lopez). Ajustar modelos según coste/precisión. Documentar el proceso como caso de uso de IA ofimática.

**Justificación**: Los datos locales muestran una alta dependencia de tareas manuales (llamadas, envíos, revisión de contratos). Un agente basado en Gemini/OpenRouter reduce tiempos de respuesta y minimiza errores. La investigación externa confirma que estas herramientas son maduras y accesibles. La recomendación equilibra la automatización con la supervisión humana (evitando la dependencia excesiva señalada por Luis Ampuero).

**Próximo paso**: Preparar el script CLI para el próximo sprint, priorizando las tareas de VN-006 (revisión contrato IberLegal) y VN-001 (confirmar demo Noelia Castro).
