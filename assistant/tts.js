const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const crypto = require("crypto");
const { execFile } = require("child_process");
const { promisify } = require("util");

const execFileAsync = promisify(execFile);

function createTTSManager({ rootDir, logger = console }) {
  const assistantDir = path.join(rootDir, "assistant");
  const runtimeDir = path.join(assistantDir, "media", "tts");
  const kokoroHelper = path.join(assistantDir, "kokoro_tts.py");
  const kokoroModelPath = path.join(rootDir, "models", "kokoro", "kokoro-v1.0.int8.onnx");
  const kokoroVoicesPath = path.join(rootDir, "models", "kokoro", "voices-v1.0.bin");
  const kokoroPythonCandidates = [
    process.env.KOKORO_PYTHON,
    path.join(rootDir, ".venv", "Scripts", "python.exe"),
  ].filter(Boolean);

  const elevenlabsApiKey = process.env.ELEVENLABS_API_KEY || "";
  const elevenlabsModelId = process.env.ELEVENLABS_TTS_MODEL || "eleven_flash_v2_5";
  const elevenlabsDefaultVoiceId = process.env.ELEVENLABS_VOICE_ID || "";
  const elevenlabsOutputFormat = process.env.ELEVENLABS_OUTPUT_FORMAT || "mp3_44100_128";
  const elevenlabsFallbackVoiceId = elevenlabsDefaultVoiceId || "JBFqnCBsd6RMkjVDRZzb";

  let cachedElevenVoiceId = elevenlabsDefaultVoiceId || null;

  fs.mkdirSync(runtimeDir, { recursive: true });

  function resolvePythonExecutable() {
    for (const candidate of kokoroPythonCandidates) {
      if (candidate && fs.existsSync(candidate)) return candidate;
    }
    return null;
  }

  function mimeFromOutputFormat(outputFormat) {
    const format = String(outputFormat || "").toLowerCase();
    if (format.startsWith("wav")) return "audio/wav";
    if (format.startsWith("pcm")) return "audio/pcm";
    return "audio/mpeg";
  }

  async function synthesize(input) {
    const provider = normalizeProvider(input.provider || process.env.TTS_PROVIDER || "kokoro");
    if (provider === "elevenlabs") {
      return synthesizeElevenLabs(input);
    }
    return synthesizeKokoro(input);
  }

  function normalizeProvider(value) {
    const normalized = String(value || "").toLowerCase().trim();
    if (normalized.includes("eleven")) return "elevenlabs";
    return "kokoro";
  }

  async function synthesizeKokoro({ text, voiceId, speed = 1.0, language = "es" }) {
    const python = resolvePythonExecutable();
    if (!python) {
      throw new Error("No encuentro un Python con kokoro_onnx disponible para Kokoro.");
    }
    if (!fs.existsSync(kokoroHelper)) {
      throw new Error("Falta el helper local de Kokoro dentro de inspector/assistant.");
    }
    if (!fs.existsSync(kokoroModelPath) || !fs.existsSync(kokoroVoicesPath)) {
      throw new Error("Faltan los modelos locales de Kokoro en inspector/models/kokoro.");
    }

    const fileName = `kokoro-${Date.now()}-${crypto.randomUUID().slice(0, 8)}.wav`;
    const outputPath = path.join(runtimeDir, fileName);
    const args = [
      kokoroHelper,
      "--text",
      String(text || ""),
      "--output",
      outputPath,
      "--model-path",
      kokoroModelPath,
      "--voices-path",
      kokoroVoicesPath,
      "--voice",
      String(voiceId || "ef_dora"),
      "--speed",
      String(speed || 1.0),
      "--language",
      String(language || "es"),
    ];

    const result = await execFileAsync(python, args, {
      env: {
        ...process.env,
        PYTHONUTF8: "1",
      },
      windowsHide: true,
      maxBuffer: 20 * 1024 * 1024,
    });

    let meta = {};
    try {
      meta = result.stdout ? JSON.parse(result.stdout) : {};
    } catch {}

    const buffer = await fsp.readFile(outputPath);
    return {
      provider: "kokoro",
      model: "kokoro-onnx",
      voiceId: meta.voice || voiceId || "ef_dora",
      mimeType: "audio/wav",
      fileName,
      path: outputPath,
      base64: buffer.toString("base64"),
    };
  }

  async function resolveElevenVoiceId() {
    if (cachedElevenVoiceId) return cachedElevenVoiceId;
    if (!elevenlabsApiKey) {
      throw new Error("ElevenLabs no tiene API key configurada.");
    }

    const response = await fetch("https://api.elevenlabs.io/v1/voices", {
      headers: {
        "xi-api-key": elevenlabsApiKey,
      },
    });
    if (!response.ok) {
      const body = await response.text();
      let parsed = null;
      try {
        parsed = body ? JSON.parse(body) : null;
      } catch {}
      const detail = parsed?.detail || {};
      if (response.status === 401 && detail.status === "missing_permissions") {
        logger.warn?.(
          "ElevenLabs no permite listar voces con esta clave; uso una voz por defecto conocida."
        );
        cachedElevenVoiceId = elevenlabsFallbackVoiceId;
        return cachedElevenVoiceId;
      }
      if (elevenlabsFallbackVoiceId) {
        logger.warn?.(
          `ElevenLabs voices no disponible (${response.status}); uso una voz por defecto conocida.`
        );
        cachedElevenVoiceId = elevenlabsFallbackVoiceId;
        return cachedElevenVoiceId;
      }
      throw new Error(`ElevenLabs voices error ${response.status}: ${body}`);
    }
    const data = await response.json();
    const voices = Array.isArray(data.voices) ? data.voices : [];
    const firstVoice = voices.find((voice) => voice?.voice_id) || voices[0];
    if (!firstVoice?.voice_id) {
      cachedElevenVoiceId = elevenlabsFallbackVoiceId;
      if (cachedElevenVoiceId) return cachedElevenVoiceId;
      throw new Error("No se encontró ninguna voz de ElevenLabs disponible.");
    }
    cachedElevenVoiceId = firstVoice.voice_id;
    return cachedElevenVoiceId;
  }

  async function synthesizeElevenLabs({ text, voiceId, speed = 1.0, language = "es" }) {
    if (!elevenlabsApiKey) {
      throw new Error("ELEVENLABS_API_KEY no está configurada.");
    }

    const selectedVoiceId = voiceId || (await resolveElevenVoiceId());
    const fileName = `elevenlabs-${Date.now()}-${crypto.randomUUID().slice(0, 8)}.mp3`;
    const outputPath = path.join(runtimeDir, fileName);
    const url = new URL(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(selectedVoiceId)}`);
    url.searchParams.set("output_format", elevenlabsOutputFormat);

    const payload = {
      text: String(text || ""),
      model_id: elevenlabsModelId,
      language_code: language || "es",
      apply_text_normalization: "auto",
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75,
      },
    };

    if (speed && Number.isFinite(Number(speed))) {
      payload.voice_settings.speed = Number(speed);
    }

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "xi-api-key": elevenlabsApiKey,
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`ElevenLabs TTS error ${response.status}: ${body}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    await fsp.writeFile(outputPath, buffer);

    return {
      provider: "elevenlabs",
      model: elevenlabsModelId,
      voiceId: selectedVoiceId,
      mimeType: mimeFromOutputFormat(elevenlabsOutputFormat),
      fileName,
      path: outputPath,
      base64: buffer.toString("base64"),
    };
  }

  return {
    synthesize,
    resolveElevenVoiceId,
    normalizeProvider,
  };
}

module.exports = { createTTSManager };
