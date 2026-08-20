# Operational BOM Review — Sprint 4.7.1

## Objective

Sprint 4.7.1 turns the PDC foundations into a practical end-to-end BOM review.
The output remains evidence and engineering-review support; PDC does not make
automatic engineering approvals.

## Operational flow

For every BOM row containing Manufacturer and/or MPN, PDC now:

1. preserves useful BOM context such as Description, Quantity and DNP;
2. checks the local Parts Master Index by Manufacturer + MPN;
3. queries DigiKey, Mouser and TME independently;
4. keeps every provider result visible, with no preferred distributor;
5. merges provider-neutral identity/engineering evidence;
6. surfaces local AIPN, lifecycle and datasheet-evidence status where present;
7. produces a concise Review Observation;
8. writes Enriched Parts, Review Required, Commercial Analysis and BOM Review Summary sheets.

DNP remains assembly context only. DNP rows are processed like fitted rows because
the component may be needed in another variant or later design state.

## Provider neutrality

The Enriched Parts dashboard has three fixed provider blocks:

- Provider #1 — DigiKey
- Provider #2 — Mouser
- Provider #3 — TME

These positions are presentation positions, not a ranking. All configured
providers are attempted for every relevant BOM identity. A provider failure or
missing configuration is shown as incomplete evidence rather than being hidden.

## TME integration

The existing TME API client and normaliser are now connected through an
operational `TmeProvider` adapter. It collects Search, Product Data and Product
Parameters, preserves the raw responses in the Knowledge Base, builds the
provider-neutral TME profile and exposes TME commercial/technical evidence to
the normal BOM-review workflow.

## Local knowledge

`Parts_Master/parts_master_index.json` is read-only during the review. Exact
Manufacturer + MPN matches can surface:

- existing AIPN;
- Parts Master lifecycle;
- datasheet evidence status;
- Active Source URL;
- Static Datasheet path.

A local match is useful context but is not an approval.

## Workbook

### BOM Review Summary

Provides a concise count of reviewed rows, rows requiring attention, match
states and local-knowledge states, plus the provider set used by the review.

### Enriched Parts

Contains BOM context, provider-neutral identity/engineering data, local
knowledge, provider inventory/commercial summaries and documentation evidence.

### Review Required

Contains rows whose provider identity result is not `Matched`.

### Commercial Analysis

Retains detailed commercial offers/price ladders from all providers.

## Review Observation

The observation is an exception-focused summary. Examples include:

- Identity requires review
- No provider identity match confirmed
- Provider collection incomplete
- Existing Parts Master identity
- Ambiguous Parts Master identity
- Lifecycle risk indicated
- Datasheet evidence needs verification

It is deliberately not an approval decision.

## Boundaries for 4.7.1

This sprint does not yet:

- automatically accept an alternative candidate;
- modify the BOM, AVL or Parts Master;
- allocate an AIPN;
- issue an ECO, concession or deviation;
- semantically analyse datasheet revisions;
- guarantee that every provider offers every requested part.

The next sprint should be driven by review of a real BOM output rather than by
adding another abstract subsystem.
