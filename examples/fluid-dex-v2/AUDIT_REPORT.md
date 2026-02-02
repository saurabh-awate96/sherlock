# Fluid DEX V2 Security Audit Report

**Repository:** https://github.com/sherlock-audit/2026-01-fluid-dex-v2-saurabh-awate96
**Audit Date:** February 1, 2026
**Scope:** fluid-contracts @ 904c2989aa404ecb9cf75eb1efa1a5fa526007b0

---

## Executive Summary

This security audit was conducted on the Fluid DEX V2 codebase, which includes:
- **DEX V2 Contracts**: D3 (Smart Collateral) and D4 (Smart Debt) pools with concentrated liquidity
- **Money Market Contracts**: Lending protocol with NFT-based position management

The codebase is complex and makes extensive use of:
- Unchecked arithmetic for gas optimization
- BigMath library for compressed storage with precision loss
- Cross-contract callbacks between DEX and Money Market
- Transient storage for reentrancy protection (Cancun-specific)

---

## Findings Summary

| Severity | Count |
|----------|-------|
| High     | 3     |
| Medium   | 4     |
| Low      | 3     |
| Informational | 4 |

---

## High Severity Findings

### H-01: Fee Growth Underflow Risk in Tick Crossing

**File:** `contracts/protocols/dexV2/dexTypes/common/d3d4common/swapModuleInternals.sol`
**Lines:** 231-232

**Description:**
During tick crossing in swaps, the fee growth outside values are calculated using unchecked subtraction:

```solidity
tickData_.feeGrowthOutside0X102 = feeGrowthGlobal0X102_ - tickData_.feeGrowthOutside0X102;
tickData_.feeGrowthOutside1X102 = feeGrowthGlobal1X102_ - tickData_.feeGrowthOutside1X102;
```

The fee growth global variables are stored using BigMath with only 74 most significant bits retained (as per README design notes). Due to precision loss during conversion to/from BigNumber format, there's a potential scenario where `feeGrowthOutside > feeGrowthGlobal` after storage and retrieval, causing an underflow.

**Impact:**
- Incorrect fee distribution to LP positions
- Potential loss of LP fees
- Corrupted tick state affecting future swaps

**Recommendation:**
Add a check before subtraction or use a saturating subtraction pattern:
```solidity
if (feeGrowthGlobal0X102_ >= tickData_.feeGrowthOutside0X102) {
    tickData_.feeGrowthOutside0X102 = feeGrowthGlobal0X102_ - tickData_.feeGrowthOutside0X102;
} else {
    tickData_.feeGrowthOutside0X102 = 0; // or handle edge case appropriately
}
```

---

### H-02: Division by Zero in Dynamic Fee Calculation

**File:** `contracts/protocols/dexV2/dexTypes/common/d3d4common/helpers.sol`
**Line:** 214

**Description:**
The zero price impact price calculation can result in division by zero:

```solidity
d_.zeroPriceImpactPriceX96 = (FM.mulDiv(sqrtPriceX96_, sqrtPriceX96_, Q96) * SIX_DECIMALS) 
    / uint256((int256(SIX_DECIMALS) + netPriceImpact_));
```

The `netPriceImpact_` is bounded by X20 (approximately 1,048,575), which when negative could theoretically equal -SIX_DECIMALS (-1,000,000), causing the denominator to become zero.

**Impact:**
- Swap transactions would revert
- Potential DoS on specific pools if price impact reaches critical values

**Recommendation:**
Add validation to ensure the denominator cannot be zero:
```solidity
int256 denominator = int256(SIX_DECIMALS) + netPriceImpact_;
if (denominator <= 0) {
    revert FluidDexV2D3D4Error(ErrorTypes.Helpers__InvalidDynamicFee);
}
```

---

### H-03: Liquidation Value Rounding Exploitation

**File:** `contracts/protocols/moneyMarket/core/liquidateModule/main.sol`
**Lines:** 131-134, 220-227, 274-276

**Description:**
The liquidation module applies multiple consecutive rounding operations that compound in favor of the protocol:

```solidity
// Line 131-133
v_.paybackValue = ((paybackAmount_ * tokenPrice_) - 1) / EIGHTEEN_DECIMALS;
if (v_.paybackValue > 0) {
    v_.paybackValue -= 1;
}

// Line 274-275
v_.withdrawValue = ((v_.withdrawValue * (THREE_DECIMALS + liquidationPenalty_)) - 1) / THREE_DECIMALS;
if (v_.withdrawValue > 0) v_.withdrawValue -= 1;
```

While each individual rounding is small, the cumulative effect across multiple calculations could result in liquidators paying slightly less than they should or receiving slightly more collateral.

**Impact:**
- Small fund leakage over many liquidations
- Incentivizes dust liquidations to maximize rounding profits
- Potential for strategic manipulation of liquidation timing

**Recommendation:**
Consider using a single rounding at the end of calculations rather than multiple intermediate roundings, or implement explicit checks for minimum liquidation sizes that account for rounding effects.

---

## Medium Severity Findings

### M-01: Per-Dex Reentrancy Lock Allows Cross-Pool Attacks

**File:** `contracts/libraries/dexV2PoolLock.sol`
**Lines:** 4-20

**Description:**
The reentrancy lock is per-dexId, not global:

```solidity
function lock(bytes32 dexId_) internal {
    bytes32 key = keccak256(abi.encode(REENTRANCY_LOCK_SLOT, dexId_));
    assembly {
        if tload(key) { revert(0, 0) }
        tstore(key, 1)
    }
}
```

This allows an attacker who gains control during a callback on Pool A to potentially call Pool B without triggering reentrancy protection.

**Impact:**
- Cross-pool price manipulation during callbacks
- Potential for flash loan attacks across multiple pools

**Recommendation:**
Consider implementing a global lock in addition to per-dex locks for critical operations, or ensure all callback paths cannot interact with other pools.

---

### M-02: Timestamp Overflow in Dynamic Fee Decay Calculation

**File:** `contracts/protocols/dexV2/dexTypes/common/d3d4common/helpers.sol`
**Lines:** 169-180

**Description:**
Only 15 bits of timestamp are stored (maximum ~32,768 seconds or ~9 hours):

```solidity
uint256 newLastUpdateTimestamp_ = block.timestamp & X15;
uint256 lastUpdateTimestamp_ = (dexVariables2_ >> DSL.BITS_DEX_V2_VARIABLES2_LAST_UPDATE_TIMESTAMP) & X15;

if (newLastUpdateTimestamp_ < lastUpdateTimestamp_) {
    timeElapsed_ = X15 + 1 + newLastUpdateTimestamp_ - lastUpdateTimestamp_;
} else {
    timeElapsed_ = newLastUpdateTimestamp_ - lastUpdateTimestamp_;
}
```

If a pool has no swaps for more than 9 hours, the timestamp wraps and the "minimum" time elapsed calculation may not reflect the actual time passed (could be 9 hours, 18 hours, 27 hours, etc.).

**Impact:**
- Incorrect fee decay calculations after extended idle periods
- Users may be charged higher fees than intended (as noted in README design choices)

**Recommendation:**
Document this behavior clearly or increase the timestamp resolution to cover longer periods.

---

### M-03: Disabled Liquidity Limit Checks in Remove Liquidity

**File:** `contracts/protocols/dexV2/dexTypes/common/d3d4common/userModuleInternals.sol`
**Lines:** 238-239, 259-260, 292-293

**Description:**
Liquidity limit checks have been disabled for removeLiquidity to prevent liquidations from getting stuck:

```solidity
// NOTE: Removing liquidity limit check from _removeLiquidity function because it can cause liquidations to get stuck
// _verifyLiquidityLimits(liquidityDecreaseRaw_);
```

**Impact:**
- Potential for dust attacks where minimal liquidity is repeatedly added/removed
- Gas griefing through many small operations

**Recommendation:**
Implement separate paths for liquidation vs user-initiated withdrawals, allowing stricter limits on the latter.

---

### M-04: Position Index Swap Logic After Deletion

**File:** `contracts/protocols/moneyMarket/core/liquidateModule/main.sol`
**Lines:** 238-241

**Description:**
When a payback position is deleted during liquidation, the withdraw position index may be updated:

```solidity
if (v_.positionDeleted && params_.withdrawPositionIndex == v_.numberOfPositions) {
    params_.withdrawPositionIndex = params_.paybackPositionIndex;
}
```

