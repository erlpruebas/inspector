Voy a revisar primero el contexto local y el `web_context.md` para extraer la necesidad técnica y el momento del contacto, y luego contrastarlo con opciones actuales de SSO en la web para Barna Health.

Ya tengo el dato local clave: Barna Health tiene una reunión técnica presencial el 18 de mayo de 2026 con IT para revisar integración con SSO. Ahora contrasto eso con proveedores actuales y documentación oficial para limitar la recomendación a opciones viables de verdad.

Estoy localizando las líneas exactas del correo y del CSV para poder citar el contacto y la necesidad técnica con precisión, no solo por nombre. Después cierro la recomendación con una comparación corta y accionable.

`rg` no está disponible en este entorno, así que saco las referencias con `Select-String` para mantener las citas exactas en los archivos locales.

Lo que sugieren los datos locales es claro: Xavier Puig, del área de IT de Barna Health, confirmó una reunión presencial en Barcelona el **18 de mayo de 2026 a las 10:00** para revisar la **integración con SSO**. En el CSV también figura como contacto de prioridad alta. Ver [emails_hilos.md](/D:/inspector/benchmarks/results/20260513_185318_064815/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/emails_hilos.md#L31) y [contactos_50.csv](/D:/inspector/benchmarks/results/20260513_185318_064815/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/contactos_50.csv#L39).

Mi lectura técnica, como inferencia a partir de ese contexto, es que Barna Health necesita un IdP de empresa con:
- `SAML` para apps legacy/enterprise
- `OIDC` para apps modernas
- `SCIM` para altas/bajas automáticas
- `MFA`, logs y controles de acceso para un entorno sanitario

**Opciones actuales recomendables**

- **Microsoft Entra ID**
  - Mejor opción si Barna Health ya vive en Microsoft 365, Windows o AD.
  - Soporta SSO con `SAML` y `OIDC`, y también `SCIM` para provisión de usuarios y grupos.
  - Microsoft publica guía específica de controles `HIPAA` para Entra, útil como base de seguridad en salud.
  - Fuentes: [SAML en Entra](https://learn.microsoft.com/en-us/entra/architecture/auth-saml), [OIDC SSO en Entra](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/add-application-portal-setup-oidc-sso), [SCIM en Entra](https://learn.microsoft.com/en-us/entra/identity/app-provisioning/scim-support-in-entra-id), [controles HIPAA](https://learn.microsoft.com/en-us/entra/standards/hipaa-access-controls).

- **Okta Workforce Identity**
  - Muy buena opción si quieren rapidez de despliegue y un catálogo amplio de integraciones.
  - Okta posiciona explícitamente su oferta para salud y habla de una `HIPAA-compliant Identity cloud`.
  - También destaca integraciones con `Epic`, `Cerner` y `AthenaHealth`, lo que la hace interesante si Barna Health tiene ecosistema clínico heterogéneo.
  - Fuentes: [Okta Healthcare](https://www.okta.com/industries/healthcare/).

- **PingOne**
  - Buena alternativa si la prioridad es federación, aprovisionamiento y auditoría más finos.
  - Su SSO usa `SAML`, `OAuth` y `OIDC`.
  - La provisión `SCIM` soporta `1.1` y `2.0`, con creación, actualización, desactivación y borrado.
  - Tiene auditoría de eventos con retención de 90 días para eventos de usuario y 2 años para eventos de configuración.
  - Fuentes: [PingOne SSO](https://docs.pingidentity.com/pingone/getting_started_with_pingone/p1_p1sso_start.html), [SCIM en PingOne](https://docs.pingidentity.com/pingone/integrations/p1_create_scim_connection.html), [Audit en PingOne](https://docs.pingidentity.com/pingone/monitoring/p1_reporting.html).

- **Keycloak**
  - Solo lo pondría como opción si Barna Health quiere `self-hosting` o control total de infraestructura.
  - Soporta `OIDC` y `SAML`, pero su `SCIM` sigue siendo experimental en Keycloak `26.6` al `10 de abril de 2026`.
  - Para una decisión de producción cercana a la reunión del 18 de mayo, lo veo más como piloto técnico que como primera elección.
  - Fuentes: [Keycloak OIDC/SAML](https://www.keycloak.org/docs/latest/server_admin/index.html), [SCIM experimental en Keycloak](https://www.keycloak.org/2026/04/scim-as-experimental-feature).

**Recomendación práctica para Barna Health**
1. Si ya tienen Microsoft 365 / AD / Windows, iría primero con **Microsoft Entra ID**.
2. Si quieren más neutralidad, mejor catálogo e integración más rápida con apps sanitarias, elegiría **Okta**.
3. Si el requisito fuerte es soberanía/autohosting, evaluaría **Keycloak**, pero no como camino principal si necesitan SCIM maduro ya.
4. Si necesitan mucha federación con sistemas externos y buen control de logs, **PingOne** es el tercero a comparar.

**Qué llevaría a la reunión del 18 de mayo**
- Mapa de apps que necesitan acceso con SSO.
- Confirmación de si el IdP actual es Microsoft, Google, Okta o ninguno.
- Requisito de aprovisionamiento `SCIM` sí/no.
- Requisito de `MFA` y políticas condicionales.
- Requisito de auditoría y retención de logs.
- Restricciones de residencia de datos / `GDPR` si operan en UE. Esto último lo tomo como inferencia razonable por Barcelona y el sector salud.

Si quieres, te preparo una comparativa en formato tabla con “fit / riesgo / coste / esfuerzo de implantación” para enviar directamente a Xavier.
