# Investigación de Proveedores de SSO para Barna Health  

**Fecha de consulta:** 21‑05‑2026  

## 1. Contexto interno  

| Campo | Valor |
|-------|-------|
| **Empresa** | Barna Health |
| **Contacto interno** | **Xavier Puig** – IT (cliente interno, prioridad alta) |
| **Email** | xavier.puig@barnahealth.es |
| **Teléfono** | +34 600 100 038 |
| **Ciudad** | Barcelona |
| **Reunión programada** | 18‑05‑2026, 10:00 (presencial en Barcelona) – “Revisaremos integración con SSO” (ver hilo E‑004) |
| **Necesidad técnica** | Implementar un sistema de Single Sign‑On (SSO) que: <br>• Centralice la autenticación de usuarios internos y externos (proveedores, partners). <br>• Cumpla con GDPR y normativas sanitarias (HIPAA‑like). <br>• Ofrezca integración con aplicaciones SaaS usadas por Barna Health (EHR, portal de pacientes, herramientas de análisis). <br>• Permita autenticación multifactor (MFA) y gestión de roles. |

## 2. Proveedores de SSO recomendados (2026)

| Proveedor | Tipo | Principales características | Ventajas | Desventajas | Modelo de precios (aprox.) |
|-----------|------|----------------------------|----------|-------------|----------------------------|
| **Okta** | Comercial | • Amplio catálogo de conectores pre‑construidos (más de 7 000). <br>• Soporte SAML, OAuth 2.0, OpenID Connect. <br>• MFA adaptable (push, biometría). <br>• Cumple con GDPR, HIPAA, SOC 2. | • Escalabilidad empresarial. <br>• Excelente UI y reporting. | • Precio elevado para pymes. | Desde 2 USD/usuario/mes (Enterprise > 5 USD). |
| **Auth0 (Now part of Okta)** | Comercial | • Plataforma “as a service”. <br>• Extensible con reglas JavaScript. <br>• Soporte de social login y passwordless. | • Flexibilidad para desarrolladores. | • Límites en número de logins en planes básicos. | Desde 23 USD/mes (hasta 2 000 usuarios). |
| **Microsoft Entra ID (Azure AD)** | Comercial | • Integración nativa con Microsoft 365, Azure y SaaS. <br>• Conditional Access, MFA, Identity Protection. | • Ideal si ya usan Azure. | • Menos conectores fuera del ecosistema Microsoft. | Incluido en licencias Microsoft 365 E3/E5; adicional para Premium P1/P2 (≈6 USD/usuario/mes). |
| **Keycloak** | Open‑source | • SAML, OpenID Connect, LDAP. <br>• MFA, federación, gestión de usuarios y grupos. <br>• Deploy on‑premise o en Kubernetes. | • Sin coste de licencia. <br>• Gran comunidad y extensibilidad. | • Requiere infraestructura y mantenimiento interno. | Gratuito (costes operacionales). |
| **SuperTokens** | Open‑source (con SaaS) | • API ligera, foco en developer‑experience. <br>• Soporta SSO, MFA, sesiones sin servidor. | • Fácil de integrar en apps modernas. | • Menos funcionalidades de reporting y compliance out‑of‑the‑box. | Gratis (self‑hosted) o planes SaaS desde 49 USD/mes. |
| **OneLogin** | Comercial | • SSO, MFA, Lifecycle Management. <br>• Cumple con HIPAA, GDPR. <br>• Amplio marketplace de apps. | • Buen equilibrio precio‑funcionalidad. | • UI menos moderna que Okta. | Desde 4 USD/usuario/mes. |
| **LoginRadius** | Comercial | • Enfocado en B2C y B2B. <br>• Social login, passwordless, MFA. | • Excelente para portales de pacientes. | • Menor presencia en entornos corporativos internos. | Desde 0,5 USD/usuario/mes (plan básico). |

> **Fuentes:**  
> - Fuente 1: “Los 10 mejores proveedores y soluciones de SSO en 2026” (Scalefusion) – lista de proveedores comerciales y de gestión de dispositivos.  
> - Fuente 2: “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto 2025” (Logto) – destaca a Keycloak, SuperTokens, etc.  
> - Fuente 3: “Las 10 mejores soluciones y proveedores de SSO (2026)” (Guru99) – menciona Okta, Auth0, OneLogin, Microsoft Entra ID.  
> - Fuente 4: “Cómo elegir el mejor proveedor de SSO para su organización” (LinkedIn) – criterios de selección (seguridad, costos, integración).  

## 3. Criterios de selección para Barna Health  

| Criterio | Peso (%) | Comentario |
|----------|----------|------------|
| **Cumplimiento normativo (GDPR, HIPAA‑like)** | 30 | Necesario para datos de pacientes y proveedores. |
| **Integración con SaaS existentes** (EHR, analytics, portal) | 25 | Conectores pre‑definidos reducen tiempo de proyecto. |
| **Escalabilidad y disponibilidad** | 15 | Soporte 99,9 % y capacidad de crecer con la empresa. |
| **Facilidad de gestión interna** (UI, reporting, provisioning) | 10 | Reduce carga al equipo de IT. |
| **Coste total de propiedad (TCO)** | 10 | Licencias + infraestructura + mantenimiento. |
| **Soporte y comunidad** | 10 | SLA y disponibilidad de recursos. |

## 4. Recomendación concreta  

| Opción | Puntuación total (sobre 100) | Razonamiento |
|--------|------------------------------|--------------|
| **Okta (Enterprise)** | **88** | Cumple con todos los criterios críticos, ofrece amplio catálogo de conectores (incluye EHR populares) y fuerte compliance. Ideal para una organización que busca rapidez y mínima carga operativa. |
| **Keycloak (self‑hosted)** | **78** | Excelente para reducir costes de licencia y mantener control total de datos, pero requiere equipo de infraestructura y mantenimiento que Barna Health debe asignar. |
| **Microsoft Entra ID (Premium P2)** | **75** | Si Barna Health ya usa Azure/M365, la integración es fluida y el coste está incluido en licencias existentes. Menor número de conectores externos. |
| **OneLogin** | **73** | Buen equilibrio precio‑funcionalidad, pero menos opciones de integración específicas para el sector salud. |
| **SuperTokens (SaaS)** | **65** | Muy fácil de integrar en apps modernas, pero carece de módulos avanzados de compliance y reporting. |

### Opción prioritaria  
**Okta Enterprise** – permite lanzar la solución de SSO en < 2 meses, con soporte 24 / 7 y certificaciones de seguridad requeridas por el sector sanitario.  

### Plan de acción sugerido  

1. **Reunión de descubrimiento (18‑05‑2026)** con Xavier Puig y equipo técnico para validar requisitos de integración (EHR, portal de pacientes, herramientas de análisis).  
2. **Prueba de concepto (PoC)** de 30 días con Okta:  
   - Configurar SAML/OIDC con los principales SaaS.  
   - Activar MFA (push + biometría).  
   - Evaluar flujos de aprovisionamiento automático vía SCIM.  
3. **Evaluación de cumplimiento**: revisión de los informes de auditoría de Okta (SOC 2, ISO 27001, HIPAA).  
4. **Análisis de coste**: estimar usuarios activos (≈ 1 200) → ~ 6 000 USD/mes (Enterprise). Comparar con presupuesto de TI.  
5. **Decisión**: si el PoC cumple, proceder a contrato anual y plan de despliegue faseado (piloto interno → ampliación a proveedores/partners).  

## 5. Próximos pasos internos  

| Acción | Responsable | Fecha límite |
|--------|--------------|--------------
