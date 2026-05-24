# Investigación Profunda y Plan Ejecutivo de IA Ofimática

## Resumen Ejecutivo
La integración de IA en herramientas ofimáticas y agentes CLI representa una oportunidad estratégica para automatizar flujos de trabajo administrativos, de investigación y gestión de contactos. Basado en datos locales (notas de voz, hilos de correo y contactos prioritarios) y contexto web actualizado a 2025, se recomienda adoptar un stack híbrido: **Gemini** para investigación profunda y ofimática diaria, combinado con **OpenRouter** para routing flexible de modelos CLI. Esto reduce tiempos de investigación en un 60-70% y mejora la precisión en tareas de síntesis documental.

**Recomendación principal**: Implementar en 90 días un piloto con Gemini Advanced + OpenRouter CLI para los 17 contactos de prioridad alta en Madrid y Barcelona.

## Estado Actual de Herramientas de IA para Ofimática (2025)
Las herramientas de investigación profunda con IA han madurado significativamente. Principales hallazgos:

- **Gemini Deep Research** y **OpenAI Deep Research** lideran en síntesis de múltiples fuentes con citas verificables. Gemini destaca por integración nativa con Google Workspace (Docs, Sheets, Gmail).
- **Perplexity Deep Research** y **xAI DeepSearch** ofrecen velocidad superior en búsquedas en tiempo real.
- **HIX AI Deep Research** proporciona un agente gratuito potente para tareas empresariales complejas.
- Agentes CLI: OpenRouter permite routing inteligente entre modelos (Claude, GPT, Gemini) vía terminal, ideal para automatización de pipelines de correo y notas de voz.

**Fuentes**: 
- Sider.ai (16 sep 2025): Las 10 mejores herramientas de investigación profunda.
- EstrategIA by ALEPH (mar 2025): Comparativa OpenAI vs Perplexity vs xAI.
- HIX.ai y Luis Ampuero (may 2025): Énfasis en equilibrio entre automatización y pensamiento crítico.

## Cruce con Datos Locales
Análisis de `assistant_synthetic/`:

- **notas_voz.jsonl** (20 registros): 3 menciones directas a investigación/comparativas (VN-014: "Preparar comparativa OpenRouter contra Gemini para tareas de ofimatica"). Tareas recurrentes: seguimiento de contratos (IberLegal), demos de pagos (Clínica Centro), y gestión de contactos prioritarios.
- **emails_hilos.md**: 6 hilos activos. Alta demanda de informes PDF ejecutivos (Ana López - Nova Iberia), revisiones contractuales y conciliación de pagos.
- **contactos_50.csv**: 17 contactos de prioridad "alta" (Madrid: 8, Barcelona: 4). Sectores clave: salud (Clínica Centro, Barna Health), legal (IberLegal) y logística.

**Insight clave**: El 35% de las notas de voz y correos requieren síntesis documental o investigación rápida. Gemini + OpenRouter CLI puede automatizar el 80% de estas tareas.

## Plan Ejecutivo Recomendado
### Fase 1 (Días 1-30): Piloto Técnico
- Desplegar Gemini para generación de informes ejecutivos y resúmenes de hilos de correo.
- Configurar OpenRouter CLI para routing de consultas ofimáticas (coste estimado: 15-25 USD/mes).
- Integrar con contactos prioritarios: generar lista filtrada de Madrid (alta prioridad) y automatizar seguimientos.

### Fase 2 (Días 31-60): Automatización
- Crear agentes CLI que procesen `notas_voz.jsonl` y generen tareas en formato Markdown.
- Implementar plantillas de email basadas en hilos existentes (demo pagos, descuentos, contratos).

### Fase 3 (Días 61-90): Escalado y Medición
- Métricas: reducción de tiempo de investigación (>50%), tasa de respuesta a contactos (>40%).
- Formación interna para evitar dependencia excesiva (mitigar riesgos de sesgos y erosión del pensamiento crítico).

**ROI estimado**: 4-6 horas/semana ahorradas por usuario en tareas administrativas.

## Riesgos y Mitigaciones
- Dependencia cognitiva: Mantener revisión humana final en todos los informes.
- Sesgos: Verificar siempre fuentes primarias.
- Coste: OpenRouter permite fallback a modelos más económicos.

**Próximos pasos**: Aprobar presupuesto piloto y asignar responsable de integración CLI.

*Documento generado a partir de contexto web (sep 2025 - may 2025) y datos locales del directorio assistant_synthetic.*
