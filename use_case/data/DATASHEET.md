# Datasheet

<!-- Written in TC2, alongside your synthetic data. This file is committed; the
     data itself is not. -->

## What this data is

**Generated on:** 2026-10-20

**Dataset:** `use_case/data/synthetic_v1.jsonl`

**Purpose:** Synthetic prototyping data for MARA (Mainframe Abend Research Assistant), an evidence-grounded mainframe batch abend investigation assistant.

**Generated from:** Eight fully synthetic, hand-authored golden examples in `use_case/evals/golden.jsonl`, the MARA input/output schema, a written generation prompt, and four documented variation axes. Five golden examples, representing the five difficulty rungs, were included in each generation prompt. No production incident records were intentionally used as seeds.

**Generator model:** `anthropic/claude-sonnet-5`, accessed through LiteLLM.

**Prompt configuration:** Three new examples requested per axis combination.

**Sampling settings:** Temperature and top-p were not explicitly specified in the S4 generation cell. Provider/model defaults were used unless otherwise supplied by the notebook configuration. No random seed was explicitly set.

**Generation results:**

| Metric | Count |
|---|---:|
| Available generation seeds | 8 |
| Variation axes | 4 |
| Theoretical axis combinations | 120 |
| Combinations attempted | 6 |
| JSON records successfully parsed | 15 |
| Unparseable JSON lines | 3 |
| Dead axis combinations (API exceptions) | 0 |
| Records retained after deduplication | 15 |
| Records passing Pydantic schema validation | 15 |
| Schema-rejected records | 0 |

**Deduplication method:** Character 4-gram Jaccard similarity applied to the string representation of each generated record's `input` field.

**Deduplication threshold:** `0.7`.

**Rows:** 15 schema-valid prototyping records, pending confirmation that the output file was written.

## What it can validate

- The MARA synthetic-data generation workflow can produce parseable JSON records using the selected seed examples and variation-axis prompts.
- All 15 retained records passed the Pydantic schema used in S4.
- The character 4-gram Jaccard deduplication process executed successfully and retained all 15 records at the `0.7` threshold.
- The notebook can identify certain repeated seed identifiers and near-twins using automated outward and inward leakage checks.
- The generated records can support development and testing of MARA's input parsing, schema handling, and investigation-report workflow.

## What it cannot validate

- It cannot establish MARA's accuracy in diagnosing real production mainframe abends because the generated expected outputs have not been independently verified by a mainframe subject matter expert.
- It cannot establish that MARA reliably distinguishes confirmed root causes from unsupported conclusions in complex IMS database failures, restart dependencies, or incidents with missing or conflicting evidence.
- It cannot establish the real-world frequency or distribution of mainframe failure categories.
- It cannot establish coverage of all 120 theoretical axis combinations. Only six combinations were attempted in this run.
- It cannot establish that generated records are semantically unique merely because all 15 passed the `0.7` character-similarity filter.
- It cannot guarantee that no distinctive operational procedures or identifying information survived generation. Automated leakage checks have limitations.

## What it must never be compared against

This dataset is **prototyping data**, not independently verified backtesting ground truth.

A separate eight-record candidate backtesting dataset is maintained in `use_case/evals/heldout_backtest.jsonl`. Those records must remain separate from synthetic-data generation and any future model tuning, and their expected outputs require independent review before they are used to support accuracy claims.

Generated outputs must not be presented as expert-verified root-cause diagnoses or used to claim production accuracy.

## Leakage check

**Outward leakage check:** 24 matches were reported between generation seeds and generated records. Visible matches included common technical terms such as `S0C7`, `IMS BMP`, and synthetic documentation labels. These findings do not independently establish sensitive-data disclosure; manual review remains necessary.

**Inward leakage check:** One of 15 generated records (`INVUPD77`) had character 4-gram Jaccard similarity of `0.64` to its nearest generation seed, exceeding the inward threshold of `0.5`. The record should not be treated as independent of the generation seeds.

**Review status:**

- [x] Generation used intentionally synthetic, hand-authored seed examples rather than production incident records.
- [ ] Confirm no real entity names, IDs, or sensitive identifiers appear in the generated dataset.
- [ ] Confirm no distinctive internal formats or operational procedures could identify a real organization.
- [ ] Confirm rare scenarios were invented rather than copied from actual incidents.
- [ ] Complete manual review of generated records and flagged leakage findings before external release.

**Data limitation:** Automated regex and similarity checks do not constitute security clearance. Any external sharing requires an appropriate review and approval.

