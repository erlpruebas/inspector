const fs = require("fs");
const http = require("http");
const path = require("path");
const { spawn } = require("child_process");
const { createAssistantCore } = require(path.join(__dirname, "assistant", "core"));

const ROOT = __dirname;
function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq < 0) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!key) continue;
    if (process.env[key] == null || process.env[key] === "") {
      process.env[key] = value;
    }
  }
}

loadEnvFile(path.join(ROOT, ".env"));

const PUBLIC_DIR = path.join(ROOT, "public");
const PROFILE_DIR = path.join(ROOT, ".chrome-profile");
const PORT = Number(process.env.PORT || 8787);
const DEBUG_PORT = Number(process.env.CHROME_DEBUG_PORT || 9333);
const CHROME_PATH = process.env.CHROME_PATH || "";
const MAIN_CHROME_USER_DATA = process.env.CHROME_USER_DATA || "";

let promptQueue = Promise.resolve();
let workerId = 0;

function sendJson(res, status, body) {
  const text = JSON.stringify(body, null, 2);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(text);
}

function readRequestJson(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 50_000_000) {
        reject(new Error("Request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => {
      if (!body.trim()) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(new Error("Invalid JSON body"));
      }
    });
    req.on("error", reject);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            reject(error);
          }
        });
      })
      .on("error", reject);
  });
}

function parseWsMessage(event) {
  const data = event && "data" in event ? event.data : event;
  if (typeof data === "string") return JSON.parse(data);
  if (data instanceof ArrayBuffer) return JSON.parse(Buffer.from(data).toString("utf8"));
  if (Buffer.isBuffer(data)) return JSON.parse(data.toString("utf8"));
  return JSON.parse(String(data));
}

function cdpSend(ws, method, params = {}) {
  const id = cdpSend.nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      ws.removeEventListener("message", onMessage);
      reject(new Error(`Chrome DevTools timeout for ${method}`));
    }, 180_000);

    function onMessage(event) {
      const message = parseWsMessage(event);
      if (message.id !== id) return;
      clearTimeout(timeout);
      ws.removeEventListener("message", onMessage);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    }

    ws.addEventListener("message", onMessage);
  });
}
cdpSend.nextId = 1;

function enqueuePrompt(work) {
  const run = promptQueue.then(work, work);
  promptQueue = run.catch(() => {});
  return run;
}

function jsString(value) {
  return JSON.stringify(String(value ?? ""));
}

async function getNanoStatus() {
  if (!CHROME_PATH) {
    return {
      href: null,
      secureContext: false,
      apiPresent: false,
      typeofLanguageModel: "undefined",
      availability: "disabled",
      params: null,
      error: "Chrome/Gemini Nano bridge disabled. Set CHROME_PATH inside .env to use the lab bridge.",
    };
  }
  return runInChromeWorker(`(async () => {
    const LM = globalThis.LanguageModel || globalThis.ai?.languageModel || globalThis.ai?.LanguageModel;
    const status = {
      href: location.href,
      secureContext: isSecureContext,
      apiPresent: Boolean(LM),
      typeofLanguageModel: typeof globalThis.LanguageModel,
      availability: null,
      params: null,
      error: null
    };
    try {
      if (LM?.availability) status.availability = await LM.availability();
      if (LM?.params) status.params = await LM.params();
    } catch (error) {
      status.error = String(error?.stack || error?.message || error);
    }
    return status;
  })()`);
}

async function promptNano({ prompt, systemPrompt }) {
  if (!prompt || typeof prompt !== "string") {
    throw new Error("Missing prompt");
  }

  return enqueuePrompt(async () => {
    return promptNanoInWorker({ prompt, systemPrompt });
  });
}

async function runInChromeWorker(expression) {
  if (!CHROME_PATH) {
    throw new Error("Chrome/Gemini Nano bridge disabled. Set CHROME_PATH inside .env to use it.");
  }
  const id = workerId++;
  const workerProfile = path.join(ROOT, `.chrome-worker-${Date.now()}-${id}`);
  const workerDebugPort = DEBUG_PORT + 1 + (id % 1000);
  fs.mkdirSync(workerProfile, { recursive: true });

  const localStateSource = MAIN_CHROME_USER_DATA ? path.join(MAIN_CHROME_USER_DATA, "Local State") : "";
  if (localStateSource && fs.existsSync(localStateSource)) {
    fs.copyFileSync(localStateSource, path.join(workerProfile, "Local State"));
  }

  for (const name of ["OptGuideOnDeviceModel", "optimization_guide_model_store"]) {
    if (!MAIN_CHROME_USER_DATA) break;
    const source = path.join(MAIN_CHROME_USER_DATA, name);
    const target = path.join(workerProfile, name);
    if (fs.existsSync(source) && !fs.existsSync(target)) {
      fs.symlinkSync(source, target, "junction");
    }
  }

  const args = [
    `--user-data-dir=${workerProfile}`,
    `--remote-debugging-port=${workerDebugPort}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--enable-features=OptimizationGuideOnDeviceModel,PromptAPIForGeminiNano,AIPromptAPIMultimodalInput",
    `http://127.0.0.1:${PORT}/bridge.html`,
  ];

  const proc = spawn(CHROME_PATH, args, {
    detached: false,
    stdio: "ignore",
  });

  let ws;
  try {
    let pages;
    let page;
    for (let i = 0; i < 100; i += 1) {
      try {
        pages = await getJson(`http://127.0.0.1:${workerDebugPort}/json`);
        if (Array.isArray(pages) && pages.length) {
          page =
            pages.find((item) => item.url === `http://127.0.0.1:${PORT}/bridge.html`) ||
            pages.find((item) => item.url && item.url.startsWith(`http://127.0.0.1:${PORT}/`));
          if (page) break;
        }
      } catch {
        // Worker Chrome is still starting.
      }
      await sleep(300);
    }

    if (!Array.isArray(pages) || !pages.length) {
      throw new Error("Chrome worker did not expose a DevTools page");
    }

    page = page || pages.find((item) => item.type === "page") || pages[0];
    ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.addEventListener("open", resolve, { once: true });
      ws.addEventListener("error", reject, { once: true });
    });
    await cdpSend(ws, "Runtime.enable");
    if (page.url !== `http://127.0.0.1:${PORT}/bridge.html`) {
      await cdpSend(ws, "Page.enable");
      await cdpSend(ws, "Page.navigate", {
        url: `http://127.0.0.1:${PORT}/bridge.html`,
      });
      for (let i = 0; i < 50; i += 1) {
        const locationResult = await cdpSend(ws, "Runtime.evaluate", {
          expression: "location.href",
          returnByValue: true,
        });
        if (locationResult.result?.value === `http://127.0.0.1:${PORT}/bridge.html`) {
          break;
        }
        await sleep(200);
      }
    }
    await cdpSend(ws, "Page.bringToFront");
    await cdpSend(ws, "Input.dispatchMouseEvent", {
      type: "mousePressed",
      x: 24,
      y: 24,
      button: "left",
      clickCount: 1,
    });
    await cdpSend(ws, "Input.dispatchMouseEvent", {
      type: "mouseReleased",
      x: 24,
      y: 24,
      button: "left",
      clickCount: 1,
    });

    const result = await cdpSend(ws, "Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
      timeout: 240_000,
    });

    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.text || "Chrome worker evaluation failed");
    }
    return result.result.value;
  } finally {
    ws?.close?.();
    proc.kill?.();
    setTimeout(() => {
      for (const name of ["OptGuideOnDeviceModel", "optimization_guide_model_store"]) {
        fs.rm(path.join(workerProfile, name), { force: true }, () => {});
      }
      fs.rm(workerProfile, { recursive: true, force: true }, () => {});
    }, 1000);
  }
}

