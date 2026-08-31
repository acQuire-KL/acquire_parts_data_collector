# PDC Housekeeping — Sprint 4.7.2d

This package has been cleaned before delivery. Generated outputs, broad caches and superseded sprint debris are not shipped.

## Delete from your working repository

These are safe housekeeping targets:

- `output/` contents — generated BOM review workbooks, staging files and generated provider-profile outputs.
- `cache/` old contents — legacy/provider cache files; only test fixtures are retained in the clean package.
- `raw_responses/` old contents — obsolete root-level captures; only the small regression fixture required by the test suite is retained.
- `docs/history/` — superseded install/patch notes; Git already preserves project history.
- `SPRINT_*_TEST_PLAN.txt` — old root sprint plans superseded by `tests/` and `CHANGELOG.md`.
- `TEST_RESULTS*.txt` — generated historical regression reports.
- `PATCH_4.7.2a_README.txt` — superseded patch note.
- `README_4.6.2b.md` — superseded README.
- `input/gb-mini-board-v0.1-draft2.csv` — obsolete operational test BOM if it still exists locally.

## Keep

Keep:

- `Parts_Master/parts_master_index.json`
- `input/AIPN Parts Master.xlsx` — still required by the current Parts Master index regression tests.
- `input/AIPN_Input_Template.xlsx`
- `tests/`
- `providers/`
- `provider_profiles/`
- `docs/` except `docs/history/`
- `tools/`
- source `.py` files
- `.env.example`
- `requirements.txt`
- `README.md`
- `CHANGELOG.md`
- `INSTALL.txt`

## Knowledge Base

Do **not** blindly delete your working `Knowledge_Base/`. It contains collected provider evidence and may be useful project data.

The clean release only carries the handful of Knowledge Base records required by regression tests. Preserve or back up your accumulated local evidence separately when replacing the application files.

## Cleanup rule for future iterations

Before each sprint package is delivered:

1. Remove generated `output/` content.
2. Remove broad runtime/cache debris not required for regression.
3. Remove superseded root sprint notes/test-result files.
4. Preserve current Parts Master/reference data and regression fixtures.
5. Run the full regression suite.
6. Verify the packaged `APP_VERSION` directly inside the ZIP.


Sprint 4.7.2e housekeeping completed before package creation; generated output content is not included.
