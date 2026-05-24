# Resultado – Investigación profunda y plan ejecutivo de IA para ofimática  

## 1. Resumen ejecutivo  
- **Objetivo:** Seleccionar y adoptar herramientas de IA que automaticen tareas de oficina (documentación, análisis de datos, gestión de correos y agenda) y que ofrezcan agentes de línea de comandos (CLI) para integrarse con los flujos de trabajo internos.  
- **Conclusión clave:** La combinación de **Gemini Pro (versión de Google)** y **OpenRouter** brinda la mejor cobertura de modelos de gran escala, precios competitivos y capacidad de orquestación mediante agentes CLI. Se recomienda iniciar con un **piloto de 3 meses** centrado en generación de informes y automatización de correos, usando Gemini para generación de texto y OpenRouter para enrutamiento a modelos especializados (p.ej. Claude 2, Llama 3).  

## 2. Estado del arte de herramientas IA para ofimática (2025‑2026)  

| Área | Herramienta principal | Funcionalidad destacada | Precio / modelo de licenciamiento | Comentario de mercado |
|------|----------------------|------------------------|-----------------------------------|-----------------------|
| **Redacción y síntesis** | **Gemini Pro** (Google) | Generación de texto con alta precisión, citación automática, soporte multilingüe. | Pago por token, plan empresarial con 1 M tokens/mes. | Referencia en Fuente 4 como una de las mejores para “deep research”. |
| | **OpenRouter** (agregador) | Acceso a 30+ LLMs (Claude 2, Llama 3, Mistral) bajo una única API. | Suscripción mensual + coste por token. | Permite elegir modelo según coste‑beneficio (Fuente 1 menciona la necesidad de “citar fuentes claras”). |
| **Análisis de datos** | **Microsoft Copilot for Office** | Integrado en Word, Excel, PowerPoint; genera tablas, gráficos y resúmenes. | Incluido en Microsoft 365 Enterprise. | Amplio despliegue corporativo, pero limitado a ecosistema Microsoft. |
| | **ChatGPT‑4o (OpenAI)** | Análisis de datos mediante plugins (Excel, CSV). | Pago por uso. | Muy flexible, pero depende de plugins externos. |
| **Automatización de flujos** | **Zapier + IA (Zapier AI)** | Conecta apps y ejecuta “actions” basadas en prompts IA. | Planes desde $20/mes. | Ideal para procesos repetitivos (p.ej. envío de minutas). |
| | **Auto‑GPT / CrewAI (CLI)** | Agentes autónomos que pueden ejecutar scripts, leer correos, generar informes. | Open‑source, coste de infraestructura. | Requiere configuración, pero permite personalizar flujos de trabajo internos. |
| **Asistentes de voz/CLI** | **HIX Deep Research (CLI)** | Agente de investigación profunda que se ejecuta desde terminal. | Gratuito (modelo SaaS). | Enfocado a investigación, útil para generar briefs rápidamente (Fuente 3). |
| | **Perplexity AI CLI** | Búsqueda y síntesis en tiempo real desde la línea de comandos. | Pago por token. | Buen rendimiento en consultas rápidas. |

### Tendencias clave (2025‑2026)  
1. **Orquestación híbrida** – combinar varios LLMs según la tarea (p.ej. Gemini para generación de texto, Claude 2 para razonamiento).  
2. **Citación automática y trazabilidad** – los usuarios exigen referencias claras (Fuente 1).  
3. **Integración nativa con suites de oficina** – Microsoft y Google están integrando IA directamente en sus apps.  
4. **Agentes CLI con capacidad de “self‑prompting”** – permiten ejecutar procesos sin intervención humana (Auto‑GPT, CrewAI).  

## 3. Comparativa OpenRouter vs Gemini (basada en VN‑014)  

