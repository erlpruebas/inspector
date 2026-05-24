const statusText = document.querySelector("#statusText");
const outputText = document.querySelector("#outputText");
const refreshStatus = document.querySelector("#refreshStatus");
const sendBrowserPrompt = document.querySelector("#sendBrowserPrompt");
const sendPrompt = document.querySelector("#sendPrompt");
const sendOpenAI = document.querySelector("#sendOpenAI");
const recordAssistant = document.querySelector("#recordAssistant");
const sendAssistant = document.querySelector("#sendAssistant");
const clearOutput = document.querySelector("#clearOutput");
const assistantVoiceStatus = document.querySelector("#assistantVoiceStatus");
const assistantAudioInput = document.querySelector("#assistantAudio");

let recorder = null;
let recorderStream = null;
let recorderChunks = [];
let recordedFile = null;
let recording = false;

function setOutput(value) {
  outputText.textContent =
    typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "content-type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || `HTTP ${response.status}`);
  }
  return data;
}

async function loadStatus() {
  refreshStatus.disabled = true;
  statusText.textContent = "Comprobando Inspector Lab...";
  try {
    const browserStatus = await getBrowserStatus();
    const serverStatus = await requestJson("/api/status");
    const assistantState = await requestJson("/api/assistant/state");
    const availability =
      browserStatus.availability || serverStatus.availability || "desconocido";
    statusText.textContent = browserStatus.apiPresent
      ? `API detectada en este Chrome. Estado: ${availability}.`
      : `Servidor activo. Estado worker: ${serverStatus.availability || "desconocido"}.`;
    setOutput({ browser: browserStatus, serverWorker: serverStatus, assistant: assistantState });
  } catch (error) {
    statusText.textContent = "No se pudo leer el estado.";
    setOutput(String(error.message || error));
  } finally {
    refreshStatus.disabled = false;
  }
}

async function getBrowserStatus() {
  const LM = globalThis.LanguageModel || globalThis.ai?.languageModel || globalThis.ai?.LanguageModel;
  const status = {
    href: location.href,
    secureContext: isSecureContext,
    apiPresent: Boolean(LM),
    typeofLanguageModel: typeof globalThis.LanguageModel,
    availability: null,
    error: null,
  };
  try {
    if (LM?.availability) status.availability = await LM.availability();
  } catch (error) {
    status.error = String(error?.message || error);
  }
  return status;
}

async function promptInBrowser({ prompt, systemPrompt }) {
  const LM = globalThis.LanguageModel || globalThis.ai?.languageModel || globalThis.ai?.LanguageModel;
  if (!LM) {
    throw new Error("LanguageModel no está disponible en este navegador.");
  }

  let availability = await LM.availability();
  if (availability === "downloadable" || availability === "downloading") {
    const started = Date.now();
    while (Date.now() - started < 180000) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      availability = await LM.availability();
      if (availability === "available") break;
    }
  }

  const options = {};
  if (systemPrompt) options.systemPrompt = systemPrompt;
  const session = await LM.create(options);
  try {
    const text = await session.prompt(prompt);
    return { model: "chrome-gemini-nano", availability, text };
  } finally {
    session.destroy?.();
  }
}

async function timed(label, element, fn) {
  const started = performance.now();
  element.textContent = `${label}...`;
  try {
    const result = await fn();
    const seconds = ((performance.now() - started) / 1000).toFixed(1);
    element.textContent = `${seconds}s`;
    return result;
  } catch (error) {
    element.textContent = "Error";
    throw error;
  }
}

async function fileToAudioPayload(file) {
  const dataUrl = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("No se pudo leer el archivo de audio."));
    reader.readAsDataURL(file);
  });
  const [, base64] = dataUrl.split(",");
  return {
    name: file.name,
    mimeType: file.type || "application/octet-stream",
    base64,
  };
}

function sanitizeResultForDisplay(value) {
  if (!value || typeof value !== "object") return value;
  const clone = structuredClone(value);
  if (clone.speech?.base64) {
    clone.speech = {
      ...clone.speech,
      base64: "[audio omitido]",
    };
  }
  return clone;
}

