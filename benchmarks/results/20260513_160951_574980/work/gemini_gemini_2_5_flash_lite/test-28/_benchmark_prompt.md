# Investigacion web y propuesta CRM para BravoSoft

Investiga opciones actuales de CRM para pymes y redacta una propuesta de seguimiento para BravoSoft usando el contexto local de Paula Ferrer.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/emails_hilos.md`
- `assistant_synthetic/contactos_50.csv`

Usa esas rutas relativas cuando necesites leer datos locales.

Contexto web preparado por el benchmark: `web_context.md`.
Lee ese archivo antes de responder. Si usas datos del contexto web, incluye las fuentes relevantes en la respuesta.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\contactos_50.csv
```text
nombre,email,telefono,ciudad,empresa,rol,tipo,prioridad
Ana Lopez,ana.lopez@novaiberia.es,+34 600 100 001,Madrid,Nova Iberia,Directora Operaciones,cliente,alta
Luis Martin,luis.martin@deltaequipos.es,+34 600 100 002,Valencia,Delta Equipos,Compras,proveedor,media
Marta Ruiz,marta.ruiz@clinicasol.es,+34 600 100 003,Sevilla,Clinica Sol,Administracion,cliente,alta
Jorge Soler,jorge.soler@logimedit.es,+34 600 100 004,Bilbao,Logimedit,Logistica,partner,media
Elena Vidal,elena.vidal@atlanticdata.es,+34 600 100 005,A Coruna,Atlantic Data,Finanzas,cliente,alta
Sergio Campos,sergio.campos@innotek.es,+34 600 100 006,Zaragoza,Innotek,CTO,cliente,alta
Paula Ferrer,paula.ferrer@bravosoft.es,+34 600 100 007,Malaga,BravoSoft,Ventas,prospecto,media
David Navarro,david.navarro@iberlegal.es,+34 600 100 008,Madrid,IberLegal,Legal,proveedor,media
Clara Molina,clara.molina@greenbox.es,+34 600 100 009,Barcelona,GreenBox,Marketing,cliente,baja
Ruben Ortega,ruben.ortega@metalsur.es,+34 600 100 010,Murcia,MetalSur,Gerencia,cliente,alta
Teresa Blanco,teresa.blanco@aquanet.es,+34 600 100 011,Vigo,AquaNet,Soporte,cliente,media
Hector Mora,hector.mora@finansys.es,+34 600 100 012,Madrid,FinanSys,Producto,partner,alta
Lucia Torres,lucia.torres@solucionesmar.es,+34 600 100 013,Cadiz,Soluciones Mar,Direccion,cliente,alta
Marcos Gil,marcos.gil@tecnoria.es,+34 600 100 014,Valladolid,Tecnoria,IT,proveedor,media
Nuria Vega,nuria.vega@almacenesnorte.es,+34 600 100 015,Santander,Almacenes Norte,Compras,cliente,media
Oscar Prieto,oscar.prieto@consultia.es,+34 600 100 016,Madrid,Consultia,Consultor,partner,baja
Irene Sanz,irene.sanz@biocentro.es,+34 600 100 017,Granada,BioCentro,Calidad,cliente,alta
Victor Leon,victor.leon@urbanlift.es,+34 600 100 018,Barcelona,UrbanLift,Operaciones,cliente,media
Raquel Cano,raquel.cano@nodalabs.es,+34 600 100 019,Madrid,Noda Labs,Data,prospecto,alta
Adrian Pons,adrian.pons@mediatres.es,+34 600 100 020,Palma,MediaTres,Cuentas,cliente,baja
Beatriz Costa,beatriz.costa@orionretail.es,+34 600 100 021,Barcelona,Orion Retail,Retail,cliente,alta
Daniel Rios,daniel.rios@ferrovia.es,+34 600 100 022,Oviedo,Ferrovia,Compras,proveedor,media
Eva Roman,eva.roman@kairon.es,+34 600 100 023,Madrid,Kairon,People,cliente,media
Gonzalo Pardo,gonzalo.pardo@mintcloud.es,+34 600 100 024,Valencia,MintCloud,Cloud,partner,alta
Helena Suarez,helena.suarez@puravida.es,+34 600 100 025,Alicante,PuraVida,Expansion,prospecto,media
Ivan Duran,ivan.duran@cobalto.es,+34 600 100 026,Madrid,Cobalto,Seguridad,proveedor,alta
Julia Iglesias,julia.iglesias@tresnaves.es,+34 600 100 027,Sevilla,Tres Naves,Direccion,cliente,alta
Kevin Ramos,kevin.ramos@aurea.es,+34 600 100 028,Barcelona,Aurea,Finanzas,cliente,media
Laura Marin,laura.marin@northwind.es,+34 600 100 029,Bilbao,Northwind ES,Ventas,cliente,alta
Miguel Santos,miguel.santos@argentalia.es,+34 600 100 030,Madrid,Argentalia,Inversiones,prospecto,media
Noelia Castro,noelia.castro@clinicacentro.es,+34 600 100 031,Madrid,Clinica Centro,Administracion,cliente,alta
Pablo Herrero,pablo.herrero@navilux.es,+34 600 100 032,Valencia,Navilux,Operaciones,cliente,media
Rocio Nieto,rocio.nieto@pixelarte.es,+34 600 100 033,Malaga,PixelArte,Diseno,proveedor,baja
Samuel Ibanez,samuel.ibanez@quantica.es,+34 600 100 034,Madrid,Quantica,Analitica,partner,alta
Silvia Rey,silvia.rey@transmed.es,+34 600 100 035,Zaragoza,TransMed,Logistica,cliente,media
Tomas Vega,tomas.vega@zenitfood.es,+34 600 100 036,Barcelona,Zenit Food,Compras,cliente,alta
Valeria Navas,valeria.navas@rednova.es,+34 600 100 037,Madrid,RedNova,Marketing,prospecto,media
Xavier Puig,xavier.puig@barnahealth.es,+34 600 100 038,Barcelona,Barna Health,IT,cliente,alta
Yolanda Cruz,yolanda.cruz@serconta.es,+34 600 100 039,Toledo,SerConta,Contabilidad,proveedor,media
Alberto Saez,alberto.saez@omniplus.es,+34 600 100 040,Madrid,OmniPlus,Direccion,cliente,alta
Belen Arias,belen.arias@vetor.es,+34 600 100 041,Gijon,Vetor,Soporte,cliente,baja
Carlos Benitez,carlos.benitez@solardesk.es,+34 600 100 042,Sevilla,SolarDesk,Operaciones,cliente,alta
Diana Estevez,diana.estevez@bluecargo.es,+34 600 100 043,Valencia,BlueCargo,Logistica,cliente,media
Esteban Lozano,esteban.lozano@helixia.es,+34 600 100 044,Madrid,Helixia,CTO,partner,alta
Fabiola Mendez,fabiola.mendez@optired.es,+34 600 100 045,Murcia,OptiRed,Ventas,prospecto,media
Guillermo Casas,guillermo.casas@neotaller.es,+34 600 100 046,Valladolid,NeoTaller,Gerencia,cliente,alta
Ines Robles,ines.robles@marketuno.es,+34 600 100 047,Madrid,MarketUno,Marketing,cliente,media
Jaime Pastor,jaime.pastor@alboran.es,+34 600 100 048,Malaga,Alboran,Legal,proveedor,media
Lorena Vidal,lorena.vidal@civitas.es,+34 600 100 049,Barcelona,Civitas,Producto,cliente,alta
Manuel Fuentes,manuel.fuentes@dueroapps.es,+34 600 100 050,Salamanca,Duero Apps,Direccion,cliente,media

