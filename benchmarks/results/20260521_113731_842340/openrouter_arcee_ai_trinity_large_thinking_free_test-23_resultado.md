# Investigación de Proveedores de SSO para Barna Health

## Contexto y Necesidades Técnicas

Basado en el análisis de archivos locales y fuentes web, Barna Health requiere una solución de **Single Sign-On (SSO)** robusta, segura y escalable, adaptada al sector salud. Los puntos clave son:

- **Fecha de reunión técnica**: 18 de mayo de 2026, 10:00, en Barcelona (presencial).
- **Contacto principal**: Xavier Puig (xavier.puig@barnahealth.es), IT, prioridad alta.
- **Necesidad explícita**: Revisar integración con SSO para sistemas internos y cumplimiento normativo.
- **Sector**: Salud (manejo de datos sensibles, cumplimiento HIPAA/GDPR).
- **Requisitos técnicos**: Autenticación centralizada, gestión de identidades, auditoría, y soporte para integración con aplicaciones médicas y de gestión.

---

## Análisis de Proveedores de SSO (2026)

### Criterios de Evaluación
- **Seguridad y Cumplimiento**: Soporte para MFA, cifrado, auditorías, certificaciones (SOC 2, HIPAA, GDPR).
- **Integraciones**: Conectores preconstruidos para aplicaciones cloud/on-premise, APIs REST.
- **Escalabilidad**: Soporte para crecimiento de usuarios y dispositivos.
- **Costo**: Modelo de precios transparente, adecuado para medianas empresas.
- **Soporte Técnico**: Disponibilidad, documentación, SLA.

### Proveedores Recomendados

#### 1. **Okta**
- **Fortalezas**: Líder en IAM, amplias integraciones (más de 7,000 apps), cumplimiento robusto (HIPAA, GDPR), interfaz intuitiva.
- **Consideraciones**: Costo elevado, puede ser excesivo para organizaciones pequeñas.
- **Fuente**: Guru99 (2026) y LinkedIn (criterios de selección).

#### 2. **Microsoft Azure AD**
- **Fortalezas**: Integración nativa con ecosistema Microsoft (Office 365, Windows), buen cumplimiento, escalabilidad.
- **Consideraciones**: Limitado para entornos heterogéneos no Microsoft.
- **Fuente**: Guru99 (2026).

#### 3. **OneLogin**
- **Fortalezas**: Equilibrio entre costo y funcionalidad, seguridad sólida, fácil despliegue.
- **Consideraciones**: Menos integraciones que Okta.
- **Fuente**: Blog Scalefusion (2026).

#### 4. **SailPoint (IdentityNow)**
- **Fortalezas**: Enfoque en gobernanza de identidad (IAM avanzado), auditoría detallada, cumplimiento.
- **Consideraciones**: Complejidad mayor, más adecuado para grandes organizaciones.
- **Fuente**: Guru99 (2026).

#### 5. **Logto** (Código abierto)
- **Fortalezas**: Flexible, auto-hospedable, protocolos modernos (OAuth 2.0, OpenID Connect), bajo costo.
- **Consideraciones**: Requiere conocimientos técnicos para implementación.
- **Fuente**: Logto.io (2025) – ideal para equipos IT con capacidad de desarrollo.

#### 6. **Keycloak** (Código abierto)
- **Fortalezas**: Gratuito, altamente personalizable, soporte para SSO, MFA, gestión de roles.
- **Consideraciones**: Mantenimiento interno requerido, curva de aprendizaje.
- **Fuente**: Logto.io (2025) – opción para organizaciones con recursos IT dedicados.

---

## Recomendación para Barna Health

### Opción Principal: **Okta**
- **Justificación**: 
  - Cumplimiento HIPAA/GDPR crítico para salud.
  - Facilidad de integración con aplicaciones médicas y de gestión.
  - Soporte técnico confiable y experiencia en sector salud.
  - Alineado con la necesidad de una solución "llave en mano" para la reunión del 18 de mayo.

### Alternativa Económica: **Logto** o **Keycloak**
- **Justificación**: 
  - Si Barna Health tiene capacidad de desarrollo IT, estas opciones de código abierto ofrecen flexibilidad y ahorro.
  - Logto es más moderno y fácil de adoptar; Keycloak es maduro pero requiere más configuración.

---

## Pasos Siguientes

1. **Preparar demo**: Coordinar con Xavier Puig para la reunión del 18 de mayo, enfocada en:
   - Demostración de SSO con integración a sistemas internos.
   - Discusión de cumplimiento normativo (HIPAA/GDPR).
   - Cotización basada en número de usuarios (~50
