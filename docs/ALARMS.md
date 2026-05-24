# Alarmas

## Que hacen

Las alarmas permiten pedir al gestor que recuerde algo mas tarde. El gestor detecta peticiones como:

- `Avisame dentro de diez minutos para revisar el correo`
- `Recuerdame dentro de media hora preparar el informe`
- `Avisame dentro de dos horas que llame al proveedor`
- `Pon una alarma a las 17:30 para revisar la entrega`
- `Avisame a las 17 y 30 de que prepare la reunion`

El gestor no programa la alarma directamente sin confirmacion. Primero responde con:

`He entendido... Propongo programar una alarma... ¿Quieres que lo haga?`

Despues se confirma con:

- `si`
- `si, hazlo`
- `vale`
- `adelante`

## Entrega de avisos

El servidor es el responsable de vigilar las alarmas cada pocos segundos. Cuando una alarma vence:

- marca la alarma como entregada
- genera voz
- reproduce el aviso por el altavoz del ordenador
- envia el texto por Telegram
- envia el audio por Telegram

La ventana Tkinter ya no consume alarmas por su cuenta, para evitar que una alarma se marque como entregada antes de avisar por Telegram.

## Consultar alarmas

Puedes pedir:

- `Que alarmas hay`
- `Dime las alarmas pendientes`
- `Lee los recordatorios`
- `Muestra los avisos`

## Cancelar alarmas

Primero consulta la lista y luego cancela por numero:

- `Cancela la alarma 1`
- `Borra el aviso 2`
- `Elimina el recordatorio 3`

## Modificar alarmas

Tambien se modifican por numero:

- `Pospone la alarma 1 media hora`
- `Cambia la alarma 2 dentro de diez minutos`
- `Modifica la alarma 1 texto revisar el informe de compras`

## Archivo legible

El gestor mantiene un resumen en:

`assistant/alarms.md`

Ese archivo se puede abrir o pedir al gestor que lo lea como contexto.
