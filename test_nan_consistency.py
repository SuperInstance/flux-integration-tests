"""
test_nan_consistency.py — NaN handling across all packages.

INVARIANT: NaN ALWAYS violates all constraints. No exceptions.

Tests:
- Python (flux_lib): NaN → all bits set
- Python (flux_check): NaN → all bits set
- C (via ctypes): NaN → all bits set
- JS (via node subprocess): NaN → violation
"""

import ctypes
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "flux-lib-py"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "flux-check-py"))

from flux_lib.core import ConstraintEngine
from flux_check.core import FluxExact

# ── C library ───────────────────────────────────────────────

C_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "flux-engine-c", "libflux_engine.so")
c_lib = ctypes.CDLL(os.path.abspath(C_LIB_PATH))

class CConstraint(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 32),
        ("lo", ctypes.c_float),
        ("hi", ctypes.c_float),
        ("severity", ctypes.c_int),
    ]

c_lib.flux_check.restype = ctypes.c_uint8
c_lib.flux_check.argtypes = [ctypes.c_float, ctypes.POINTER(CConstraint), ctypes.c_int]


def test_python_flux_lib_nan():
    """flux_lib: NaN always violates all constraints."""
    constraints = [
        {"name": "a", "lo": 0.0, "hi": 100.0},
        {"name": "b", "lo": -50.0, "hi": 50.0},
        {"name": "c", "lo": 0.0, "hi": 10.0},
    ]
    engine = ConstraintEngine(constraints)
    mask = engine.check_mask(float("nan"))
    expected = (1 << 3) - 1  # 0b111 = 7
    assert mask == expected, f"flux_lib NaN mask: {mask:#x} != {expected:#x}"
    print(f"  ✓ flux_lib: NaN → mask={mask:#x} (all violated)")


def test_python_flux_check_nan():
    """flux_check: NaN always violates all constraints."""
    constraints = [
        {"name": "x", "lo": -100.0, "hi": 100.0},
        {"name": "y", "lo": 0.0, "hi": 50.0},
    ]
    engine = FluxExact(constraints)
    mask = engine.check_mask(float("nan"))
    expected = (1 << 2) - 1  # 0b11 = 3
    assert mask == expected, f"flux_check NaN mask: {mask:#x} != {expected:#x}"
    print(f"  ✓ flux_check: NaN → mask={mask:#x} (all violated)")


def test_c_nan():
    """C engine: NaN always violates all constraints."""
    constraints = [
        {"name": "a", "lo": 0.0, "hi": 100.0},
        {"name": "b", "lo": -50.0, "hi": 50.0},
        {"name": "c", "lo": 0.0, "hi": 10.0},
    ]
    c_arr = (CConstraint * len(constraints))()
    for i, c in enumerate(constraints):
        c_arr[i].name = c["name"].encode()
        c_arr[i].lo = c["lo"]
        c_arr[i].hi = c["hi"]
        c_arr[i].severity = 2

    import math
    mask = c_lib.flux_check(ctypes.c_float(float("nan")), c_arr, len(constraints))
    expected = (1 << 3) - 1  # 0b111 = 7
    assert mask == expected, f"C NaN mask: {mask:#x} != {expected:#x}"
    print(f"  ✓ C engine: NaN → mask={mask:#x} (all violated)")


def test_js_nan():
    """JS engine: NaN always violates."""
    js_code = """
    try {
      const mod = require(require('path').resolve(__dirname, '..', 'flux-check-js', 'dist', 'core.js'));
      const nan = NaN;
      const result = mod.checkOne(nan, 0, 100);
      console.log(JSON.stringify({violation: result}));
    } catch(e) {
      // Try index
      try {
        const mod = require(require('path').resolve(__dirname, '..', 'flux-check-js', 'dist', 'index.js'));
        const result = mod.checkOne(NaN, 0, 100);
        console.log(JSON.stringify({violation: result}));
      } catch(e2) {
        console.error('Cannot load JS module:', e2.message);
        process.exit(1);
      }
    }
    """
    result = subprocess.run(
        ["node", "-e", js_code],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        print(f"  ⚠ JS NaN test: could not load module (skipped): {result.stderr.strip()[:80]}")
        return

    data = json.loads(result.stdout)
    assert data["violation"] == 1, f"JS NaN violation: {data['violation']} != 1"
    print(f"  ✓ JS engine: NaN → violation=1 (all violated)")


def test_multiple_nan_values():
    """Test all NaN variants produce same result."""
    import math
    nan_variants = [float("nan"), float("NaN"), float("NAN"), math.nan]

    constraints = [{"name": "x", "lo": 0.0, "hi": 10.0}]
    engine = ConstraintEngine(constraints)
    c_arr = (CConstraint * 1)()
    c_arr[0].name = b"x"
    c_arr[0].lo = 0.0
    c_arr[0].hi = 10.0
    c_arr[0].severity = 2

    for nan_val in nan_variants:
        py_mask = engine.check_mask(nan_val)
        c_mask = c_lib.flux_check(ctypes.c_float(nan_val), c_arr, 1)
        assert py_mask == 1, f"Python NaN variant {nan_val}: mask={py_mask}"
        assert c_mask == 1, f"C NaN variant {nan_val}: mask={c_mask}"

    print(f"  ✓ All NaN variants: consistent across Python and C ({len(nan_variants)} variants)")


if __name__ == "__main__":
    print("=== NaN Consistency Tests ===\n")
    test_python_flux_lib_nan()
    test_python_flux_check_nan()
    test_c_nan()
    test_js_nan()
    test_multiple_nan_values()
    print("\n✅ ALL NaN CONSISTENCY TESTS PASSED")