async function promptNanoInWorker({ prompt, systemPrompt }) {
  return runInChromeWorker(`(async () => {
        const LM = globalThis.LanguageModel || globalThis.ai?.languageModel || globalThis.ai?.LanguageModel;
        if (!LM) throw new Error("LanguageModel API is not available in Chrome");

        const availability = LM.availability ? await LM.availability() : "unknown";
        if (availability === "downloading" || availability === "downloadable") {
          const started = Date.now();
          while (Date.now() - started < 180000) {
            await new Promise((resolve) => setTimeout(resolve, 2000));
            const next = await LM.availability();
            if (next === "available") break;
          }
        }
        const options = {};
        const systemPrompt = ${jsString(systemPrompt)};
        if (systemPrompt) options.systemPrompt = systemPrompt;

        const session = await LM.create(options);
        try {
          const text = await session.prompt(${jsString(prompt)});
          return { model: "chrome-gemini-nano", availability, text };
        } finally {
          session.destroy?.();
        }
      })()`);
}

function messagesToPrompt(messages) {
  if (!Array.isArray(messages)) return "";
  return messages
    .map((message) => {
      const role = message.role || "user";
      const content = Array.isArray(message.content)
        ? message.content
            .map((part) => (typeof part === "string" ? part : part.text || ""))
            .join("\\n")
        : String(message.content ?? "");
      return `${role.toUpperCase()}: ${content}`;
    })
    .join("\\n\\n");
}

const assistantCore = createAssistantCore({
  rootDir: ROOT,
  promptNano,
  logger: console,
});

function extFromMime(mimeType) {
  const map = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
    "video/mp4": ".mp4",
  };
  return map[String(mimeType || "").toLowerCase()] || "";
}

async function handleAssistantMessage(body) {
  let audioPath = body.audioPath || null;
  let createdFile = null;

  if (!audioPath && body.audio?.base64) {
    const buffer = Buffer.from(String(body.audio.base64).split(",").pop() || "", "base64");
    const fileName = body.audio.name || `upload-${Date.now()}${extFromMime(body.audio.mimeType)}`;
    createdFile = await assistantCore.writeAudioBuffer({
      buffer,
      fileName,
      mimeType: body.audio.mimeType,
    });
    audioPath = createdFile.path;
  }

  const result = await assistantCore.processInboundMessage({
    source: body.source || "desktop",
    threadId: body.threadId || body.chatId || "default",
    chatId: body.chatId || body.threadId || "default",
    label: body.label || body.userName || body.source || "desktop",
    text: body.text || "",
    audioPath,
    files: Array.isArray(body.files) ? body.files : [],
    language: body.language || "es",
    preferGroq: body.preferGroq,
    synthesize: body.synthesize,
    userName: body.userName || "",
  });

  return {
    ...result,
    createdFile,
  };
}

async function telegramApi(token, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Telegram ${method} error ${response.status}: ${body}`);
  }
  return response.json();
}

async function telegramSendAudio(token, chatId, filePath, caption = "") {
  if (!token || !chatId || !filePath || !fs.existsSync(filePath)) return null;
  const bytes = await fs.promises.readFile(filePath);
  const form = new FormData();
  form.append("chat_id", String(chatId));
  if (caption) form.append("caption", String(caption).slice(0, 1024));
  form.append("audio", new Blob([bytes], { type: "audio/mpeg" }), path.basename(filePath));
  const response = await fetch(`https://api.telegram.org/bot${token}/sendAudio`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Telegram sendAudio error ${response.status}: ${body}`);
  }
  return response.json();
}

function getDefaultTelegramChatIds() {
  return [
    ...parseIdList(process.env.TELEGRAM_NOTIFY_CHAT_IDS),
    ...parseIdList(process.env.TELEGRAM_ALLOWED_CHAT_IDS || process.env.TELEGRAM_ALLOWED_CHAT_ID),
    ...parseIdList(process.env.TELEGRAM_ALLOWED_USER_IDS || process.env.TELEGRAM_ALLOWED_USER_ID),
  ];
}

function playLocalAudio(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return;
  const python = fs.existsSync(path.join(ROOT, ".venv", "Scripts", "python.exe"))
    ? path.join(ROOT, ".venv", "Scripts", "python.exe")
    : "python";
  const script = path.join(ROOT, "assistant", "play_audio.py");
  const child = spawn(python, [script, "--file", filePath], {
    cwd: ROOT,
    detached: true,
    stdio: "ignore",
    windowsHide: true,
  });
  child.unref();
}

