# Land Direct Supply Showcase

This is a coverage-heavy demo case intended for GitHub publishing and first-run evaluation.

It demonstrates:

- SQL import with `comment on column`
- JSON import for supplemental mappings
- TXT import for quick alias ingestion
- structure editing workflow
- style analysis
- project-level threshold tuning
- field generation with exact, lexical, semantic, and LLM fallback paths
- PostgreSQL SQL export

## Suggested walkthrough

1. Create a project named `土地直供案例`.
2. Import [01_import_land_schema.sql](01_import_land_schema.sql).
3. Import [02_import_land_extensions.json](02_import_land_extensions.json).
4. Import [03_import_land_aliases.txt](03_import_land_aliases.txt).
5. In structure editor, review the notice-number fields described in [04_structure_adjustments.md](04_structure_adjustments.md).
6. In style analysis, apply thresholds from [05_thresholds.json](05_thresholds.json).
7. Generate fields using [06_generation_input.txt](06_generation_input.txt).
8. Compare the result with [07_expected_match_notes.md](07_expected_match_notes.md).
9. Export PostgreSQL SQL and compare with [08_expected_generated_pg.sql](08_expected_generated_pg.sql).

## Coverage notes

- `exact`: deterministic and should be stable.
- `lexical`: deterministic and should be stable if the current normalization/similarity logic is unchanged.
- `semantic`: depends on embedding model availability and similarity thresholds.
- `llm`: depends on active AI source and may vary slightly across providers/models.