```

### assistant_synthetic\emails_hilos.md
```text
# Historial de correos sinteticos

## Hilo E-001: Clinica Centro - demo pagos
De: Noelia Castro <noelia.castro@clinicacentro.es>
Para: equipo@inspector.local
Fecha: 2026-05-06 09:12
Asunto: Demo modulo de pagos

Podemos ver la demo el jueves 14 de mayo a las 11:30? Necesito que venga alguien de administracion.

De: equipo@inspector.local
Para: Noelia Castro <noelia.castro@clinicacentro.es>
Fecha: 2026-05-06 10:04

Confirmo disponibilidad. Prepararemos una demo centrada en conciliacion y estado de pagos.

## Hilo E-002: Delta Equipos - descuento monitores
De: Luis Martin <luis.martin@deltaequipos.es>
Fecha: 2026-05-05 12:40
Asunto: Oferta monitores

Si cerramos antes del dia 13 puedo aplicar un 4% de descuento sobre los monitores 27.

## Hilo E-003: IberLegal - contrato
De: David Navarro <david.navarro@iberlegal.es>
Fecha: 2026-05-04 17:15
Asunto: Revision contrato soporte

Necesito comentarios antes del 12 de mayo. Me preocupan la clausula 8 de responsabilidad y la renovacion automatica.

## Hilo E-004: Barna Health - visita Barcelona
De: Xavier Puig <xavier.puig@barnahealth.es>
Fecha: 2026-05-07 18:22
Asunto: Reunion tecnica

