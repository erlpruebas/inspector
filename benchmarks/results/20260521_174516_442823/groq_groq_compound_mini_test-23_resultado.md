# Informe de opciones de SSO para Barna Health  

**Fecha de elaboración:** 21‑05‑2026  

## 1. Contexto y necesidad técnica  

- **Cliente:** Barna Health (Barcelona)  
- **Contacto interno:** Xavier Puig – IT (email: xavier.puig@barnahealth.es, teléfono: +34 600 100 038) – prioridad **alta**.  
- **Reunión programada:** 18 de mayo de 2026, 10:00 (presencial en Barcelona) para revisar la integración con SSO (ver hilo de correo “Barna Health - visita Barcelona”).  
- **Necesidad:** Implementar un sistema de Single Sign‑On que permita a los usuarios de Barna Health acceder a sus aplicaciones internas y SaaS de forma segura, con soporte para protocolos estándar (SAML, OpenID Connect), gestión de usuarios y cumplimiento normativo (GDPR, SOC 2).  

## 2. Opciones de proveedores de SSO (2026)

| Proveedor | Tipo | Principales características | Pros | Contras |
|-----------|------|-----------------------------|------|---------|
| **OneLogin** | SaaS (propietario) | SAML, OIDC, MFA, gestión de usuarios, integración con más de 5 000 apps. | Fácil de implementar, buena UI, soporte multilingüe. | Precio por usuario relativamente alto. |
| **Okta** | SaaS (propietario) | Amplio catálogo de conectores, políticas de seguridad avanzadas, API robusta. | Escalabilidad, excelente documentación y soporte. | Coste elevado para pequeñas organizaciones. |
| **Auth0 (now part of Okta)** | SaaS | Soporta SAML, OIDC, reglas personalizadas, extensiones de código. | Gran flexibilidad, buen ecosistema de extensiones. | Complejidad en configuraciones avanzadas. |
| **Keycloak** | Open‑Source | SAML, OIDC, LDAP, MFA, gestión de usuarios y grupos, auto‑hosted. | Sin coste de licencia, alta personalización. | Requiere infraestructura y mantenimiento interno. |
| **Logto** | Open‑Source | SAML, OIDC, UI configurable, SDKs para múltiples lenguajes. | Ligero, fácil de desplegar en cloud, comunidad activa. | Menor número de integraciones pre‑construidas que Okta/OneLogin. |
| **SuperTokens** | Open‑Source | Sesiones sin servidor, SAML/OIDC, enfoque en seguridad de tokens. | Muy buena gestión de sesiones, código abierto. | Menos enfoque en gestión de usuarios corporativos. |
| **Azure AD** | SaaS (Microsoft) | Integración nativa con Office 365, Azure, SAML/OIDC, Conditional Access. | Ideal si ya usan Azure, buen soporte empresarial. | Dependencia del ecosistema Microsoft. |
| **Google Workspace Identity** | SaaS | SAML, OIDC, gestión de usuarios Google, MFA. | Simple si usan Google Workspace. | Limitado fuera del ecosistema Google. |

> **Fuentes:**  
> - Los 10 mejores proveedores y soluciones de SSO en 2026 (Fuente 1) – lista de proveedores líderes.  
> - Los 5 principales proveedores de IAM OSS 2025 (Fuente 2) – menciona Keycloak, Logto, SuperTokens, etc.  
> - Las 10 mejores soluciones y proveedores de SSO (2026) (Fuente 3) – confirma la popularidad de Okta, OneLogin, Auth0.  

## 3. Criterios de selección para Barna Health  

1. **Compatibilidad con protocolos** (SAML, OIDC).  
2. **Facilidad de integración** con aplicaciones médicas existentes (EHR, portal de pacientes).  
3. **Cumplimiento normativo** (GDPR, SOC 2).  
4. **Modelo de despliegue** (cloud vs on‑premise) según la política de datos de salud.  
5. **Coste total de propiedad** (licencias + operación).  
6. **Soporte y SLA** (importante para entornos críticos).  

## 4. Recomendación  

| Recomendación | Motivo |
|---------------|--------|
| **Okta** (plan Enterprise) | Cumple con todos los criterios críticos: amplio catálogo de conectores (incluidos EHR), fuerte cumplimiento (SOC 2, GDPR), despliegue totalmente en la nube (sin infraestructura propia) y SLA 99.9 %. Ideal para una organización que busca rapidez y soporte robusto. |
| **Keycloak** (auto‑hosted) | Alternativa OSS si Barna Health prefiere mantener el control total de los datos y tiene capacidad de operar infraestructura. Requiere equipo interno para gestión y actualizaciones. |
| **OneLogin** | Opción intermedia en coste y funcionalidades, buena UI y soporte multilingüe, útil si se prioriza rapidez de puesta en marcha sin la escala de Okta. |

**Acción recomendada:** Iniciar pruebas piloto con Okta (plan de 30 días) y, paralelamente, desplegar una instancia de prueba de Keycloak en un entorno de desarrollo para comparar esfuerzo de integración y costes operativos.

## 5. Próximos pasos  

1. **Confirmar disponibilidad** de Xavier Puig para la reunión del 18 de may 2026 (ya agendada).  
2. **Solicitar a Okta** una demo enfocada en integración con los sistemas actuales de Barna Health (EHR, portal de pacientes).  
3. **Instalar** una versión de prueba de Keycloak en el entorno de staging y validar flujos SAML/OIDC con una aplicación interna.  
4. **Elaborar matriz de comparación** (coste, tiempo de integración, cumplimiento) después de las pruebas.  
5. **Presentar** resultados y propuesta final al comité de TI antes del 31 de may 2026.  

## 6. Información de contacto  

- **Xavier Puig** – IT, Barna Health  
  - Email: xavier.puig@barnahealth.es  
  - Teléfono: +34 600 100 038  

---  

*Este informe se basa en datos locales (contactos y correo interno) y fuentes web actualizadas a mayo 2026.*
