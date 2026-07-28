# TME API Implementation Notes

## Purpose

This document records implementation observations learned while connecting PDC to TME. It is not a replacement for the official TME API documentation.

## Current core endpoints

| PDC capture stage | Endpoint | Current use |
|---|---|---|
| Product Search | `/products/search` | Resolve the TME symbol, manufacturer, description and basic catalogue data. |
| Product Data | `/products/data` | Capture commercial data requested through one or more `scope[]` values. |
| Product Parameters | `/products/parameters` | Capture provider technical parameters. |

## Authentication

- Authentication uses `POST /auth/token`.
- PDC currently uses the OAuth client-credentials flow.
- The returned access token is reused for all endpoint calls in one capture run.
- Customer-linked and anonymous request contexts are kept distinct in Knowledge Base metadata.

## Product Search

The implemented search request sends:

- `country`
- `scope[]=products`
- `phrase=<MPN>`

The first returned product is currently used to resolve the TME symbol and manufacturer for the following calls. This behaviour should be revisited when match selection is introduced.

## Product Data

`/products/data` requires at least one `scope[]` value. Omitting it produced:

- HTTP 400
- `E_INPUT_PARAMS_VALIDATION_ERROR`
- Field: `scope`
- Message: `This value should not be blank.`

PDC currently defaults to:

- `scope[]=prices`
- `scope[]=stock`

The client accepts an iterable of scopes so additional supported scopes can be tested without redesigning the method. The connectivity utility exposes repeatable `--data-scope` arguments.

Delivery-related data is intentionally deferred until the quantity-dependent request requirements and intended PDC use are understood.

## Product Parameters

The implemented request currently sends:

- `country`
- `symbols[]=<TME symbol>`

Raw responses are preserved before any provider-neutral mapping is introduced.

## Error handling

Authentication is a prerequisite for the run. After authentication, Search, Product Data and Product Parameters are attempted independently. A failure in one endpoint is reported but does not prevent the remaining endpoints from being attempted.

## Knowledge Base capture

Current responses are stored under:

```text
Knowledge_Base/Current/TME/
    Product_Search/
    Product_Data/
    Product_Parameters/
```

Timestamped historical responses are stored under the corresponding `Knowledge_Base/History/TME/` folders.

## Open questions

- Confirm all useful `/products/data` scopes and their request dependencies.
- Determine whether account-linked pricing differs from public catalogue pricing.
- Confirm how stock, delivery and lead-time fields behave by region and account.
- Review the complete parameter vocabulary before creating the TME mapper.
- Define behaviour for multiple search matches rather than selecting the first result.
- Compare TME capabilities with later providers before fixing a common onboarding contract.
