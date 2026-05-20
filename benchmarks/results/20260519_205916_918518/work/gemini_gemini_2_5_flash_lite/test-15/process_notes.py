import csv
import json
from io import StringIO

# --- Input data from previous tool calls ---
contacts_csv_data = """nombre,email,telefono,ciudad,empresa,rol,tipo,prioridad
PERSON_0069,EMAIL_0055,PHONE_0062,Madrid,PERSON_0068,PERSON_0067,cliente,alta
PERSON_0066,EMAIL_0054,PHONE_0061,Valencia,PERSON_0065,Compras,proveedor,media
PERSON_0064,EMAIL_0053,PHONE_0060,Sevilla,Clinica Sol,Administracion,cliente,alta
PERSON_0063,EMAIL_0052,PHONE_0059,Bilbao,Logimedit,Logistica,partner,media
PERSON_0062,EMAIL_0051,PHONE_0058,A Coruna,PERSON_0061,Finanzas,cliente,alta
PERSON_0060,EMAIL_0050,PHONE_0057,Zaragoza,Innotek,CTO,cliente,alta
PERSON_0059,EMAIL_0049,PHONE_0056,Malaga,BravoSoft,Ventas,prospecto,media
PERSON_0058,EMAIL_0048,PHONE_0055,Madrid,IberLegal,Legal,proveedor,media
PERSON_0057,EMAIL_0047,PHONE_0054,Barcelona,GreenBox,Marketing,cliente,baja
PERSON_0056,EMAIL_0046,PHONE_0053,Murcia,MetalSur,Gerencia,cliente,alta
PERSON_0055,EMAIL_0045,PHONE_0052,Vigo,AquaNet,Soporte,cliente,media
PERSON_0054,EMAIL_0044,PHONE_0051,Madrid,FinanSys,Producto,partner,alta
PERSON_0053,EMAIL_0043,PHONE_0050,Cadiz,PERSON_0052,Direccion,cliente,alta
PERSON_0051,EMAIL_0042,PHONE_0049,Valladolid,Tecnoria,IT,proveedor,media
PERSON_0050,EMAIL_0041,PHONE_0048,Santander,PERSON_0049,Compras,cliente,media
PERSON_0048,EMAIL_0040,PHONE_0047,Madrid,Consultia,Consultor,partner,baja
PERSON_0047,EMAIL_0039,PHONE_0046,Granada,BioCentro,Calidad,cliente,alta
PERSON_0046,EMAIL_0038,PHONE_0045,Barcelona,UrbanLift,Operaciones,cliente,media
PERSON_0045,EMAIL_0037,PHONE_0044,Madrid,Noda Labs,Data,prospecto,alta
PERSON_0044,EMAIL_0036,PHONE_0043,Palma,MediaTres,Cuentas,cliente,baja
PERSON_0043,EMAIL_0035,PHONE_0042,Barcelona,PERSON_0042,Retail,cliente,alta
PERSON_0041,EMAIL_0034,PHONE_0041,Oviedo,Ferrovia,Compras,proveedor,media
PERSON_0040,EMAIL_0033,PHONE_0040,Madrid,Kairon,People,cliente,media
PERSON_0039,EMAIL_0032,PHONE_0039,Valencia,MintCloud,Cloud,partner,alta
PERSON_0038,EMAIL_0031,PHONE_0038,Alicante,PuraVida,Expansion,prospecto,media
PERSON_0037,EMAIL_0030,PHONE_0037,Madrid,Cobalto,Seguridad,proveedor,alta
PERSON_0036,EMAIL_0029,PHONE_0036,Sevilla,PERSON_0035,Direccion,cliente,alta
PERSON_0034,EMAIL_0028,PHONE_0035,Barcelona,Aurea,Finanzas,cliente,media
PERSON_0033,EMAIL_0027,PHONE_0034,Bilbao,Northwind ES,Ventas,cliente,alta
PERSON_0032,EMAIL_0026,PHONE_0033,Madrid,Argentalia,Inversiones,prospecto,media
PERSON_0001,EMAIL_0025,PHONE_0032,Madrid,ORG_0005,Administracion,cliente,alta
PERSON_0031,EMAIL_0024,PHONE_0031,Valencia,Navilux,Operaciones,cliente,media
PERSON_0030,EMAIL_0023,PHONE_0030,Malaga,PixelArte,Diseno,proveedor,baja
PERSON_0029,EMAIL_0022,PHONE_0029,Madrid,Quantica,Analitica,partner,alta
PERSON_0028,EMAIL_0021,PHONE_0028,Zaragoza,TransMed,Logistica,cliente,media
PERSON_0027,EMAIL_0020,PHONE_0027,Barcelona,PERSON_0026,Compras,cliente,alta
PERSON_0025,EMAIL_0019,PHONE_0026,Madrid,RedNova,Marketing,prospecto,media
PERSON_0024,EMAIL_0018,PHONE_0025,Barcelona,Barna Health,IT,cliente,alta
PERSON_0023,EMAIL_0017,PHONE_0024,Toledo,SerConta,Contabilidad,proveedor,media
PERSON_0022,EMAIL_0016,PHONE_0023,Madrid,OmniPlus,Direccion,cliente,alta
PERSON_0021,EMAIL_0015,PHONE_0022,Gijon,Vetor,Soporte,cliente,baja
PERSON_0020,EMAIL_0014,PHONE_0021,Sevilla,SolarDesk,Operaciones,cliente,alta
PERSON_0019,EMAIL_0013,PHONE_0020,Valencia,BlueCargo,Logistica,cliente,media
PERSON_0018,EMAIL_0012,PHONE_0019,Madrid,Helixia,CTO,partner,alta
PERSON_0017,EMAIL_0011,PHONE_0018,Murcia,OptiRed,Ventas,prospecto,media
PERSON_0016,EMAIL_0010,PHONE_0017,Valladolid,NeoTaller,Gerencia,cliente,alta
PERSON_0015,EMAIL_0009,PHONE_0016,Madrid,MarketUno,Marketing,cliente,media
PERSON_0014,EMAIL_0008,PHONE_0015,Malaga,Alboran,Legal,proveedor,media
PERSON_0013,EMAIL_0007,PHONE_0014,Barcelona,Civitas,Producto,cliente,alta
PERSON_0012,EMAIL_0006,PHONE_0013,Salamanca,PERSON_0011,Direccion,cliente,media
"""

