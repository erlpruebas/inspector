# Investigación de proveedores de SSO para Barna Health

**Fecha de investigación:** Mayo 2026

**Contexto local:**
- **Contacto clave:** Xavier Puig (xavier.puig@barnahealth.es), responsable de IT en Barna Health, Barcelona.
- **Necesidad técnica confirmada:** Reunión presencial programada para el 18 de mayo de 2026 a las 10:00 en Barcelona para revisar la integración con SSO (Hilo E-004).
- **Perfil de la empresa:** Barna Health es un cliente con prioridad "alta" según el registro de contactos.

**Opciones de proveedores de SSO (basado en investigación web):**

1.  **Scalefusion (OneIdP)** - Fuente: "Los 10 mejores proveedores y soluciones de SSO en 2026" (blog.scalefusion.com, consulta mayo 2026). Se presenta como una solución que mejora la postura de seguridad y el acceso de los usuarios. Su material menciona experiencia en el sector sanitario.

2.  **Proveedores listados por Guru99** - Fuente: "Las 10 mejores soluciones y proveedores de SSO (2026)" (guru99.com, consulta mayo 2026). El artículo destaca que el SSO permite a los usuarios acceder a diferentes aplicaciones con un solo conjunto de credenciales, mejorando la productividad y la experiencia de usuario.

3.  **Proveedores IAM de código abierto** - Fuente: "Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto 2025" (blog.logto.io, consulta mayo 2026). Incluye opciones como Logto, Keycloak, NextAuth, Casdoor y SuperTokens. Estas soluciones ofrecen autenticación, autorización, gestión de usuarios y organizaciones, siendo esenciales para políticas de seguridad y cumplimiento normativo (ej. GDPR).

**Factores a considerar para la selección (según mejores prácticas):**
- **Compatibilidad:** Con las aplicaciones y sistemas actuales de Barna Health.
- **Protocolos soportados:** SAML, OAuth 2.0, OpenID Connect.
- **Experiencia de usuario:** Simplicidad en el inicio de sesión.
- **Seguridad y cumplimiento:** MFA, auditorías, cumplimiento de normativas relevantes para el sector salud.
- **Costos:** Modelo de licencia (por usuario, anual) y costos de implementación/soporte.
- **Soporte e integración:** Calidad del soporte técnico y facilidad de integración.

**Recomendación de acción para la reunión del 18 de mayo:**
Preparar una comparativa detallada de 2-3 proveedores (ej., una solución empresarial como Scalefusion/OneIdP, una opción de código abierto como Keycloak o Logto, y otro proveedor comercial destacado), evaluándolos frente a los factores anteriores y al contexto específico de Barna Health. Se sugiere solicitar a Xavier Puig detalles sobre el stack tecnológico actual, el número de usuarios y aplicaciones a integrar, y cualquier requisito de cumplimiento específico.
