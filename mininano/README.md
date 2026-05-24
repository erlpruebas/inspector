# Mini Nano Bridge

Aplicación local con dos piezas:

- `app.py`: interfaz de escritorio en Tkinter y servidor local de puente.
- `index.html`: página abierta en el navegador que ejecuta Gemini Nano y responde a las peticiones de la app.
- `MiniNano.bat`: lanzador para abrirlo todo con doble clic.
- `server/`: servidor OpenAI-compatible separado para usar desde otros ordenadores.

## Cómo ejecutarlo

1. Abre una terminal en `D:\mininano`.
2. Lanza la app:

   ```powershell
   py app.py
   ```

   O, si prefieres doble clic, abre `MiniNano.bat`.

3. La app abrirá tu navegador en `http://127.0.0.1:8787/index.html`.
4. Si Chrome soporta Gemini Nano, deja esa pestaña abierta para que actúe como puente.
5. Escribe mensajes en la ventana de Tkinter. Las respuestas aparecerán arriba, como un chat normal.

## Prueba sin modelo real

Si quieres validar el cableado sin depender de Gemini Nano, abre:

```text
http://127.0.0.1:8787/index.html?mock=1
```

Ese modo simula el streaming y sirve para comprobar que el puente y la GUI funcionan.

También puedes lanzar el escritorio en modo prueba con:

```powershell
py app.py --mock
```

O con doble clic:

```text
MiniNano.bat mock
```

## Qué significa `mock`

`mock` no es Gemini Nano real. Es un simulador local que devuelve una respuesta falsa pero con el mismo formato de eventos que usarías con el modelo real. Sirve para comprobar tres cosas:

- que la app de Tkinter envía peticiones,
- que `index.html` recibe el trabajo,
- que la respuesta vuelve por el puente en trozos, igual que un streaming.

En la prueba que hicimos, el navegador emitió `started`, varios `delta` y un `done`, que es justo lo que necesitas para validar el flujo.

## Servidor OpenAI-compatible

Si lo que quieres es la versión que acepta llamadas desde otros clientes, entra en la carpeta `server` y usa:

```powershell
cd D:\mininano\server
py server.py
```

O abre `MiniNanoServer.bat`.

## Notas

- Si `py app.py` dice que el puerto está ocupado, cierra el servidor viejo que estaba sirviendo `D:\mininano`.
- Si Chrome no tiene activa la API local, activa las flags experimentales en `chrome://flags/` y reinicia.
- Revisa `chrome://on-device-internals` si necesitas comprobar el estado del modelo.
