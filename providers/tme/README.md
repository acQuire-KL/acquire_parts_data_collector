# TME Provider

Operational TME integration for PDC.

- `client.py` - TME API client.
- `normalizer.py` - TME responses to `PDCPartProfile` mapping.
- `checks/` - provider-specific connectivity/capture and profile validation utilities.

From the repository root:

```bash
py -m providers.tme.checks.connectivity_check MCP1711T-25I/OT
py -m providers.tme.checks.profile_check
```

# TME Provider — Sprint 4.2.2c

## Scope

The TME client now captures the three core raw Product API responses needed
before provider-neutral mapping begins:

- `/products/search` — product identity and catalogue summary
- `/products/data` — commercial/product data, including account-linked context
- `/products/parameters` — technical parameters

Raw responses are preserved unchanged in the Knowledge Base. No TME mapper or
workbook integration is included in this sprint.

## Required environment variables

```text
TME_TOKEN=
TME_APPLICATION_SECRET=
```

Optional settings:

```text
TME_BASE_URL=https://api.tme.eu
TME_AUTH_PATH=/auth/token
TME_SEARCH_PATH=/products/search
TME_DATA_PATH=/products/data
TME_PARAMETERS_PATH=/products/parameters
TME_COUNTRY=IE
TME_LANGUAGE=en
TME_CURRENCY=EUR
TME_TIMEOUT_SECONDS=30
```

Do not include `/v2` in the endpoint paths.

## Capture all three endpoints

```bash
py -m providers.tme.checks.connectivity_check MCP1711T-25I/OT
```

For anonymous/public market context:

```bash
py -m providers.tme.checks.connectivity_check MCP1711T-25I/OT --anonymous
```

A successful run writes Current and History copies beneath:

```text
Knowledge_Base/Current/TME/Product_Search/
Knowledge_Base/Current/TME/Product_Data/
Knowledge_Base/Current/TME/Product_Parameters/
```

Use `--only search`, `--only data`, or `--only parameters` for diagnostics.
When Search is skipped, the supplied command-line part number is also used as
the TME symbol.

## Last reviewed

2026-07-28