async function playSpeech(speech) {
  if (!speech?.base64) return;
  const audio = new Audio(`data:${speech.mimeType || "audio/mpeg"};base64,${speech.base64}`);
  await audio.play().catch(() => {});
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Tu navegador no permite grabación de audio.");
  }
  recorderStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  recorderChunks = [];
  recordedFile = null;
  recorder = new MediaRecorder(recorderStream);
  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) recorderChunks.push(event.data);
  };
  recorder.onstop = () => {
    const mimeType = recorder?.mimeType || "audio/webm";
    const blob = new Blob(recorderChunks, { type: mimeType });
    recordedFile = new File([blob], `grabacion-${Date.now()}.webm`, { type: mimeType });
    recorderChunks = [];
    recorderStream?.getTracks?.().forEach((track) => track.stop());
    recorderStream = null;
    assistantVoiceStatus.textContent = "Grabación lista para enviar.";
  };
  recorder.start();
  recording = true;
  recordAssistant.textContent = "Detener";
  assistantVoiceStatus.textContent = "Grabando...";
}

function stopRecording() {
  if (recorder && recording) {
    recorder.stop();
  }
  recorder = null;
  recording = false;
  recordAssistant.textContent = "Grabar";
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".tabPage").forEach((page) => page.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}`).classList.add("active");
  });
});

refreshStatus.addEventListener("click", loadStatus);

recordAssistant.addEventListener("click", async () => {
  try {
    if (recording) {
      stopRecording();
      return;
    }
    await startRecording();
  } catch (error) {
    assistantVoiceStatus.textContent = String(error.message || error);
    stopRecording();
  }
});

sendBrowserPrompt.addEventListener("click", async () => {
  sendBrowserPrompt.disabled = true;
  try {
    const result = await timed("Generando", document.querySelector("#browserTiming"), () =>
      promptInBrowser({
        systemPrompt: document.querySelector("#browserSystemPrompt").value,
        prompt: document.querySelector("#browserPrompt").value,
      })
    );
    setOutput(result);
  } catch (error) {
    setOutput(String(error.message || error));
  } finally {
    sendBrowserPrompt.disabled = false;
  }
});

sendPrompt.addEventListener("click", async () => {
  sendPrompt.disabled = true;
  try {
    const result = await timed("Generando", document.querySelector("#directTiming"), () =>
      requestJson("/api/prompt", {
        method: "POST",
        body: JSON.stringify({
          systemPrompt: document.querySelector("#systemPrompt").value,
          prompt: document.querySelector("#prompt").value,
        }),
      })
    );
    setOutput(result);
  } catch (error) {
    setOutput(String(error.message || error));
  } finally {
    sendPrompt.disabled = false;
  }
});

sendOpenAI.addEventListener("click", async () => {
  sendOpenAI.disabled = true;
  try {
    const messages = JSON.parse(document.querySelector("#openaiMessages").value);
    const result = await timed("Generando", document.querySelector("#openaiTiming"), () =>
      requestJson("/v1/chat/completions", {
        method: "POST",
        body: JSON.stringify({
          model: "chrome-gemini-nano",
          messages,
        }),
      })
    );
    setOutput(result);
  } catch (error) {
    setOutput(String(error.message || error));
  } finally {
    sendOpenAI.disabled = false;
  }
});

sendAssistant.addEventListener("click", async () => {
  sendAssistant.disabled = true;
  const timing = document.querySelector("#assistantTiming");
  try {
    const text = document.querySelector("#assistantText").value;
    const threadId = document.querySelector("#assistantThread").value || "desktop";
    const userName = document.querySelector("#assistantUser").value || "desktop";
    const file = recordedFile || assistantAudioInput.files?.[0] || null;
    const payload = {
      source: "desktop",
      threadId,
      userName,
      label: userName,
      text,
      language: "es",
      preferGroq: true,
    };
    if (file) {
      payload.audio = await fileToAudioPayload(file);
    }
    const result = await timed("Procesando", timing, () =>
      requestJson("/api/assistant/message", {
        method: "POST",
        body: JSON.stringify(payload),
      })
    );
    const displayResult = sanitizeResultForDisplay(result);
    setOutput(displayResult);
    assistantVoiceStatus.textContent = `Voz actual: ${result.thread?.ttsProvider || "kokoro"}.`;
    await playSpeech(result.speech);
    recordedFile = null;
    assistantAudioInput.value = "";
  } catch (error) {
    setOutput(String(error.message || error));
  } finally {
    sendAssistant.disabled = false;
  }
});

clearOutput.addEventListener("click", () => setOutput("Todavía no hay respuesta."));

loadStatus();
