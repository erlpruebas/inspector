const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const crypto = require("crypto");
const { execFile } = require("child_process");
const { promisify } = require("util");

const execFileAsync = promisify(execFile);

function createAssistantCore({ rootDir, promptNano, logger = console }) {
  const assistantDir = path.join(rootDir, "assistant");
  const mediaDir = path.join(assistantDir, "media");
  const stateFile = path.join(assistantDir, "state.json");
  const alarmsMarkdownFile = path.join(assistantDir, "alarms.md");
  const modelsDir = path.join(rootDir, "models");
  const localHelper = path.join(assistantDir, "local_transcribe.py");
  const localPython = path.join(rootDir, ".venv", "Scripts", "python.exe");
  const { createTTSManager } = require(path.join(assistantDir, "tts"));
  const ttsManager = createTTSManager({ rootDir, logger });

  const config = {
    groqApiKey: process.env.GROQ_API_KEY || "",
    groqRouterModel: process.env.GROQ_ROUTER_MODEL || "llama-3.1-8b-instant",
    groqModel: process.env.GROQ_STT_MODEL || "whisper-large-v3-turbo",
    localModel: process.env.LOCAL_STT_MODEL || "tiny",
    routerProvider: process.env.ROUTER_PROVIDER || "groq",
    preferGroq: process.env.STT_PROVIDER !== "local",
    ttsProvider: process.env.TTS_PROVIDER || "kokoro",
    ttsVoiceId: process.env.TTS_VOICE_ID || "",
    ttsSpeed: Number(process.env.TTS_SPEED || 1.0),
    ttsLanguage: process.env.TTS_LANGUAGE || "es",
    ttsEnabled: process.env.TTS_ENABLED !== "false",
    ttsMaxChars: Number(process.env.TTS_MAX_CHARS || 700),
  };

  ensureDirSync(assistantDir);
  ensureDirSync(mediaDir);

  let state = loadState();
  let saveQueue = Promise.resolve();
  writeAlarmsMarkdown().catch(() => {});

  function ensureDirSync(dir) {
    fs.mkdirSync(dir, { recursive: true });
  }

  function loadState() {
    try {
      const parsed = JSON.parse(fs.readFileSync(stateFile, "utf8"));
      return normalizeState(parsed);
    } catch {
      return normalizeState({});
    }
  }

  function normalizeState(raw) {
    return {
      version: 1,
      threads: raw.threads && typeof raw.threads === "object" ? raw.threads : {},
      alarms: Array.isArray(raw.alarms) ? raw.alarms : [],
      updatedAt: raw.updatedAt || new Date().toISOString(),
    };
  }

  function persistState() {
    const snapshot = JSON.stringify(state, null, 2);
    saveQueue = saveQueue.then(async () => {
      const tmp = `${stateFile}.tmp`;
      await fsp.writeFile(tmp, snapshot, "utf8");
      await fsp.rename(tmp, stateFile);
      await writeAlarmsMarkdown();
    });
    return saveQueue.catch((error) => {
      logger.warn?.("No se pudo guardar el estado del asistente:", error);
    });
  }

  function makeThreadKey(source, threadId) {
    return `${source}:${threadId || "default"}`;
  }

  function createThread({ source, threadId, label }) {
    return {
      threadKey: makeThreadKey(source, threadId),
      source,
      threadId: threadId || "default",
      label: label || source,
      title: label || "Nueva tarea",
      summary: "Sin contexto previo",
      status: "idle",
      activeSystem: null,
      activeModel: null,
      currentTask: null,
      continueCurrentTask: false,
      ttsProvider: config.ttsProvider,
      ttsVoiceId: config.ttsVoiceId,
      lastTranscription: null,
      lastRouter: null,
      lastSpeech: null,
      pending: null,
      history: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastDecision: null,
    };
  }

  function getThread({ source, threadId, label }) {
    const key = makeThreadKey(source, threadId);
    if (!state.threads[key]) {
      state.threads[key] = createThread({ source, threadId, label });
    }
    const thread = state.threads[key];
    if (label && thread.label !== label) thread.label = label;
    return thread;
  }

  function trimHistory(thread, maxEntries = 24) {
    if (!Array.isArray(thread.history)) thread.history = [];
    if (thread.history.length > maxEntries) {
      thread.history = thread.history.slice(thread.history.length - maxEntries);
    }
  }

  function addHistory(thread, entry) {
    thread.history.push({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      ...entry,
    });
    trimHistory(thread);
    thread.updatedAt = new Date().toISOString();
    state.updatedAt = thread.updatedAt;
    persistState();
  }

  function guessMimeFromName(name) {
    const ext = path.extname(name || "").toLowerCase();
    const map = {
      ".mp3": "audio/mpeg",
      ".wav": "audio/wav",
      ".m4a": "audio/mp4",
      ".aac": "audio/aac",
      ".ogg": "audio/ogg",
      ".oga": "audio/ogg",
      ".webm": "audio/webm",
      ".flac": "audio/flac",
      ".mp4": "video/mp4",
      ".mpeg": "audio/mpeg",
      ".mpga": "audio/mpeg",
    };
    return map[ext] || "application/octet-stream";
  }

  function safeFileName(name, fallbackPrefix = "audio") {
    const base = path.basename(String(name || ""));
    const cleaned = base.replace(/[^a-zA-Z0-9._-]+/g, "_").replace(/^_+|_+$/g, "");
    if (cleaned && cleaned !== "." && cleaned !== "..") return cleaned;
    return `${fallbackPrefix}-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
  }

  function resolveLocalPython() {
    return fs.existsSync(localPython) ? localPython : "python";
  }

  function trimForSpeech(text) {
    const normalized = normalizeIncomingText(text);
    if (!Number.isFinite(config.ttsMaxChars) || config.ttsMaxChars <= 0) return normalized;
    if (normalized.length <= config.ttsMaxChars) return normalized;
    return `${normalized.slice(0, config.ttsMaxChars).replace(/\s+\S*$/, "")}...`;
  }

  function normalizeIncomingText(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function splitParagraphs(text) {
    return String(text || "")
      .split(/\n\s*\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function isLongForVoice(text) {
    const raw = String(text || "").trim();
    if (!raw) return false;
    if (splitParagraphs(raw).length > 2) return true;
    return normalizeIncomingText(raw).length > config.ttsMaxChars;
  }

  function wantsFullVoice(text) {
    const normalized = foldText(text);
    return /(lee|leeme|dame|di).*(respuesta|texto|mensaje).*(completa|completo|entera|entero)/.test(normalized) ||
      /(no me resumas|sin resumir|voz completa|audio completo|leelo todo|lee todo)/.test(normalized);
  }

  function findLastAssistantText(thread) {
    const history = Array.isArray(thread.history) ? thread.history : [];
    for (let i = history.length - 1; i >= 0; i -= 1) {
      const item = history[i];
      if (item.role === "assistant" && item.content) return String(item.content);
    }
    return "";
  }

  function parseSpanishNumber(value) {
    const normalized = foldText(value);
    if (/^\d+$/.test(normalized)) return Number(normalized);
    const map = {
      un: 1,
      una: 1,
      uno: 1,
      dos: 2,
      tres: 3,
      cuatro: 4,
      cinco: 5,
      seis: 6,
      siete: 7,
      ocho: 8,
      nueve: 9,
      diez: 10,
      once: 11,
      doce: 12,
      trece: 13,
      catorce: 14,
      quince: 15,
      veinte: 20,
      treinta: 30,
      media: 30,
    };
    return map[normalized] || null;
  }

  function parseAbsoluteTimeRequest(rawText) {
    const raw = normalizeIncomingText(rawText);
    const normalized = foldText(raw);
    const timeMatch =
      normalized.match(/\b(?:a las|para las|sobre las)\s+(\d{1,2})(?:(?::|\.|\s+y\s+|\s+)(\d{1,2}))?\b/) ||
      normalized.match(/\b(?:a la|para la|sobre la)\s+(\d{1,2})(?:(?::|\.|\s+y\s+|\s+)(\d{1,2}))?\b/);
    if (!timeMatch) return null;

    const hour = Number(timeMatch[1]);
    const minute = timeMatch[2] == null ? 0 : Number(timeMatch[2]);
    if (!Number.isInteger(hour) || !Number.isInteger(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
      return null;
    }

    const due = new Date();
    due.setHours(hour, minute, 0, 0);
    if (due.getTime() <= Date.now()) {
      due.setDate(due.getDate() + 1);
    }

    const task = raw
      .replace(/^(pon|crea|programa|establece)?\s*(una\s*)?(alarma|alerta|aviso|recordatorio)?\s*/i, "")
      .replace(/\b(a las|para las|sobre las|a la|para la|sobre la)\s+\d{1,2}(?:(?::|\.|\s+y\s+|\s+)\d{1,2})?\b/i, "")
      .trim()
      .replace(/^(para|que|de que|avisame|avísame|recuerdame|recuérdame|notificame|notifícame)\s+/i, "")
      .replace(/^(me\s+)?(avises|recuerdes|notifiques)\s+(de\s+que|que)?\s*/i, "")
      .trim();

    return {
      minutes: Math.max(1, Math.round((due.getTime() - Date.now()) / 60000)),
      dueAt: due.toISOString(),
      task: task || raw,
      mode: "absolute",
    };
  }

  function parseReminderRequest(text) {
    const raw = normalizeIncomingText(text);
    const normalized = foldText(raw);
    if (!/(avisame|recuerdame|recordarme|alarma|alerta|notificame)/.test(normalized)) return null;

    let minutes = null;
    let match = normalized.match(/dentro de\s+(\d+|un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|media)\s+(minutos|minuto|horas|hora)/);
    if (match) {
      const amount = parseSpanishNumber(match[1]);
      if (amount) minutes = match[2].startsWith("hora") ? amount * 60 : amount;
    }
    if (minutes == null && /dentro de media hora/.test(normalized)) minutes = 30;
    if (minutes == null) return parseAbsoluteTimeRequest(raw);

    const dueAt = new Date(Date.now() + minutes * 60 * 1000).toISOString();
    const task = raw
      .replace(/^(avisame|avísame|recuerdame|recuérdame|notificame|notifícame)\s*/i, "")
      .replace(/dentro de\s+.+?(minutos|minuto|horas|hora)\s*/i, "")
      .replace(/^(para|que)\s+/i, "")
      .trim();
    return {
      minutes,
      dueAt,
      task: task || raw,
      mode: "relative",
    };
  }

  function getScheduledAlarms() {
    return state.alarms
      .filter((alarm) => alarm.status === "scheduled")
      .sort((a, b) => Date.parse(a.dueAt) - Date.parse(b.dueAt));
  }

  function formatAlarmLine(alarm, index) {
    return `${index + 1}. ${new Date(alarm.dueAt).toLocaleString("es-ES")} - ${alarm.task}`;
  }

  function buildAlarmsReply() {
    const scheduled = getScheduledAlarms();
    if (!scheduled.length) return "No tienes alarmas pendientes.";
    return ["Alarmas pendientes:", ...scheduled.map(formatAlarmLine)].join("\n");
  }

  async function writeAlarmsMarkdown() {
    const scheduled = getScheduledAlarms();
    const lines = [
      "# Alarmas de Inspector",
      "",
      "Este archivo lo actualiza el gestor. Sirve para leer rapidamente que alarmas hay pendientes.",
      "",
      "## Pendientes",
      "",
      scheduled.length ? scheduled.map(formatAlarmLine).join("\n") : "No hay alarmas pendientes.",
      "",
      "## Comandos utiles",
      "",
      "- Que alarmas hay",
      "- Cancela la alarma 1",
      "- Pospone la alarma 1 media hora",
      "- Modifica la alarma 1 texto revisar el informe",
      "",
    ];
    await fsp.writeFile(alarmsMarkdownFile, lines.join("\n"), "utf8");
  }

  function parseAlarmCommand(text) {
    const raw = normalizeIncomingText(text);
    const normalized = foldText(raw);
    if (!/(alarma|alarmas|avisos|recordatorios)/.test(normalized)) return null;

    if (/(que|cuales|lista|lee|dime|muestra|recuerda).*(alarma|alarmas|avisos|recordatorios)/.test(normalized)) {
      return { action: "list" };
    }

    const indexMatch = normalized.match(/(?:alarma|aviso|recordatorio)\s+(\d+)/) || normalized.match(/\b(\d+)\b/);
    const index = indexMatch ? Number(indexMatch[1]) : null;
    if (/(cancela|borra|elimina|quita|anula)/.test(normalized)) {
      return { action: "cancel", index };
    }

    if (/(modifica|cambia|pospone|retrasa|adelanta)/.test(normalized)) {
      const reminder = parseReminderRequest(raw) || parseRelativeAlarmUpdate(raw);
      const taskMatch = raw.match(/(?:texto|tarea|mensaje|sobre)\s*[:=]?\s*(.+)$/i);
      return {
        action: "update",
        index,
        reminder,
        task: taskMatch ? normalizeIncomingText(taskMatch[1]) : null,
      };
    }

    return null;
  }

  function parseRelativeAlarmUpdate(text) {
    const raw = normalizeIncomingText(text);
    const normalized = foldText(raw);
    let minutes = null;
    const match = normalized.match(/(?:a|para|dentro de|en)\s+(\d+|un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|media)\s+(minutos|minuto|horas|hora)/);
    if (match) {
      const amount = parseSpanishNumber(match[1]);
      if (amount) minutes = match[2].startsWith("hora") ? amount * 60 : amount;
    }
    if (minutes == null && /media hora/.test(normalized)) minutes = 30;
    if (minutes == null) return null;
    return {
      minutes,
      dueAt: new Date(Date.now() + minutes * 60 * 1000).toISOString(),
      task: null,
    };
  }

  async function applyAlarmCommand(thread, command) {
    const scheduled = getScheduledAlarms();
    if (command.action === "list") {
      return {
        reply: buildAlarmsReply(),
        decision: {
          intent: "alarm_list",
          requires_confirmation: false,
          should_execute: false,
          next_step: "answer",
        },
      };
    }

    if (!command.index || command.index < 1 || command.index > scheduled.length) {
      return {
        reply: scheduled.length
          ? `Necesito que me digas el numero de alarma. ${buildAlarmsReply()}`
          : "No tienes alarmas pendientes para modificar.",
        decision: {
          intent: "alarm_manage",
          requires_confirmation: false,
          should_execute: false,
          next_step: "clarify",
        },
      };
    }

    const alarm = scheduled[command.index - 1];
    if (command.action === "cancel") {
      alarm.status = "cancelled";
      alarm.cancelledAt = new Date().toISOString();
      state.updatedAt = alarm.cancelledAt;
      await persistState();
      return {
        reply: `He cancelado la alarma ${command.index}: ${alarm.task}.`,
        decision: {
          intent: "alarm_cancel",
          requires_confirmation: false,
          should_execute: true,
          next_step: "answer",
        },
      };
    }

    if (command.action === "update") {
      if (command.reminder?.dueAt) alarm.dueAt = command.reminder.dueAt;
      if (command.task) alarm.task = command.task;
      alarm.updatedAt = new Date().toISOString();
      state.updatedAt = alarm.updatedAt;
      await persistState();
      return {
        reply: `He actualizado la alarma ${command.index}: ${new Date(alarm.dueAt).toLocaleString("es-ES")} - ${alarm.task}.`,
        decision: {
          intent: "alarm_update",
          requires_confirmation: false,
          should_execute: true,
          next_step: "answer",
        },
      };
    }

    return null;
  }

  function foldText(text) {
    return normalizeIncomingText(text)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function normalizeAffirmation(text) {
    const normalized = foldText(text);
    return /(^|[\s,;:.!?-])(si|vale|ok|dale|adelante|hazlo|continua|correcto|perfecto|de acuerdo)(?=$|[\s,;:.!?-])/i.test(
      normalized
    );
  }

  function normalizeCorrection(text) {
    const normalized = foldText(text);
    return /(^|[\s,;:.!?-])(no|corrige|correccion|reformula|mejor|cambia|ajusta|espera|rectifica|no es eso)(?=$|[\s,;:.!?-])/i.test(normalized);
  }

  function parseTtsDirective(text) {
    const normalized = foldText(text);
    const isConfig = /(^|[\s,;:.!?-])(configuracion|configura|cambia|pon|usa|modo|voz)(?=$|[\s,;:.!?-])/.test(normalized);
    if (!isConfig) return null;
    if (/(eleven\s*labs|elevenlabs|eleven)/.test(normalized)) {
      return { provider: "elevenlabs" };
    }
    if (/(kokoro|local)/.test(normalized)) {
      return { provider: "kokoro" };
    }
    return null;
  }

  function extractJsonBlock(text) {
    const raw = String(text || "").trim();
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {}
    const match = raw.match(/\{[\s\S]*\}$/);
    if (!match) return null;
    try {
      return JSON.parse(match[0]);
    } catch {
      return null;
    }
  }

  function buildRouterPrompt({ thread, incomingText, source }) {
    const context = {
      source,
      thread: {
        title: thread.title,
        summary: thread.summary,
        pending: thread.pending,
        lastMessages: thread.history.slice(-8).map((item) => ({
          role: item.role,
          content: item.content,
          kind: item.kind,
        })),
      },
      incomingText,
    };

    return {
      systemPrompt: [
        "Eres un enrutador de tareas en español.",
        "Devuelve SOLO JSON válido, sin markdown ni explicaciones.",
        "Tienes que mantener la sensación de hilo y detectar si el mensaje sigue la tarea actual o abre una nueva.",
        "El JSON debe tener estas claves:",
        "{",
        '  "intent": "task|question|confirmation|correction|new_topic|inform",',
        '  "thread_title": "breve título del hilo",',
        '  "thread_summary": "resumen breve del hilo actual",',
        '  "understood": "qué has entendido del mensaje actual",',
        '  "proposal": "qué propones hacer",',
        '  "reply": "mensaje breve y natural para el usuario",',
        '  "requires_confirmation": true,',
        '  "should_execute": false,',
        '  "topic_changed": false,',
        '  "confidence": 0.0,',
        '  "next_step": "wait_confirmation|execute|answer|clarify",',
        '  "correction_needed": false',
        "}",
        "Si el usuario confirma una propuesta pendiente, marca intent=confirmation, should_execute=true y requires_confirmation=false.",
        "Si hay corrección sobre una propuesta pendiente, marca intent=correction, correction_needed=true y requires_confirmation=true.",
        "Si el mensaje es una tarea nueva, explica claramente lo entendido y la propuesta antes de pedir confirmación.",
        "Si es una pregunta simple, puedes responder sin pedir confirmación.",
      ].join("\n"),
      prompt: JSON.stringify(context, null, 2),
    };
  }

  async function groqChat({ systemPrompt, prompt, temperature = 0 }) {
    if (!config.groqApiKey) {
      throw new Error("GROQ_API_KEY no está configurada");
    }

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.groqApiKey}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: config.groqRouterModel,
        temperature,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: prompt },
        ],
      }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Groq chat error ${response.status}: ${body}`);
    }

    const data = await response.json();
    const content = data?.choices?.[0]?.message?.content || "";
    return {
      provider: "groq",
      model: config.groqRouterModel,
      content,
      raw: data,
    };
  }

  function heuristicDecision({ thread, incomingText, source }) {
    const text = normalizeIncomingText(incomingText);
    const lower = text.toLowerCase();
    const isYes = normalizeAffirmation(text);
    const isFix = normalizeCorrection(text);
    const hasQuestionMark = text.includes("?");

    if (thread.pending && isYes) {
      return {
        intent: "confirmation",
        thread_title: thread.title,
        thread_summary: thread.summary,
        understood: `Confirmas la propuesta pendiente sobre "${thread.pending.thread_title || thread.title}"`,
        proposal: thread.pending.proposal || "ejecutar la propuesta guardada",
        reply: `Perfecto. He entendido que confirmas la propuesta pendiente y la ejecuto ahora.`,
        requires_confirmation: false,
        should_execute: true,
        topic_changed: false,
        confidence: 0.97,
        next_step: "execute",
        correction_needed: false,
      };
    }

    if (thread.pending && isFix) {
      return {
        intent: "correction",
        thread_title: thread.pending.thread_title || thread.title,
        thread_summary: thread.summary,
        understood: `Hay una corrección sobre la propuesta pendiente: ${text}`,
        proposal: `replantear la tarea con la corrección indicada`,
        reply: `He entendido la corrección. Recompongo el hilo con lo que acabas de decir y te propongo una versión ajustada.`,
        requires_confirmation: true,
        should_execute: false,
        topic_changed: false,
        confidence: 0.91,
        next_step: "wait_confirmation",
        correction_needed: true,
      };
    }

    if (hasQuestionMark || /^(que|como|cual|cuando|dime|explícame|explicame)/i.test(foldText(text))) {
      return {
        intent: "question",
        thread_title: thread.title,
        thread_summary: thread.summary,
        understood: `Has hecho una pregunta sobre ${text.replace(/\?+$/, "")}`,
        proposal: "responder directamente a la pregunta",
        reply: "He entendido tu pregunta y voy a responderla directamente.",
        requires_confirmation: false,
        should_execute: false,
        topic_changed: false,
        confidence: 0.72,
        next_step: "answer",
        correction_needed: false,
      };
    }

    return {
      intent: "task",
      thread_title: thread.title,
      thread_summary: thread.summary,
      understood: text || "mensaje vacío",
      proposal: "preparar una respuesta o acción más concreta",
      reply: "He entendido el mensaje y voy a dejar claro qué he captado y qué propongo hacer.",
      requires_confirmation: true,
      should_execute: false,
      topic_changed: false,
      confidence: 0.63,
      next_step: "wait_confirmation",
      correction_needed: false,
    };
  }

  async function llmDecision({ thread, incomingText, source }) {
    if (config.routerProvider !== "groq" || !config.groqApiKey) return null;
    const { systemPrompt, prompt } = buildRouterPrompt({ thread, incomingText, source });
    try {
      const result = await groqChat({ systemPrompt, prompt, temperature: 0 });
      const parsed = extractJsonBlock(result?.content || result);
      if (!parsed || typeof parsed !== "object") return null;
      return parsed;
    } catch (error) {
      logger.warn?.("Router LLM no disponible, uso heurísticas:", error?.message || error);
      return null;
    }
  }

  function normalizeDecision(decision, fallback) {
    const base = fallback || {};
    const merged = {
      intent: "task",
      thread_title: base.thread_title || "Nueva tarea",
      thread_summary: base.thread_summary || "Sin contexto previo",
      understood: base.understood || normalizeIncomingText(decision?.understood || ""),
      proposal: base.proposal || "esperar a una confirmación más clara",
      reply: base.reply || "",
      requires_confirmation: true,
      should_execute: false,
      topic_changed: false,
      confidence: 0.5,
      next_step: "wait_confirmation",
      correction_needed: false,
      ...decision,
    };

    if (merged.next_step === "clarify") {
      merged.requires_confirmation = false;
      merged.should_execute = false;
    }
    if (merged.requires_confirmation && /^\s*[¿?]/.test(String(merged.proposal || ""))) {
      merged.requires_confirmation = false;
      merged.next_step = "clarify";
    }

    if (!merged.reply && merged.next_step === "clarify") {
      merged.reply = merged.proposal || "Necesito un poco más de detalle para seguir.";
    }
    if (!merged.reply) {
      merged.reply = buildConfirmationReply(merged);
    }
    merged.thread_title = normalizeIncomingText(merged.thread_title) || "Nueva tarea";
    merged.thread_summary = normalizeIncomingText(merged.thread_summary) || "Sin contexto previo";
    merged.understood = normalizeIncomingText(merged.understood) || "mensaje recibido";
    merged.proposal = normalizeIncomingText(merged.proposal) || "esperar confirmación";
    merged.reply = normalizeIncomingText(merged.reply) || buildConfirmationReply(merged);
    return merged;
  }

  function attachReminderDecision(decision, incomingText) {
    const reminder = parseReminderRequest(incomingText);
    if (!reminder) return decision;
    return {
      ...decision,
      intent: "task",
      tool: "alarm",
      reminder,
      understood:
        reminder.mode === "absolute"
          ? `quieres que te avise a las ${new Date(reminder.dueAt).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })} sobre: ${reminder.task}`
          : `quieres que te avise dentro de ${reminder.minutes} minutos sobre: ${reminder.task}`,
      proposal: `programar una alarma para ${new Date(reminder.dueAt).toLocaleString("es-ES")} y guardar la tarea: ${reminder.task}`,
      reply: "",
      requires_confirmation: true,
      should_execute: false,
      next_step: "wait_confirmation",
    };
  }

  function buildConfirmationReply(decision) {
    return `He entendido: ${decision.understood}. Propongo: ${decision.proposal}. ¿Quieres que lo haga?`;
  }

  async function executeApprovedDecision({ thread, decision, inputText }) {
    if (decision.tool === "alarm" && decision.reminder) {
      const alarm = {
        id: crypto.randomUUID(),
        threadKey: thread.threadKey,
        source: thread.source,
        threadId: thread.threadId,
        label: thread.label,
        dueAt: decision.reminder.dueAt,
        task: decision.reminder.task,
        status: "scheduled",
        createdAt: new Date().toISOString(),
      };
      state.alarms.push(alarm);
      await persistState();
      return {
        text: `Perfecto. He programado el aviso para ${new Date(alarm.dueAt).toLocaleString("es-ES")}: ${alarm.task}.`,
        executed: true,
        executionMode: "alarm",
        alarm,
      };
    }

    const executionPrompt = [
      "Eres un asistente que ejecuta la decisión ya confirmada por el usuario.",
      "Responde en español, de forma clara y breve.",
      "No pidas confirmación otra vez.",
      `Tarea confirmada: ${decision.proposal}`,
      `Contexto del hilo: ${thread.summary}`,
      `Último mensaje: ${inputText}`,
    ].join("\n");

    if (config.routerProvider === "groq" && config.groqApiKey) {
      try {
        const result = await groqChat({
          systemPrompt:
            "Responde como asistente operativo y devuelve solo el texto final, sin listas innecesarias.",
          prompt: executionPrompt,
          temperature: 0.2,
        });
        const text = normalizeIncomingText(result?.content || result);
        if (text) {
          return {
            text,
            executed: true,
            executionMode: "groq",
          };
        }
      } catch (error) {
        logger.warn?.("No se pudo ejecutar con Groq, uso salida simple:", error?.message || error);
      }
    }

    return {
      text: `Perfecto. He dejado la tarea confirmada: ${decision.proposal}.`,
      executed: true,
      executionMode: "fallback",
    };
  }

  async function writeAudioBuffer({ buffer, fileName, mimeType }) {
    ensureDirSync(mediaDir);
    const safeName =
      safeFileName(fileName) ||
      `audio-${Date.now()}-${crypto.randomUUID().slice(0, 8)}${path.extname(fileName || "") || ""}`;
    const target = path.join(mediaDir, safeName);
    await fsp.writeFile(target, buffer);
    return { path: target, fileName: safeName, mimeType: mimeType || guessMimeFromName(safeName) };
  }

  async function transcribeWithGroq({ filePath, language }) {
    if (!config.groqApiKey) {
      throw new Error("GROQ_API_KEY no está configurada");
    }

    const bytes = await fsp.readFile(filePath);
    const form = new FormData();
    const fileName = path.basename(filePath);
    form.append("model", config.groqModel);
    form.append("temperature", "0");
    form.append("response_format", "json");
    if (language) form.append("language", language);
    form.append("file", new Blob([bytes], { type: guessMimeFromName(fileName) }), fileName);

    const response = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.groqApiKey}`,
      },
      body: form,
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Groq STT error ${response.status}: ${body}`);
    }

    const data = await response.json();
    return {
      provider: "groq",
      model: config.groqModel,
      text: normalizeIncomingText(data.text || ""),
      raw: data,
    };
  }

  async function transcribeWithLocal({ filePath, language }) {
    const args = [
      "-X",
      "utf8",
      localHelper,
      "--audio",
      filePath,
      "--model",
      config.localModel,
      "--models-dir",
      modelsDir,
    ];
    if (language) args.push("--language", language);

    const result = await execFileAsync(resolveLocalPython(), args, {
      env: {
        ...process.env,
        PYTHONUTF8: "1",
      },
      maxBuffer: 20 * 1024 * 1024,
      windowsHide: true,
    });

    const parsed = JSON.parse(result.stdout);
    return {
      provider: "local",
      model: config.localModel,
      ...parsed,
      text: normalizeIncomingText(parsed.text || ""),
    };
  }

  async function transcribeAudio({ filePath, language, preferGroq = config.preferGroq }) {
    const started = Date.now();
    const attempts = [];

    if (preferGroq) {
      try {
        const groq = await transcribeWithGroq({ filePath, language });
        return {
          ...groq,
          elapsedMs: Date.now() - started,
          attempts,
        };
      } catch (error) {
        attempts.push({
          provider: "groq",
          error: String(error?.message || error),
        });
      }
    }

    try {
      const local = await transcribeWithLocal({ filePath, language });
      return {
        ...local,
        elapsedMs: Date.now() - started,
        attempts,
      };
    } catch (error) {
      attempts.push({
        provider: "local",
        error: String(error?.message || error),
      });
      const combined = attempts.map((item) => `${item.provider}: ${item.error}`).join(" | ");
      throw new Error(`No se pudo transcribir el audio. ${combined}`);
    }
  }

  function summarizeThread(thread) {
    return {
      threadKey: thread.threadKey,
      source: thread.source,
      threadId: thread.threadId,
      label: thread.label,
      title: thread.title,
      summary: thread.summary,
      status: thread.status,
      activeSystem: thread.activeSystem,
      activeModel: thread.activeModel,
      currentTask: thread.currentTask,
      continueCurrentTask: thread.continueCurrentTask,
      ttsProvider: thread.ttsProvider,
      ttsVoiceId: thread.ttsVoiceId,
      lastTranscription: thread.lastTranscription,
      lastRouter: thread.lastRouter,
      lastSpeech: thread.lastSpeech,
      pending: thread.pending,
      history: thread.history.slice(-12),
      updatedAt: thread.updatedAt,
    };
  }

  async function prepareSpeechText({ text, forceFull = false }) {
    const raw = String(text || "").trim();
    if (!raw) return "";
    if (forceFull) return normalizeIncomingText(raw);
    if (!isLongForVoice(raw)) return trimForSpeech(raw);

    const fallback = () => {
      const paragraphs = splitParagraphs(raw);
      const compact = paragraphs.length > 1 ? paragraphs.slice(0, 2).join("\n\n") : normalizeIncomingText(raw);
      return trimForSpeech(compact);
    };

    if (!config.groqApiKey) return fallback();

    try {
      const result = await groqChat({
        systemPrompt: [
          "Resume respuestas largas para voz en espanol.",
          "Maximo dos parrafos cortos.",
          "Conserva decisiones, avisos y acciones pendientes.",
          "No anadas informacion nueva.",
        ].join("\n"),
        prompt: raw,
        temperature: 0,
      });
      return trimForSpeech(result?.content || result || fallback());
    } catch (error) {
      logger.warn?.("No se pudo resumir la voz, uso recorte local:", error?.message || error);
      return fallback();
    }
  }

  async function maybeSynthesizeReply({ thread, text, forceFull = false }) {
    if (!text || !config.ttsEnabled) return null;
    const provider = thread.ttsProvider || config.ttsProvider;
    try {
      const speechText = await prepareSpeechText({ text, forceFull });
      const speech = await ttsManager.synthesize({
        text: speechText,
        provider,
        voiceId: thread.ttsVoiceId || config.ttsVoiceId,
        speed: config.ttsSpeed,
        language: config.ttsLanguage,
      });
      thread.lastSpeech = {
        provider: speech.provider,
        voiceId: speech.voiceId || null,
        model: speech.model || null,
        fileName: speech.fileName,
        mimeType: speech.mimeType,
        summarized: speechText !== normalizeIncomingText(text),
        createdAt: new Date().toISOString(),
      };
      speech.text = speechText;
      speech.summarized = speechText !== normalizeIncomingText(text);
      return speech;
    } catch (error) {
      logger.warn?.("No se pudo sintetizar voz:", error?.message || error);
      thread.lastSpeech = {
        provider,
        error: String(error?.message || error),
        createdAt: new Date().toISOString(),
      };
      return null;
    }
  }

  async function routeMessage({ thread, incomingText, source }) {
    const llm = await llmDecision({ thread, incomingText, source });
    return attachReminderDecision(
      normalizeDecision(llm, heuristicDecision({ thread, incomingText, source })),
      incomingText
    );
  }

  async function synthesizeForThread({ source = "desktop", threadId = "default", label = source, text, forceFull = false }) {
    const thread = getThread({ source, threadId, label });
    const speech = await maybeSynthesizeReply({ thread, text, forceFull });
    await persistState();
    return speech
      ? {
          provider: speech.provider,
          voiceId: speech.voiceId || null,
          model: speech.model || null,
          mimeType: speech.mimeType || "audio/mpeg",
          fileName: speech.fileName,
          path: speech.path || null,
          text: speech.text || null,
          summarized: Boolean(speech.summarized),
          base64: speech.base64,
        }
      : null;
  }

  function publicSpeech(speech) {
    return speech
      ? {
          provider: speech.provider,
          voiceId: speech.voiceId || null,
          model: speech.model || null,
          mimeType: speech.mimeType || "audio/mpeg",
          fileName: speech.fileName,
          path: speech.path || null,
          text: speech.text || null,
          summarized: Boolean(speech.summarized),
          base64: speech.base64,
        }
      : null;
  }

  function getDueAlarms({ markDelivered = true } = {}) {
    const now = Date.now();
    const due = state.alarms.filter((alarm) => alarm.status === "scheduled" && Date.parse(alarm.dueAt) <= now);
    if (markDelivered && due.length) {
      for (const alarm of due) {
        alarm.status = "delivered";
        alarm.deliveredAt = new Date().toISOString();
      }
      state.updatedAt = new Date().toISOString();
      persistState();
    }
    return due;
  }

  async function processInboundMessage(input) {
    const source = input.source || "desktop";
    const threadId = input.threadId || input.chatId || "default";
    const label = input.label || input.userName || source;
    const thread = getThread({ source, threadId, label });
    const audioPath = input.audioPath || null;
    const synthesize = input.synthesize !== false;

    let incomingText = normalizeIncomingText(input.text || "");
    let transcription = null;

    if (!incomingText && audioPath) {
      transcription = await transcribeAudio({
        filePath: audioPath,
        language: input.language || "es",
        preferGroq: input.preferGroq ?? config.preferGroq,
      });
      incomingText = transcription.text;
      thread.activeSystem = transcription.provider;
      thread.activeModel = transcription.model;
      thread.lastTranscription = transcription;
    }

    if (!incomingText) {
      incomingText = "(mensaje sin texto)";
    }

    addHistory(thread, {
      role: "user",
      kind: audioPath ? "audio" : "text",
      content: incomingText,
      audioPath: audioPath || undefined,
      transcription,
      source,
    });

    if (wantsFullVoice(incomingText)) {
      const lastText = findLastAssistantText(thread);
      const reply = lastText
        ? "Te leo la respuesta completa."
        : "No tengo una respuesta anterior completa para leer todavia.";
      const decision = {
        intent: "speech_replay",
        thread_title: thread.title,
        thread_summary: thread.summary,
        understood: "quieres escuchar la respuesta completa sin resumen",
        proposal: "leer por voz la ultima respuesta completa",
        reply,
        requires_confirmation: false,
        should_execute: false,
        topic_changed: false,
        confidence: 0.99,
        next_step: "answer",
        correction_needed: false,
      };
      const speech = synthesize && lastText ? await maybeSynthesizeReply({ thread, text: lastText, forceFull: true }) : null;
      addHistory(thread, {
        role: "assistant",
        kind: "speech_replay",
        content: reply,
        decision,
        speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
      });
      await persistState();
      return {
        thread: summarizeThread(thread),
        transcription,
        decision,
        reply,
        voiceText: lastText || reply,
        forceFullVoice: Boolean(lastText),
        speech: publicSpeech(speech),
      };
    }

    const alarmCommand = parseAlarmCommand(incomingText);
    if (alarmCommand) {
      const alarmResult = await applyAlarmCommand(thread, alarmCommand);
      if (alarmResult) {
        thread.status = "active";
        thread.lastDecision = alarmResult.decision;
        thread.currentTask = "Gestion de alarmas";
        thread.updatedAt = new Date().toISOString();
        state.updatedAt = thread.updatedAt;
        const speech = synthesize ? await maybeSynthesizeReply({ thread, text: alarmResult.reply }) : null;
        addHistory(thread, {
          role: "assistant",
          kind: "alarm",
          content: alarmResult.reply,
          decision: alarmResult.decision,
          speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
        });
        await persistState();
        return {
          thread: summarizeThread(thread),
          transcription,
          decision: alarmResult.decision,
          reply: alarmResult.reply,
          speech: publicSpeech(speech),
        };
      }
    }

    const ttsDirective = parseTtsDirective(incomingText);
    if (ttsDirective?.provider) {
      thread.ttsProvider = ttsDirective.provider;
      if (ttsDirective.provider === "elevenlabs") {
        thread.ttsVoiceId = thread.ttsVoiceId || config.ttsVoiceId;
      }
      const reply =
        ttsDirective.provider === "elevenlabs"
          ? "Perfecto. He cambiado la voz a ElevenLabs para esta conversación."
          : "Perfecto. He cambiado la voz a Kokoro local para esta conversación.";
      const decision = {
        intent: "configuration",
        thread_title: thread.title,
        thread_summary: thread.summary,
        understood: `Has pedido cambiar la voz a ${ttsDirective.provider}`,
        proposal: `usar ${ttsDirective.provider} como sintetizador de voz`,
        reply,
        requires_confirmation: false,
        should_execute: false,
        topic_changed: false,
        confidence: 0.99,
        next_step: "answer",
        correction_needed: false,
      };
      thread.lastDecision = decision;
      thread.status = "active";
      thread.updatedAt = new Date().toISOString();
      state.updatedAt = thread.updatedAt;
      const speech = synthesize ? await maybeSynthesizeReply({ thread, text: reply }) : null;
      addHistory(thread, {
        role: "assistant",
        kind: "configuration",
        content: reply,
        decision,
        speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
      });
      await persistState();
      return {
        thread: summarizeThread(thread),
        transcription,
        decision,
        reply,
        speech: publicSpeech(speech),
      };
    }

    if (thread.pending && normalizeAffirmation(incomingText)) {
      const execution = await executeApprovedDecision({
        thread,
        decision: thread.pending,
        inputText: incomingText,
      });
      thread.summary = thread.pending.thread_summary || thread.summary;
      thread.title = thread.pending.thread_title || thread.title;
      thread.lastDecision = thread.pending;
      thread.activeSystem =
        thread.activeSystem || (config.groqApiKey ? `groq:${config.groqRouterModel}` : "heuristic");
      thread.activeModel = thread.activeModel || (config.groqApiKey ? config.groqRouterModel : "local");
      thread.lastRouter = {
        provider: config.groqApiKey ? "groq" : "heuristic",
        model: config.groqApiKey ? config.groqRouterModel : "heuristic",
      };
      thread.currentTask = thread.pending.proposal || thread.currentTask;
      thread.status = "executed";
      thread.continueCurrentTask = false;
      thread.pending = null;
      thread.updatedAt = new Date().toISOString();
      state.updatedAt = thread.updatedAt;
      const speech = synthesize ? await maybeSynthesizeReply({ thread, text: execution.text }) : null;
      addHistory(thread, {
        role: "assistant",
        kind: "execution",
        content: execution.text,
        execution,
        speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
      });
      await persistState();
      return {
        thread: summarizeThread(thread),
        transcription,
        decision: {
          intent: "confirmation",
          should_execute: true,
          requires_confirmation: false,
          next_step: "execute",
        },
        reply: execution.text,
        executed: execution,
        speech: publicSpeech(speech),
      };
    }

    if (thread.pending && normalizeCorrection(incomingText)) {
      const mergedThread = {
        ...thread,
        summary: `${thread.summary} | Corrección: ${incomingText}`,
      };
      const decision = await routeMessage({
        thread: mergedThread,
        incomingText: `${thread.pending.proposal}\nCorrección del usuario: ${incomingText}`,
        source,
      });
      thread.title = decision.thread_title;
      thread.summary = decision.thread_summary;
      thread.pending = decision.requires_confirmation ? decision : null;
      thread.lastDecision = decision;
      thread.activeSystem = config.groqApiKey ? `groq:${config.groqRouterModel}` : "heuristic";
      thread.activeModel = config.groqApiKey ? config.groqRouterModel : "local";
      thread.lastRouter = {
        provider: config.groqApiKey ? "groq" : "heuristic",
        model: config.groqApiKey ? config.groqRouterModel : "heuristic",
      };
      thread.currentTask = decision.proposal;
      thread.status = decision.requires_confirmation ? "awaiting_confirmation" : "active";
      thread.continueCurrentTask = Boolean(decision.requires_confirmation);
      const replyText = buildConfirmationReply(decision);
      const speech = synthesize ? await maybeSynthesizeReply({ thread, text: replyText }) : null;
      addHistory(thread, {
        role: "assistant",
        kind: "router",
        content: replyText,
        decision,
        speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
      });
      await persistState();
      return {
        thread: summarizeThread(thread),
        transcription,
        decision,
        reply: replyText,
        speech: publicSpeech(speech),
      };
    }

    const decision = await routeMessage({
      thread,
      incomingText,
      source,
    });

    thread.title = decision.thread_title;
    thread.summary = decision.thread_summary;
    thread.lastDecision = decision;
    thread.pending = decision.requires_confirmation ? decision : null;
    thread.activeSystem = config.groqApiKey ? `groq:${config.groqRouterModel}` : "heuristic";
    thread.activeModel = config.groqApiKey ? config.groqRouterModel : "local";
    thread.lastRouter = {
      provider: config.groqApiKey ? "groq" : "heuristic",
      model: config.groqApiKey ? config.groqRouterModel : "heuristic",
    };
    thread.currentTask = decision.proposal;
    thread.status = decision.requires_confirmation ? "awaiting_confirmation" : "active";
    thread.continueCurrentTask = Boolean(decision.requires_confirmation);
    const replyText = decision.requires_confirmation ? buildConfirmationReply(decision) : decision.reply;
    const speech = synthesize ? await maybeSynthesizeReply({ thread, text: replyText }) : null;
    addHistory(thread, {
      role: "assistant",
      kind: decision.requires_confirmation ? "proposal" : "answer",
      content: replyText,
      decision,
      speech: speech ? { provider: speech.provider, voiceId: speech.voiceId || null, model: speech.model || null, fileName: speech.fileName } : null,
    });
    await persistState();

    return {
      thread: summarizeThread(thread),
      transcription,
      decision,
      reply: replyText,
      speech: publicSpeech(speech),
    };
  }

  function getSnapshot(threadId, source = "desktop") {
    if (!threadId) {
      return {
        version: state.version,
        threads: Object.values(state.threads).map(summarizeThread),
        alarms: state.alarms,
      };
    }
    const thread = state.threads[makeThreadKey(source, threadId)];
    return thread ? summarizeThread(thread) : null;
  }

  return {
    config,
    mediaDir,
    stateFile,
    modelsDir,
    processInboundMessage,
    transcribeAudio,
    writeAudioBuffer,
    getSnapshot,
    getDueAlarms,
    synthesizeForThread,
    loadState: () => state,
  };
}

module.exports = { createAssistantCore };
