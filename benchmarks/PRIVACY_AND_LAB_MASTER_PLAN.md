# Privacy And Lab Master Plan

This document is the running contract for the benchmark lab and the privacy layer.
It is meant to be the single place where we keep the architecture, the execution
order, the guardrails, and the rationale for the current rollout.

## Current Objectives

1. Build a local privacy layer that can turn sensitive documents into three copies:
   - `original`: untouched source
   - `mixed`: source text plus stable tokens, for audit
   - `redacted`: token-only text for model consumption
2. Keep a stable global entity map so the same person, phone number, organization,
   or address always receives the same token across documents and runs.
3. Run the benchmark lab against clear and redacted documents so we can measure
   the quality loss caused by privacy protection.
4. Keep Mini Nano in the loop as a local semantic reviewer for privacy, not as the
   only privacy mechanism.
5. Leave a durable file trail so the work can be resumed without re-deriving the
   architecture.

## Design Choices

### Privacy Strategy

The lab uses hybrid pseudonymization, not model-only anonymization.

Deterministic rules handle obvious PII:

- email addresses
- phone numbers
- DNI/NIE/NIF
- IBAN
- URLs
- addresses
- dates where relevant
- amounts where needed

Mini Nano is used as a secondary semantic reviewer for:

- indirect references
- people or companies that appear in messy prose
- context that regex will miss
- sanity checking the redacted output

This follows the broad direction of the community and of official guidance:

- NIST IR 8053 on de-identification and re-identification risk
- NIST SP 800-122 on protecting PII
- Google Sensitive Data Protection de-identification and tokenization
- Microsoft Presidio anonymization and deanonymization patterns

References:

- [NIST IR 8053](https://csrc.nist.gov/pubs/ir/8053/final)
- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final)
- [Google de-identification](https://cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data)
- [Google transformations](https://cloud.google.com/sensitive-data-protection/docs/transformations-reference)
- [Presidio anonymizer](https://microsoft.github.io/presidio/anonymizer/)

### Token Format

Use stable uppercase tokens with type prefixes:

- `PERSON_0001`
- `ORG_0001`
- `EMAIL_0001`
- `PHONE_0001`
- `ADDRESS_0001`
- `ID_NUMBER_0001`
- `BANK_0001`
- `DATE_0001`
- `URL_0001`

Mixed copy format:

`Emilio Rodriguez [PERSON_0001]`

The bracket form is preferred because it is easy for models to parse and easy for
the lab to recover later.

### Global Stability

The same canonical entity must always map to the same token.

Example:

- `Javier Martinez Lopez` -> `PERSON_0015`
- `+34 600 111 222` -> `PHONE_0025`

This mapping lives in a durable JSONL store inside the repo so we can reuse it
across runs.

### Storage Layout

We keep the privacy artifacts separate from the task inputs:

```text
benchmarks/privacy_store/entity_map.jsonl
benchmarks/privacy_guard/
benchmarks/privacy_tasks.json
benchmarks/privacy_samples/
```

Inside a run directory, privacy artifacts are written under:

```text
privacy/original/
privacy/mixed/
privacy/redacted/
privacy/report.json
```

## Execution Order

1. Implement the privacy package.
2. Add scheduler support for `--privacy-mode clear|mixed|redacted`.
3. Make workspace context builders ignore the `privacy/` tree.
4. Create a small privacy task suite that reuses existing synthetic documents.
5. Run smoke tests for:
   - entity detection
   - stable token allocation
   - redacted output
   - hydration
   - verifier
6. Run a canary benchmark comparing clear vs redacted.
7. Generate the final strategy report.

## Benchmarks To Run

### Health

```powershell
python .\benchmarks\provider_health.py --live
```

### Canary

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine-matrix .\benchmarks\engine_matrix_ready.json --task test-01 --task test-02 --task test-05 --once --heuristic-only
```

### Privacy Mode

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\privacy_tasks.json --engine gemini_api:gemini-2.5-flash-lite --engine openrouter:deepseek/deepseek-v3.2 --engine vikingnano:gemini-nano-local --privacy-mode redacted --privacy-review mini-nano --once --heuristic-only
```

### Full Lab

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine-matrix .\benchmarks\engine_matrix_ready.json --cooldown-seconds 7200 --cycle-sleep-seconds 7200
```

## Model Roles

- `codex:gpt-5.4-mini`: main implementation engine
- `codex:gpt-5.5`: design review and final decisions
- `gemini_api:gemini-2.5-flash-lite`: cheap judge and classifier
- `groq:llama-3.1-8b-instant`: fast router when quota allows
- `openrouter:deepseek/deepseek-v3.2`: cost-quality worker
- `vikingnano:gemini-nano-local`: local semantic reviewer and small extractor
- `opencode:*`: CLI agent comparison layer

## Decision Rules

- Use `clear` only for non-sensitive or already-public data.
- Use `mixed` for human auditing and debugging.
- Use `redacted` for anything that leaves the local machine or goes to external
  APIs.
- Treat Cloudflare `524`, `429`, `503`, and timeouts as transient.
- Do not let Mini Nano be the only privacy layer.

## Acceptance Criteria

1. Stable entity IDs across files and runs.
2. Redacted text contains no obvious PII.
3. Mixed text preserves traceability.
4. Hydration restores canonical values locally.
5. The scheduler can run tasks in privacy mode without leaking `privacy/` artifacts.
6. Mini Nano can review privacy chunks without blocking the main pipeline.
7. The final report can compare clear vs redacted quality loss.

