# Investigación de Proveedor SSO para Barna Health  

**Fecha de elaboración:** 21‑05‑2026  

---

## 1. Contexto y necesidad técnica  

- **Cliente:** Barna Health  
- **Contacto interno:** Xavier Puig (IT) – xavier.puig@barnahealth.es – Tel. +34 600 100 038 – Barcelona  
- **Reunión programada:** 18 de mayo 2026, 10:00 h (presencial en Barcelona) – objetivo: revisar integración con SSO (ver hilo de correo **E‑004**).  

Barna Health necesita una solución de **Single Sign‑On (SSO)** que permita:  

1. **Integración rápida** con sus aplicaciones internas y SaaS (CRM, ERP, herramientas de telemedicina).  
2. **Cumplimiento** con normativas de salud (GDPR, ISO 27001, HIPAA‑like).  
3. **Escalabilidad** para usuarios internos y externos (proveedores, pacientes).  
4. **Gestión de identidades** (provisionamiento, MFA, políticas de acceso).  

---

## 2. Contactos relevantes (CSV)  

| Nombre | Email | Teléfono | Ciudad | Empresa | Rol | Tipo | Prioridad |
|--------|-------|----------|--------|---------|-----|------|-----------|
| **Xavier Puig** | xavier.puig@barnahealth.es | +34 600 100 038 | Barcelona | Barna Health | IT | cliente | alta |

---

## 3. Proveedores SSO evaluados  

| Proveedor | Tipo | Principales características | Compatibilidad con estándares (SAML, OIDC, OAuth) | Cumplimiento normativo | Modelo de precios | Comentario de fuentes |
|-----------|------|----------------------------|---------------------------------------------------|------------------------|-------------------|-----------------------|
| **Okta** | SaaS | Amplio catálogo de integraciones, MFA adaptativa, gestión de usuarios y grupos, API robusta. | SAML, OIDC, OAuth 2.0 | GDPR, ISO 27001, SOC 2, HIPAA (con plan Enterprise) | Suscripción por usuario activo (≈ $2‑$8/mes). | Referido como uno de los líderes del mercado en guías de 2026 (Fuente 2). |
| **Microsoft Azure AD** | SaaS / híbrido | Integración nativa con Office 365, Azure, Windows, soporte de dispositivos híbridos, Conditional Access. | SAML, OIDC, OAuth 2.0, WS‑Fed | GDPR, ISO 27001, HIPAA, SOC 2 | Incluido en licencias Microsoft 365 o por usuario adicional (≈ $6/mes). | Aparece en listados de mejores soluciones SSO 2026 (Fuente 1). |
| **OneLogin** | SaaS | SSO + IAM, MFA, gestión de riesgos, integración con directorios on‑premise. | SAML, OIDC, OAuth 2.0 | GDPR, ISO 27001, SOC 2, HIPAA | Por usuario activo (≈ $4‑$7/mes). | Mencionado en comparativas de proveedores (Fuente 2). |
| **Auth0 (now part of Okta)** | SaaS | Plataforma de autenticación extensible, reglas personalizadas, extensas librerías SDK. | SAML, OIDC,
