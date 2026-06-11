# Learned Capability Matrix

Last updated: 2026-06-11

## Purpose

The learned capability matrix aggregates `RouterExperience` records into
evidence-backed statistics for each:

- tool
- operational capability
- task shape

It is the quantitative bridge between the benchmark arena and the router
promotion policy.

## What It Measures

Each cell records:

- samples
- pass rate
- mean judge score
- mean latency
- latency dispersion
- confidence
- judge sample count

## Current Sources

The matrix currently draws from:

- imported historical benchmark experiences
- arena runs stored in `agent_v2_2` experience storage

## CLI

Use:

```bash
python -m agent_v2_2.cli audit matrix
```

The command prints a markdown summary with:

- total experiences
- tool coverage
- capability coverage
- task-shape coverage
- representative cells

## Current State

The matrix builder is implemented and tested. The HITL gate currently sees
1,891 valid experiences, 161 valid blind judgments, all 17 operational
capabilities and 31 task shapes. Invalidated, simulated, unavailable and queued
records are excluded from learned evidence.

Training coverage is tracked independently from historical volume:

- expected compatible pairs: 56;
- demonstrated with a passing live blind judgment: 56;
- trained with at least three samples: 21;
- pending first demonstration: 0.

For portable deployments, Agent 2.2 includes a sanitized seed with 111 judged
experiences. A clean workspace bootstraps from that seed and passes readiness
with all 56 expected tool-capability pairs, all 17 capabilities and all 9
selectable tools represented.
