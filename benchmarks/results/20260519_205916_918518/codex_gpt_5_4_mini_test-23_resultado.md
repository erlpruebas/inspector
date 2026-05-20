Voy a leer primero el contexto local y el `web_context.md` para extraer la necesidad técnica y el momento de contacto, y después contrastaré opciones actuales de SSO con fuentes oficiales para aterrizar una recomendación concreta.

Ya tengo el contexto local: el contacto relevante es `PERSON_0024` en IT, Barcelona, prioridad alta, y el hilo marca una reunión técnica presencial sobre SSO para el `18 de mayo de 2026` a las `10:00`. Ahora voy a contrastar proveedores actuales con documentación oficial para no recomendar nada desactualizado.

Ya tengo los candidatos técnicos. Voy a sacar ahora las líneas exactas del hilo y del CSV para referenciar el contacto, la fecha y la prioridad, y luego cierro con una recomendación basada en fuentes oficiales actuales.

**Conclusión**
Mi recomendación base para Barna Health es **Microsoft Entra ID** si el entorno ya es Microsoft 365/AD o tiene bastante carga híbrida. Si el stack es más heterogéneo y priorizan catálogo amplio de integraciones y rapidez de despliegue, la segunda opción sería **Okta Workforce Identity**. **PingOne SSO** queda como tercera opción sólida para federación estándar y entornos híbridos complejos.

**Contexto usado**
- El hilo interno marca una reunión técnica presencial en Barcelona el **18 de mayo de 2026 a las 10:00** para revisar integración con SSO; hoy es **20 de mayo de 2026**, así que ese hito ya pasó, pero sigue siendo el punto de partida operativo. Ver [`emails_hilos.md`](D:/inspector/benchmarks/results/20260519_205916_918518/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/emails_hilos.md#L35).
- El contacto relevante es `PERSON_0024`, en **IT**, **Barcelona**, prioridad **alta**. Ver [`contactos_50.csv`](D:/inspector/benchmarks/results/20260519_205916_918518/work/codex_gpt_5_4_mini/test-23/assistant_synthetic/contactos_50.csv#L39).
- El contexto web de Banner Health indica acceso remoto a **Banner Email, Workforce Center, VPN, Benefits y Workday** desde Internet pública, lo que apunta a un caso de SSO de plantilla, no solo de app aislada. Ver [`web_context.md`](D:/inspector/benchmarks/results/20260519_205916_918518/work/codex_gpt_5_4_mini/test-23/web_context.md#L10).

**Comparativa rápida**
| Proveedor | Encaje para Barna Health | Puntos fuertes | Riesgo / límite |
|---|---|---|---|
| Microsoft Entra ID | Muy bueno si ya usan Microsoft 365, AD o Windows híbrido | SSO para cloud y on-prem, Seamless SSO, soporte SAML/OIDC/OAuth, Application Proxy, SSO gratis para apps enterprise preintegradas | Depende mucho de cómo esté licenciado y de si el stack ya es Microsoft |
| Okta Workforce Identity | Muy bueno si el portfolio de apps es mixto y quieren rapidez de integración | Plataforma de workforce identity, SSO + MFA + Access Gateway, página de salud con foco en healthcare y acceso para clinicians/empleados/partners/contratistas | Suele tener más coste y conviene validar TCO frente a la pila actual |
| PingOne SSO | Bueno para federación estándar y entornos complejos | SAML, OAuth y OIDC, acceso one-click, buen ajuste para integraciones híbridas y estándares | Menos evidencia pública de “fit” healthcare específico en comparación con Okta/Entra |

**Recomendación**
- **Primera apuesta: Microsoft Entra ID.** Esta es una inferencia razonable, no un dato confirmado en los archivos. La hago porque el contexto local habla de acceso a correo, Workday y VPN desde fuera, y Microsoft documenta soporte para apps cloud, apps on-prem y Seamless SSO sin componentes extra on-prem en muchos escenarios.
- **Segunda apuesta: Okta Workforce Identity** si el inventario de aplicaciones es muy diverso, hay mucho SaaS externo y quieren acelerar integraciones con una plataforma neutral.
- **Tercera apuesta: PingOne SSO** si el equipo valora mucho los estándares y la federación entre sistemas heterogéneos, especialmente en escenarios híbridos.

**Qué validaría en la próxima reunión**
- Si el directorio maestro es **Microsoft Entra / AD**, **Okta** o **Ping**.
- Qué aplicaciones entran en el alcance inicial: **email, Workday, VPN, intranet, beneficios**.
- Qué protocolos soportan esas apps: **SAML, OIDC, OAuth, SCIM**.
- Si necesitan **Conditional Access**, MFA resistente a phishing y políticas por dispositivo.
- Si hay apps on-prem que requieran **Application Proxy** o un gateway similar.
- Requisitos de auditoría y compliance para entorno sanitario.

**Fuentes oficiales usadas**
- Microsoft Entra, plan de despliegue de SSO: https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/plan-sso-deployment
- Microsoft Entra Seamless SSO: https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-sso
- Okta Workforce Identity: https://www.okta.com/products/workforce-identity/
- Okta Healthcare: https://www.okta.com/industries/healthcare/
- PingOne SSO: https://docs.pingidentity.com/pingone/getting_started_with_pingone/p1_p1sso_start.html
- Banner Health employees: https://www.bannerhealth.com/employees
