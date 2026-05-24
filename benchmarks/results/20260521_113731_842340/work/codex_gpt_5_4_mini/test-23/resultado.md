Voy a leer primero el contexto local y el `web_context.md` para entender la necesidad técnica y el contacto, y después contrastaré opciones actuales de SSO con fuentes oficiales.

Ya tengo el hilo de Barna Health: Xavier Puig, rol IT, con reunión técnica presencial en Barcelona el 18 de mayo a las 10:00 para revisar integración con SSO. Ahora voy a concretar esa necesidad con el contacto local y contrastarla con proveedores actuales desde fuentes oficiales.

**Contexto**
- El contacto clave es `Xavier Puig`, rol `IT`, empresa `Barna Health`, `Barcelona`, prioridad `alta` [contactos_50.csv](D:\inspector\benchmarks\results\20260521_113731_842340\work\codex_gpt_5_4_mini\test-23\assistant_synthetic\contactos_50.csv#L39)
- En el hilo interno aparece una reunión técnica presencial en Barcelona el `18 de mayo de 2026` para revisar `integración con SSO` [emails_hilos.md](D:\inspector\benchmarks\results\20260521_113731_842340\work\codex_gpt_5_4_mini\test-23\assistant_synthetic\emails_hilos.md#L31-L32)

**Lectura técnica**
- Esto apunta a un SSO de `workforce` o `enterprise access`, no solo a login de pacientes.
- Para ese caso, la combinación que más importa es: `SAML 2.0`, `OIDC`, `SCIM` para aprovisionamiento, `MFA/Conditional Access`, auditoría y alguna opción de residencia de datos si manejan requisitos GDPR o sanitarios.

**Opciones actuales recomendadas**
| Opción | Encaje para Barna Health | Cuándo la elegiría |
|---|---|---|
| Microsoft Entra ID | Muy alto | Si ya usan Microsoft 365/Azure o quieren el camino más directo para SSO empresarial con `Conditional Access`, `SAML/OIDC` y `SCIM` |
| Okta Workforce Identity | Muy alto | Si tienen un parque SaaS heterogéneo y necesitan catálogo amplio de apps, provisión y gobierno de identidades |
| PingOne | Alto | Si tienen entorno híbrido, aplicaciones legacy o necesitan más control de federación y MFA |
| Keycloak | Alto si quieren control propio | Si prefieren autogestionar la plataforma y minimizar dependencia de un SaaS comercial |
| Auth0 | Medio, sobre todo para portal externo | Si el caso real es más `patient portal` / `partner portal` que SSO interno de empleados |

**Mi recomendación práctica**
1. `Microsoft Entra ID` como primera opción si Barna Health ya está en el ecosistema Microsoft. Tiene SAML, OIDC, SCIM, Conditional Access y opciones de residencia de datos por geografía. [Microsoft Entra SAML](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/add-application-portal-setup-sso), [Microsoft Entra SCIM](https://learn.microsoft.com/en-us/entra/identity/app-provisioning/scim-support-in-entra-id), [Microsoft Entra data residency](https://learn.microsoft.com/en-us/entra/fundamentals/data-residency), [Conditional Access](https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview?azure-portal=true)
2. `Okta` como segunda opción si la prioridad es gobernar muchas aplicaciones SaaS y automatizar altas/bajas con buen nivel de madurez. [Okta SSO](https://help.okta.com/en-us/content/topics/apps/apps_overview_of_managing_apps_and_sso.htm), [Okta provisioning/SCIM](https://help.okta.com/oie/en-us/content/topics/provisioning/lcm/con-okta-prov.htm), [Okta governance](https://help.okta.com/en-us/Content/Topics/identity-governance/iga.htm), [Okta data residency](https://www.okta.com/okta-data-residency/)
3. `PingOne` si el entorno es más híbrido o enterprise pesado. Soporta SSO, SCIM, MFA y residencia de datos por región. [PingOne SSO](https://docs.pingidentity.com/pingone/getting_started_with_pingone/p1_p1sso_start.html), [PingOne SCIM](https://docs.pingidentity.com/pingone/integrations/p1_create_scim_connection.html), [PingOne MFA](https://docs.pingidentity.com/pingone/strong_authentication_mfa/p1_strong_authentication_start.html), [PingOne data residency](https://docs.pingidentity.com/pingoneaic/tenants/single-page.html)
4. `Keycloak` si la prioridad es control operativo y despliegue propio. Es viable para federación SAML/OIDC, pero exige más trabajo de plataforma. [Keycloak server admin guide](https://www.keycloak.org/docs/latest/server_admin/)
5. `Auth0` solo lo pondría arriba si Barna Health está construyendo un portal externo de pacientes o partners, no como primera elección para SSO corporativo puro. [Auth0 SSO](https://auth0.com/docs/authenticate/single-sign-on), [Auth0 SAML](https://auth0.com/docs/saml-configuration), [Auth0 inbound SCIM](https://auth0.com/docs/authenticate/protocols/scim/configure-inbound-scim), [Auth0 healthcare](https://auth0.com/es/healthcare)

**Conclusión**
- Para el caso más probable de Barna Health, empezaría con `Microsoft Entra ID`.
- Si el stack es muy heterogéneo o el gobierno de identidades es la prioridad, probaría `Okta`.
- Si me dices qué usan hoy en correo, directorio, ERP y apps clínicas, te puedo dejar una recomendación cerrada con un shortlist de 2 proveedores y los requisitos de integración exactos.
