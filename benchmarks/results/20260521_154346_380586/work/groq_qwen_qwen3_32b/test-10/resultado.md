<think>
Okay, let's tackle this problem. The user wants me to create a CSV of suppliers from the given contact_50.csv file. The columns needed are Nombre, Empresa, Rol, Email, Ciudad, and Prioridad. 

First, I need to read the contact_50.csv file. The file has columns like nombre, email, telefono, ciudad, empresa, rol, tipo, and prioridad. The task is to filter out only the rows where the tipo is 'proveedor' and then select the required columns.

Wait, the user mentioned "proveedores", so I should check the 'tipo' column for entries that are 'proveedor'. Let me look at the sample data. For example, Luis Martin has tipo 'proveedor', David Navarro is 'proveedor', Marcos Gil is 'proveedor', Rocio Nieto is 'proveedor', Yolanda Cruz is 'proveedor', and Jaime Pastor is 'proveedor'. So there are six entries that fit.

Next, I need to map the columns. The original CSV has 'nombre', 'empresa', 'rol', 'email', 'ciudad', and 'prioridad'. The target columns are the same names but in Spanish. So the mapping is straightforward. I just need to select these columns for the rows where tipo is 'proveedor'.

I should also ensure that the order of the columns in the output CSV is Nombre, Empresa, Rol, Email, Ciudad, Prioridad. Let me check the order in the sample data. The original order is nombre, email, telefono, ciudad, empresa, rol, tipo, prioridad. So the required columns are scattered, but I can rearrange them as needed.

Now, I need to write the filtered data into a new CSV file. The output should be in the same directory, and the user wants the final content in resultado.md. Wait, the user specified the output as resultado.md, but the content is a CSV. The instruction says if the output is CSV, JSON, or ICS, don't use markdown or code blocks. So the final output should be plain text CSV without any markdown formatting.

Let me verify each entry. For example, Luis Martin: Nombre is Luis Martin, Empresa is Delta Equipos, Rol is Compras, Email is luis.martin@deltaequipos.es, Ciudad is Valencia, Prioridad is media. That's correct. Similarly, David Navarro's entry should be included as he's a proveedor.

I need to make sure there are no typos in the data. Let me cross-check each of the six entries. Once confirmed, arrange them in the correct column order and format the CSV properly with commas and line breaks. No headers are mentioned, but typically CSVs include headers. Wait, the user didn't specify whether to include headers. Looking back at the problem statement, the example shows the contact_50.csv has headers. The user's instruction says "crea un CSV de proveedores con columnas...", so I should include the headers in the output.

So the final CSV should start with the headers: Nombre,Empresa,Rol,Email,Ciudad,Prioridad followed by the six rows. Let me compile that now.
</think>

Nombre,Empresa,Rol,Email,Ciudad,Prioridad
Luis Martin,Delta Equipos,Compras,luis.martin@deltaequipos.es,Valencia,media
David Navarro,IberLegal,Legal,david.navarro@iberlegal.es,Madrid,media
Marcos Gil,Tecnoria,IT,marcos.gil@tecnoria.es,Valladolid,media
Rocio Nieto,PixelArte,Diseno,rocio.nieto@pixelarte.es,Malaga,baja
Yolanda Cruz,SerConta,Contabilidad,yolanda.cruz@serconta.es,Toledo,media
Jaime Pastor,Alboran,Legal,jaime.pastor@alboran.es,Malaga,media
