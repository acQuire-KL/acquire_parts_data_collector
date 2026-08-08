# TME Capability Review — Sprint 4.2.2a

Status: **Awaiting first successful live v2 response**

The official TME material confirms that the Product API provides product data,
availability and prices, and that a private key linked to a TME customer account
can expose customer-specific pricing. The `request-context: anonymous` header is
available when public market data is required.

The following mapping must be completed from the saved live JSON rather than by
assumption:

| PDC field | TME v2 status | Evidence needed |
|---|---|---|
| Manufacturer | To verify | Exact response path |
| Manufacturer Part Number | To verify | Exact response path |
| TME symbol | To verify | Exact response path |
| Description | To verify | Exact response path |
| Available quantity | To verify | Meaning and response path |
| Lead time | To verify | Direct, derived or absent |
| MOQ | To verify | Direct, derived or absent |
| Standard pack quantity | To verify | Direct, derived or absent |
| Currency | To verify | Response path and scope |
| Price breaks | To verify | Quantity/price structure |
| Lifecycle/status | To verify | Status vocabulary |
| Datasheet URL | To verify | Direct or separate endpoint |
| Image URL | To verify | Direct or separate endpoint |

## Exit criteria for Sprint 4.2.2a

1. A live request returns HTTP success.
2. The unmodified JSON is saved under `raw_responses/`.
3. The endpoint, authentication contract and required parameters are confirmed.
4. This matrix is updated from the actual response before Sprint 4.2.2b begins.