| Criterio | **Gemini Pro** | **OpenRouter** |
|----------|----------------|----------------|
| **Cobertura de modelos** | Un único modelo (Gemini) con versiones “lite” y “pro”. | Acceso a más de 30 modelos diferentes (Claude 2, Llama 3, Mistral, etc.). |
| **Calidad de generación** | Excelente en lenguaje natural y citación; entrenado con datos de Google. | Variable según modelo; permite elegir el más barato para tareas simples. |
| **Coste** | Precio fijo por token; puede ser más caro en volúmenes altos. | Modelo “pay‑as‑you‑go”; se pueden mezclar modelos baratos para tareas rutinarias. |
| **Facilidad de integración CLI** | SDK oficial, pero limitado a API de Google. | API REST universal; fácil de envolver en scripts Bash/Python. |
| **Control de privacidad** | Google mantiene logs; opciones de “no‑store” bajo contrato empresarial. | Cada modelo tiene su propia política; posible elegir proveedores con mayor privacidad. |
| **Soporte de citación** | Genera referencias automáticas (p.ej. estilo APA). | Depende del modelo; Claude 2 y algunos Llama 3 ofrecen citación, pero no siempre estructurada. |

**Recomendación:** Utilizar **Gemini Pro** para generación de documentos oficiales (informes, minutas, PDFs) donde la calidad y citación son críticas. Emplear **OpenRouter** para tareas de bajo coste (resúmenes rápidos, clasificación de correos, extracción de datos) y para experimentar con nuevos modelos sin cambiar la arquitectura del código.

## 4. Oportunidades de negocio con la base de contactos  

| Segmento | Prioridad | Necesidad IA detectada (a partir de correos/ notas) | Acción recomendada |
|----------|-----------|---------------------------------------------------|--------------------|
| **Madrid – clientes alta** (Ana Lopez, Elena Vidal, Sergio Campos, etc.) | Alta | Necesitan informes PDF con resumen ejecutivo (E‑005) y gestión de riesgos de seguridad (VN‑004). | Implementar **Gemini Pro** para generación automática de PDFs y usar **Auto‑GPT** para crear minutas de riesgos. |
| **Proveedores media** (Luis Martin, David Navarro, etc.) | Media | Requieren descuentos y revisión de contratos (E‑002, E‑003). | Automatizar extracción de cláusulas clave con **OpenRouter + Claude 2** y generar propuestas de descuento con **Gemini**. |
| **Prospectos** (Paula Ferrer, Raquel Cano, etc.) | Media‑baja | Seguimiento de propuestas y recordatorios (VN‑015, VN‑009). | Configurar **Zapier AI** + **CLI agents** para enviar recordatorios personalizados y generar alternativas de encuesta barata (para GreenBox). |
| **Partners** (Xavier Puig, Hector Mora, etc.) | Alta | Coordinación de reuniones técnicas y SSO (E‑004). | Usar **HIX Deep Research CLI** para crear agendas y **Gemini** para redactar actas de reunión. |

## 5. Plan de acción (3 meses)  

| Fase | Duración | Actividades | Responsable | KPI |
|------|----------|-------------|-------------|-----|
| **Fase 1 – Evaluación** | 0‑2 sem | - Crear sandbox de pruebas con Gemini Pro y OpenRouter.<br>- Definir casos de uso: generación de informes (clientes alta) y clasificación de correos (proveedores).<br>- Capacitar a 2 usuarios clave (Ana Lopez, Sergio Campos). | Equipo de IA + IT | % de casos de uso implementados (objetivo ≥ 70 %). |
| **Fase 2 – Piloto** | 3‑8 sem | - Desplegar agente CLI (Auto‑GPT) que lea la bandeja de entrada y genere borradores de respuestas usando OpenRouter.<br>- Integrar Gemini Pro con Microsoft Word para crear plantillas PDF automáticas.<br>- Medir tiempo ahorrado en generación de informes (meta: –30 %). | PM de IA + Soporte | Reducción de tiempo de generación de informes
