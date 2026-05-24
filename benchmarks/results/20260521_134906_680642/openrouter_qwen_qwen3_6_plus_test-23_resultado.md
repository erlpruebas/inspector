# Informe de Investigación: Proveedor de SSO para Barna Health

## Contexto y Datos de Contacto
- **Cliente:** Barna Health (Sector Sanitario)
- **Contacto Técnico:** Xavier Puig (Departamento IT)
- **Email:** xavier.puig@barnahealth.es | **Teléfono:** +34 600 100 038
- **Ubicación:** Barcelona
- **Fecha de Reunión Técnica:** 18 de mayo de 2026 a las 10:00 h (Presencial)
- **Necesidad Técnica:** Revisión e integración de solución de Single Sign-On (SSO) para unificar accesos y mejorar la postura de seguridad. *(Fuente local: Hilo E-004, `emails_hilos.md`)*

## Análisis de Opciones de SSO (Contexto 2025-2026)
Basado en la investigación actual y las necesidades específicas del sector sanitario, se presentan las siguientes opciones alineadas con estándares de seguridad y cumplimiento normativo (GDPR/LOPDGDD, SOC 2):

### 1. Soluciones Empresariales SaaS (Líderes del mercado)
- **Microsoft Entra ID (Azure AD) / Okta:** Estándar de facto en entornos corporativos y sanitarios. Ofrecen integración nativa con suites de productividad, MFA avanzado, y cumplimiento robusto. Ideales si Barna Health busca un despliegue rápido con soporte empresarial y gestión centralizada de identidades.
- **Scalefusion OneIdP:** Combina SSO con gestión MDM/UEM, optimizando el acceso seguro en dispositivos médicos, tablets y estaciones de trabajo compartidas. *(Fuente web: Scalefusion Blog, Mayo 2026)*

### 2. Soluciones Open Source / IAM Moderno
- **Keycloak:** Solución IAM de código abierto ampliamente adoptada. Permite control total de los datos (crítico en salud), soporta SAML 2.0, OIDC y OAuth 2.0, y facilita la auditoría de accesos sin costes de licencia recurrentes. *(Fuente web: Logto Blog, 2025)*
- **Logto / SuperTokens:** Alternativas modernas centradas en la experiencia de desarrollo y despliegue ágil. Ofrecen gestión de identidades multi-tenant, políticas de autorización granulares y rápida integración con APIs sanitarias. *(Fuente web: Logto Blog, 2025)*

## Criterios de Selección para Barna Health
Según las mejores prácticas actuales para elegir un proveedor SSO, se recomienda evaluar los siguientes factores antes de la reunión:
1. **Cumplimiento Normativo:** Certificaciones específicas para el sector salud y protección de datos en la UE.
2. **Protocolos Soportados:** Compatibilidad nativa con SAML, OIDC y OAuth 2.0 para integrar aplicaciones clínicas (HIS/EHR) y administrativas existentes.
3. **Gestión de Ciclo de Vida:** Aprovisionamiento automático (SCIM) y auditorías de acceso para cumplir con políticas internas de IT y rotación de personal clínico.
4. **Coste y Mantenimiento:** Balance entre licencias SaaS (menor carga operativa) vs. infraestructura propia/Open Source (mayor control de datos). *(Fuente web: LinkedIn Advice, 2026)*

## Próximos Pasos para la Reunión del 18/05/2026
- Validar el inventario actual de aplicaciones y sistemas legacy a integrar con el SSO.
- Definir requisitos de MFA y políticas de acceso condicional diferenciadas para personal clínico, administrativo y externo.
- Solicitar demos técnicas de 2-3 proveedores shortlisted (ej. Entra ID, Keycloak, Okta) enfocadas en el flujo de autenticación sanitaria.
- Establecer un plan de migración por fases y rollback para minimizar interrupciones en la operativa asistencial.

---
**Fuentes consultadas:**
- Scalefusion Blog: *Los 10 mejores proveedores y soluciones de SSO en 2026* (https://blog.scalefusion.com/es/las-mejores-soluciones-sso/)
- Logto Blog: *Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto 2025* (https://blog.logto.io/es/top-oss-iam-providers-2025)
- Guru99: *Las 10 mejores soluciones y proveedores de SSO (2026)* (https://www.guru99.com/es/best-single-sign-on-sso-solution-providers.html)
- LinkedIn Advice