Confirmo reunion presencial en Barcelona el 18 de mayo a las 10:00. Revisaremos integracion con SSO.

## Hilo E-005: Nova Iberia - informe ejecutivo
De: Ana Lopez <ana.lopez@novaiberia.es>
Fecha: 2026-05-08 08:10
Asunto: Formato informes

Por favor, enviadme siempre PDF con una pagina de resumen ejecutivo y anexos separados.

## Hilo E-006: BravoSoft - propuesta pendiente
De: Paula Ferrer <paula.ferrer@bravosoft.es>
Fecha: 2026-05-02 13:35
Asunto: Re: propuesta CRM

Lo reviso con direccion y os digo algo la semana que viene. Si no contesto, insistidme con un correo corto.

```

### web_context.md
```text
# Web context

Consulta preparada por el benchmark: Investigacion web y propuesta CRM para BravoSoft

Usa estas fuentes como contexto. Si la tarea pide datos actuales, cita la fuente y la fecha de consulta.

## Fuente 1: 8 ejemplos de CRM para empresas y para qué sirven | Brevo
URL: https://www.brevo.com/es/blog/crm-ejemplos/
Resumen buscador: En este artículo, podrás encontrar ocho ejemplos de CRM que te mostrarán cómo se pueden aprovechar estas plataformas en negocios de distinto tipo.
Extracto: 8 ejemplos de CRM para empresas y para qué sirven | Brevo Plataforma Funcionalidades Funcionalidades Campañas y automatización Impulsa las conversiones con recorridos de cliente multicanal automatizados. Mensajería transaccional Envia emails, SMS y WhatsApp en tiempo real mediante SMTP o API. Gestión de ventas Impulsa ingresos con pipelines a medida, automatización de ventas, chat y más. Brevo Data Platform Unifica, gestiona y sincroniza los datos de tus clientes para acelerar su valorización. Integraciones Integra Brevo con más de 150 herramientas digitales como Shopify, WordPress, Stripe, Zapier y más. Canales Canales Email SMS WhatsApp Notificaciones push web & mobile Chat en vivo Chatbot Wallet VoIP Phone Soluciones Emprendedores y pequeñas empresas Emprendedores y pequeñas empresas Lanza campañas, automatiza tu marketing y gestiona tus contactos fácilmente. Medianas y grandes empresas Medianas y grandes empresas Adaptada a tus necesidades: onboarding dedicado, control de tus datos y seguridad avanzada. Ecommerce & retail Ecommerce & retail Recupera carritos abandonados, personaliza recomendaciones de producto e impulsa la lealtad. Desarrolladores Desarrolladores Crea soluciones personalizadas con guías para desarrolladores, API abiertas, SDKs y ejemplos de código. Precios Recursos Recursos Blog E-books Testimonios Plantillas de email Herramientas de email marketing Cómo en

## Fuente 2: Cómo crear una estrategia de CRM en 6 pasos (incluye ejemplos)
URL: https://asana.com/es/resources/crm-strategy
Resumen buscador: Una estrategia de CRM representa el plan de negocios de una empresa para mejorar las relaciones con sus clientes. En este artículo, detallaremos cómo armar una estrategia de CRM paso a paso y cómo puedes implementarla con un software de CRM .
Extracto: Cómo crear una estrategia de CRM en 6 pasos (incluye ejemplos) [2026] • Asana Asana Home Producto chevron-down icon Soluciones chevron-down icon Apoyo chevron-down icon Precios Choose your preferred language Bahasa Indonesia Deutsch English Español Français Italiano 日本語 한국어 Nederlands Polski Português Русский Svenska 繁體中文 Contactar a Ventas Inicia sesión Comenzar Iniciar Asana Cambiar de plan Contactar a Ventas chevron-down icon settings icon Mis tareas Bandeja de entrada My organization Centro de ayuda Language plus icon Add another account Cerrar sesión Producto chevron-down icon PLATAFORMA Resumen del producto Todas las funciones Integraciones con aplicaciones Último lanzamiento de funciones CAPACIDADES Gestión de proyectos Flujos de trabajo y automatización Objetivos e informes Gestión de recursos Administración y seguridad IA DE ASANA IA de Asana AI Studio AI Teammates Asistentes Inteligentes TODOS LOS PLANES list icon Personal premium icon Starter briefcase icon Avanzado Soluciones chevron-down icon Tipo de empresa Enterprise Pequeña empresa Organizaciones sin fines de lucro Startup Equipos Operaciones Marketing TI Líderes Sectores Gobierno Salud Venta minorista Servicios financieros Educación Fabricación Casos de uso Gestión de objetivos Planificación organizativa Recepción de proyectos Planificación de recursos Lanzamientos de productos Ver todos los casos de uso arrow-

