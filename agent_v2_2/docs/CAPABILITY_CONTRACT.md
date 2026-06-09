# Canonical Request And Capability Contract

Version: `1.0`

Implementation:
`agent_v2_2/src/agent_v2_2/routing/contract.py`

## Purpose

The fast router does not choose a tool directly. It converts a user request
into a validated `RequestContract`. Deterministic code then filters and ranks
tools against this contract.

## Contract Sections

### `prepare`

A short ordered list of data preparation actions:

- memory or conversation lookup;
- file discovery, partial reading or file preparation;
- OCR, audio transcription or archive extraction;
- punctual web lookup or multi-source web research;
- calendar or contact lookup.

Each action has a unique `output_key`. Small results can be injected as text.
Files remain structured attachments or workspace paths.

### `execute`

Describes the actual operation:

- operation such as extract, compare, calculate, diagnose or modify artifact;
- cognitive level: none, light, general or reasoning;
- concrete cognitive requirements;
- mandatory instrumental capabilities;
- file formats and required operations;
- guarantees such as exact values, current information, citations, verified
  artifacts or human confirmation.

### File requirements

Formats and operations are separate. A tool can therefore support reading an
XLSX without claiming that it can modify it or preserve formatting.

Supported format families include text, Markdown, CSV, JSON, XML, HTML, PDF,
DOCX, XLSX, PPTX, legacy Office, OpenDocument, image, audio, email, archives,
code and directories.

Operations are read, extract, create, modify, preserve and verify.

## Validation Rules

- Contract schema versions must match exactly.
- Preparation output keys must be unique.
- Web research requires multi-source web capability.
- Web lookup requires current-web capability.
- Fresh-information guarantees require a web preparation action.
- Declared ambiguity requires the `ask_if_missing` guarantee.
- Format preservation must explicitly request the preserve operation.

## Selection Boundary

The contract describes requirements, not preferences. Tool selection belongs
to the deterministic selector and the learned capability matrix.

