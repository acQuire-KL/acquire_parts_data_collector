# Provider Onboarding Toolkit

This folder is for provider-neutral onboarding work. It is deliberately separate from `providers/`, which contains integrations PDC already knows how to use operationally.

## Principle

- `providers/<provider>/` = operational provider integration.
- `tools/provider_onboarding/` = repeatable method and utilities for understanding a new provider before it becomes operational.

## Recommended onboarding flow

1. Confirm developer account, credentials and API terms.
2. Perform a minimal connectivity/authentication test.
3. Capture representative raw JSON without discarding provider fields.
4. Inspect the response structure and available attributes.
5. Compare available attributes with `PDCPartProfile` and identify genuine gaps.
6. Implement the provider-specific client and normalizer under `providers/<provider>/`.
7. Add provider-specific checks under `providers/<provider>/checks/`.
8. Validate parsed values against the raw provider response.
9. Cross-check technical attributes against other providers where useful, while retaining manufacturer-controlled evidence as the authority for engineering decisions.
10. Run the full regression suite before registering the provider for normal PDC use.

## Generic helpers

### Inspect a raw JSON response

```bash
py -m tools.provider_onboarding.inspect_json path/to/raw_response.json
```

This prints the JSON field paths and representative scalar values. It is intended to expose what the provider actually returns before a normalizer is written.

### Compare two JSON structures

```bash
py -m tools.provider_onboarding.attribute_gap_analysis provider_response.json reference_profile.json
```

This compares flattened field paths to highlight fields present only in one input. It is a discovery aid, not an engineering equivalence test.

## Promotion into providers/

A provider is ready to move into normal PDC operation only when its integration has:

- a documented client/authentication method;
- raw-response preservation;
- a provider-to-`PDCPartProfile` normalizer;
- provider-specific checks;
- error/no-match handling;
- regression coverage;
- a provider README describing known capabilities and limitations.
