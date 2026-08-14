# Intelligent Local Candidate Matching — Sprint 4.6.2a

PDC now uses the enriched `Parts_Master/parts_master_index.json` for local descriptive-component matching.

The candidate discovery gate is **component family + nominal value + footprint**. PDC then uses every additional engineering requirement explicitly present in the BOM to qualify the candidates, including voltage rating, tolerance, dielectric and technology where available.

A candidate may be rejected locally only because it fails a requirement that is actually stated in the BOM. PDC must not invent missing requirements. For example, a 6.3 V capacitor is rejected when the BOM explicitly requires 10 V, but it is not rejected merely because PDC would prefer 10 V when the BOM states no voltage.

Candidate ranking and filtering use engineering attributes only. Commercial information does not influence engineering qualification. Every surviving descriptive candidate still requires Engineering approval.

DNP is preserved as assembly/variant context and does not change component identification processing.
