We need to read contactos_50.csv, filter rows where tipo = "proveedor". Then output CSV with columns: Nombre, Empresa, Rol, Email, Ciudad, Prioridad. The original columns: nombre, email, telefono, ciudad, empresa, rol, tipo, prioridad. So we need to map: Nombre -> nombre, Empresa -> empresa, Rol -> rol, Email -> email, Ciudad -> ciudad, Prioridad -> prioridad. Keep order as specified.

We need to output CSV (no markdown, no code block). Just plain CSV lines, with header line.

Let's parse the data.

List rows with tipo=proveedor:

From data:

- Luis Martin,luis.martin@deltaequipos.es,+34 600 100 002,Valencia,Delta Equipos,Compras,proveedor,media
- David Navarro,david.navarro@iberlegal.es,+34 600 100 008,Madrid,IberLegal,Legal,proveedor,media
- Marcos Gil,marcos.gil@tecnoria.es,+34 600 100 014,Valladolid,Tecnoria,IT,proveedor,media
- Daniel Rios,daniel.rios@ferrovia.es,+34 600 100 022,Oviedo,Ferrovia,Compras,proveedor,media
- Ivan Duran,ivan.duran@cobalto.es,+34 600 100 026,Madrid,Cobalto,Seguridad,proveedor,alta
- Rocio Nieto,rocio.nieto@pixelarte.es,+34 600 100 033,Malaga,PixelArte,Diseno,proveedor,baja
- Yolanda Cruz,yolanda.cruz@serconta.es,+34 600 100 039,Toledo,SerConta,Contabilidad,proveedor,media
- Jaime Pastor,jaime.pastor@alboran.es,+34 600 100 048,Malaga,Alboran,Legal,proveedor,media

Check also any other proveedor: Let's scan again:

Row list:
