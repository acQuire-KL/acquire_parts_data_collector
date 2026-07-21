# Changelog

## v0.1.1 — 2026-07-21

- Resolve the supplied manufacturer against DigiKey's manufacturer catalogue.
- Pass DigiKey `manufacturerId` with ProductDetails requests.
- Validate both returned manufacturer ID and normalised MPN.
- Use manufacturer-specific product cache filenames.
- Add aliases for common manufacturer naming variations.
- Route unresolved or ambiguous manufacturer names to Review Required.
- Exclude `.env`, `.venv`, `.idea`, cache, output and raw responses from Git.
