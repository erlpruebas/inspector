# Investigación de Proveedores de SSO para Barna Health

## 1. Contexto para Barna Health

*   **Contacto:** Xavier Puig (xavier.puig@barnahealth.es, +34 600 100 038) - Rol: IT
*   **Fecha de Contexto:** 7 de mayo de 2026 (referencia a reunión técnica el 18 de mayo de 2026).
*   **Necesidad Técnica:** Barna Health está revisando la integración con soluciones de Inicio de Sesión Único (SSO).

## 2. Opciones de Proveedores de SSO

A continuación, se presentan opciones de proveedores de SSO, considerando tanto soluciones comerciales como de código abierto, según la información disponible en las fuentes consultadas.

### 2.1. Soluciones Comerciales/Empresariales

*   **EMÚ, OneIdP, Veltar:** Mencionados como proveedores de soluciones de SSO en 2026. (Fuente 1: blog.scalefusion.com, consultado el 21 de mayo de 2026)
    *   *Nota:* La Fuente 1 también destaca la integración de SSO con la gestión de dispositivos móviles (MDM), lo cual podría ser un factor a considerar si Barna Health gestiona dispositivos corporativos o BYOD.

### 2.2. Soluciones de Código Abierto (OSS) para Gestión de Identidad y Acceso (IAM) / SSO

Estas opciones pueden ofrecer flexibilidad y control, siendo una buena alternativa si Barna Health prefiere soluciones auto-gestionadas o con requisitos de personalización específicos.

*   **Logto:** Un proveedor de IAM de código abierto que facilita la integración de autenticación de usuarios. (Fuente 2: blog.logto.io, consultado el 21 de mayo de 2026)
*   **Keycloak:** Reconocido por sus características, protocolos e integraciones en el ámbito de IAM de código abierto. (Fuente 2: blog.logto.io, consultado el 21 de mayo de 2026)
*   **NextAuth:** Mencionado en el contexto de proveedores de IAM de código abierto. (Fuente 2: blog.logto.io, consultado el 21 de mayo de 2026)
*   **Casdoor:** Otro proveedor de IAM de código abierto. (Fuente 2: blog.logto.io, consultado el 21 de mayo de 2026)
*   **SuperTokens:** También listado entre los principales proveedores de IAM de código abierto. (Fuente 2: blog.logto.io, consultado el 21 de mayo de 2026)

*   *Nota:* Los proveedores de IAM (Identity and Access Management) de código abierto generalmente cubren cuatro pilares: Autenticación, Autorización, Gestión de usuarios y Gestión de organizaciones. (Fuente 2: blog.logto.io)

## 3. Factores a Considerar al Elegir un Proveedor de SSO

Al evaluar las opciones, Barna Health debería considerar los siguientes factores:

*   **Beneficios de SSO:** Productividad mejorada y mejor experiencia de usuario al eliminar la necesidad de recordar múltiples credenciales. (Fuente 3: guru99.com)
*   **Tipos de SSO:** Evaluar qué tipos de SSO se adaptan mejor a la infraestructura y aplicaciones de Barna Health. (Fuente 4: linkedin.com)
*   **Características de SSO:** Analizar las funcionalidades específicas que cada proveedor ofrece, como soporte para diferentes protocolos (SAML, OAuth, OIDC), integraciones con directorios de usuarios existentes (LDAP, Active Directory), y capacidades de multi-factor authentication (MFA). (Fuente 4: linkedin.com)
*   **Costos de SSO:** Considerar el modelo de precios, incluyendo licencias, soporte, implementación y mantenimiento. Para soluciones OSS, se deben evaluar los costos asociados a la implementación y el soporte interno o de terceros. (Fuente 4: linkedin.com)
*   **Requisitos de Seguridad y Cumplimiento:** Asegurarse de que el proveedor cumpla con las normativas y estándares de seguridad relevantes para el sector sanitario, como SOC 2 y GDPR. (Fuente 2: blog.logto.io)
*   **Gestión de Usuarios y Organizaciones:** La capacidad de administrar usuarios, roles y auditorías de forma eficiente, así como la estructuración de equipos y permisos si es aplicable a un entorno multi-tenencia. (Fuente 2: blog.logto.io)
