Voy a leer primero el contexto local y el contexto web preparado para anclar la recomendación a la necesidad concreta de Barna Health y evitar asumir requisitos que no estén en los datos.

A fecha **20 de mayo de 2026**, con los datos locales disponibles, el contacto operativo para Barna Health es **PERSON_0024 <EMAIL_0018>**, rol **IT**, en **Barcelona**, cliente de **prioridad alta**. Hay una **reunión técnica presencial en Barcelona el 18 de mayo a las 10:00** para revisar **integración con SSO**.

**Recomendación corta**

Para Barna Health, priorizaría:

1. **Microsoft Entra ID** si ya usan Microsoft 365, Windows, Intune o Azure. Es la opción más pragmática para una clínica/empresa sanitaria que necesita SSO rápido, MFA, acceso condicional, auditoría y soporte amplio de apps. Microsoft documenta SSO con **SAML**, **OpenID Connect**, OAuth y opciones para aplicaciones on-premises mediante Application Proxy.  
   Fuente: Microsoft Learn, “Plan a single sign-on deployment” y “SAML protocol”.

2. **Okta Workforce Identity** si necesitan un IdP neutral, con muchas integraciones SaaS y menos dependencia de Microsoft. Buen candidato si Barna Health integra varias aplicaciones clínicas, ERP, RRHH, proveedores externos o apps cloud heterogéneas. Okta soporta SSO con **SAML** y **OIDC**.  
   Fuente: Okta Developer, “Build a Single Sign-On integration”.

3. **Keycloak** solo si Barna Health exige control propio, despliegue en infraestructura propia o máxima soberanía técnica. Soporta **OpenID Connect** y **SAML 2.0**, pero exige operación seria: alta disponibilidad, backups, parches, monitorización, rotación de claves y respuesta ante incidentes.  
   Fuente: Keycloak Server Administration Guide.

**Alternativas útiles**

- **OneLogin**: buena opción SaaS de complejidad intermedia. Soporta apps cloud y detrás del firewall, MFA, políticas contextuales y protocolos como SAML/OIDC. Puede encajar si quieren algo más sencillo que Okta/Ping.  
  Fuente: OneLogin SSO product page.

- **Ping Identity / PingOne**: fuerte en entornos empresariales, híbridos y regulados. Lo miraría si hay integraciones complejas, múltiples dominios, federación avanzada o requisitos de identidad a gran escala.  
  Fuente: PingOne SSO docs.

- **Auth0**: lo consideraría más para aplicaciones propias orientadas a pacientes, partners o clientes externos, no como primera opción de SSO interno de plantilla sanitaria. Soporta SSO, SAML y OIDC, pero su encaje natural es CIAM/desarrollo de producto.  
  Fuente: Auth0 Docs, “Single Sign-On” y “Enterprise Identity Providers”.

**Criterios para Barna Health**

Para la reunión técnica con PERSON_0024, validaría estos puntos antes de elegir:

- Directorio actual: Microsoft 365/Entra, Google Workspace, LDAP/AD local u otro.
- Apps a integrar: clínicas, ERP, facturación, soporte, correo, VPN, intranet, herramientas SaaS.
- Protocolos requeridos: **SAML 2.0** para apps empresariales antiguas; **OIDC/OAuth2** para apps modernas.
- Seguridad mínima: MFA obligatorio, acceso condicional por dispositivo/ubicación/riesgo, logs exportables, alertas.
- Cumplimiento: GDPR, DPA, residencia de datos, auditoría, trazabilidad de accesos y baja rápida de usuarios.
- Operación: quién administrará altas/bajas, grupos, roles, certificados SAML, recuperación de cuentas y rotación de secretos.

**Decisión recomendada**

Si Barna Health ya está en Microsoft 365: **Microsoft Entra ID P1/P2** como primera opción.

Si no hay stack Microsoft claro o quieren independencia de proveedor: **Okta** como primera alternativa SaaS.

Si el requisito dominante es soberanía/on-prem y tienen equipo técnico para operarlo: **Keycloak**, preferiblemente con soporte profesional o despliegue gestionado.

Fuentes usadas:  
- Contexto local: `assistant_synthetic/emails_hilos.md`, `assistant_synthetic/contactos_50.csv`  
- Contexto web preparado: Scalefusion “Los 10 mejores proveedores y soluciones de SSO en 2026”, Logto “Top OSS IAM providers 2025”  
- Microsoft: https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/plan-sso-deployment  
- Okta: https://developer.okta.com/docs/guides/build-sso-integration/main/  
- Keycloak: https://www.keycloak.org/docs/latest/server_admin/  
- OneLogin: https://www.onelogin.com/product/sso  
- Ping Identity: https://docs.pingidentity.com/pingone/getting_started_with_pingone/p1_p1sso_start.html  
- Auth0: https://auth0.com/docs/authenticate/single-sign-on
