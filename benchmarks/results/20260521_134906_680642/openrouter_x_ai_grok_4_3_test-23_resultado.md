# Investigación de Proveedores de SSO para Barna Health

**Fecha del informe:** 2026-05-09  
**Contacto principal:** Xavier Puig (IT, Barna Health, Barcelona) – xavier.puig@barnahealth.es  
**Contexto técnico:** Reunión presencial confirmada para el 18 de mayo de 2026 a las 10:00 en Barcelona para revisar integración con SSO (ver hilo E-004 en emails_hilos.md). Prioridad alta según contactos_50.csv.

## Necesidad técnica identificada
Barna Health requiere una solución SSO que facilite la integración con sistemas sanitarios existentes, garantice cumplimiento normativo (GDPR, sector salud) y soporte autenticación segura para personal clínico y administrativo. La reunión del 18 de mayo se centrará en protocolos SAML/OIDC y aprovisionamiento de usuarios.

## Opciones de proveedores SSO recomendadas (2026)
Basado en fuentes web actualizadas:

1. **Keycloak (código abierto)**  
   - Fuente: https://blog.logto.io/es/top-oss-iam-providers-2025 (consultado mayo 2026)  
   - Ventajas: Soporte completo de SAML, OIDC, OAuth2; integración fácil con entornos sanitarios; gratuito y altamente personalizable.  
   - Adecuado para Barna Health por su flexibilidad en multi-tenencia y auditoría.

2. **Logto**  
   - Fuente: https://blog.logto.io/es/top-oss-iam-providers-2025  
   - Ventajas: Enfoque moderno en IAM, soporte para identidades sociales y MFA; ideal para startups y clínicas en crecimiento.  
   - Recomendado para pruebas rápidas antes de la reunión del 18 de mayo.

3. **EMÚ OneIdP (Scalefusion)**  
   - Fuente: https://blog.scalefusion.com/es/las-mejores-soluciones-sso/  
   - Ventajas: Integración MDM-SSO, gestión de dispositivos en sector salud; fuerte en cumplimiento y seguridad.  
   - Precios orientados a empresas con necesidades BYOD.

4. **Soluciones de Guru99 (incluye Okta, Auth0, OneLogin)**  
   - Fuente: https://www.guru99.com/es/best-single-sign-on-sso-solution-providers.html  
   - Ventajas: Alta escalabilidad, soporte enterprise y SSO para aplicaciones sanitarias.  
   - Considerar para entornos con alto volumen de usuarios.

## Recomendación inicial
Preparar demo de Keycloak o Logto para la reunión del 18 de mayo, enfocada en integración con sistemas existentes de Barna Health. Contactar a Xavier Puig para confirmar agenda técnica.

**Fuentes consultadas:** web_context.md (Fuente 1-4, mayo 2026).
