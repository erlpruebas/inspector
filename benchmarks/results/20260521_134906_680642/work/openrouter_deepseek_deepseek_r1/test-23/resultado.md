# Investigación de Proveedor SSO para Barna Health

**Fecha de investigación:** 14 de mayo de 2026
**Próxima reunión con el cliente:** 18 de mayo de 2026, 10:00 (presencial en Barcelona)
**Contacto principal en Barna Health:** Xavier Puig (xavier.puig@barnahealth.es), Departamento de IT. Prioridad: Alta.

## 1. Necesidad y Contexto
Según el historial de correos (Hilo E-004), Barna Health ha solicitado una reunión técnica para el 18 de mayo con el objetivo de revisar la integración con un sistema de Inicio de Sesión Único (SSO). Esto indica una necesidad activa de implementar o mejorar su infraestructura de gestión de identidades y accesos, probablemente para centralizar el acceso a múltiples aplicaciones internas o para socios, mejorando la seguridad y la experiencia del usuario.

## 2. Opciones de Proveedores y Soluciones SSO (Basado en Investigación Web 2026)
A continuación, se presentan las opciones identificadas a partir de fuentes de referencia del sector.

### 2.1. Principales Proveedores Comerciales y de Código Abierto
Basado en las listas de los mejores proveedores para 2025-2026 (Fuentes 1, 2 y 3).

| Proveedor/Solución | Tipo | Características Clave Notables (según fuentes) | Notas / Enfoque |
| :--- | :--- | :--- | :--- |
| **Scalefusion** | Comercial | Solución de gestión de dispositivos móviles (MDM/UEM) que incluye capacidades SSO. Mencionado para el sector sanitario. | Fuente 1 lo lista como un proveedor top en 2026. Podría ser adecuado si Barna Health también necesita gestión de dispositivos. |
| **Logto** | Código Abierto (OSS) | Proveedor de IAM (Gestión de Identidad y Acceso) moderno. Enfocado en autenticación, autorización, gestión de usuarios y organizaciones. | Fuente 2 lo destaca como uno de los 5 principales proveedores IAM OSS en 2025. Buen control y personalización. |
| **Keycloak** | Código Abierto (OSS) | Solución IAM ampliamente adoptada, con soporte para protocolos estándar (OpenID Connect, SAML). Alta flexibilidad. | Mencionado en la Fuente 2 como una opción OSS líder. Requiere recursos técnicos para implementación y mantenimiento. |
| **NextAuth.js / Auth.js** | Código Abierto (OSS) | Conjunto de herramientas para autenticación en aplicaciones web, especialmente ecosistema JavaScript/Next.js. | Listado en la Fuente 2. Ideal si el stack tecnológico de Barna Health está basado