voice_notes_jsonl_data = """
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
"""

# Parse CSV
contacts = []
csvfile = StringIO(contacts_csv_data)
reader = csv.DictReader(csvfile)
for row in reader:
    contacts.append({
        "nombre": row["nombre"],
        "email": row["email"],
        "empresa": row["empresa"]
    })

# Parse JSONL
voice_notes = []
for line in StringIO(voice_notes_jsonl_data):
    if line.strip(): # Ignore empty lines
        data = json.loads(line)
        voice_notes.append({
            "id": data["id"],
            "transcript": data["transcript"]
        })

# Cross-reference and build results
results = []
for note in voice_notes:
    transcript = note["transcript"]
    for contact in contacts:
        # Check if the contact's name is in the transcript.
        # This check is case-sensitive and exact for the name string.
        # We use a simple substring check here.
        if contact["nombre"] in transcript:
            results.append({
                "tarea": transcript,
                "persona": contact["nombre"],
                "empresa": contact["empresa"],
                "email": contact["email"]
            })

# Format as Markdown table
markdown_output = "| Tarea | Persona | Empresa | Email |
"
markdown_output += "|---|---|---|---|
"

for row in results:
    # Sanitize potential markdown in transcript to avoid breaking table
    escaped_transcript = str(row["tarea"]).replace('|', '\|')
    escaped_persona = str(row["persona"]).replace('|', '\|')
    escaped_empresa = str(row["empresa"]).replace('|', '\|')
    escaped_email = str(row["email"]).replace('|', '\|')
    markdown_output += f"| {escaped_transcript} | {escaped_persona} | {escaped_empresa} | {escaped_email} |
"

# Write to file
output_file_path = "resultado.md"
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(markdown_output)

print(f"Successfully generated {output_file_path}")
