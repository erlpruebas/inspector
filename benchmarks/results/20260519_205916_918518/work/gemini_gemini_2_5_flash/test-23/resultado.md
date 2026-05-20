# Investigación de Proveedores de SSO para Barna Health

## Contexto del Cliente

Según el archivo `emails_hilos.md`, Barna Health tiene una necesidad explícita de integración con SSO. Se programó una reunión técnica en Barcelona para el 18 de mayo a las 10:00 AM para revisar este tema.

El contacto principal en Barna Health para esta iniciativa es:
*   **Nombre:** PERSON_0024
*   **Email:** EMAIL_0018
*   **Empresa:** Barna Health
*   **Ciudad:** Barcelona
*   **Rol:** IT
*   **Prioridad:** Alta

Esta información fue extraída de `assistant_synthetic/contactos_50.csv` y `assistant_synthetic/emails_hilos.md`.

## Necesidades Técnicas y Sectoriales

Barna Health opera en el sector de la salud, lo que implica requisitos de seguridad y cumplimiento normativo potencialmente estrictos. La integración de SSO es crucial para mejorar la seguridad y la experiencia del usuario, permitiendo el acceso a múltiples aplicaciones con un único conjunto de credenciales.

## Opciones de Proveedores de SSO

Basado en el contexto web (`web_context.md`), se identifican las siguientes opciones que podrían ser adecuadas para Barna Health, considerando su sector y necesidad técnica:

### 1. Scalefusion (Fuente 1)
*   **Relevancia para Barna Health:** Scalefusion menciona explícitamente el "Sector Sanitario" como una de las industrias a las que sirve. Su integración de SSO con MDM (Mobile Device Management) se destaca por mejorar la postura de seguridad y el acceso de los usuarios, lo cual es fundamental en un entorno de salud.
*   **Soluciones mencionadas:** EMÚ OneIdP Veltar.
*   **Fecha de consulta de la fuente:** 19 de Mayo de 2026.

### 2. Keycloak (Fuente 2)
*   **Relevancia para Barna Health:** Keycloak es un proveedor de Gestión de Identidad y Acceso (IAM) de código abierto. Ofrece alta flexibilidad y personalización, lo que puede ser ventajoso para cumplir con requisitos específicos de seguridad y cumplimiento en el sector sanitario. Proporciona pilares clave como autenticación, autorización, gestión de usuarios y gestión de organizaciones.
*   **Tipo:** Código abierto.
*   **Fecha de consulta de la fuente:** 3 de Diciembre de 2025.

### 3. Logto (Fuente 2)
*   **Relevancia para Barna Health:** Similar a Keycloak, Logto es otro proveedor de IAM de código abierto. Permite una integración rápida de la autenticación de usuarios, lo que podría acelerar la implementación de SSO en Barna Health, manteniendo la seguridad y el control.
*   **Tipo:** Código abierto.
*   **Fecha de consulta de la fuente:** 3 de Diciembre de 2025.

## Factores a Considerar en la Elección (Fuente 4)

Al seleccionar el proveedor de SSO, Barna Health deberá evaluar los siguientes factores, tal como se sugiere en el artículo de LinkedIn sobre cómo elegir el mejor proveedor de SSO:
*   **Beneficios del SSO:** Evaluar cómo cada solución mejora la productividad y la experiencia del usuario.
*   **Tipos de SSO:** Considerar los protocolos y estándares que soporta cada proveedor (ej. SAML, OAuth, OIDC).
*   **Características del SSO:** Analizar las funcionalidades específicas ofrecidas, como soporte para múltiples factores de autenticación (MFA), aprovisionamiento de usuarios, auditoría, y gestión de políticas.
*   **Costos del SSO:** Comparar los modelos de precios, incluyendo licencias, implementación, mantenimiento y soporte.

## Próximos Pasos

Se recomienda a Barna Health profundizar en las características específicas, las capacidades de integración con sus sistemas existentes y los modelos de costos de Scalefusion, Keycloak y Logto. Dada la "alta" prioridad y el rol de "IT" del contacto, es esencial una evaluación técnica detallada.
