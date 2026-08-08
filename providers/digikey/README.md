# DigiKey Provider

Operational DigiKey integration for PDC.

- `client.py` - DigiKey Product Information API client and Knowledge Base capture.
- `provider.py` - provider-framework adapter.
- `normalizer.py` - DigiKey response to `PDCPartProfile` mapping.
- `checks/` - provider-specific validation utilities.

From the repository root, run the profile validation utility with:

```bash
py -m providers.digikey.checks.profile_check
```
