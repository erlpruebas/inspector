Voy a leer el CSV y filtrar los contactos de Madrid para sacar una lista prioritaria con nombre, empresa, rol y email. Primero reviso la estructura del archivo para no asumir columnas.

Ya tengo el criterio. Ahora voy a inspeccionar el CSV para identificar columnas y filtrar solo los contactos de Madrid con prioridad alta, sin inventar ningún campo.

La estructura ya está clara: hay columnas de ciudad y prioridad, así que el filtro es directo. Voy a extraer solo `ciudad = Madrid` y `prioridad = alta` y luego devolver el resultado limpio.

He filtrado `assistant_synthetic/contactos_50.csv` por `ciudad = Madrid` y `prioridad = alta`.

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

Si quieres, también puedo devolvértela en CSV o Excel.
