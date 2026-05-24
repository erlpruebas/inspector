# Resultado: proveedor de SSO para Barna Health

## Contexto local relevante
- Contacto clave interno: **Xavier Puig** — `xavier.puig@barnahealth.es`, IT, Barcelona.
- Necesidad técnica explícita: en el hilo **E-004** Xavier confirma una **reunión presencial en Barcelona el 18 de mayo a las 10:00** para **revisar la integración con SSO**.
- Señal de prioridad: Xavier figura en `contactos_50.csv` como **cliente, prioridad alta**, lo que refuerza que el caso es relevante para IT y probablemente sensible por impacto operativo.

## Requerimiento inferido
Barna Health necesita una solución de SSO orientada a entorno sanitario, con foco en:
- integración sencilla con aplicaciones existentes,
- soporte de protocolos estándar de identidad,
- seguridad y control de acceso,
- escalabilidad para usuarios internos y potencialmente terceros,
- buena encaje con cumplimiento y auditoría.

## Opciones actuales de SSO adecuadas

### 1) Microsoft Entra ID
**Encaje recomendado: muy alto**
- Adecuado si Barna Health ya usa Microsoft 365, Windows o un entorno híbrido.
- Buen soporte para SAML, OAuth2 y OpenID Connect.
- Facilita MFA, Conditional Access y gobierno de identidad.
- Suele ser la opción más sólida para organizaciones sanitarias con ecosistema Microsoft.

**Ventajas**
- Integración amplia con aplicaciones empresariales.
- Administración centralizada.
- Buen nivel de seguridad y auditoría.

**Riesgos / límites**
- Coste puede crecer según licencias y funcionalidades avanzadas.
- Menor flexibilidad que una solución autoalojada para casos muy personalizados.

### 2) Okta
**Encaje recomendado: alto**
- Muy fuerte en SSO empresarial y conectores SaaS.
- Buena experiencia para despliegues rápidos y gestión de múltiples apps.
- Adecuado si Barna Health busca independencia del stack Microsoft.

**Ventajas**
- Catálogo de aplicaciones amplio.
- Implementación madura de SSO y MFA.
- Buena experiencia de administración.

**Riesgos / límites**
- Coste de licencia.
- Dependencia de un proveedor SaaS externo.

### 3) Keycloak
**Encaje recomendado: alto si prima control técnico**
- Opción open source muy usada para IAM/SSO.
- Soporta SAML, OpenID Connect y OAuth2.
- Interesante si Barna Health quiere control, autoalojamiento y flexibilidad.

**Ventajas**
- Sin coste de licencia.
- Muy configurable.
- Buena opción para integraciones a medida.

**Riesgos / límites**
- Requiere equipo técnico para operación, mantenimiento y hardening.
- Menor simplicidad funcional que una suite comercial.

### 4) Google Cloud Identity / Workspace SSO
**Encaje recomendado: medio**
- Buena opción si la organización está ya muy alineada con Google Workspace.
- Menos habitual como núcleo de IAM en organizaciones sanitarias con entorno mixto.

### 5) OneLogin
**Encaje recomendado: medio-alto**
- Alternativa empresarial sólida.
- Menor presencia que Entra ID u Okta, pero válida para SSO centralizado.

## Recomendación principal para Barna Health
**Recomendaría Microsoft Entra ID como primera opción**, salvo que Barna Health tenga una estrategia explícita de autoservicio técnico o independencia tecnológica, en cuyo caso **Keycloak** sería la alternativa más interesante.

### Motivo de la recomendación
- En un entorno sanitario, la combinación de **seguridad, MFA, auditoría y control de acceso** es crítica.
- Entra ID suele ofrecer el mejor equilibrio entre **gobierno, integración y adopción**.
- Si el entorno ya es Microsoft, reduce fricción y acelera la implantación.
- Si la prioridad es soberanía técnica y coste de licencia, Keycloak es fuerte, pero exige más operación interna.

## Consideraciones técnicas para la reunión del 18 de mayo
Puntos que Xavier debería validar:
- aplicaciones que deben federarse primero,
- si necesitan **SAML**, **OIDC** o ambos,
- método de aprovisionamiento de usuarios: manual, SCIM o sincronización con directorio,
- MFA obligatorio para acceso remoto,
- requisitos de trazabilidad y auditoría,
- soporte para personal clínico, administrativo y proveedores externos,
- si se requiere alta disponibilidad y recuperación ante fallos.

## Fuentes web utilizadas
- Scalefusion, “Los 10 mejores proveedores y soluciones de SSO en 2026” — contexto de mercado y soluciones SSO actuales.
- Guru99, “Las 10 mejores soluciones y proveedores de SSO (2026)” — visión general de opciones vigentes.
- Logto Blog, “Los 5 principales proveedores de Gestión de Identidad y Acceso (IAM)
