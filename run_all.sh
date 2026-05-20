#!/bin/bash
# run_all.sh — Run all FLUX integration tests and report results.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS_FILE="$SCRIPT_DIR/results.md"

echo "# FLUX Integration Test Results" > "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

TOTAL=0
PASSED=0
FAILED=0

run_test() {
    local name="$1"
    local cmd="$2"
    echo ""
    echo "▶ $name"
    echo "### $name" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"

    TOTAL=$((TOTAL + 1))

    if eval "$cmd" > /tmp/flux_test_output.txt 2>&1; then
        PASSED=$((PASSED + 1))
        echo "  ✅ PASSED"
        echo "| Status | Result |" >> "$RESULTS_FILE"
        echo "|--------|--------|" >> "$RESULTS_FILE"
        echo "| ✅ PASS | All assertions passed |" >> "$RESULTS_FILE"
        # Append details
        echo "" >> "$RESULTS_FILE"
        echo '<details><summary>Output</summary>' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        cat /tmp/flux_test_output.txt >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "</details>" >> "$RESULTS_FILE"
    else
        FAILED=$((FAILED + 1))
        echo "  ❌ FAILED"
        echo "| Status | Result |" >> "$RESULTS_FILE"
        echo "|--------|--------|" >> "$RESULTS_FILE"
        echo "| ❌ FAIL | See details below |" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '<details><summary>Output</summary>' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        cat /tmp/flux_test_output.txt >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "</details>" >> "$RESULTS_FILE"
    fi
    echo "" >> "$RESULTS_FILE"
}

echo "═══════════════════════════════════════════════"
echo "  FLUX Integration Test Suite"
echo "═══════════════════════════════════════════════"

run_test "Cross-Language Parity (Python vs C)" "python3 $SCRIPT_DIR/test_cross_language.py"
run_test "Presets Parity (All Packages)" "python3 $SCRIPT_DIR/test_presets_parity.py"
run_test "NaN Consistency (All Packages)" "python3 $SCRIPT_DIR/test_nan_consistency.py"
run_test "Fracture Equivalence (Python, C, Rust)" "python3 $SCRIPT_DIR/test_fracture_equivalence.py"

# ── Summary ─────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════"
echo "  SUMMARY"
echo "═══════════════════════════════════════════════"

echo "## Summary" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "| Metric | Count |" >> "$RESULTS_FILE"
echo "|--------|-------|" >> "$RESULTS_FILE"
echo "| Total  | $TOTAL |" >> "$RESULTS_FILE"
echo "| Passed | $PASSED |" >> "$RESULTS_FILE"
echo "| Failed | $FAILED |" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [ "$FAILED" -eq 0 ]; then
    echo "  ✅ $PASSED/$TOTAL tests passed — ALL GREEN"
    echo "**Result: ALL GREEN** ✅" >> "$RESULTS_FILE"
else
    echo "  ❌ $FAILED/$TOTAL tests failed"
    echo "**Result: $FAILED FAILURES** ❌" >> "$RESULTS_FILE"
fi

echo ""
echo "Full results: $RESULTS_FILE"
