# Learned Capability Matrix

Last updated: 2026-06-09

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

The matrix builder is implemented and tested. On the current stored experience
set it reports 1,769 experiences and 1,024 tool/capability/shape cells.

When the benchmark arena is executed with fresh judge scores, the matrix
continues to absorb those results automatically through the shared experience
store.
