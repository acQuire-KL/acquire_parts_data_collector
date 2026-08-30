# Sprint 4.7.2a — Operational Provider Presentation, Lead-Time Normalisation & Performance

## Provider dashboard
Provider #1/#2/#3 are presentation positions, not fixed distributors. For each BOM row PDC skips providers that returned no useful commercial data and fills the positions with providers that did. Current order is the neutral provider registration order. A later policy may rank valid results by user preference, build-quantity price, availability or a composite rule.

## Lead time
User-facing lead time is always presented in whole weeks and rounded up. Raw provider evidence is retained unchanged. `0 Days`/zero is treated conservatively as `Request Delivery Quote`. Calendar delivery notation such as `Week 45` is treated as an ISO delivery week; it is converted to the number of weeks from the run date and the target week start is shown for clarity.

## Performance
Independent DigiKey, Mouser and TME detail calls are executed concurrently for each BOM row. TME obtains one access token for its logical detail operation and reuses it across Product Search, Product Data and Product Parameters. Console and BOM Review Summary diagnostics report provider operation counts and cumulative provider time. Cumulative provider times can overlap because collection is concurrent.

Commercial information remains live-provider evidence unless the provider itself supplies a current Knowledge Base result. This patch does not introduce a stale-commercial-data cache policy.
