# Investigación de proveedores SSO para Barna Health

## Contexto Local y Necesidad Técnica
- **Contacto clave:** Xavier Puig (Departamento IT, Barna Health), Barcelona. Teléfono: +34 600 100 038.
- **Fecha de referencia:** Mayo 2026.
- **Necesidad técnica:** Según el hilo de correo E-004, se ha confirmado una reunión presencial para el 18 de mayo de 2026 a las 10:00 en Barcelona con el objetivo explícito de revisar la integración con SSO (Single Sign-On) en la infraestructura de Barna Health.

## Opciones de Proveedores SSO (Contexto de Mercado 2025-2026)
A partir del análisis de fuentes actualizadas, se presentan las soluciones más relevantes para un entorno corporativo/sanitario:

### 1. Plataformas Comerciales y Empresariales
- **Scalefusion / EMÚ OneIdP / Veltar:** Mencionados en los rankings de 2026 como soluciones líderes que integran SSO con gestión de dispositivos (MDM/UEM) y seguridad perimetral. Destacan por su soporte a sectores regulados como el sanitario y su capacidad de despliegue híbrido.
- **Guru99 (2026):** Recomienda evaluar proveedores con enfoque en experiencia de usuario, reducción de fricción en credenciales y compatibilidad con arquitecturas cloud-native.

### 2. Soluciones Open Source / IAM Moderno
- **Logto, Keycloak, NextAuth, Casdoor y SuperTokens:** Identificados en 2025 como los principales proveedores de código abierto para Gestión de Identidad y Acceso (IAM). Ofrecen control total sobre los datos, cumplimiento de GDPR/SOC 2 y protocolos estándar (OIDC, SAML, OAuth 2.0). Ideales si Barna Health prioriza la autosuficiencia técnica y la privacidad de datos de salud.

### 3. Criterios de Selección Recomendados
- **Protocolos y Estándares:** Soporte nativo para SAML 2.0 y OIDC para integración con ERPs, CRM y portales de pacientes.
- **Cumplimiento Normativo:** Certificaciones SOC 2, ISO 27001 y adaptación a RGPD/Ley de Protección de Datos sanitarios.
- **Experiencia de Usuario:** Reducción de fatiga de contraseñas, soporte para MFA adaptativo y acceso sin fricción en dispositivos corporativos y BYOD.
- **Costos y Escalabilidad:** Modelos de licenciamiento por usuario/activo, costes de implementación y mantenimiento, y capacidad de escalar sin degradar el rendimiento.

## Recomendación y Próximos Pasos
1. **Preparar la reunión del 18/05/2026:** Agendar con Xavier Puig una sesión técnica para mapear los sistemas actuales de Barna Health, requisitos de integración y políticas de acceso.
2. **Solicitar demos/POC:** Contactar a proveedores comerciales (Scalefusion/EMÚ) y evaluar entornos sandbox de Keycloak o Logto para pruebas de integración con SAML/OIDC.
3. **Validar cumplimiento:** Verificar certificaciones de seguridad y cláusulas de tratamiento de datos antes de la decisión final.

## Fuentes Consultadas
- Fuente 1: Scalefusion Blog. "Los 10 mejores proveedores y soluciones de SSO en 2026". 20 de mayo de 2026. https://blog.scalefusion.com/es/las-mejores-soluciones-sso/
- Fuente 2: Logto Blog. "Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto 2025". 12 de marzo de 2025. https://blog.logto.io/es/top-oss-iam-providers-2025
- Fuente 3: Guru99. "Las 10 mejores soluciones y proveedores de SSO (2026)". 2026. https://www.guru99.com/es/best-single-sign-on-sso-solution-providers.html
- Fuente 4: LinkedIn Advice. "Cómo elegir el mejor proveedor de SSO para su organización". 2025-2026. https://www.linkedin.com/advice/0/how-do-you-choose-best-sso-provider-your-organization?lang=es