## Variation axes

| Axis | Values | Reason |
| --- | --- | --- |
| Diagnostic completeness | `COMPLETE`, `PARTIAL`, `MISSING` | COMPLETE: JES and application diagnostics provide sufficient evidence to investigate the failure. PARTIAL: Some diagnostics are available, but important information is missing. MISSING: Essential JES and application diagnostics are unavailable; MARA must not invent a root cause and should report insufficient evidence. |
| Evidence consistency | `CONSISTENT`, `CONFLICTING` | CONSISTENT: Available diagnostic and historical evidence agrees. CONFLICTING: Diagnostic or historical findings contradict one another; MARA must acknowledge the contradiction rather than assume a cause. |
| Failure category | `APPLICATION_DATA`, `IMS_DATABASE`, `DATASET_STORAGE`, `JCL_CONFIGURATION`, `SYSTEM_OPERATION` | APPLICATION_DATA: Invalid numeric data, record-format errors, or application validation failures. IMS_DATABASE: IMS BMP processing, database access, or resource contention. DATASET_STORAGE: Missing datasets, GDG configuration, or insufficient SORT work space. JCL_CONFIGURATION: Incorrect JCL references, missing modules, or skipped prerequisite steps. SYSTEM_OPERATION: Planned IPL, system interruption, or operational recovery. |
| Failure sequence | `SINGLE_FAILURE`, `RESTART_RECOVERY`, `RESTART_FAILURE`, `DEPENDENCY_CHAIN` | SINGLE_FAILURE: One failure without a subsequent restart. RESTART_RECOVERY: A failed job completes after an authorized restart. RESTART_FAILURE: A restart attempt fails or introduces another problem. DEPENDENCY_CHAIN: An earlier step or prerequisite affects a downstream job or step. |

## What it can validate

- The synthetic data generation workflow can produce structured mainframe abend investigation examples using the defined MARA variation axes.
- In the initial experiment, 15 generated records were successfully parsed, and all 15 passed Pydantic schema validation.
- All 15 parsed records were retained after character 4-gram Jaccard deduplication using a threshold of 0.7.
- The dataset can support prototyping and testing of MARA's input/output handling, including job details, probable root cause, confidence level, investigation status, and recommended next steps.
- The workflow can identify potential similarity and leakage findings that require further review.

## What it cannot validate

- The dataset cannot establish MARA's accuracy in diagnosing actual mainframe production abends because the generated root causes have not been independently verified by mainframe subject matter experts.
- Synthetic records cannot establish the real-world frequency or distribution of S0C7, IMS, JCL, dataset, or other production failures.
- The initial experiment attempted only 6 of the 120 theoretical variation combinations, so complete coverage has not been demonstrated.
- Passing Pydantic schema validation does not guarantee that a probable root cause or recommended recovery step is technically correct or operationally safe.
- Deduplication and automated leakage checks cannot guarantee semantic diversity or the absence of sensitive organizational patterns.
- The dataset cannot validate MARA's reliability in complex restart scenarios, conflicting diagnostic evidence, or incidents where essential information is missing.

## What it must never be compared against

- These synthetic records must not be treated as verified production incident records or independently established diagnostic ground truth.
- They must not be used to claim MARA's accuracy, precision, recall, or real-world effectiveness in identifying mainframe abend root causes.
- The 8 generation seeds in `use_case/evals/golden.jsonl` were used to guide generation and must not be treated as an independent evaluation set.
- The 8 examples in `use_case/evals/heldout_backtest.jsonl` are separate backtesting candidates, but their expected outcomes also require independent verification before being treated as authoritative ground truth.
- Synthetic results must not be presented as evidence that MARA can safely recommend or execute production recovery actions.

## Leakage check

- [x] No real record was used as a seed.
- [ ] No real entity names, IDs, or identifiers appear.
- [ ] No distinctive internal formats that would identify the firm.
- [ ] Rare categories were generated, not copied.

**Leakage review findings:**

- **Outward leakage check:** 24 regex matches were reported. These included common mainframe terminology and synthetic identifiers. A match is not necessarily a confirmed disclosure, and manual review remains necessary.
- **Inward leakage check:** 1 of 15 generated records (`INVUPD77`) exceeded the 0.5 similarity threshold against the generation seeds, with a Jaccard similarity of 0.64.
- The inward check compared generated records with the generation seeds; it did not establish whether there was overlap with the separate held-out backtesting candidates.
- No real production incident data was intentionally used in generation. The remaining checklist items require manual review before they can be marked complete.