async function notifyWithVoice({ source = "desktop", threadId = "default", label = "Inspector", text, telegramChatIds = [] }) {
  const speech = await assistantCore.synthesizeForThread({
    source,
    threadId,
    label,
    text,
  });
  if (speech?.path) {
    playLocalAudio(speech.path);
  }

  const token = process.env.TELEGRAM_BOT_TOKEN || "";
  const chatIds = [...new Set(telegramChatIds.filter(Boolean).map(String))];
  if (token && chatIds.length) {
    for (const chatId of chatIds) {
      try {
        await telegramApi(token, "sendMessage", {
          chat_id: chatId,
          text,
        });
        if (speech?.path) {
          await telegramSendAudio(token, chatId, speech.path);
        }
      } catch (error) {
        console.error("Telegram notify error:", error?.message || error);
      }
    }
  }
  return speech;
}

async function telegramDownload(token, fileId) {
  const fileInfo = await telegramApi(token, "getFile", { file_id: fileId });
  const filePath = fileInfo?.result?.file_path;
  if (!filePath) throw new Error("Telegram no devolvió file_path");
  const url = `https://api.telegram.org/file/bot${token}/${filePath}`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Telegram download error ${response.status}: ${body}`);
  }
  const arrayBuffer = await response.arrayBuffer();
  return {
    buffer: Buffer.from(arrayBuffer),
    fileName: path.basename(filePath),
    mimeType: response.headers.get("content-type") || guessTelegramMime(filePath),
  };
}

function guessTelegramMime(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const map = {
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
  };
  return map[ext] || "application/octet-stream";
}

function isAudioMime(mimeType, fileName = "") {
  const mime = String(mimeType || "").toLowerCase();
  const ext = path.extname(fileName || "").toLowerCase();
  return mime.startsWith("audio/") || [".ogg", ".oga", ".mp3", ".wav", ".m4a", ".webm", ".flac", ".aac", ".mpga", ".mpeg"].includes(ext);
}

function parseIdList(value) {
  return String(value || "")
    .split(/[,\s]+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function telegramAllowed(message) {
  const allowedUsers = parseIdList(process.env.TELEGRAM_ALLOWED_USER_IDS || process.env.TELEGRAM_ALLOWED_USER_ID);
  const allowedChats = parseIdList(process.env.TELEGRAM_ALLOWED_CHAT_IDS || process.env.TELEGRAM_ALLOWED_CHAT_ID);
  const userId = message.from?.id != null ? String(message.from.id) : "";
  const chatId = message.chat?.id != null ? String(message.chat.id) : "";

  if (!allowedUsers.length && !allowedChats.length) return true;
  if (allowedUsers.length && allowedUsers.includes(userId)) return true;
  if (allowedChats.length && allowedChats.includes(chatId)) return true;
  return false;
}

let telegramPollingStarted = false;
let alarmWatcherStarted = false;

async function handleTelegramUpdate(token, update) {
  const message = update.message || update.edited_message;
  if (!message) return;

  const chatId = message.chat?.id;
  if (!chatId) return;
  if (!telegramAllowed(message)) return;

  const userName =
    message.from?.username ||
    [message.from?.first_name, message.from?.last_name].filter(Boolean).join(" ") ||
    message.chat?.title ||
    "telegram";

  const text = message.text || message.caption || "";
  let audioPath = null;
  const files = [];

  if (message.voice?.file_id || message.audio?.file_id || message.document?.file_id || message.video?.file_id || message.photo?.length) {
    const photo = Array.isArray(message.photo) && message.photo.length ? message.photo[message.photo.length - 1] : null;
    const fileId =
      message.voice?.file_id ||
      message.audio?.file_id ||
      message.document?.file_id ||
      message.video?.file_id ||
      photo?.file_id;
    const file = await telegramDownload(token, fileId);
    if (message.document?.file_name) file.fileName = message.document.file_name;
    const saved = await assistantCore.writeInboxBuffer({
      ...file,
      source: "telegram",
      threadId: String(chatId),
      userName,
    });
    files.push(saved.path);
    if (message.voice?.file_id || message.audio?.file_id || isAudioMime(saved.mimeType, saved.fileName)) {
      audioPath = saved.path;
    }
  }

  const result = await handleAssistantMessage({
    source: "telegram",
    threadId: String(chatId),
    chatId: String(chatId),
    label: userName,
    userName,
    text,
    audioPath,
    files,
    language: "es",
    preferGroq: true,
  });

  await telegramApi(token, "sendMessage", {
    chat_id: chatId,
    text: result.reply,
  });
  if (result.speech?.path) {
    await telegramSendAudio(token, chatId, result.speech.path);
  }
}

async function startTelegramPolling() {
  const token = process.env.TELEGRAM_BOT_TOKEN || "";
  if (!token || telegramPollingStarted) return;
  telegramPollingStarted = true;
  let offset = 0;
  console.log("Telegram polling activado");

  (async function poll() {
    while (telegramPollingStarted) {
      try {
        const response = await fetch(`https://api.telegram.org/bot${token}/getUpdates`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            timeout: 30,
            offset,
            allowed_updates: ["message", "edited_message"],
          }),
        });
        if (!response.ok) {
          const body = await response.text();
          throw new Error(`Telegram getUpdates error ${response.status}: ${body}`);
        }
        const payload = await response.json();
        for (const update of payload.result || []) {
          offset = Math.max(offset, update.update_id + 1);
          try {
            await handleTelegramUpdate(token, update);
          } catch (error) {
            console.error("Telegram update error:", error?.message || error);
          }
        }
      } catch (error) {
        console.error("Telegram polling error:", error?.message || error);
        await sleep(3000);
      }
    }
  })();
}

