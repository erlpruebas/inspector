# Informe de incidencias de Clinica Centro

Elabora un informe de incidencias y oportunidades para Clinica Centro usando notas, emails y contactos.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/notas_voz.jsonl`
- `assistant_synthetic/emails_hilos.md`
- `assistant_synthetic/contactos_50.csv`

Usa esas rutas relativas cuando necesites leer datos locales.

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

### assistant_synthetic\notas_voz.jsonl
```text
{"id": "VN-001", "timestamp": "2026-05-03 08:12", "transcript": "Recordar llamar a Noelia de Clinica Centro antes del jueves para confirmar demo del modulo de pagos."}
{"id": "VN-002", "timestamp": "2026-05-03 09:40", "transcript": "Enviar a Luis de Delta Equipos el CSV actualizado de monitores; falta incluir descuento del 4 por ciento."}
{"id": "VN-003", "timestamp": "2026-05-03 11:18", "transcript": "Comprar billete para Barcelona el dia 18 si Xavier confirma la reunion de Barna Health."}
{"id": "VN-004", "timestamp": "2026-05-04 07:55", "transcript": "Preparar minuta para Sergio Campos con riesgos de seguridad y coste de auditoria."}
{"id": "VN-005", "timestamp": "2026-05-04 12:03", "transcript": "Pedir a Elena Vidal las facturas de abril que no aparecen en el banco."}
{"id": "VN-006", "timestamp": "2026-05-05 10:34", "transcript": "Crear tarea para revisar contrato de IberLegal; David pidio respuesta antes del 12."}
{"id": "VN-007", "timestamp": "2026-05-05 17:10", "transcript": "Agendar seguimiento con Marta Ruiz el martes a las cuatro por el tema de administracion."}
{"id": "VN-008", "timestamp": "2026-05-06 08:05", "transcript": "No olvidar que Ana Lopez prefiere recibir informes en PDF y resumen ejecutivo corto."}
{"id": "VN-009", "timestamp": "2026-05-06 14:29", "transcript": "Buscar alternativa barata a herramienta de encuestas para GreenBox."}
{"id": "VN-010", "timestamp": "2026-05-07 09:00", "transcript": "Llamar a Tomas de Zenit Food por pedido de licencias y confirmar direccion fiscal."}
{"id": "VN-011", "timestamp": "2026-05-07 15:12", "transcript": "Enviar agenda de implantacion a Laura Marin; incluir hito de formacion el dia 22."}
{"id": "VN-012", "timestamp": "2026-05-08 08:43", "transcript": "Revisar gastos de marzo porque hay dos cargos duplicados de hotel."}
{"id": "VN-013", "timestamp": "2026-05-08 13:20", "transcript": "Poner recordatorio para renovar certificado SSL de Cobalto antes del 28."}
{"id": "VN-014", "timestamp": "2026-05-09 10:02", "transcript": "Preparar comparativa OpenRouter contra Gemini para tareas de ofimatica."}
{"id": "VN-015", "timestamp": "2026-05-09 16:44", "transcript": "Enviar email amable a Paula Ferrer, no ha contestado la propuesta de BravoSoft."}
{"id": "VN-016", "timestamp": "2026-05-10 09:16", "transcript": "Cruzar pagos de Norte SA con facturas, creo que falta una de 847 con cincuenta."}
{"id": "VN-017", "timestamp": "2026-05-10 11:52", "transcript": "Crear lista de contactos prioritarios de Madrid con nivel alta."}
{"id": "VN-018", "timestamp": "2026-05-10 19:30", "transcript": "Investigar si Apple ha subido mas que Microsoft en los ultimos seis meses."}
{"id": "VN-019", "timestamp": "2026-05-11 08:25", "transcript": "Preparar informe mensual de incidencias: incluir Clinica Centro y facturacion."}
{"id": "VN-020", "timestamp": "2026-05-11 10:00", "transcript": "Recordar reservar sala para reunion interna del viernes a las nueve y media."}

```