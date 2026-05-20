# Validar descuento Delta Equipos con mercado

Valida si el descuento del 4% ofrecido por Delta Equipos para monitores 27 parece competitivo frente a referencias web actuales.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/emails_hilos.md`
- `assistant_synthetic/notas_voz.jsonl`

Usa esas rutas relativas cuando necesites leer datos locales.

Contexto web preparado por el benchmark: `web_context.md`.
Lee ese archivo antes de responder. Si usas datos del contexto web, incluye las fuentes relevantes en la respuesta.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\emails_hilos.md
```text
# PERSON_0071 correos sinteticos

## Hilo ORG_0006 - demo pagos
De: PERSON_0001 <EMAIL_0025>
Para: EMAIL_0056
Fecha: PHONE_0069:12
Asunto: Demo modulo de pagos

Podemos ver la demo el jueves 14 de mayo a las 11:30? Necesito que venga alguien de administracion.

De: EMAIL_0056
Para: PERSON_0001 <EMAIL_0025>
Fecha: PHONE_0068:04

Confirmo disponibilidad. Prepararemos una demo centrada en conciliacion y estado de pagos.

## Hilo E-002: PERSON_0065 - descuento monitores
De: PERSON_0066 <EMAIL_0054>
Fecha: PHONE_0067:40
Asunto: Oferta monitores

Si cerramos antes del dia 13 puedo aplicar un 4% de descuento sobre los monitores 27.

## Hilo E-003: IberLegal - contrato
De: PERSON_0058 <EMAIL_0048>
Fecha: PHONE_0066:15
Asunto: Revision contrato soporte

Necesito comentarios antes del 12 de mayo. Me preocupan la clausula 8 de responsabilidad y la renovacion automatica.

## Hilo E-004: Barna Health - visita PERSON_0070: PERSON_0024 <EMAIL_0018>
Fecha: PHONE_0065:22
Asunto: Reunion tecnica

Confirmo reunion presencial en Barcelona el 18 de mayo a las 10:00. Revisaremos integracion con SSO.

## Hilo E-005: PERSON_0068 - informe ejecutivo
De: PERSON_0069 <EMAIL_0055>
Fecha: PHONE_0064:10
Asunto: Formato informes

Por favor, enviadme siempre PDF con una pagina de resumen ejecutivo y anexos separados.

## Hilo E-006: BravoSoft - propuesta pendiente
De: PERSON_0059 <EMAIL_0049>
Fecha: PHONE_0063:35
Asunto: Re: propuesta CRM

Lo reviso con direccion y os digo algo la semana que viene. Si no contesto, insistidme con un correo corto.

```

### assistant_synthetic\notas_voz.jsonl
```text
{"id": "VN-001", "timestamp": "PHONE_0088:12", "transcript": "Recordar llamar a Noelia de ORG_0005 antes del jueves para confirmar PERSON_0009l modulo de pagos."}
{"id": "VN-002", "timestamp": "PHONE_0087:40", "transcript": "Enviar a PERSON_0074 el CSV actualizado de monitores; falta incluir descuento del 4 por ciento."}
{"id": "VN-003", "timestamp": "PHONE_0086:18", "transcript": "Comprar billete para Barcelona el dia 18 si Xavier confirma la reunion de Barna Health."}
{"id": "VN-004", "timestamp": "PHONE_0085:55", "transcript": "Preparar minuta para PERSON_0060 con riesgos de seguridad y coste de auditoria."}
{"id": "VN-005", "timestamp": "PHONE_0084:03", "transcript": "Pedir a PERSON_0073 facturas de abril que no aparecen en el banco."}
{"id": "VN-006", "timestamp": "PHONE_0083:34", "transcript": "Crear tarea para revisar contrato de IberLegal; David pidio respuesta antes del 12."}
{"id": "VN-007", "timestamp": "PHONE_0082:10", "transcript": "Agendar seguimiento con PERSON_0064 el martes a las cuatro por el tema de administracion."}
{"id": "VN-008", "timestamp": "PHONE_0081:05", "transcript": "No olvidar que PERSON_0069 prefiere recibir informes en PDF y resumen ejecutivo corto."}
{"id": "VN-009", "timestamp": "PHONE_0080:29", "transcript": "Buscar alternativa barata a herramienta de encuestas para GreenBox."}
{"id": "VN-010", "timestamp": "PHONE_0079:00", "transcript": "Llamar a PERSON_0072 por pedido de licencias y confirmar direccion fiscal."}
{"id": "VN-011", "timestamp": "PHONE_0078:12", "transcript": "Enviar agenda de implantacion a PERSON_0033; incluir hito de formacion el dia 22."}
{"id": "VN-012", "timestamp": "PHONE_0064:43", "transcript": "Revisar gastos de marzo porque hay dos cargos duplicados de hotel."}
{"id": "VN-013", "timestamp": "PHONE_0077:20", "transcript": "Poner recordatorio para renovar certificado SSL de Cobalto antes del 28."}
{"id": "VN-014", "timestamp": "PHONE_0076:02", "transcript": "Preparar comparativa OpenRouter contra Gemini para tareas de ofimatica."}
{"id": "VN-015", "timestamp": "PHONE_0075:44", "transcript": "Enviar email amable a PERSON_0059, no ha contestado la propuesta de BravoSoft."}
{"id": "VN-016", "timestamp": "PHONE_0074:16", "transcript": "ORG_0008 con facturas, creo que falta una de 847 con cincuenta."}
{"id": "VN-017", "timestamp": "PHONE_0073:52", "transcript": "Crear lista de contactos prioritarios de Madrid con nivel alta."}
{"id": "VN-018", "timestamp": "PHONE_0072:30", "transcript": "Investigar si Apple ha subido mas que Microsoft en los ultimos seis meses."}
{"id": "VN-019", "timestamp": "PHONE_0071:25", "transcript": "Preparar informe mensual de incidencias: incluir ORG_0007 facturacion."}
{"id": "VN-020", "timestamp": "PHONE_0070:00", "transcript": "Recordar reservar sala para reunion interna del viernes a las nueve y media."}

