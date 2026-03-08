# Experimental DP-SGD Research

⚠️ **NOT FOR PRODUCTION USE**

This directory contains experimental implementations and validation reports for differential privacy research.

## Contents

### `/reports/`
- `federated_validation_results.json` - Federated validation comparing batch-level vs strict per-sample DP

## Strict Per-Sample DP-SGD Status

**Validation Date:** March 1, 2026  
**Status:** ❌ REJECTED for production

**Key Findings:**
- Convergence: 24× worse than batch-level DP (Loss: 128.41 vs 5.35)
- Runtime: 1.09× slowdown (acceptable)
- Epsilon: Same budget (5.0 per 5 rounds)
- **Blocker:** Unacceptable loss degradation

**Recommendation:** Continue using batch-level DP in production.

## Implementation Location

Experimental strict DP code remains in:
- `backend/app/ml/tft_forecaster.py::_train_strict_dp()` (with runtime safeguard)

**Production Lock:** `STRICT_DP_MODE = False` (hardcoded, safeguarded)

## References

- Archived test modules: `backend/app/ml/tft_dp_sgd_*_test.py`
- Documentation: Root directory `DP_SGD_*.md` files
- ADR: `ADR-001_STRICT_DP_SGD_DECISION.md`
