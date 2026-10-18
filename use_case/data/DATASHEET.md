# Datasheet

<!-- Written in TC2, alongside your synthetic data. This file is committed; the
     data itself is not. -->

## What this data is

**Generated on:** <!-- date -->
**Generated from:** <!-- the schema + a written description, NOT real records -->
**Rows:** <!-- n -->

## Variation axes

<!-- What you varied to get coverage: persona, format, difficulty, edge cases. -->

| Axis | Values | Reason |
| --- | --- | --- |
| Diagnostic completeness | COMPLETE, PARTIAL, MISSING | Tests complete, partial, and missing diagnostic evidence. MISSING includes the mandatory should-decline case, where MARA must not invent a root cause. |
| Evidence consistency | CONSISTENT, CONFLICTING | Tests whether MARA identifies contradictory evidence instead of making unsupported root-cause conclusions. |
| Failure category | APPLICATION_DATA, IMS_DATABASE, DATASET_STORAGE, JCL_CONFIGURATION, SYSTEM_OPERATION | Covers different mainframe failure types that require distinct investigation approaches. |
| Failure sequence | SINGLE_FAILURE, RESTART_RECOVERY, RESTART_FAILURE, DEPENDENCY_CHAIN | Tests whether MARA follows the sequence of failures, restarts, and prerequisite dependencies. |

## What it can validate

<!-- Which claims this data supports. Be narrow. -->

## What it cannot validate

<!-- The important half. Synthetic data cannot tell you about real distribution,
     real frequency, or failure modes you did not think to generate. Say so. -->

## What it must never be compared against

<!-- If you have real ground truth somewhere, say where, and say explicitly that
     these rows are not it. -->

## Leakage check

- [ ] No real record was used as a seed.
- [ ] No real entity names, IDs, or identifiers appear.
- [ ] No distinctive internal formats that would identify the firm.
- [ ] Rare categories were generated, not copied.