## Fuente 3: Los 20 mejores CRM del momento para tu empresa - Cyberclick
URL: https://www.cyberclick.es/numerical-blog/los-mejores-crm-del-momento-para-tu-empresa
Resumen buscador: Si estás pensando en contratar un CRM te presentamos los mejores del momento con un amplio abanico de posibilidades. Por David Tomás, Cyberclick.
Extracto: Los 20 mejores CRM del momento para tu empresa Saltar al contenido principal Saltar a navegación Nosotros Metodologías propias Valores y equipo Únete a nosotros Sala de prensa Servicios Content Inbound Marketing Influencer Marketing Video Marketing Redes Sociales Data Inteligencia Artificial Data Science & BI Data Analytics Data Integration Google Analytics 4 Technology Account Based Marketing Ecommerce CRO CRM Marketplaces Feedest Media SEM Social Ads Email Marketing Publicidad Programática Digital Advisory Growth Marketing Auditoría Digital Formación In Company Casos de éxito Academy Contenido destacado ¿Por qué hacer Marketing? ¿Para qué sirve la Publicidad? Inteligencia Artificial (IA) y su aplicación al Marketing ¿Qué es el Inbound Marketing? ¿Qué es y por qué elegir HubSpot? ¿Qué es el Marketing Automation? ¿Cómo captar Leads? ¿Qué es SEM? ¿Qué es SEO? ¿Por qué escoger una Agencia de Marketing? Recursos IA Expert Program ADM Program Webinars Recursos digitales Podcast Respuestas de Marketing Diccionario de Marketing 143 Tendencias y Predicciones de Marketing Digital 2026 Descargar ebook blog Nosotros Metodologías propias Valores y equipo Únete a nosotros Sala de prensa Servicios Content Inbound Marketing Influencer Marketing Video Marketing Redes Sociales Data Inteligencia Artificial Data Science & BI Data Analytics Data Integration Google Analytics 4 Technology Account B

## Fuente 4: Proyecto CRM pasos, consejos y ejemplos de software crm
URL: https://www.appvizer.es/revista/relacion-cliente/software-crm/proyecto-crm
Resumen buscador: ¿Cómo puede poner en marcha un proyecto CRM eficaz y convertirlo en un motor de rendimiento para su empresa? Aquí tiene nuestros consejos sobre las distintas etapas y los puntos a los que debe prestar atención.
Extracto: Proyecto CRM ✅ pasos, consejos y ejemplos de software crm Appvizer , el experto que encuentra su software profesional","HOME.LATEST_ARTICLES":"Últimos artículos","HOME.SEE_ALL_ARTICLES":"Ver todos los artículos","HOME.RESOURCES":"Recursos","HOME.SEE_ALL_RESOURCES":"Ver todos los recursos","HOME.MOST_VIEWED":"Los más consultados","HOME.TOP_CATEGORY":"Categorías principales","HOME.SOFTWARE_PRESENTATION.TITLE":"Software del momento","HOME.SOFTWARE_CATEGORIES":"Categorías de software","HOME.SOFTWARE_CATEGORY":"Software de {title}","HOME.SCROLL_LABEL":"Encuentre el software adecuado para usted","HOME.DESKTOP_SUB_BASELINE":"Nuestra IA diseñada para profesionales recomienda las herramientas SaaS adecuadas , gracias a miles de análisis de Appvizer y contenidos de expertos.","HOME.MOBILE_SUB_BASELINE":"Nuestra IA diseñada para profesionales recomienda las herramientas SaaS adecuadas .","HOME.ASK_INFO":"Cuanto más precisa sea su pregunta, mejor podrá responderle nuestra IA (varias líneas con shift + enter ).","NOT_FOUND.META.TITLE":"Appvizer - Página no encontrada","ARTICLE.TAGS.GUEST":"Análisis de experto","ARTICLE.TAGS.HOW_TO":"Consejos","ARTICLE.TAGS.DEFINITION":"Definición","ARTICLE.TAGS.WHITE_PAPER":"Libro blanco","ARTICLE.TAGS.SOFTWARE":"Software","ARTICLE.TAGS.SOFTWARE_COMPARISON":"Comparativa de software","ARTICLE.TAGS.NEWS":"Actualidad","ARTICLE.TAGS.MODEL":"Modelo","ARTICLE.TAG

```