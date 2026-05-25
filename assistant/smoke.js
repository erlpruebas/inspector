const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { createAssistantCore } = require("./core");

async function main() {
  process.env.STT_PROVIDER = "local";
  process.env.ROUTER_PROVIDER = "local";
  process.env.TTS_ENABLED = "false";
  process.env.ASSISTANT_REQUEST_MODE = "legacy";

  const rootDir = path.resolve(__dirname, "..");
  const core = createAssistantCore({
    rootDir,
    promptNano: null,
    logger: console,
  });

  const audioPath = path.join(rootDir, "assistant", "media", "smoke-sample.wav");
  const threadId = `smoke-thread-${Date.now()}`;
  let transcription = {
    provider: "text-fixture",
    text: "Prueba local del gestor Inspector para validar router, memoria y confirmacion sin depender de archivos externos.",
  };

  if (fs.existsSync(audioPath)) {
    transcription = await core.transcribeAudio({
      filePath: audioPath,
      language: "es",
      preferGroq: false,
    });
    assert.equal(transcription.provider, "local");
  }
  assert.ok(transcription.text.length > 20, "expected a non-empty transcription");

  const first = await core.processInboundMessage({
    source: "desktop",
    threadId,
    text: transcription.text,
    label: "Desktop",
    preferGroq: false,
  });

  assert.ok(first.reply.length > 0, "expected a reply");
  assert.ok(first.thread.pending, "expected a pending proposal after first turn");

  const second = await core.processInboundMessage({
    source: "desktop",
    threadId,
    text: "si, adelante",
    label: "Desktop",
    preferGroq: false,
  });

  assert.ok(second.executed, "expected confirmation flow to execute");
  console.log(
    JSON.stringify(
      {
        transcriptionProvider: transcription.provider,
        transcriptionLength: transcription.text.length,
        firstReply: first.reply,
        secondReply: second.reply,
      },
      null,
      2
    )
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
