Voy a leer primero `web_context.md` y los archivos locales para extraer señales de uso, luego cruzo eso con documentación y estado actual de herramientas de IA para ofimática y agentes CLI. Después sintetizo una recomendación ejecutiva con criterios prácticos y fuentes.

Ya tengo la señal local: el trabajo es claramente administrativo/comercial, con necesidad de redacción, seguimiento, PDFs ejecutivos, contratos, facturas y recordatorios. Ahora verifico el estado actual de las plataformas oficiales para distinguir qué sirve de verdad para ofimática y qué encaja mejor como agente CLI.

Ya tengo las fuentes oficiales clave. Ahora saco un resumen cuantitativo de los datos locales para no convertir la recomendación en una opinión genérica: tipos de contacto, prioridades y tareas recurrentes que empujan la elección hacia una u otra plataforma.

**Conclusión ejecutiva**

Con fecha **13 de mayo de 2026**, mi recomendación es esta:

- **Capa principal de ofimática:** usa la IA que ya vive dentro de tu suite documental y de correo, no un agregador genérico.
- **Capa de investigación y reportes:** añade **ChatGPT Deep Research** para informes con citas cuando el entregable sea externo o de mercado.
- **Capa CLI/automatización:** usa un agente de terminal para tareas repetitivas, scripts y transformación de archivos.
- **OpenRouter:** déjalo como **capa técnica de routing** y control de proveedores, no como interfaz principal para usuarios de negocio.

**Lectura de tus datos locales**

En los ficheros locales veo un patrón muy claro:

- En [contactos_50.csv](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-30/assistant_synthetic/contactos_50.csv) hay **30 clientes**, **8 proveedores**, **6 partners** y **6 prospectos**; además, **23 contactos son prioridad alta**.
- En [notas_voz.jsonl](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-30/assistant_synthetic/notas_voz.jsonl) abundan tareas de:
  - seguimiento y recordatorios
  - email y coordinación comercial
  - facturas, pagos y gastos
  - contratos y riesgos legales
  - informes ejecutivos y comparativas
- En [emails_hilos.md](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-30/assistant_synthetic/emails_hilos.md) aparecen señales muy concretas:
  - una demo de pagos
  - revisión de contrato
  - visita presencial
  - formato de informe en PDF con resumen ejecutivo
  - follow-up corto a un prospecto

Mi inferencia: tu caso no es “hacer chat”, sino **reducir fricción operativa** en correo, documentos, hojas, calendarios, PDFs y seguimiento comercial.

**Estado actual del mercado**

| Capa | Mejor encaje hoy | Qué aporta | Limitación clave |
|---|---|---|---|
| Ofimática en Google | **Google Workspace + Gemini** | Gemini está integrado en Gmail, Docs, Sheets, Slides, Meet y Drive; Google documenta control de datos y disponibilidad en español | Menos natural si tu organización ya está casada con Microsoft |
| Ofimática en Microsoft | **Microsoft 365 Copilot** | Muy fuerte en Word, Excel, PowerPoint, Outlook y Teams; ahora hay agentes para crear archivos y editar dentro del flujo de trabajo | La nueva capa de agentes y modelos aún se despliega por fases en algunos tenants |
| Investigación con fuentes | **ChatGPT Deep Research** | Planifica, busca en web, usa archivos subidos y apps conectadas, y devuelve reportes con citas/exportables | No sustituye la suite ofimática diaria |
| Agente CLI | **Gemini CLI / Claude Code / Codex CLI** | Automatizan terminal, archivos y scripts; útiles para pipelines, lotes y tareas técnicas | No son la mejor interfaz para usuarios no técnicos |
| Routing de modelos | **OpenRouter** | Unifica cientos de modelos y ofrece fallback, routing por proveedor, control de datos y ZDR | Es infraestructura, no producto de usuario final |

