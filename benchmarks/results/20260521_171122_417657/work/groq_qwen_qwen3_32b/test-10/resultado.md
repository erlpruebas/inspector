<think>
Okay, let's tackle this problem. The user wants me to create a CSV of suppliers from the given contact_50.csv file. The output should be in a markdown file called resultado.md, but the actual content should just be the CSV without any markdown formatting.

First, I need to read the contact_50.csv file. The columns in the original CSV are nombre, email, telefono, ciudad, empresa, rol, tipo, and prioridad. The task is to extract only the suppliers (proveedores), which are identified by the 'tipo' column having the value 'proveedor'. 

Looking at the sample data, there's one entry for Luis Martin with tipo 'proveedor' and another for David Navarro also as 'proveedor'. So those two should be included in the output. The other entries are clients, partners, or prospects, so they should be excluded.

The required columns for the output CSV are Nombre, Empresa, Rol, Email, Ciudad, and Prioridad. I need to map these to the original columns. The original 'nombre' becomes 'Nombre', 'empresa' is 'Empresa', 'rol' is 'Rol', 'email' is 'Email', 'ciudad' is 'Ciudad', and 'prioridad' is 'Prioridad'. 

So I'll filter the rows where 'tipo' is 'proveedor', then select the relevant columns and rename them as specified. Then, I'll format the data into a CSV string without using markdown. The final step is to write this CSV into resultado.md, but since the user wants only the content, I'll just output the CSV directly.

Let me double-check the data. Luis Martin is from Delta Equipos, role Compras, email luis.martin@deltaequipos.es, Valencia, prioridad media. David Navarro is from IberLegal, role Legal, email david.navarro@iberlegal.es, Madrid, prioridad media. Both are proveedores. That's two entries. 

I need to make sure the CSV headers are correct and the data matches. No other entries should be included. The order of the columns should be Nombre, Empresa, Rol, Email, Ciudad, Prioridad. Let me structure the CSV accordingly.
</think>

Nombre,Empresa,Rol,Email,Ciudad,Prioridad
Luis Martin,Delta Equipos,Compras,luis.martin@deltaequipos.es,Valencia,media
David Navarro,IberLegal,Legal,david.navarro@iberlegal.es,Madrid,media
