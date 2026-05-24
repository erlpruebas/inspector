# Mini Nano Server

Servidor local OpenAI-compatible que usa una pestana del navegador como motor de Gemini Nano y puede publicarse con Cloudflare Tunnel.

## Archivos

- `server.py`: servidor HTTP local y API compatible.
- `bridge.html`: pestana local que ejecuta Gemini Nano y procesa peticiones.
- `index.html`: chat web remoto que consume `/v1/chat/completions`.
- `MiniNanoServer.bat`: lanza el servidor local.
- `Tunnel.bat`: levanta el servidor y abre Cloudflare Tunnel.
- `ApiChatTk.py`: cliente de escritorio para probar cualquier API OpenAI-compatible.
- `ApiChatTk.bat`: lanza el cliente de escritorio.

## Uso local

```powershell
cd D:\mininano\server
py server.py
```

O abre `MiniNanoServer.bat`.

Esto levanta el servidor en `http://127.0.0.1:8788`, abre la pestana puente y deja listos:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `GET /chat`
- `GET /bridge.html`

## Acceso por internet

Para crear un tunel temporal:

```powershell
cd D:\mininano\server
.\Tunnel.bat
```

Cuando Cloudflare muestre una URL como `https://algo.trycloudflare.com`, esa URL sirve para dos cosas:

- abrir el chat web remoto desde otro ordenador,
- usarla como Base URL de una API compatible con OpenAI.

## Seguridad

Antes de abrir el tunel puedes proteger la API con una clave:

```powershell
set MINI_NANO_API_KEY=pon-una-clave-larga
.\Tunnel.bat
```

En el chat web pega esa clave en `Clave API opcional`.

En clientes OpenAI-compatible usa:

```text
Base URL: https://algo.trycloudflare.com/v1
API Key: pon-una-clave-larga
Model: gemini-nano-local
```

## Modo mock

Para probar sin Gemini Nano real:

```powershell
py server.py --mock
```

O:

```text
MiniNanoServer.bat mock
```

`mock` simula respuestas y permite validar el chat, la API y el streaming.

## Cliente Tkinter

Para probar la API desde una ventana de escritorio:

```powershell
cd D:\mininano\server
.\ApiChatTk.bat
```

Valores recomendados:

```text
Base URL local: http://127.0.0.1:8788/v1
Base URL Cloudflare: https://TU-URL.trycloudflare.com/v1
Model: gemini-nano-local
API Key: local
```

## Volver a abrir todo

1. Ejecuta `MiniNanoServer.bat`.
2. Espera a que se abra `bridge.html` en Chrome.
3. Deja abierta esa pestana.
4. Ejecuta `Tunnel.bat` si necesitas acceso desde fuera de tu red.
5. Ejecuta `ApiChatTk.bat` para probar la API desde una interfaz de escritorio.

## Nota

La pestana `bridge.html` tiene que quedar abierta en el navegador de la misma maquina. La API puede publicarse por internet, pero el modelo vive dentro del navegador local.
