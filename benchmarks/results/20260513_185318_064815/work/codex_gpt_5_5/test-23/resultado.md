Voy a leer primero el contexto web preparado y los datos locales para anclar la recomendación a la necesidad real de Barna Health, incluyendo contactos y fecha.

**Resumen Ejecutivo**

Para Barna Health, priorizaría **Microsoft Entra ID** o **Okta Workforce Identity**. La necesidad local es clara: Xavier Puig, IT de Barna Health, cliente de alta prioridad en Barcelona, confirmó una reunión técnica presencial el **18 de mayo de 2026 a las 10:00** para revisar integración con SSO.

**Recomendación Principal**

1. **Microsoft Entra ID**
   Mejor opción si Barna Health ya usa Microsoft 365, Windows/Active Directory o Azure.
   - Soporta SSO con **SAML**, **OpenID Connect/OAuth** y apps SaaS/on-prem.
   - Soporta **SCIM 2.0** para aprovisionamiento y desaprovisionamiento de usuarios.
   - Buen encaje para controles de acceso, MFA, Conditional Access, auditoría y entornos sanitarios regulados.
   - Menor fricción operativa si el directorio corporativo ya está en Microsoft.

2. **Okta Workforce Identity**
   Mejor opción si Barna Health quiere un IdP neutral, multi-cloud y con muchas integraciones.
   - Okta destaca por SSO, Adaptive MFA, lifecycle management, governance y acceso a aplicaciones legacy.
   - Tiene posicionamiento específico para healthcare y una nube de identidad orientada a cumplimiento HIPAA.
   - Suele ser más caro, pero fuerte si tienen muchas aplicaciones clínicas/SaaS heterogéneas.

3. **Google Cloud Identity / Google Workspace SSO**
   Opción razonable solo si Barna Health trabaja principalmente con Google Workspace.
   - Google documenta SSO con SAML y OIDC.
   - Bueno para ecosistema Google, pero lo pondría por detrás de Entra/Okta como IdP principal sanitario si hay muchas apps clínicas o legacy.

4. **Keycloak**
   Opción open-source si Barna Health quiere control total o integración muy custom.
   - Soporta SAML, OIDC, OAuth2, LDAP/AD, identity brokering y MFA.
   - Requiere operar alta disponibilidad, parches, seguridad, logging y cumplimiento. No lo recomendaría como primera opción salvo que Barna tenga equipo IAM/DevOps maduro.

5. **Auth0**
   Encaja mejor para aplicaciones de pacientes, portales o apps B2C/B2B, no tanto como IdP interno de plantilla.
   - Útil si el problema es “login de usuarios externos”.
   - Para cumplimiento sanitario, revisar plan Enterprise/BAA y contrato.

**Decisión Recomendada Para La Reunión**

Llevar dos caminos:

- Si Barna Health ya usa Microsoft 365 o AD: **proponer Microsoft Entra ID como opción preferente**.
- Si tienen mezcla fuerte de SaaS clínico, partners, contratistas y apps legacy: **comparar Entra vs Okta con una matriz técnica y coste total**.

Preguntas clave para Xavier Puig:
- Directorio actual: Microsoft AD/Entra, Google Workspace, LDAP u otro.
- Apps objetivo: SaaS clínico, intranet, ERP, portal paciente, VPN, apps on-prem.
- Protocolos requeridos: SAML, OIDC, SCIM.
- Necesidad de MFA resistente a phishing: FIDO2/WebAuthn/passkeys.
- Requisitos de GDPR, ENS, residencia de datos, auditoría y retención de logs.

**Fuentes Consultadas**

Consulta realizada el **13 de mayo de 2026**.

- Microsoft Entra SSO: https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-single-sign-on  
- Microsoft Entra SCIM: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/scim-support-in-entra-id  
- Microsoft HIPAA/HITECH: https://learn.microsoft.com/en-us/compliance/regulatory/offering-hipaa-hitech  
- Okta Workforce Identity: https://www.okta.com/workforce-identity/  
- Okta Healthcare: https://www.okta.com/solutions/healthcare/  
- Google SSO: https://support.google.com/a/answer/60224  
- Keycloak docs: https://www.keycloak.org/docs/latest/server_admin/  
- Auth0 pricing/compliance features: https://auth0.com/pricing  
- Contexto web preparado: Guru99, Scalefusion, Logto y Google Help incluidos en `web_context.md`.
