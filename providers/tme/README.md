# TME Provider — Sprint 4.2.2a

## Scope

This folder currently contains only the TME Product API v2 connectivity client.
It does not yet map TME data into the PDC provider-neutral model or write to the
Knowledge Base/workbook.


## Status

Connectivity verified
Verified: 2026-07-26

## Required environment variables

```text
TME_TOKEN=
TME_APPLICATION_SECRET=
```

Optional settings:

```text
TME_BASE_URL=https://api.tme.eu
TME_SEARCH_PATH=/products/search
TME_COUNTRY=IE
TME_LANGUAGE=en
TME_TIMEOUT_SECONDS=30
```

## Connectivity check

```bash
python tme_connectivity_check.py MCP1711T-25I/OT
```

For public market context rather than customer-linked pricing:

```bash
python tme_connectivity_check.py MCP1711T-25I/OT --anonymous
```

A successful response is written unchanged to `raw_responses/`.

## Important validation point

TME introduced a new API generation for applications created after 14 May 2026.
Sprint 4.2.2a deliberately keeps the endpoint and request construction isolated
in `client.py`. The first live run confirms the current Swagger request contract
before any mapper or production integration is added.

## Notes

Important:

Do NOT include "/v2" in the API endpoint paths.

Correct:

https://api.tme.eu/products/search

Incorrect:

https://api.tme.eu/v2/products/search

Raw responses are saved under:

raw_responses/



## Last reviewed

2026-07-26
