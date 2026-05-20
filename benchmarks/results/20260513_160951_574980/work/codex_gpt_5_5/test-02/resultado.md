Voy a leer el CSV local, filtrar contactos de Madrid con prioridad alta y devolver la lista con los campos pedidos.

El archivo tiene columnas directas para ciudad y prioridad. Ahora extraigo solo `Madrid` + `alta` y selecciono nombre, empresa, rol y email.

La primera extracción falló por interpolación de `$_.` en el comando anidado de PowerShell; repito el filtro escapando esa variable.

Contactos en Madrid con prioridad alta:

| Nombre | Empresa | Rol | Email |
|---|---|---|---|
| Ana Lopez | Nova Iberia | Directora Operaciones | ana.lopez@novaiberia.es |
| Hector Mora | FinanSys | Producto | hector.mora@finansys.es |
| Raquel Cano | Noda Labs | Data | raquel.cano@nodalabs.es |
| Ivan Duran | Cobalto | Seguridad | ivan.duran@cobalto.es |
| Noelia Castro | Clinica Centro | Administracion | noelia.castro@clinicacentro.es |
| Samuel Ibanez | Quantica | Analitica | samuel.ibanez@quantica.es |
| Alberto Saez | OmniPlus | Direccion | alberto.saez@omniplus.es |
| Esteban Lozano | Helixia | CTO | esteban.lozano@helixia.es |
