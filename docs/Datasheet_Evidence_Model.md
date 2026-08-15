# Sprint 4.6.3a — Datasheet Evidence Model, Manufacturer Source Resolution & Local Archive

PDC retains both a **Static Evidence Copy** and an **Active Source URL**. Distributor discovery provenance is preserved even when the resolved or independently verified active source is the manufacturer.

Source resolution may inspect redirect targets and embedded URLs, but must never create a manufacturer URL by blindly stripping distributor text. A Manufacturer Source URL is marked verified only after independent testing by the acquisition layer. If distributor and manufacturer downloads are both available, SHA-256 comparison can prove they are byte-for-byte identical.

Evidence source types are `MFG`, `DISTI`, `DISTI_COPY_OF_MFG`, and `UNKNOWN`.

Static files are archived as:

```text
datasheets/<Manufacturer>/<MPN>/YYYY-MM-DD__<MPN>__<MFG|DISTI>__<Source>__<Document>.pdf
```

Different content is never silently overwritten. The stored SHA-256 plus Active Source URL provides the foundation for a later **What's Changed** review: same hash = `No Change`; different hash = `Changed`. This sprint does not yet interpret semantic PDF differences or perform provider-specific network acquisition.
