## Summary

The `StEthStrategy` fails to account for **7-14 days worth of capital locked in the Lido withdrawal queue**, causing the `ftYieldWrapper` to report an artificially low TVL. This inaccurate accounting triggers a **False-Positive Denial of Service (DoS)** in the `CircuitBreaker`, which calculates withdrawal capacities based on the reported TVL and erroneously blocks valid user withdrawals as "limit-exceeding."

## Links to affected code

* [StEthStrategy.sol#L157-L160](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/strategies/StEthStrategy.sol#L157-L160)
* [ftYieldWrapper.sol#L588](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftYieldWrapper.sol#L588)

## Root Cause

In [StEthStrategy.sol:157-160](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/strategies/StEthStrategy.sol#L157-L160), the `valueOfCapital()` function only returns liquid assets:

```solidity
function valueOfCapital() public view returns (uint256) {
    uint256 liquid = WETH.balanceOf(address(this)) + address(this).balance;
    return liquid + stETH.balanceOf(address(this));
    // MISSING: Assets in Lido withdrawal queue (unstETH NFTs)
}
```

When a user initiates a withdrawal via `withdrawQueued()`, the stETH is burned and an unstETH NFT is created—but this NFT is NOT counted in `valueOfCapital()`. Capital "disappears" from accounting for 7-14 days.

**This is OPPOSITE to the Phantom TVL issue (#54)**: Here TVL is under-reported (CB too restrictive), not over-reported (CB too permissive).

## Internal Pre-conditions

1. `ftYieldWrapper` utilizes the `StEthStrategy`.
2. A portion of capital has entered the Lido withdrawal queue.
3. `CircuitBreaker` is active with configured rate limits.

## External Pre-conditions

1. Lido protocol has a non-zero withdrawal time (7-14 days typical).

## Attack Path

1. **Initial State**: Real TVL = 1000 ETH (500 stETH + 500 in Lido queue). `StEthStrategy.valueOfCapital()` reports: 500 ETH (missing queue).
2. **CB Configuration**: 10% withdrawal limit per period.
3. **User Attempts Withdrawal**: User requests 80 ETH (8% of real TVL).
4. **CB Calculation**: CB calculates limit as 10% of reported 500 = 50 ETH.
5. **Result**: 80 > 50 → Transaction REVERTS. User's valid 8% withdrawal is blocked as if it were 16%.

## Impact

**False-Positive Denial of Service (High)**. The Circuit Breaker is designed to protect against excessive withdrawals. By under-reporting TVL, it over-protects and harms legitimate users. All users face restricted withdrawals for 7-14 days per queue cycle.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract StEthTVLUnderReportTest is Test {
    function test_WithdrawalQueueExcludedFromTVL() public {
        // Setup: 1000 ETH deposited
        uint256 stEthBalance = 500 ether;
        uint256 queuedAmount = 500 ether;
        
        // What valueOfCapital returns
        uint256 reportedTVL = stEthBalance; // 500
        
        // What it SHOULD return
        uint256 realTVL = stEthBalance + queuedAmount; // 1000
        
        // CB rate limit of 10%
        uint256 rateLimit = 10;
        uint256 userWithdrawal = 80 ether;
        
        // CB calculation with REPORTED TVL
        uint256 cbAllowedReported = (reportedTVL * rateLimit) / 100; // 50 ETH
        
        // CB calculation with REAL TVL
        uint256 cbAllowedReal = (realTVL * rateLimit) / 100; // 100 ETH
        
        // User's 80 ETH withdrawal:
        assertLt(userWithdrawal, cbAllowedReal, "Should be allowed (8% of real TVL)");
        assertGt(userWithdrawal, cbAllowedReported, "Incorrectly blocked (16% of reported TVL)");
        
        console.log("RESULT: Valid 8% withdrawal blocked as 16%");
    }
}
```

## Mitigation

Update `valueOfCapital()` to include pending withdrawal queue value:

```solidity
function valueOfCapital() public view returns (uint256) {
    uint256 liquid = WETH.balanceOf(address(this)) + address(this).balance;
    uint256 staked = stETH.balanceOf(address(this));
    uint256 queued = _pendingWithdrawalValue();
    return liquid + staked + queued;
}
```
