# BOM Existing Knowledge Matching — Sprint 4.6.2

This stage runs after fresh BOM normalisation/classification and before any provider search.

Rules:
- DNP is assembly context only. DNP items are identified and matched exactly like fitted items.
- Existing AIPN is retained when present in the Parts Master; PDC does not allocate a new AIPN here.
- MFG+MPN rows are checked against the local Parts Master, then the local Knowledge Base.
- Value+Footprint rows are checked against the Parts Master using conservative engineering-value and package normalisation.
- A unique Value+Footprint result is still only a **candidate**. Engineering must approve it.
- Multiple Value+Footprint results are all exposed as candidates.
- No provider/API calls and no automatic approvals occur in Sprint 4.6.2.

The next stage may send only unresolved, processable items to providers. Exclusion/item-type intelligence will be added conservatively at normalisation; DNP will never be used as an exclusion rule.
