**Recomendación de proveedores de SSO para Barna Health**

1. **Okta (Enterprise SaaS)**
   * **Ventajas**  
     * Cumplimiento HIPAA, SOC 2, GDPR y certificaciones de seguridad de la industria sanitaria.  
     * Integración nativa con Office 365, Google Workspace, Salesforce y sistemas de EMR.  
     * Gestión de usuarios y grupos con políticas de acceso basadas en roles (RBAC).  
     * Soporte de MFA, SAML 2.0, OpenID Connect y SCIM para aprovisionamiento automático.  
   * **Desventajas**  
     * Costo mensual por usuario; puede ser elevado para un hospital con cientos de usuarios.  
     * Dependencia de la nube de Okta; requiere alta disponibilidad de Internet.  
   * **Cita**: Fuente 1 – “Los 10 mejores proveedores y soluciones de SSO en 2026” menciona a Okta como líder de mercado.  

2. **Azure Active Directory (Microsoft Entra ID)**
   * **Ventajas**  
     * Integración profunda con Windows Server, Exchange, Teams y sistemas de gestión hospitalaria.  
     * Cumplimiento HIPAA y SOC 2; auditorías y registros de acceso integrados.  
     * MFA, Conditional Access y Zero Trust con Azure AD Conditional Access.  
     * Modelo de precios por usuario con descuentos por volumen.  
   * **Desventajas**  
     * Requiere licencias de Microsoft 365 o licencias de Azure AD Premium.  
     * Configuración inicial puede ser compleja para equipos sin experiencia en Azure.  
   * **Cita**: Fuente 2 – “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto” menciona Azure AD como referencia de mercado, aunque no es OSS.  

3. **Auth0 (SaaS)**
   * **Ventajas**  
     * API‑first, con SDKs para Java, .NET, Node.js, Python, etc.  
     * Soporte de MFA, SAML, OpenID Connect y reglas de autorización personalizadas.  
     * Cumplimiento HIPAA con planes Enterprise.  
   * **Desventajas**  
     * Costo por número de conexiones y usuarios activos.  
     * Dependencia de la nube de Auth0; requiere plan Enterprise para HIPAA.  
   * **Cita**: Fuente 1 – menciona Auth0 como una de las soluciones de SSO líderes.  

4. **Keycloak (Open‑Source)**
   * **Ventajas**  
     * Totalmente libre y personalizable; se puede alojar en infraestructuras on‑premise o en la nube.  
     * Soporte de SAML, OpenID Connect, OAuth 2.0 y SCIM.  
     * Comunidad activa y extensiones para integraciones con sistemas de EMR.  
   * **Desventajas**  
     * Requiere personal de TI para despliegue, mantenimiento y actualizaciones de seguridad.  
     * No incluye soporte oficial; depende de la comunidad o de un contrato de soporte de terceros.  
   * **Cita**: Fuente 2 – “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto” incluye a Keycloak como opción OSS.  

5. **Logto (Open‑Source)**
   * **Ventajas**  
     * Arquitectura moderna basada en microservicios, con API GraphQL y SDKs.  
     * Soporte de MFA, SAML, OpenID Connect y gestión de usuarios.  
     * Licencia MIT; fácil de desplegar en Kubernetes.  
   * **Desventajas**  
     * Comunidad más pequeña que Keycloak; menos integraciones pre‑construidas.  
     * Requiere personal de TI para soporte y personalización.  
   * **Cita**: Fuente 2 – menciona a Logto como uno de los cinco principales proveedores OSS.  

---

## Recomendación específica para Barna Health

| Criterio | Okta | Azure AD | Auth0 | Keycloak | Logto |
|----------|------|----------|-------|----------|-------|
| Cumplimiento HIPAA | ✔ | ✔ | ✔ | ❌ (depende de despliegue) | ❌ |
| Integración con EMR | ✔ (con conectores) | ✔ (con Azure API) | ✔ | ✔ (con adaptadores) | ✔ |
| Costo | Alto | Medio | Alto | Bajo (solo infraestructura) | Bajo |
| Soporte | 24/7 | 24/7 | 24/7 | Comunidad | Comunidad |
| Escalabilidad | Alta | Alta | Alta | Alta (auto‑escalable) | Alta |

**Conclusión**  
Para un hospital que necesita cumplimiento HIPAA, integración con sistemas existentes y soporte continuo, **Okta** o **Azure Active Directory** son las opciones más seguras y rápidas de implementar. Si el presupuesto es limitado y el equipo de TI puede gestionar la infraestructura, **Keycloak** o **Logto** ofrecen una solución de código abierto con total control sobre la configuración y la seguridad.

---

## Próximos pasos

1. **Reunión técnica** – Confirmar la agenda con Xavier Puig (IT, Barna Health) el 18 de mayo a las 10:00 h.  
2. **Prueba piloto** – Seleccionar 2‑3 usuarios de cada departamento (Administración, TI, Seguridad) para probar Okta y Azure AD en un entorno de laboratorio.  
3. **Evaluación de costos** – Obtener cotizaciones de Okta y Azure AD con planes Enterprise (HIPAA).  
4. **Plan de migración** – Definir cronograma de aprovisionamiento de usuarios, configuración de MFA y políticas de acceso.  
5. **Capacitación** – Programar sesiones de formación para usuarios finales y administradores de TI.  

**Contacto clave**  
- **Xavier Puig** – IT, Barna Health – xavier.puig@barnahealth.es – Tel: +34 600 100 038 (Barcelona).  

---

**Fuentes**  
- Fuente 1: “Los 10 mejores proveedores y soluciones de SSO en 2026” (blog.scalefusion.com).  
- Fuente 2: “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM) de código abierto” (blog.logto.io).