```

### web_context.md
```text
# Web context

Consulta preparada por el benchmark: Validar descuento Delta Equipos con mercado

Usa estas fuentes como contexto. Si la tarea pide datos actuales, cita la fuente y la fecha de consulta.

## Fuente 1: Verificador de Ofertas - Histórico de precios de ecommerce
URL: https://www.verificadordeofertas.com/
Resumen buscador: La finalidad de esta información puede ser muy diversa, desde mejorar tu experiencia en la página web mostrando el contenido en tu idioma o recomendar otros contenidos de tu interés, hasta identificarte como usuario a la hora de acceder a áreas privadas de la web.
Extracto: Verificador de Ofertas - Histórico de precios de ecommerce Verificador de Ofertas Indícanos el link de un producto y comprobaremos la calidad de su oferta . Buscamos en más de 30 millones de productos a lo largo de 500 webs monitorizadas en España. ¿Eres tienda o marca? Monitorización de Precios de la Competencia Dynamic Pricing Privacy & Cookie Policy Terms & Conditions Whistleblower Channel En este sitio utilizamos cookies En este sitio utilizamos cookies propias y de terceros y/o tecnologías similares que almacenan y registran información mientras navegas por la web. La finalidad de esta información puede ser muy diversa, desde mejorar tu experiencia en la página web mostrando el contenido en tu idioma o recomendar otros contenidos de tu interés, hasta identificarte como usuario a la hora de acceder a áreas privadas de la web. Puedes aceptar todas las cookies pulsando el botón “Aceptar”, configurarlas desde “Configuración de cookies” o rechazar su uso clicando en el botón “Rechazar”. Puedes conocer las diferentes cookies que utilizamos en nuestro Aviso legal, política de privacidad y cookies. Rechazar Aceptar Configuración de cookies Configuración de cookies Cookies Técnicas y Funcionales Estas cookies son necesarias para el correcto funcionamiento del sitio web y el acceso a áreas privadas. La página web no puede funcionar adecuadamente sin estas cookies. Cookies de Análisi

## Fuente 2: 5 herramientas para saber si una oferta es real o falsa - APPerlas
URL: https://apperlas.com/verificadores-de-ofertas-descuentos-reales-o-falsos/
Resumen buscador: Evita descuentos engañosos con estas 5 herramientas que muestran el historial de precios y comparan ofertas reales.
Extracto: 5 herramientas para saber si una oferta es real o falsa Ir al contenido iPhone Fotografía en iPhone Música en iPhone Seguridad iPhone Trucos para iPhone Trucos para apps Apple Watch Apps Apple Watch Salud y deporte Trucos Apple Watch iOS Aplicaciones Apps de noticias Compras Deporte y salud Educación Entretenimiento Fotografía y vídeo Idiomas Música y audio Productividad Social Turismo y navegación TV, cine y vídeos Utilidades Juegos Juegos arcade Juegos de estrategia Juegos educativos Juegos gratis Atajos y automatizaciones Automatizaciones iPhone Fotografía en iPhone Música en iPhone Seguridad iPhone Trucos para iPhone Trucos para apps Apple Watch Apps Apple Watch Salud y deporte Trucos Apple Watch iOS Aplicaciones Apps de noticias Compras Deporte y salud Educación Entretenimiento Fotografía y vídeo Idiomas Música y audio Productividad Social Turismo y navegación TV, cine y vídeos Utilidades Juegos Juegos arcade Juegos de estrategia Juegos educativos Juegos gratis Atajos y automatizaciones Automatizaciones Inicio Aplicaciones para iPhone y iPad Compras ¿Descuento real o timo? Estas 5 herramientas lo desenmascaran ¿Descuento real o timo? Estas 5 herramientas lo desenmascaran Por Mariano Lopez / 11/11/2025 ¿Te suena eso de ver un «70 % de descuento» y pensar: ¿de verdad es una ganga o me están engañando? ? Hoy en día, muchas tiendas inflan precios antes de aplicar supuestas reb