This assumes that position deletion always swaps the last position into the deleted slot. If the storage behavior differs, this could cause incorrect position access.

**Impact:**
- Potential for liquidating wrong collateral position
- Could lead to unexpected behavior in edge cases

**Recommendation:**
Add explicit validation that the new position index contains expected data before proceeding.

---

## Low Severity Findings

### L-01: Bare Revert Statements Without Error Messages

**Files:** Multiple
**Examples:** `operateModule/main.sol:15`, `callbackModule/main.sol:17`, `main.sol:49`

**Description:**
Many revert statements use `revert()` without error types or messages, making debugging difficult.

**Recommendation:**
Use custom error types consistently throughout the codebase.

---

### L-02: DEX_V2.startOperation Return Value Not Validated

**File:** `contracts/protocols/moneyMarket/core/operateModule/main.sol`
**Line:** 113

**Description:**
The return value from `DEX_V2.startOperation` is not validated in the operate module:

```solidity
DEX_V2.startOperation(abi.encode(dexKey_, s_));
```

**Impact:**
If the operation fails silently, the Money Market state may become inconsistent with DEX state.

**Recommendation:**
Validate return values or use explicit success checks.

---

### L-03: Unchecked Liquidity Multiplication Could Overflow

**File:** `contracts/protocols/dexV2/dexTypes/common/d3d4common/helpers.sol`
**Line:** 137

**Description:**
In `_verifyLiquidityChangeLimits`, the multiplication could overflow for very large liquidity values:

```solidity
unchecked {
    if (liquidityChange_ < (liquidity_ / NINE_DECIMALS) || 
        (liquidity_ != 0 && liquidityChange_ > (liquidity_ * NINE_DECIMALS))) {
```

**Impact:**
Could cause unexpected reverts or incorrect validation for edge cases.

**Recommendation:**
Move the multiplication check outside of unchecked or use SafeMath for this specific check.

---

## Informational Findings

### I-01: Read-Only Reentrancy Accepted Risk

The protocol explicitly accepts read-only reentrancy as a known risk. External protocols integrating with Fluid should be aware that reading state during a callback may return inconsistent values.

### I-02: No Bad Debt Absorption Mechanism

The Money Market contracts do not include functionality to absorb or socialize bad debt. If positions become underwater and liquidation fails, bad debt will accumulate.

### I-03: Protocol Fees Tracked Off-Chain

Protocol fees are not collected or accounted for on-chain. This is a deliberate design choice but requires robust off-chain infrastructure.

### I-04: BigMath Precision Loss by Design

The use of BigMath for compressed storage intentionally trades precision for gas efficiency. Integrators should account for this in their implementations.

---

## Recommendations Summary

1. **Critical:** Implement overflow/underflow protection for fee growth calculations in tick crossing
2. **Critical:** Add division-by-zero check in dynamic fee calculation
3. **High:** Review and potentially consolidate rounding operations in liquidation
4. **Medium:** Consider global reentrancy protection for cross-pool security
5. **Medium:** Add comprehensive error messages for debugging
6. **Low:** Validate return values from external contract calls

---

## Files Reviewed

- `contracts/libraries/bigMathMinified.sol`
- `contracts/libraries/dexV2PoolLock.sol`
- `contracts/protocols/dexV2/base/core/main.sol`
- `contracts/protocols/dexV2/dexTypes/common/d3d4common/swapModuleInternals.sol`
- `contracts/protocols/dexV2/dexTypes/common/d3d4common/userModuleInternals.sol`
- `contracts/protocols/dexV2/dexTypes/common/d3d4common/helpers.sol`
- `contracts/protocols/dexV2/dexTypes/d3/core/swapModule.sol`
- `contracts/protocols/dexV2/dexTypes/d4/core/swapModule.sol`
- `contracts/protocols/moneyMarket/core/liquidateModule/main.sol`
- `contracts/protocols/moneyMarket/core/operateModule/main.sol`
- `contracts/protocols/moneyMarket/core/callbackModule/main.sol`

---

## Disclaimer

This audit report represents a point-in-time assessment based on the code available at commit `904c2989aa404ecb9cf75eb1efa1a5fa526007b0`. Security audits cannot guarantee the absence of vulnerabilities. The findings and recommendations are based on the auditor's professional judgment and should be validated by the development team.
