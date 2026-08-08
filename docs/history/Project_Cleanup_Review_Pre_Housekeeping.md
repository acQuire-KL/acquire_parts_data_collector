# PDC Project Cleanup Review

## Safe to delete locally

These are generated or machine-specific and are already excluded by `.gitignore`:

- `.venv/`
- `.idea/` if PyCharm project settings do not need to be shared
- every `__pycache__/` directory
- every `*.pyc` file
- generated files under `output/`, retaining `output/.gitkeep`
- legacy response files under `raw_responses/`, retaining `raw_responses/.gitkeep`, once the Knowledge Base is confirmed as the authoritative evidence store
- legacy files under `cache/`, retaining `cache/.gitkeep`, once migration into the Knowledge Base has been verified

## Retain

- `.env.example`
- `Knowledge_Base/`
- `input/AIPN_Input_Template.xlsx`
- provider adapters and shared provider framework files
- test files
- documentation

## Review before deletion

### `archive/`

The two files under `archive/` are not imported by the active application. They appear to be historical versions of `main.py` and `manufacturer_resolver.py`. They are redundant at runtime, but should only be deleted after confirming Git history contains the versions that need to be preserved.

### Top-level `digikey_client.py`

This file is active. `providers/digikey/provider.py` imports `DigiKeyClient` from it, so it must not be deleted yet.

### Top-level `manufacturer_resolver.py`

This file is active and is imported by both `main.py` and `multi_provider_summary.py`.

## Recommended repository cleanup command

From the project root in Git Bash:

```bash
find . -type d -name __pycache__ -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

Machine-specific `.venv/` and `.idea/` folders can then be removed manually if desired. No active Python source file was deleted as part of Sprint 4.2.1.