## Fuente 3: Validación | Coupontools Help Center
URL: https://help.coupontools.com/es/category/validacion-1fs8jwn/
Resumen buscador: Con el método del widget de validación, puedes guardar información adicional después de validar un cupón de un cliente. Puedes guardar el género, nombre y apellido, correo electrónico, número de teléfono y también la cantidad de dinero que han gastado en tu tienda.
Extracto: Validación | Coupontools Help Center German English Spanish Dutch Ir al sitio web Volver Artículos sobre: Validación Toda la información que necesitas sobre las validaciones de los cupones Categorías Vales Cupones Tarjetas de fidelidad Directorios Cupones gamificados Páginas de aterrizaje Billetera móvil Validación Distribución de cupones Análisis/estadística Marca blanca y subcuentas Automatización y API Protección de datos Preguntas generales sobre la plataforma Facturación y precios Licencia de dominio personalizada ¿Cómo se pueden validar los cupones? ¿Mostrarme todos los métodos de validación disponibles? Por el momento tenemos 6 métodos diferentes para validar un cupón. Puedes usar 1 método o combinar varios métodos para cada cupón. 1. En dispositivo móvil Valida el cupón en el dispositivo del cliente ingresando una contraseña o simplemente presionando un botón 'canjear' sin contraseña. (Esta opción no funciona para cupones imprimibles). 2. Validación del códig Algunos lectores ¿Cómo mostrar códigos de descuento para tiendas web en la página de validación de mi cupón? Para mostrar un código de descuento en la página de validación de tu cupón, ve a las opciones de validación en Después del reclamo de tu creador de cupones Allí puedes configurar un valor de cupón en la página de validación. Pero el valor del cupón se puede cambiar a 'Código de promoción' y eso puede actuar 

## Fuente 4: Productos de incentivo de certificados electrónicos no monetarios de Delta
URL: https://pro.delta.com/content/agency/erp/es/products-and-services/ecertificate-programs/delta-ecerts---non-cash-incentive-products.html
Resumen buscador: ¿Valen los certificados electrónicos de Delta para Air France o KLM? Verifique los términos y condiciones de cada certificado para determinar para qué compañía aérea son válidos.
Extracto: Productos de incentivo de certificados electrónicos no monetarios de Delta ENGLISH DEUTSCH FRANÇAIS NEDERLANDS ITALIANO ESPAÑOL Europe INICIO Recursos para agentes BIBLIOTECA DE POLÍTICAS PRODUCTOS Y SERVICIOS NOTICIAS MIS OPCIONES MIS OPCIONES - Mantenimiento administrador Usuarios Manejo de Administrador de usuarios Detalles de la agencia Configuraciones de la aplicación Acceso corporativo Administrar mi agencia > VOLVER A PRODUCTOS Y SERVICIOS Productos de incentivo de certificados electrónicos no monetarios de Delta Los certificados electrónicos de Delta se pueden canjear por una variedad de ofertas en vuelos elegibles, incluidos: Un descuento específico en dólares del coste de una tarifa elegible. Un porcentaje de descuento específico del coste de una tarifa elegible. Un valor monetario específico que se pueda aplicar como pago para un billete. Un certificado de viaje que cubra el coste de un billete y requiera que el cliente pague únicamente los impuestos y cargos aplicables. Una subida de clase de cortesía. Según los términos y condiciones del certificado electrónico de Delta, estos se pueden combinar con otros certificados electrónicos o créditos electrónicos. Para consultar los detalles y los términos y condiciones del certificado, visite es.delta.com/redeem e introduzca el número y el código de canje del certificado electrónico de Delta. Preguntas frecuentes ¿Cómo pue

```