Fuentes oficiales que sostienen esto:
- Microsoft 365 Copilot: [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-overview)
- Agentes Word/Excel/PowerPoint en Copilot: [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/wordexcelppt-agents)
- Gemini en Workspace: [Google Help](https://support.google.com/docs/answer/15123226?hl=en) y [privacidad](https://support.google.com/docs/answer/14615114?hl=en)
- Gemini CLI: [GitHub oficial](https://github.com/google-gemini/gemini-cli)
- Claude Code: [Claude Code](https://www.claude.com/product/claude-code) y [docs](https://code.claude.com/docs?curius=1051)
- Codex CLI: [OpenAI Help Center](https://help.openai.com/en/articles/11096431)
- OpenRouter routing: [docs oficiales](https://openrouter.ai/docs/features/provider-routing/)
- Deep Research: [OpenAI Help Center](https://help.openai.com/en/articles/10500283-deep-research)

**Recomendación ejecutiva**

Si no tenéis ya un estándar impuesto por la empresa, mi recomendación es:

1. **Elegir una suite principal y no mezclarla en la interfaz de usuario.**
   - Si trabajáis más en Gmail/Docs/Sheets/Drive, adopta **Google Workspace + Gemini**.
   - Si trabajáis más en Outlook/Excel/Word/Teams, adopta **Microsoft 365 Copilot**.

2. **Para este caso concreto, me inclino ligeramente por Google Workspace + Gemini** como primera apuesta, porque tus datos locales muestran un uso muy centrado en:
   - correo
   - documentos
   - hojas de cálculo
   - resúmenes ejecutivos
   - coordinación y recordatorios
   - trabajo en español

   Gemini en Workspace está muy alineado con eso y Google documenta soporte en español y controles de privacidad dentro del dominio.

3. **Usar OpenRouter solo donde aporte valor real.**
   - Úsalo en backend para probar modelos, aplicar fallback, controlar precio o imponer ZDR.
   - No lo pondría como herramienta principal para usuarios de negocio, porque no resuelve el flujo de correo/documento/calendario de forma nativa.

4. **Añadir un agente CLI para automatización.**
   - **Gemini CLI** como opción base si quieres velocidad, búsqueda web, operaciones de archivos y una entrada muy simple.
   - **Claude Code** si priorizas trabajo complejo con subagentes y control fino de herramientas.
   - **Codex CLI** si tu foco es edición local segura con approvals y trabajo técnico.

5. **Para informes de dirección, añadir ChatGPT Deep Research.**
   - Encaja bien con tareas como comparativas, análisis de mercado, investigación legal/comercial y reportes con citas.
   - Además permite exportar a Markdown, Word o PDF, que encaja con la preferencia local de “PDF con resumen ejecutivo”.

**Plan de adopción 30/60/90**

- **30 días**
  - Pilotar 5 flujos: respuestas a emails, resumen de hilos, creación de informes, clasificación de contactos y extracción de acciones de contratos/facturas.
  - Medir tiempo ahorrado por usuario y tasa de edición manual posterior.

- **60 días**
  - Conectar la capa de IA con los documentos y plantillas reales.
  - Estandarizar prompts para:
    - resumen ejecutivo
    - respuesta corta a prospectos
    - minuta de riesgos
    - actualización de CRM/contactos
    - extracción de tareas de emails

- **90 días**
  - Decidir si la capa primaria será Google o Microsoft.
  - Mantener OpenRouter solo como plano técnico de pruebas/routing.
  - Definir el CLI estándar del equipo y su política de permisos.

**Mi síntesis final**

- **Para ofimática diaria:** Gemini en Workspace o Copilot en Microsoft, según suite.
- **Para investigación con trazabilidad:** ChatGPT Deep Research.
- **Para automatización de terminal:** Gemini CLI o Claude Code.
- **Para selección de modelo y fallback:** OpenRouter, pero detrás, no delante.

Si quieres, en el siguiente paso te lo convierto en una **matriz de decisión ejecutiva de 1 página** o en un **plan de implantación por departamentos**.
