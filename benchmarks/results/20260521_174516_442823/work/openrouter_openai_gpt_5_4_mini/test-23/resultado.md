# resultado.md

## Investigación de proveedor SSO para Barna Health

### Contexto local relevante
- **Contacto técnico principal:** Xavier Puig, IT, Barna Health  
  - Email: `xavier.puig@barnahealth.es`
  - Teléfono: `+34 600 100 038`
  - Ciudad: Barcelona
  - Prioridad: alta
- **Necesidad técnica detectada en el historial:**  
  - **Fecha del correo:** 2026-05-07 18:22  
  - **Asunto:** Reunion tecnica  
  - **Contenido clave:** “Confirmo reunion presencial en Barcelona el 18 de mayo a las 10:00. Revisaremos integracion con SSO.”
- **Interpretación:** Barna Health ya tiene una reunión técnica agendada para revisar la integración de SSO, por lo que la necesidad es inmediata y centrada en compatibilidad de integración, seguridad y facilidad de despliegue.

### Recomendación principal
Para Barna Health, la opción más equilibrada suele ser **Microsoft Entra ID** si ya usan ecosistema Microsoft, o **Okta** si buscan una solución independiente y muy madura en integraciones SAML/OIDC.  
Si el objetivo es minimizar licencias y mantener más control técnico, **Keycloak** es la alternativa open source más sólida.

### Opciones actuales de SSO adecuadas

#### 1) Microsoft Entra ID
**Encaje probable:** muy alto si la organización usa Microsoft 365, Teams, Azure o dispositivos Windows.  
**Ventajas:**
- Integración nativa con muchas aplicaciones empresariales.
- Buen soporte de SAML, OAuth2 y OpenID Connect.
- MFA, acceso condicional y gobierno de identidades.
- Suele acelerar despliegues en entornos corporativos.

**Riesgos / limitaciones:**
- Mejor valor cuando ya existe una base Microsoft.
- Puede requerir trabajo adicional si hay aplicaciones legacy o híbridas.

**Cuándo elegirlo:** si Barna Health prioriza rapidez, gobierno centralizado y ya está en ecosistema Microsoft.

#### 2) Okta
**Encaje probable:** muy alto para una estrategia de SSO agnóstica de proveedor.  
**Ventajas:**
- Muy fuerte en SSO, MFA, lifecycle management e integraciones SaaS.
- Amplio catálogo de conectores.
- Buen soporte para organizaciones con múltiples aplicaciones clínicas, administrativas y de terceros.

**Riesgos / limitaciones:**
- Coste normalmente superior al de alternativas open source.
- Puede ser “demasiado” si el alcance inicial es pequeño.

**Cuándo elegirlo:** si Barna Health necesita máxima compatibilidad con terceros y una plataforma madura de IAM/SSO.

#### 3) Keycloak
**Encaje probable:** muy alto si la prioridad es control técnico y coste contenido.  
**Ventajas:**
- Open source, muy usado para SSO empresarial.
- Soporta SAML, OIDC y LDAP.
- Flexible para integraciones personalizadas.
- Adecuado si IT quiere controlar despliegue, branding y políticas.

**Riesgos / limitaciones:**
- Requiere más operación interna.
- La experiencia de administración y hardening depende del equipo técnico.
- Menos “out of the box” que soluciones comerciales premium.

**Cuándo elegirlo:** si Barna Health tiene equipo IT capaz de operar IAM y quiere reducir dependencia de licencias.

#### 4) Auth0
**Encaje probable:** alto si necesitan velocidad de implementación y foco en desarrollo.  
**Ventajas:**
- Muy buen soporte para desarrolladores.
- Buenas capacidades OIDC/OAuth2/SAML
