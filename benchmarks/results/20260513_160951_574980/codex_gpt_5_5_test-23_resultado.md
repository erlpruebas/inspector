Voy a leer primero el contexto web y los datos locales para entender qué necesidad concreta aparece en los hilos y quién sería el contacto relevante.

**Resumen para Barna Health**

Contacto local: Xavier Puig, IT, `xavier.puig@barnahealth.es`, +34 600 100 038, Barcelona.  
Necesidad detectada: reunión técnica presencial en Barcelona el **18 de mayo de 2026 a las 10:00** para revisar **integración con SSO**.

**Recomendación**

1. **Microsoft Entra ID**
   Mejor opción si Barna Health ya usa Microsoft 365, Azure AD/Active Directory o Windows endpoints. Cubre SAML, OIDC, apps SaaS, apps on-prem mediante Application Proxy, aprovisionamiento y controles de acceso condicional. Para una clínica, es la opción más pragmática si ya existe ecosistema Microsoft.

2. **Okta Workforce Identity**
   Mejor opción neutral si Barna Health tiene muchas aplicaciones heterogéneas y quiere un IdP independiente. Okta documenta soporte para SAML/OIDC, miles de integraciones OIN y provisioning/deprovisioning. Buena candidata si buscan madurez enterprise y flexibilidad multi-cloud.

3. **Google Cloud Identity / Google Workspace SSO**
   Adecuada si Barna Health ya usa Google Workspace. Google soporta SSO con SAML y OIDC en Workspace, con perfiles SSO por grupos u OUs. Menos atractiva como IdP principal si el entorno principal es Microsoft.

4. **PingOne / PingFederate**
   Opción enterprise fuerte para escenarios complejos: federación avanzada, legacy, múltiples dominios, partners o integración con directorios existentes. Suele tener más sentido si el proyecto requiere arquitectura IAM sofisticada.

5. **Keycloak**
   Opción open source si Barna Health quiere control propio, despliegue on-prem o evitar lock-in. Soporta SSO, OIDC, OAuth 2.0, SAML, LDAP/Active Directory y MFA, pero exige operación interna: alta disponibilidad, parches, monitorización, backups y hardening.

**Mi shortlist para la reunión**

Si no conocemos su stack, llevaría esta propuesta:

- **Primera opción:** Microsoft Entra ID si usan Microsoft 365/AD.
- **Alternativa vendor-neutral:** Okta si quieren IdP independiente con integraciones SaaS.
- **Alternativa self-hosted:** Keycloak solo si tienen equipo técnico para operarlo.
- **Google Cloud Identity:** solo si Workspace es su sistema principal.
- **PingOne:** reservarlo para requisitos complejos de federación o legacy.

**Puntos técnicos a validar con Xavier**

- Directorio actual: Microsoft AD, Entra ID, Google Workspace, LDAP u otro.
- Aplicaciones a integrar: ¿soportan SAML 2.0, OIDC o solo login local?
- Necesidad de SCIM para altas, bajas y cambios de rol.
- MFA obligatoria, acceso condicional, grupos y roles.
- Auditoría, logs exportables, retención y trazabilidad.
- Requisitos GDPR, residencia de datos, DPA y certificaciones.
- Usuarios internos vs pacientes/externos. Para apps de pacientes, Auth0 puede entrar como CIAM, pero no lo pondría como primera opción para SSO interno.

**Fuentes consultadas el 13 de mayo de 2026**

- Microsoft Entra SSO: https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-single-sign-on  
- Okta SSO/OIDC/SAML: https://developer.okta.com/docs/guides/oin-sso-overview/  
- Google Cloud Identity SSO: https://docs.cloud.google.com/architecture/identity/single-sign-on  
- PingOne SSO: https://docs.pingidentity.com/pingone/getting_started_with_pingone/p1_p1sso_start.html  
- Keycloak Server Admin Guide: https://www.keycloak.org/docs/latest/server_admin/index.html  
- Contexto web preparado: Guru99 y Scalefusion como comparativas 2026 de mercado; Logto como comparativa IAM open source 2025.
