# Resultado  

## 1. Resumen Ejecutivo  
- **Objetivo**: Seleccionar la plataforma de IA que maximice la productividad ofimática y los flujos de trabajo CLI en nuestra organización, alineada con los contactos estratégicos y la carga de trabajo actual.  
- **Conclusión principal**: Adoptar **OpenRouter** como motor de orquestación de modelos (flexibilidad, multi‑modelo, precios competitivos) y **Gemini** como modelo especializado para integraciones con Google Workspace y generación de contenido de alta calidad.  
- **Primeros pasos**: Piloto de 3 meses con los contactos de alta prioridad en Madrid (Esteban Lozano – CTO Helixia; Lorena Vidal – Producto Civitas) y con los equipos de ventas y legal que ya manejan gran volumen de documentos (Clínica Centro, IberLegal).  

## 2. Estado del arte de herramientas de IA para ofimática (2025‑2026)  

| Área | Herramienta líder | Principales capacidades | Ventajas competitivas |
|------|-------------------|------------------------|-----------------------|
| **Procesamiento de texto** | Microsoft Copilot (Word) | Resumen, redacción, generación de tablas, revisión de estilo | Integración nativa con Office 365, cumplimiento empresarial |
| **Hojas de cálculo** | Google Workspace AI (Sheets) | Fórmulas automáticas, análisis de datos, visualizaciones con lenguaje natural | Acceso a datos en tiempo real, colaboración en tiempo real |
| **Presentaciones** | Canva Magic Write + Slides AI | Creación de diapositivas a partir de prompts, diseño automático | Plantillas profesionales, export a múltiples formatos |
| **Gestión de correo** | Superhuman AI + Outlook Copilot | Prioriza, redacta respuestas, extrae tareas | Reducción de tiempo de gestión de bandeja |
| **Asistentes de escritura** | Grammarly Business, Notion AI | Corrección gramatical, tono, generación de contenido estructurado | Soporte multilingüe, integración con documentos |
| **Investigación profunda** | Perplexity AI, HIX Deep Research, OpenAI Deep Research | Búsqueda multi‑fuente, citación automática, síntesis de informes | Alta fidelidad de fuentes, generación de bibliografías [Fuente 1][1] |
| **Agentes CLI** | **OpenRouter** (orquestador multi‑modelo), **Gemini** (modelo de Google), **AutoGPT**, **LangChain CLI** | Ejecutan scripts, generan código, interactúan con APIs, automatizan flujos de trabajo desde terminal | Flexibilidad (OpenRouter) vs. integración profunda con ecosistema Google (Gemini) |

### Tendencias clave  
- **Modelo híbrido**: combinar LLMs de propósito general (OpenRouter) con modelos especializados (Gemini) para obtener mejor relación coste‑beneficio.  
- **Citación y trazabilidad**: las herramientas de investigación profunda ahora incluyen referencias automáticas, requisito crítico para auditorías y cumplimiento [Fuente 1][1].  
- **CLI como capa de orquestación**: los agentes de línea de comandos permiten integrar IA en pipelines de datos, CI/CD y automatización de documentos sin depender de UI gráficas.  

## 3. Comparativa OpenRouter vs. Gemini para tareas de ofimática  

| Criterio | OpenRouter | Gemini |
|----------|------------|--------|
| **Catálogo de modelos** | > 30 proveedores (Claude, Llama, Mistral, etc.) → permite seleccionar el modelo óptimo por coste/precisión. | Modelo único, optimizado por Google para tareas de generación de texto y código. |
| **Coste** | Pago por token con precios variables; posibilidad de usar modelos gratuitos para pruebas. | Precio fijo por token (Google Cloud); descuentos por uso sostenido. |
| **Latencia** | Media‑alta (dependiendo del modelo). | Baja latencia dentro de la infraestructura Google. |
| **Integración con Google Workspace** | Necesita conectores personalizados (REST, OAuth). | API nativa con Docs, Sheets, Slides, Gmail. |
| **Flexibilidad de prompts** | Soporta “system prompts” avanzados, chaining de modelos. | Soporta “system messages” pero menos opciones de chaining. |
| **Seguridad y cumplimiento** | Opciones de encriptado por modelo, auditoría de logs. | Cumple con ISO‑27001, SOC 2, integración con Cloud DLP. |
| **Ecosistema CLI** | SDK oficial y wrappers para Python/Node; fácil de integrar en scripts. | SDK de Gemini AI (Python) con ejemplos de CLI, pero menos maduro. |
| **Adecuación a casos de uso** | - Generación de borradores de contratos (IberLegal). <br>- Creación de CSV de monitores con descuento (Delta Equipos). <br>- Automatización de minutas y reportes internos. | - Resumen ejecutivo de informes (Nova Iberia). <br>- Generación de presentaciones automáticas para reuniones (Barna Health). <br>- Traducción y adaptación de correos a varios idiomas. |

