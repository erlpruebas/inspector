# Investigación de Proveedor SSO para Barna Health

## Contexto del Cliente
- **Empresa:** Barna Health
- **Contacto principal:** Xavier Puig (xavier.puig@barnahealth.es)
- **Teléfono:** +34 600 100 038
- **Ubicación:** Barcelona
- **Rol:** IT
- **Evento próximo:** Reunión técnica presencial programada para el **18 de mayo de 2026** a las 10:00 en Barcelona para revisar integración con SSO

## Necesidades Identificadas
Basándonos en los datos locales y contexto del sector salud, Barna Health requiere:
1. Solución SSO que cumpla con regulaciones del sector salud (HIPAA/GDPR)
2. Capacidades de integración con sistemas existentes
3. Seguridad robusta para proteger datos sensibles de pacientes
4. Experiencia de usuario fluida para personal médico
5. Escalabilidad para crecimiento futuro

## Opciones de SSO Investigadas (Fuente: blog.scalefusion.com - Febrero 2026)

### Top 10 Proveedores SSO para 2026

1. **Scalefusion OneIdP** - $2 por dispositivo/mes
   - SSO federado con SAML, OAuth2/OIDC
   - Reglas condicionales basadas en navegador, Wi-Fi, IP
   - Ideal para entornos cloud-first e híbridos
   - G2 Rating: 4.7/5

2. **Okta** - $2-$5 por usuario/mes
   - Líder en gestión de identidad y acceso (IAM)
   - Integración con miles de aplicaciones
   - Autenticación MFA adaptativa
   - G2 Rating: 4.5/5

3. **Duo (Cisco)** - $3-$9 por usuario/mes
   - Enfoque en autenticación MFA
   - Políticas de acceso adaptativo
   - Opciones sin contraseña
   - G2 Rating: 4.5/5

4. **LastPass** - $4-$6 por usuario/mes
   - Gestión segura de contraseñas
   - Autocompletado automático
   - Compartir seguro
   - G2 Rating: 4.4/5

5. **PingOne** - $3-$6 por usuario/mes
   - Federación de identidades (SAML, OIDC)
   - Autenticación basada en riesgos
   - Soporte móvil robusto
   - G2 Rating: 4.4/5

6. **OneLogin** - $4-$8 por usuario/mes
   - Gestión de acceso unificada
   - Integración con directorios (AD/LDAP)
   - Catálogo extenso de aplicaciones
   - G2 Rating: 4.4/5

7. **JumpCloud** - $2 por usuario/año + $3 por dispositivo/mes
   - Directorio basado en cloud
   - SSO multi-plataforma
   - Control de acceso basado en roles
   - G2 Rating: 4.5/5

8. **RSA SecurID** - $2-$4 por mes
   - Ideal para entornos híbridos (cloud + local)
   - Amplio soporte de protocolos
   - Enfoque en seguridad robusta
   - G2 Rating: 4.4/5

9. **CyberArk Workforce Identity** - $3.50 por dispositivo/mes
   - Enfoque Zero Trust
   - MFA adaptativo
   - Puerta de enlace para aplicaciones heredadas
   - G2 Rating: 4.4/5

10. **ForgeRock Identity Platform** - Precio bajo consulta
    - Personalización profunda
    - Escalabilidad empresarial
    - Soporte para entornos complejos
    - G2 Rating: 4.0/5

## Evaluación para Sector Salud

### Criterios Críticos para Barna Health

1. **Cumplimiento Normativo:**
   - HIPAA (para datos de salud)
   - GDPR (protección de datos europea)
   - ISO 27001 (gestión de seguridad)

2. **Seguridad Específica:**
   - Autenticación MFA obligatoria
   - Auditoría de accesos completa
   - Encriptación de datos en tránsito y reposo
   - Políticas de acceso basadas en roles

3. **Integración:**
   - Compatibilidad con sistemas EHR existentes
   - Soporte para dispositivos médicos
   - API para desarrollo personalizado

## Recomendaciones para Barna Health

### Opción Principal Recomendada: **Okta**
**Razones:**
1. **Cumplimiento:** Certificaciones HIPAA, GDPR, SOC 2
2. **Sector Salud:** Experiencia comprobada en healthcare
3. **Escalabilidad:** Crecimiento empresarial garantizado
4. **Integración:** Amplio catálogo de aplicaciones médicas
5. **Seguridad:** MFA adaptativa y detección de amenazas

### Opción Alternativa: **Duo (Cisco)**
**Ventajas:**
1. **Enfoque seguridad:** Autenticación robusta especializada
2. **Cisco ecosistema:** Integración con infraestructura existente
3. **Costos:** Opciones escalables según necesidades

### Opción Económica: **Scalefusion OneIdP**
**Para considerar si:**
1. Presupuesto limitado inicial
2. Entorno cloud-first
3. Necesidad de implementación rápida

## Pasos Recomendados para la Reunión del 18 de mayo

1. **Evaluar infraestructura actual:** Directorios (Active Directory, LDAP), aplicaciones críticas
2. **Definir requisitos específicos:** Número de usuarios, aplicaciones a integrar, dispositivos
3. **Solicitar demostraciones:** Okta Healthcare, Duo Healthcare Edition
4. **Analizar costos:** Licencias por usuario vs dispositivo, costos de implementación
5. **Plan de implementación:** Fases, recursos necesarios, capacitación

## Consideraciones Adicionales

- **Migración:** Plan para migración gradual de sistemas existentes
- **Capacitación:** Programa de formación para personal médico y administrativo
- **Soporte:** Acuerdos de nivel de servicio (SLA) con proveedor
- **Backup:** Estrategia de recuperación ante desastres

**Fecha de investigación:** 21 de mayo de 2026
**Fuentes consultadas:** Blog Scalefusion (Febrero 2026), datos locales de contacto, historial de correos