# Mouser Provider

Operational Mouser integration for PDC.

- `client.py` - Mouser Search API client.
- `provider.py` - provider-framework adapter.
- `normalizer.py` - Mouser response to `PDCPartProfile` mapping.
- `checks/` - provider-specific connectivity and profile validation utilities.

From the repository root:

```bash
py -m providers.mouser.checks.connectivity_check MCP1711T-25I/OT
py -m providers.mouser.checks.profile_check
```