**Conclusión**: OpenRouter es la mejor opción para **orquestar** múltiples modelos y adaptar costes a cada caso; Gemini es la opción más eficiente cuando la integración con Google Workspace es crítica.  

## 4. Análisis de datos locales  

| Fuente | Insight relevante para IA ofimática |
|-------|--------------------------------------|
| **contactos_50.csv** | 2 contactos de alta prioridad en Madrid (Esteban Lozano – CTO Helixia; Lorena Vidal – Producto Civitas). Priorizar pruebas piloto con ellos. |
| **emails_hilos.md** | - Necesidad de **demo de módulo de pagos** (Clínica Centro) → requiere generación de documentos de conciliación automática. <br>- Solicitud de **PDF con resumen ejecutivo** (Nova Iberia) → oportunidad para usar Gemini para formatear PDFs. <br>- **Propuesta pendiente** (BravoSoft) → automatizar recordatorios vía agente CLI. |
| **notas_voz.jsonl** | - VN‑014: “Preparar comparativa OpenRouter contra Gemini para tareas de ofimática”. <br>- VN‑017: “Crear lista de contactos prioritarios de Madrid con nivel alta”. <br>- VN‑015: “Enviar email amable a Paula Ferrer”. <br>Estos recordatorios confirman la necesidad de automatizar generación de correos y gestión de contactos. |

## 5. Recomendaciones estratégicas  

1. **Arquitectura híbrida**  
   - **Core**: OpenRouter como motor de orquestación, seleccionando modelos económicos para generación de texto y código.  
   - **Extensión**: Gemini para integración directa con Google Docs/Sheets y generación de PDFs con formato corporativo.  

2. **Piloto de 3 meses**  
   - **Objetivo**: Reducir el tiempo medio de elaboración de documentos legales y financieros en un 30 %.  
   - **Equipos**: Legal (IberLegal), Finanzas (Clínica Centro), Ventas (Delta Equipos).  
   - **KPIs**: tiempo de respuesta de email, número de borradores generados, precisión de datos (errores < 2 %).  

3. **Automatización de flujos CLI**  
   - Implementar scripts que:  
     - Generen CSV de productos con descuentos (usando OpenRouter + LangChain).  
     - Extraigan datos de correos y creen tareas en el gestor interno (AutoGPT).  
     - Programen recordatorios y envíen follow‑ups (p.ej., a Paula Ferrer).  

4. **Capacitación y gobernanza**  
   - Workshops mensuales (2 h) para usuarios clave (CTO, Gerencia de Producto).  
   - Política de revisión humana antes de publicar documentos críticos (legal, financiero).  

5. **Escalado**  
   - Tras validar el piloto, extender a toda la organización y negociar precios corporativos con OpenRouter y Google Cloud (Gemini).  

## 6. Plan de implementación (12 semanas)

| Semana | Acción | Responsable |
|--------|--------|--------------|
| 1‑2 | Configuración de cuentas OpenRouter & Gemini; creación de claves API. | Equipo de IT |
| 3 | Desarrollo de scripts CLI para generación de CSV y envío de emails. | Equipo de Desarrollo |
| 4 | Integración de Gemini con Google Docs (templates de informes). | Equipo de IT |
| 5‑6 | Capacitación piloto (Esteban Lozano, Lorena Vidal) y pruebas de caso de uso (demo pagos, contrato IberLegal). | PM + Formación |
| 7 | Medición de KPIs iniciales; ajuste de prompts y selección de modelo OpenRouter. | Analista de datos |
| 8‑9 | Automatización de recordatorios (VN‑015, VN‑016) y generación de minutas (VN‑004). | Equipo de Desarrollo |
| 10 | Revisión de resultados, informe de impacto y propuesta de expansión. | PM |
| 11‑12 | Negociación con proveedores y despliegue a resto de departamentos. | Dirección + Legal |

## 7. Bibliografía  

1. **Fuente 1** – “Las 10 mejores herramientas de investigación profunda con IA para dominar en 2025”. *Sider.ai*, 16 sep 2025. Disponible en: https://sider.ai/es/blog/ai-tools/best-ai-deep-research-tools-to-master-in-2025  
2. **Fuente 2** – “estrategIA #75 Cómo usar la IA para hacer mejores investigaciones”. *Estrategia by Aleph*, 5 mar 2025. Disponible en: https://estrategiabyaleph.substack.com/p/estrategia-75-como-usar-la-ia-para  
3. **Fuente 3** – “Investigación profunda de IA: Agente gratuito de investigación profunda”. *HIX AI*, 2025. Disponible en: https://hix.ai/es/deep-research  
4. **Fuente 4** – “Investigación Profunda con IA: Un equilibrio necesario”. *Luis Ampuero*, 10 may 2025. Disponible en: https://luisampuero.com/2025/05/investigacion-profunda-con-ia-un-equilibrio-necesario/  

---  

*Documento generado el 21 may 2026, basado en los archivos locales proporcionados y en la información de fuentes web citadas.*