function startAlarmWatcher() {
  if (alarmWatcherStarted) return;
  alarmWatcherStarted = true;
  console.log("Alarm watcher activado");

  setInterval(async () => {
    try {
      const due = assistantCore.getDueAlarms({ markDelivered: true });
      for (const alarm of due) {
        const text = `Aviso: ${alarm.task}`;
        const chatIds = new Set(getDefaultTelegramChatIds());
        if (alarm.source === "telegram" && alarm.threadId) chatIds.add(String(alarm.threadId));
        await notifyWithVoice({
          source: alarm.source || "desktop",
          threadId: alarm.threadId || "default",
          label: alarm.label || "Inspector",
          text,
          telegramChatIds: [...chatIds],
        });
      }
    } catch (error) {
      console.error("Alarm watcher error:", error?.message || error);
    }
  }, Number(process.env.ALARM_POLL_MS || 5000));
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://127.0.0.1:${PORT}`);
  const pathname = url.pathname === "/" ? "/index.html" : url.pathname;
  const resolved = path.normalize(path.join(PUBLIC_DIR, pathname));

  if (!resolved.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.readFile(resolved, (error, data) => {
    if (error) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }

    const extension = path.extname(resolved).toLowerCase();
    const contentTypes = {
      ".html": "text/html; charset=utf-8",
      ".css": "text/css; charset=utf-8",
      ".js": "text/javascript; charset=utf-8",
      ".json": "application/json; charset=utf-8",
    };
    res.writeHead(200, {
      "content-type": contentTypes[extension] || "application/octet-stream",
      "cache-control": "no-store",
    });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://127.0.0.1:${PORT}`);

    if (req.method === "GET" && url.pathname === "/api/status") {
      sendJson(res, 200, await getNanoStatus());
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/prompt") {
      const body = await readRequestJson(req);
      sendJson(res, 200, await promptNano(body));
      return;
    }

    if (req.method === "GET" && url.pathname === "/api/assistant/state") {
      sendJson(res, 200, assistantCore.getSnapshot());
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/assistant/message") {
      const body = await readRequestJson(req);
      sendJson(res, 200, await handleAssistantMessage(body));
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/assistant/transcribe") {
      const body = await readRequestJson(req);
      let audioPath = body.audioPath || null;
      let createdFile = null;
      if (!audioPath && body.audio?.base64) {
        const buffer = Buffer.from(String(body.audio.base64).split(",").pop() || "", "base64");
        const fileName = body.audio.name || `upload-${Date.now()}${extFromMime(body.audio.mimeType)}`;
        createdFile = await assistantCore.writeAudioBuffer({
          buffer,
          fileName,
          mimeType: body.audio.mimeType,
        });
        audioPath = createdFile.path;
      }
      if (!audioPath) throw new Error("Missing audio");
      const transcription = await assistantCore.transcribeAudio({
        filePath: audioPath,
        language: body.language || "es",
        preferGroq: body.preferGroq,
      });
      sendJson(res, 200, { transcription, createdFile });
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/assistant/speech") {
      const body = await readRequestJson(req);
      const speech = await assistantCore.synthesizeForThread({
        source: body.source || "desktop",
        threadId: body.threadId || "default",
        label: body.label || body.userName || body.source || "desktop",
        text: body.text || "",
        forceFull: Boolean(body.forceFull),
      });
      if (body.notifyTelegram) {
        const token = process.env.TELEGRAM_BOT_TOKEN || "";
        const chatIds = [...new Set(getDefaultTelegramChatIds())];
        if (token && chatIds.length) {
          const notifyText = body.notifyText || body.text || "";
          for (const chatId of chatIds) {
            try {
              await telegramApi(token, "sendMessage", {
                chat_id: chatId,
                text: notifyText,
              });
              if (speech?.path) {
                await telegramSendAudio(token, chatId, speech.path);
              }
            } catch (error) {
              console.error("Telegram notify error:", error?.message || error);
            }
          }
        }
      }
      sendJson(res, 200, { speech });
      return;
    }

    if (req.method === "GET" && url.pathname === "/api/assistant/alarms/due") {
      sendJson(res, 200, {
        alarms: assistantCore.getDueAlarms({ markDelivered: url.searchParams.get("deliver") === "1" }),
      });
      return;
    }

    if (req.method === "GET" && url.pathname === "/v1/models") {
      sendJson(res, 200, {
        object: "list",
        data: [{ id: "chrome-gemini-nano", object: "model", owned_by: "local-chrome" }],
      });
      return;
    }

    if (req.method === "POST" && url.pathname === "/v1/chat/completions") {
      const body = await readRequestJson(req);
      if (body.stream) {
        sendJson(res, 400, {
          error: {
            message: "Streaming is not implemented in this minimal prototype yet.",
            type: "unsupported_request",
          },
        });
        return;
      }

      const systemPrompt = Array.isArray(body.messages)
        ? body.messages
            .filter((message) => message.role === "system")
            .map((message) => message.content)
            .join("\\n")
        : "";
      const prompt = messagesToPrompt(
        Array.isArray(body.messages)
          ? body.messages.filter((message) => message.role !== "system")
          : []
      );
      const result = await promptNano({ prompt, systemPrompt });
      sendJson(res, 200, {
        id: `chatcmpl-local-${Date.now()}`,
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: body.model || "chrome-gemini-nano",
        choices: [
          {
            index: 0,
            message: { role: "assistant", content: result.text },
            finish_reason: "stop",
          },
        ],
        usage: null,
      });
      return;
    }

    if (req.method === "OPTIONS") {
      res.writeHead(204, {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "access-control-allow-headers": "content-type,authorization",
      });
      res.end();
      return;
    }

    serveStatic(req, res);
  } catch (error) {
    sendJson(res, 500, {
      error: {
        message: String(error?.message || error),
      },
    });
  }
});

server.listen(PORT, "127.0.0.1", async () => {
  console.log(`Inspector Lab: http://127.0.0.1:${PORT}`);
  console.log("Chrome workers will start on demand");
  startTelegramPolling().catch((error) => {
    console.error("No se pudo iniciar Telegram:", error?.message || error);
  });
  startAlarmWatcher();
});

function shutdown() {
  telegramPollingStarted = false;
  server.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
