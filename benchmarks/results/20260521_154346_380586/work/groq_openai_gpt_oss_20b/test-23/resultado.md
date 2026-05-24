**Resumen ejecutivo**  
Barna Health necesita integrar un proveedor de Single Sign-On (SSO) para sus aplicaciones internas y externas. El objetivo es mejorar la experiencia de los usuarios, reforzar la seguridad y cumplir con normativas de protección de datos. La reunión técnica con el equipo de IT está programada para el 18 de mayo 2026, donde se revisará la viabilidad de las opciones propuestas.

---

### Contacto clave
| Campo | Información |
|-------|-------------|
| Nombre | Xavier Puig |
| Cargo | IT – Barna Health |
| Email | xavier.puig@barnahealth.es |
| Ciudad | Barcelona |
| Prioridad | Alta |
| Fecha de contacto | 07 de mayo 2026 (hilo E‑004) |

---

### Necesidad técnica
- **SSO** con soporte para SAML 2.0 y OpenID Connect (OIDC).  
- Integración con aplicaciones SaaS y on‑premises.  
- Gestión de usuarios y grupos, aprovisionamiento automático.  
- Cumplimiento de GDPR y SOC 2.  
- Escalabilidad para 1 000 usuarios internos y 5 000 externos.  

---

### Proveedores evaluados

| Proveedor | Tipo | Integraciones principales | Coste estimado | Ventajas | Desventajas |
|-----------|------|---------------------------|----------------|----------|-------------|
| **EMÚ OneIdP** | Enterprise | SAML, OIDC, LDAP, SCIM | €12 000/año (licencia + soporte) | Soporte 24/7, cumplimiento normativo, integración con MDM | Costo elevado, licenciamiento complejo |
| **Veltar** | Enterprise | SAML, OIDC, API REST | €9 000/año | Interfaz intuitiva, gestión de dispositivos | Menos opciones de personalización |
| **Keycloak** | OSS | SAML, OIDC, LDAP, SCIM | Gratis (hosting propio) | Open source, extensible, comunidad activa | Requiere recursos internos para mantenimiento |
| **Logto** | OSS | OIDC, SAML, API | Gratis (hosting propio) | Configuración rápida, SDKs modernos | Comunidad más pequeña que Keycloak |
| **NextAuth.js** | OSS | OIDC, OAuth 2.0 | Gratis (hosting propio) | Integración con frameworks JavaScript, fácil despliegue | Menos soporte para SAML |
| **Casdoor** | OSS | SAML, OIDC, OAuth 2.0 | Gratis (hosting propio) | Soporte multi‑tenant, UI personalizable | Menos documentación en español |
| **SuperTokens** | OSS | OIDC, OAuth 2.0 | Gratis (hosting propio) | API de gestión de sesiones, SDKs | Menos opciones de SAML |

---

### Recomendación

| Criterio | Preferencia |
|----------|-------------|
| **Costo** | OSS (Keycloak o Logto) |
| **Seguridad** | Keycloak (comprobado en entornos hospitalarios) |
| **Facilidad de implementación** | Logto (configuración rápida) |
| **Soporte** | EMÚ OneIdP (si se necesita soporte dedicado) |

**Propuesta**: Adoptar **Keycloak** como solución OSS, con despliegue en infraestructura propia de Barna Health. Se recomienda contratar un servicio de consultoría externa para la configuración inicial y la integración con los sistemas existentes (ERP, CRM, sistemas de gestión de pacientes). Si el presupuesto lo permite, se puede complementar con **EMÚ OneIdP** para la gestión de dispositivos móviles y MDM.

---

### Próximos pasos

1. **Reunión de 18 mayo 2026** – Confirmar requisitos técnicos y definir alcance de la prueba piloto.  
2. **Evaluación técnica** – Desplegar un entorno de prueba con Keycloak y probar la autenticación con una aplicación interna.  
3. **Comparativa de costos** – Obtener cotizaciones de EMÚ OneIdP y Veltar.  
4. **Decisión de compra** – Basada en resultados de la prueba piloto y análisis de ROI.  
5. **Plan de migración** – Definir cronograma de transición y capacitación para usuarios finales.

---

### Fuentes consultadas (consultado el 21 de mayo 2026)

- Fuente 1: “Los 10 mejores proveedores y soluciones de SSO en 2026” – Scalefusion.  
- Fuente 2: “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto 2025” – Logto.  
- Fuente 3: “Las 10 mejores soluciones y proveedores de SSO (2026)” – Guru99.  

---
