# Investigación de proveedores de SSO para Barna Health

**Fecha de investigación:** 2026-05-08  
**Contacto en Barna Health:** Xavier Puig (xavier.puig@barnahealth.es, +34 600 100 038), rol IT, prioridad alta  
**Próxima reunión técnica:** 18 de mayo de 2026, 10:00, Barcelona (confirmada en hilo E-004)

## Contexto técnico y necesidad

Barna Health requiere una solución de inicio de sesión único (SSO) para integrar sus sistemas de gestión sanitaria, facilitar el acceso seguro a aplicaciones internas y externas, y mejorar la experiencia de usuarios (personal clínico, administrativo y partners). La integración con SSO es crítica para la seguridad y el cumplimiento normativo en el sector salud.

## Criterios de selección aplicables

Basados en el artículo de LinkedIn «Cómo elegir el mejor proveedor de SSO para su organización» (Fuente 4), se consideran:
- **Beneficios**: reducción de costes de soporte, mejora de productividad, seguridad centralizada.
- **Tipos de SSO**: federado (SAML, OIDC) vs. basado en contraseñas.
- **Características**: autenticación multifactor (MFA), soporte de protocolos estándar, escalabilidad, integración con aplicaciones sanitarias (EHR, facturación, etc.).
- **Costes**: licencias por usuario, modelo SaaS vs. on-premise.

## Principales proveedores identificados

De las fuentes consultadas, se destacan los siguientes:

### 1. Scalefusion (OneIdP) – Fuente 1
- Solución completa de gestión de dispositivos y SSO.
- Adecuada para entornos sanitarios con gestión de endpoints.
- Integración con MDM, ideal para clínicas con dispositivos móviles.
- Precios no detallados, pero ofrece demo.

### 2. Keycloak (Open Source IAM) – Fuente 2
- Proveedor de código abierto líder en gestión de identidad y acceso.
- Amplia adopción en el sector salud por su flexibilidad y cumplimiento con SOC 2, GDPR.
- Protocolos: SAML, OIDC, OAuth 2.0.
- Ventajas: sin coste de licencia, personalizable, comunidad activa.
- Desventajas: requiere recursos internos para implementación y mantenimiento.

### 3. Logto (Open Source) – Fuente 2
- Solución moderna con autenticación y gestión de usuarios.
- Ideal para startups y empresas que buscan rápida integración.
- Soporte para SSO social y empresarial, MFA.
- Ofrece versión cloud y self-hosted.

### 4. Proveedores listados en Guru99 (Fuente 3)
- Incluye soluciones como Okta, Microsoft Azure AD, OneLogin, Ping Identity, etc.
- Empresas consolidadas con amplia experiencia en el sector salud.
- Okta: altamente recomendado para cumplimiento HIPAA.
- Azure AD: integración nativa con Microsoft 365, común en hospitales.

## Recomendación inicial para Barna Health

Dadas las características del sector salud (seguridad, cumplimiento normativo, escalabilidad) y la disponibilidad de recursos técnicos (Xavier Puig lidera IT), se sugiere evaluar:

1. **Okta** – Para cumplimiento estricto y soporte sanitario.
2. **Keycloak** – Si se prefiere código abierto y personalización.
3. **Azure AD** – Si Barna Health ya usa Microsoft 365 u otras herramientas de Microsoft.

Se recomienda preparar una comparativa de costes (licencias por usuario vs. auto-gestionado) y una prueba de concepto (PoC) para la reunión del 18 de mayo.

## Próximos pasos

- Solicitar demo a Scalefusion (mencionado en Fuente 1) y a Okta.
- Analizar requisitos específicos de integración (aplicaciones actuales, número de usuarios, cumplimiento RGPD/LOPD).
- Preparar cuestionario técnico para Keycloak y Logto.
- Incluir en la agenda de la reunión con Xavier Puig.
