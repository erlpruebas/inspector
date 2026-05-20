Voy a leer primero el contexto local y el `web_context.md` para entender la necesidad técnica y a quién va dirigido, y luego contrastaré opciones actuales de SSO con fuentes oficiales.

Ya tengo el contexto local: el contacto clave es Xavier Puig, de IT en Barna Health, y la reunión para revisar la integración SSO está fijada para el 18 de mayo de 2026. Ahora voy a verificar opciones vigentes en documentación oficial de proveedores para contrastarlas con ese escenario.

Ya tengo suficientes candidatos para comparar. Voy a extraer las referencias locales exactas de Barna Health para poder anclar la recomendación a la reunión, el rol de Xavier y la necesidad de integración.

A fecha de hoy, 13 de mayo de 2026, yo enfocaría la evaluación de Barna Health como un proyecto de SSO de **workforce / partners**: en el hilo local, Xavier Puig (IT) confirma una reunión técnica en Barcelona para el **18 de mayo de 2026 a las 10:00** y explícitamente dice que revisarán la **integración con SSO**. En el CSV, Xavier figura como **IT**, **cliente** y **prioridad alta**.  
Fuentes locales: [emails_hilos.md](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/emails_hilos.md#L31), [contactos_50.csv](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/contactos_50.csv#L39)

**Mi shortlist para Barna Health**
| Opción | Encaje | Por qué la pondría arriba | Riesgo / límite |
|---|---|---|---|
| Microsoft Entra ID | Muy alto si ya usan Microsoft 365, Windows o Azure | SSO para apps con OIDC y SAML, aprovisionamiento SCIM, B2B/guest access y buena historia para entornos híbridos/on-prem | Menos atractivo si su stack es claramente Google o si quieren evitar dependencia Microsoft |
| Okta Workforce Identity | Muy alto si el parque de apps es heterogéneo | SAML/OIDC + SCIM muy maduros, buen catálogo de integraciones y lifecycle management fuerte | Suele ser más caro y su valor depende de cuántas apps SaaS quieran gobernar |
| Google Workspace SSO | Alto solo si Google ya es el directorio dominante | Soporta SAML y OIDC, con perfiles de SSO por grupos / OUs | OIDC está limitado en la práctica a Microsoft Entra ID como IdP; encaja peor como IdP corporativo “neutral” |
| Auth0 | Alto si el SSO es para un portal o producto propio | Muy fuerte en federación B2B, conexiones enterprise, SAML/OIDC y flujos de delegación de SSO | Es más CIAM / producto digital que IAM corporativo puro |
| Keycloak | Alto si quieren control total y autoalojamiento | OIDC + SAML, sin lock-in de SaaS, útil si el dato y la operación deben quedar bajo control propio | Más carga operativa: alta disponibilidad, upgrades, hardening, backups y soporte quedan del lado de Barna Health |

**Conclusión práctica**
- Si Barna Health busca un **IdP corporativo para empleados, clinicians y proveedores**, mi primera elección sería **Microsoft Entra ID**.
- Si tienen un entorno mixto con muchas SaaS y quieren la mejor capa de gobierno de identidades, **Okta** es la alternativa más sólida.
- Si el objetivo real es el **SSO de una aplicación propia** o un portal externo, entonces miraría antes **Auth0** o **Keycloak**.
- Solo pondría **Google Workspace** como primera opción si Google ya es su base de identidad y administración.

**Criterios técnicos que yo pediría en la reunión**
- Protocolos: `SAML 2.0` y `OIDC`
- Aprovisionamiento: `SCIM 2.0` para altas, bajas y cambios
- MFA y políticas condicionales
- Soporte para usuarios internos y externos
- Auditoría y trazabilidad
- Si hay requisitos regulatorios: residencia de datos / región UE y opciones de tenant

**Fuentes web consultadas**
- Microsoft Entra:
  - [Configure OIDC SSO for gallery and custom applications](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/add-application-portal-setup-oidc-sso)
  - [Enable SAML single sign-on for an enterprise application](https://learn.microsoft.com/en-us/azure/active-directory/manage-apps/add-application-portal-setup-sso)
  - [SCIM support in Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/identity/app-provisioning/scim-support-in-entra-id)
  - [Microsoft Entra External ID overview](https://learn.microsoft.com/en-us/entra/external-id/external-identities-overview)
- Okta:
  - [SCIM Protocol](https://developer.okta.com/docs/api/openapi/okta-scim/guides/)
  - [Build a SCIM provisioning integration overview](https://developer.okta.com/docs/guides/scim-provisioning-integration-overview/main/)
  - [Enable SAML or OIDC authentication for supported apps](https://help.okta.com/oie/en-us/content/topics/security/healthinsight/saml-authentication.htm)
- Google Workspace:
  - [About SSO](https://support.google.com/a/answer/60224?hl=en-EN)
  - [Setting up SSO](https://support.google.com/a/answer/12032922?hl=en)
  - [Technical overview of SAML-based SSO](https://support.google.com/a/answer/6262987?hl=en-419)
- Auth0:
  - [Enterprise Connections](https://auth0.com/docs/authenticate/enterprise-connections)
  - [Enterprise Identity Providers](https://auth0.com/docs/connections/enterprise)
  - [Self-Service Enterprise Configuration](https://auth0.com/docs/authenticate/enterprise-connections/self-service-enterprise-configuration)
- Keycloak:
  - [Documentation](https://www.keycloak.org/documentation)
  - [Planning for securing applications and services](https://www.keycloak.org/securing-apps/overview)
  - [Securing Applications and Services Guide](https://www.keycloak.org/docs/25.0.6/securing_apps/index.html)

Si quieres, puedo convertir esto en una **tabla comparativa de compra** con precio relativo, esfuerzo de implantación y recomendación final para enviar a Xavier.
