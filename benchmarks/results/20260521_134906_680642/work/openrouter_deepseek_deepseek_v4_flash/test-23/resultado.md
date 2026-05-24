# Investigación de Proveedores de SSO para Barna Health

**Fecha del informe:** 2026-05-08  
**Contexto consultado:** Web, correos internos y base de contactos de Barna Health.

---

## 1. Contexto de Barna Health

Según el registro de contactos, Xavier Puig (xavier.puig@barnahealth.es) es el responsable de IT en Barna Health, con alta prioridad como cliente. En el hilo E-004 se confirma una reunión presencial en Barcelona el **18 de mayo de 2026 a las 10:00** para revisar la integración con SSO. Esto indica que Barna Health está evaluando activamente proveedores de inicio de sesión único y necesita una solución que se adapte al sector sanitario.

---

## 2. Opciones de Proveedores de SSO (2025-2026)

Basado en las fuentes consultadas, se identifican los siguientes proveedores relevantes:

### 2.1. Escalables y comerciales (recomendados para el sector salud)

| Proveedor | Descripción | Ideal para |
|-----------|-------------|------------|
| **Okta** | Plataforma líder de identidad en la nube con amplia integración de aplicaciones. Ofrece SSO, MFA y gestión de ciclo de vida. | Empresas que necesitan cumplir con normativas sanitarias (HIPAA, GDPR). |
| **Microsoft Azure AD** | Integración nativa con Office 365 y entornos híbridos. SSO basado en SAML/OIDC. | Organizaciones que ya usan ecosistema Microsoft. |
| **OneLogin** (One Identity) | SSO con políticas de acceso contextual y directorios de aplicaciones preintegradas. | Empresas que buscan despliegue rápido y bajo coste total. |
| **Ping Identity** | Plataforma de identidad inteligente con orquestación de políticas. | Entornos con múltiples identidades federadas. |

*Fuente: [Scalefusion - Los 10 mejores proveedores SSO 2026]*, que menciona el sector sanitario como industria atendida.

### 2.2. Código abierto (opciones autogestionadas)

| Proveedor | Descripción | Ideal para |
|-----------|-------------|------------|
| **Keycloak** | Proyecto Red Hat, soporta SAML, OIDC, LDAP, MFA. Amplia comunidad y personalización. | Equipos con capacidad técnica para autogestionar infraestructura. |
| **Logto** | IAM open source moderno, fácil integración, multi-tenencia, auditoría. | Startups o empresas que buscan agilidad en desarrollo. |
| **Casdoor** | Basado en Go, con interfaz web y RBAC. Compatible con OAuth 2.0, SAML y CAS. | Aplicaciones que requieren autenticación social y empresarial. |
| **SuperTokens** | SDK para autenticación, fácil de integrar en aplicaciones web/móviles. | Proyectos que priorizan experiencia de desarrollador. |

*Fuente: [Logto Blog - Top 5 OSS IAM providers 2025]*. El artículo compara características, protocolos y ventajas/desventajas, destacando que Keycloak es el más maduro y Logto el más moderno.

### 2.3. Otras soluciones destacadas (Guru99 2026)

El ranking de Guru99 incluye proveedores como **JumpCloud**, **Rippling** y **SecureAuth**, aunque no se analizan en detalle en el contexto extraído. Se recomienda revisar la lista completa para evaluar costes y funcionalidades adicionales.

---

## 3. Criterios de Selección (basados en LinkedIn)

La fuente de LinkedIn [Cómo elegir el mejor proveedor de SSO] sugiere considerar:

1. **Beneficios de SSO** – mejora de productividad, reducción de contraseñas.
2. **Tipos de SSO** – SAML, OIDC, federación (determinar cuáles soporta la aplicación objetivo).
3. **Características** – MFA, políticas de acceso basadas en riesgo, aprovisionamiento SCIM, cumplimiento normativo.
4. **Costos** – licencias por usuario, costes de implantación y mantenimiento (mayor en on-premise con open source).

Aplicando a Barna Health en el sector sanitario, se deben priorizar:

- Cumplimiento con **GDPR** y **HIPAA** (si trabaja con datos de
