"""
test_cross_language.py — Python vs C constraint checking parity.

Runs 1000 random value vectors through both flux-lib-py (Python) and
flux-engine-c (via ctypes) and asserts zero mismatches on error masks.
"""

import ctypes
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "flux-lib-py"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "flux-check-py"))

from flux_lib.core import ConstraintEngine

# ── Load C library ──────────────────────────────────────────

C_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "flux-engine-c", "libflux_engine.so")
c_lib = ctypes.CDLL(os.path.abspath(C_LIB_PATH))

# C struct: FluxConstraint { char name[32]; float lo; float hi; int severity; }
class CConstraint(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 32),
        ("lo", ctypes.c_float),
        ("hi", ctypes.c_float),
        ("severity", ctypes.c_int),
    ]

c_lib.flux_check.restype = ctypes.c_uint8
c_lib.flux_check.argtypes = [ctypes.c_float, ctypes.POINTER(CConstraint), ctypes.c_int]

c_lib.flux_check_batch.restype = None
c_lib.flux_check_batch.argtypes = [
    ctypes.POINTER(ctypes.c_float), ctypes.c_int,
    ctypes.POINTER(CConstraint), ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint8),
]

N_TRIALS = 1000
SEED = 42


def make_c_constraints(constraints):
    """Convert Python constraint dicts to C array."""
    arr = (CConstraint * len(constraints))()
    for i, c in enumerate(constraints):
        arr[i].name = c.get("name", f"C{i}").encode()[:31]
        arr[i].lo = float(c["lo"])
        arr[i].hi = float(c["hi"])
        arr[i].severity = c.get("severity", 2)
    return arr


def test_basic_parity():
    """Same 3 constraints, random values → Python mask == C mask."""
    constraints = [
        {"name": "temp", "lo": -40.0, "hi": 150.0, "severity": 3},
        {"name": "speed", "lo": 0.0, "hi": 300.0, "severity": 2},
        {"name": "pressure", "lo": 0.0, "hi": 200.0, "severity": 1},
    ]
    engine = ConstraintEngine(constraints)
    c_arr = make_c_constraints(constraints)

    random.seed(SEED)
    mismatches = 0
    for _ in range(N_TRIALS):
        value = random.uniform(-500, 1000)
        py_mask = engine.check_mask(value)
        c_mask = c_lib.flux_check(ctypes.c_float(value), c_arr, len(constraints))
        if py_mask != c_mask:
            mismatches += 1

    assert mismatches == 0, f"Basic parity: {mismatches}/{N_TRIALS} mismatches"
    print(f"  ✓ Basic parity: {N_TRIALS} values, 0 mismatches")


def test_boundary_values():
    """Test exact boundary values (lo, hi, lo-ε, hi+ε)."""
    constraints = [
        {"name": "a", "lo": 0.0, "hi": 100.0},
        {"name": "b", "lo": -50.0, "hi": 50.0},
        {"name": "c", "lo": 0.001, "hi": 999.999},
    ]
    engine = ConstraintEngine(constraints)
    c_arr = make_c_constraints(constraints)

    test_values = [0.0, 100.0, -0.001, 100.001, -50.0, 50.0, 0.001, 999.999]
    mismatches = 0
    for v in test_values:
        py_mask = engine.check_mask(v)
        c_mask = c_lib.flux_check(ctypes.c_float(v), c_arr, len(constraints))
        if py_mask != c_mask:
            mismatches += 1
            print(f"    Boundary mismatch at value={v}: py={py_mask:#x} c={c_mask:#x}")

    assert mismatches == 0, f"Boundary values: {mismatches} mismatches"
    print(f"  ✓ Boundary values: {len(test_values)} values, 0 mismatches")


def test_nan_parity():
    """NaN must produce all-bits-set in both Python and C."""
    constraints = [
        {"name": "x", "lo": 0.0, "hi": 10.0},
        {"name": "y", "lo": -5.0, "hi": 5.0},
    ]
    engine = ConstraintEngine(constraints)
    c_arr = make_c_constraints(constraints)

    py_mask = engine.check_mask(float("nan"))
    c_mask = c_lib.flux_check(ctypes.c_float(float("nan")), c_arr, 2)

    expected = (1 << 2) - 1  # 0b11 = 3
    assert py_mask == expected, f"Python NaN mask: {py_mask:#x} != {expected:#x}"
    assert c_mask == expected, f"C NaN mask: {c_mask:#x} != {expected:#x}"
    print(f"  ✓ NaN parity: both produce mask={expected:#x}")


def test_batch_parity():
    """Batch mode: 1000 random values through both."""
    constraints = [
        {"name": "a", "lo": -100.0, "hi": 100.0},
        {"name": "b", "lo": 0.0, "hi": 50.0},
        {"name": "c", "lo": -10.0, "hi": 10.0},
        {"name": "d", "lo": 500.0, "hi": 1500.0},
    ]
    engine = ConstraintEngine(constraints)
    c_arr = make_c_constraints(constraints)

    random.seed(SEED + 1)
    n = N_TRIALS
    values = [random.uniform(-200, 2000) for _ in range(n)]

    # Python batch
    import numpy as np
    py_masks = engine.check_batch(np.array(values, dtype=np.float64))

    # C batch
    c_values = (ctypes.c_float * n)(*[ctypes.c_float(v) for v in values])
    c_masks = (ctypes.c_uint8 * n)()
    c_lib.flux_check_batch(c_values, n, c_arr, len(constraints), c_masks)

    mismatches = 0
    for i in range(n):
        if py_masks[i] != c_masks[i]:
            mismatches += 1

    assert mismatches == 0, f"Batch parity: {mismatches}/{n} mismatches"
    print(f"  ✓ Batch parity: {n} values, 0 mismatches")


def test_with_presets():
    """Test with real preset constraints from flux-engine-c."""
    # Use C preset functions
    c_lib.flux_preset_automotive.restype = ctypes.c_int
    c_lib.flux_preset_automotive.argtypes = [ctypes.POINTER(CConstraint)]

    c_preset = (CConstraint * 8)()
    n = c_lib.flux_preset_automotive(c_preset)

    # Build matching Python constraints from C data
    py_constraints = []
    for i in range(n):
        py_constraints.append({
            "name": c_preset[i].name.decode(),
            "lo": float(c_preset[i].lo),
            "hi": float(c_preset[i].hi),
            "severity": c_preset[i].severity,
        })

    engine = ConstraintEngine(py_constraints)

    random.seed(SEED + 2)
    mismatches = 0
    for _ in range(N_TRIALS):
        value = random.uniform(-100, 10000)
        py_mask = engine.check_mask(value)
        c_mask = c_lib.flux_check(ctypes.c_float(value), c_preset, n)
        if py_mask != c_mask:
            mismatches += 1

    assert mismatches == 0, f"Preset parity: {mismatches}/{N_TRIALS} mismatches"
    print(f"  ✓ Preset parity (automotive): {N_TRIALS} values, 0 mismatches")


if __name__ == "__main__":
    print("=== Cross-Language Parity Tests (Python vs C) ===\n")
    test_basic_parity()
    test_boundary_values()
    test_nan_parity()
    test_batch_parity()
    test_with_presets()
    print("\n✅ ALL CROSS-LANGUAGE TESTS PASSED")
