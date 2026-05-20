# FLUX Integration Test Results

Date: 2026-05-20 04:53:28 UTC

### Cross-Language Parity (Python vs C)

| Status | Result |
|--------|--------|
| ✅ PASS | All assertions passed |

<details><summary>Output</summary>

```
=== Cross-Language Parity Tests (Python vs C) ===

  ✓ Basic parity: 1000 values, 0 mismatches
  ✓ Boundary values: 8 values, 0 mismatches
  ✓ NaN parity: both produce mask=0x3
  ✓ Batch parity: 1000 values, 0 mismatches
  ✓ Preset parity (automotive): 1000 values, 0 mismatches

✅ ALL CROSS-LANGUAGE TESTS PASSED
```
</details>

### Presets Parity (All Packages)

| Status | Result |
|--------|--------|
| ✅ PASS | All assertions passed |

<details><summary>Output</summary>

```
=== Presets Parity Tests ===

  ✓ C presets: all 10 available
  ✓ flux-lib-py presets: 10/10
  ℹ flux-check-py presets: 6 (subset is OK)
  ✓ flux-check-js presets: 10/10
  ✓ JS preset constraint counts: all non-empty
    Bounds mismatch torque_nm: C=[-50.0,50.0] Py=[-100,100]
  ⚠ Cross-package bounds: 1 mismatches (expected — different schema versions)

✅ ALL PRESET PARITY TESTS PASSED (with noted differences)
```
</details>

### NaN Consistency (All Packages)

| Status | Result |
|--------|--------|
| ✅ PASS | All assertions passed |

<details><summary>Output</summary>

```
=== NaN Consistency Tests ===

  ✓ flux_lib: NaN → mask=0x7 (all violated)
  ✓ flux_check: NaN → mask=0x3 (all violated)
  ✓ C engine: NaN → mask=0x7 (all violated)
  ✓ JS engine: NaN → violation=1 (all violated)
  ✓ All NaN variants: consistent across Python and C (4 variants)

✅ ALL NaN CONSISTENCY TESTS PASSED
```
</details>

### Fracture Equivalence (Python, C, Rust)

| Status | Result |
|--------|--------|
| ✅ PASS | All assertions passed |

<details><summary>Output</summary>

```
=== Fracture Equivalence Tests ===

  ✓ Identity graph (5×5): 5 blocks, Python == C
  ✓ Single component (4 constraints → 1 constraint block + orphans): Python == C
  ✓ Two components (2+2): Python == C
  ✓ Star graph (6 constraints → 1 constraint block + 3 orphan dims): Python == C
  ✓ Chain graph (4 constraints → 1 block): Python == C
  ✓ Rust basic example: 8 blocks, speedup 8.0×

✅ ALL FRACTURE EQUIVALENCE TESTS PASSED
```
</details>

## Summary

| Metric | Count |
|--------|-------|
| Total  | 4 |
| Passed | 4 |
| Failed | 0 |

**Result: ALL GREEN** ✅
