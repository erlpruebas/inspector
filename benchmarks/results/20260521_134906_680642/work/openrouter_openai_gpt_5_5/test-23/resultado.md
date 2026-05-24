# Investigación de proveedor SSO para Barna Health

## Contexto local

- **Cliente:** Barna Health  
- **Contacto técnico:** Xavier Puig  
- **Rol:** IT  
- **Email:** xavier.puig@barnahealth.es  
- **Teléfono:** +34 600 100 038  
- **Ciudad:** Barcelona  
- **Prioridad:** alta  
- **Hilo relacionado:** “Barna Health - visita Barcelona”  
- **Fecha del correo:** 2026-05-07 18:22  
- **Reunión confirmada:** presencial en Barcelona, **18 de mayo de 2026 a las 10:00**  
- **Necesidad técnica indicada:** revisar **integración con SSO**

## Necesidad estimada

Para Barna Health, por tratarse de una organización sanitaria y con contacto IT directo, el proveedor SSO debería priorizar:

1. **SSO estándar** con SAML 2.0 y OpenID Connect/OAuth 2.0.
2. **MFA fuerte**: aplicación móvil, FIDO2/WebAuthn, passkeys o llaves físicas.
3. **Provisioning y deprovisioning** mediante SCIM.
4. **Integración con directorio existente**, especialmente si usan Microsoft 365, Google Workspace, LDAP o Active Directory.
5. **Auditoría y trazabilidad** para accesos administrativos y clínicos.
6. **Políticas condicionales** por ubicación, dispositivo, riesgo o rol.
7. **Cumplimiento GDPR** y preferiblemente residencia de datos o garantías contractuales para UE.
8. **Alta disponibilidad** y soporte empresarial.
9. **Facilidad de integración con aplicaciones internas o sanitarias** mediante SAML/OIDC.
10. **Modelo operativo asumible por el equipo IT de Barna Health**.

## Opciones recomendadas

| Opción | Encaje para Barna Health | Fortalezas | Riesgos / puntos a validar | Recomendación |
|---|---:|---|---|---|
| **Microsoft Entra ID** | Muy alto si usan Microsoft 365 o Active Directory | Integración nativa con M365, MFA, Conditional Access, SCIM, SAML/OIDC, buena adopción empresarial | Coste real depende de licencias P1/P2; validar requisitos de auditoría avanzada | **Primera opción si Barna Health ya está en ecosistema Microsoft
