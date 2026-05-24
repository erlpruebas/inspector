Voy a leer primero el contexto web y los datos locales indicados para anclar la recomendación a la necesidad concreta de Barna Health.

**Contexto local usado**

Barna Health figura como cliente de prioridad alta en Barcelona. El contacto técnico es Xavier Puig, IT, `xavier.puig@barnahealth.es`, `+34 600 100 038`. En el hilo local E-004 confirmó una reunión presencial en Barcelona el **18 de mayo de 2026 a las 10:00** para revisar integración con SSO. Hoy es **21 de mayo de 2026**, así que la recomendación debe servir para seguimiento post-reunión.

**Recomendación corta**

Para Barna Health, priorizaría **Microsoft Entra ID P1/P2** como primera opción si ya usan Microsoft 365, Windows/AD o Intune. Como alternativa fuerte, **Okta Workforce Identity** si necesitan independencia de proveedor, muchas integraciones SaaS, portal de pacientes/partners o evolución a Zero Trust más amplia. Mantendría **OneLogin** como opción coste/implantación intermedia y **Keycloak** solo si Barna Health quiere autogestionar identidad con equipo técnico suficiente.

| Opción | Encaje para Barna Health | Puntos fuertes | Riesgo/coste |
|---|---|---|---|
| **Microsoft Entra ID P1/P2** | Mejor opción por defecto para SSO corporativo sanitario si ya hay Microsoft 365 | SSO, MFA, Conditional Access, integración con AD/Windows/M365; P1 desde **$6 usuario/mes** y P2 desde **$9 usuario/mes** según Microsoft | Menos neutral si el stack no es Microsoft |
| **Okta Workforce Identity** | Mejor si hay muchas apps clínicas/SaaS, partners externos o portal paciente | Foco sanitario, HIPAA, SSO, MFA, lifecycle, Access Gateway, muchas integraciones | Precio suele requerir contacto comercial; mayor coste |
| **OneLogin** | Buena alternativa pragmática para SSO + MFA + directorios + RADIUS/VPN | SAML/OIDC ilimitado en planes, MFA, directorios, RADIUS, apps on-prem/homegrown en Enterprise | Menor posicionamiento enterprise que Okta/Microsoft |
| **Keycloak** | Solo si quieren control total/self-hosted | Open source, OIDC, SAML, flexible, sin licencia por usuario | Operación, HA, parches, auditoría y soporte recaen en Barna Health |
| **Google Cloud Identity** | Solo si Barna Health está centrada en Google Workspace | SSO a miles de SaaS; Premium publicado a **$7.20 usuario/mes** | Menos natural si ya están en Microsoft/AD |

**Criterios técnicos para decidir**

Para la integración de Barna Health pediría en la siguiente llamada con Xavier Puig:

1. Directorio actual: Microsoft Entra/AD, Google Workspace, LDAP u otro.
2. Protocolos requeridos por las aplicaciones: **SAML 2.0**, **OIDC/OAuth2**, y si necesitan **SCIM** para altas/bajas.
3. MFA obligatorio: app push, FIDO2/WebAuthn/passkeys, hardware keys, SMS solo como respaldo.
4. Aplicaciones críticas: historia clínica, portal paciente, VPN, WiFi/RADIUS, ERP, correo, BI.
5. Requisitos de cumplimiento: GDPR, DPA, residencia/transferencias de datos, logs exportables a SIEM, revisiones de acceso.
6. Modelo de usuarios: empleados, médicos externos, administrativos, proveedores, pacientes.

**Mi shortlist para propuesta**

1. **Microsoft Entra ID P1** como piloto si Barna Health ya usa Microsoft 365. Subir a **P2** si necesitan Identity Protection, governance o controles de riesgo más avanzados.
2. **Okta Workforce Identity** como comparativa si tienen entorno heterogéneo o quieren una capa neutral para apps clínicas, partners y pacientes.
3. **OneLogin Enterprise** si la prioridad es implantar rápido SSO/MFA con directorios, RADIUS/VPN y apps on-prem sin ir a una suite tan amplia.
4. **Keycloak** solo para escenario técnico específico: presupuesto de licencia bajo, equipo DevOps/IAM interno y tolerancia a operar infraestructura crítica.

**Fuentes consultadas**

- Microsoft Entra pricing, consultado el 21/05/2026: https://www.microsoft.com/en-us/security/business/microsoft-entra-pricing  
- Microsoft Entra HIPAA guidance: https://learn.microsoft.com/en-us/entra/standards/hipaa-configure-for-compliance  
- Okta Healthcare Identity: https://www.okta.com/industries/healthcare/  
- Okta pricing/features: https://www.okta.com/pricing/  
- OneLogin pricing/features: https://www.onelogin.com/product/pricing  
- OneLogin SOC 2 / GDPR / HIPAA mapping: https://www.onelogin.com/compliance/soc-2-type-2  
- Google Cloud Identity plans: https://docs.cloud.google.com/identity/docs/how-to/compare-cloud-identity-billing-plans  
- Keycloak docs OIDC/SAML: https://www.keycloak.org/docs/25.0.6/securing_apps/index.html  
- Contexto web preparado: Scalefusion “Los 10 mejores proveedores y soluciones de SSO en 2026”, Guru99 “Las 10 mejores soluciones y proveedores de SSO (2026)”.
