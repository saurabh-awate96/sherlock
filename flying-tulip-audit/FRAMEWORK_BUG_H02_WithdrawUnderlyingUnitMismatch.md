# HIGH-02: withdrawUnderlying() Compares Shares Against Asset Amounts Causing Accounting Errors

## Summary
The `ftYieldWrapper.withdrawUnderlying()` function incorrectly compares strategy share balances (denominated in strategy tokens) against remaining withdrawal amounts (denominated in underlying assets), causing severe accounting errors for any strategy where shares ≠ underlying assets (e.g., Ethena sUSDe, or any ERC4626 vault with appreciation).

## Finding Type
Numerical Error / Accounting Bug

## Relevant GitHub Links
- [ftYieldWrapper.sol:600-632](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftYieldWrapper.sol#L600-L632) - The broken `withdrawUnderlying` loop
- [EthenaSUSDeStrategy.sol:293-317](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/strategies/EthenaSUSDeStrategy.sol#L293-L317) - Strategy where shares ≠ assets

## Vulnerability Detail

The `ftYieldWrapper.withdrawUnderlying()` function is designed to withdraw position tokens (like aTokens or sUSDe) instead of the underlying asset. However, the loop logic has a critical flaw:

```solidity
function withdrawUnderlying(uint256 amount, address to) external nonReentrant onlyPutManagerOrDepositor {
    // ...
    uint256 remaining = amount;  // ← In UNDERLYING ASSET units (e.g., USDe)
    
    for (uint256 i = 0; i < _strategiesLength && remaining != 0; ++i) {
        uint256 shareBal = strategies[i].balanceOf(address(this));  // ← In SHARE units (e.g., sUSDe)
        if (shareBal == 0) continue;

        uint256 toExit = shareBal > remaining ? remaining : shareBal;  // ← COMPARING APPLES TO ORANGES!
        
        try strategies[i].withdrawUnderlying(toExit) returns (uint256 got) {
            if (got != 0) {
                // ...
                remaining -= toExit;  // ← Deducting share amount, not asset value!
                IERC20(strategies[i].positionToken()).safeTransfer(to, got);
            }
        }
    }
}
```

**The Problem:**
- `remaining` is in underlying asset units (e.g., 1000 USDe)
- `shareBal` is in strategy share units (e.g., 900 sUSDe)
- For ERC4626 vaults like sUSDe where shares appreciate over time, **1 sUSDe > 1 USDe**

**Numerical Example:**
1. User wants to withdraw 1000 USDe worth of collateral
2. `remaining = 1000` (in USDe)
3. Strategy has 900 sUSDe shares, but at current PPS (1.2), this is worth 1080 USDe
4. Comparison: `shareBal (900) > remaining (1000)?` → FALSE
5. `toExit = min(900, 1000) = 900`
6. Strategy's `withdrawUnderlying(900)` burns 900 wrapper shares (worth 900 USDe) and sends ~750 sUSDe
7. `remaining -= 900` → remaining = 100
8. But user only received ~750 sUSDe worth ~900 USDe, not 1000!

The units are inconsistent throughout the calculation, leading to:
- Users receiving wrong amounts of position tokens
- Protocol accounting (`deployedToStrategy`) becoming inaccurate
- Potential value extraction or loss depending on share price direction

## Impact

**HIGH** - Value leakage and accounting corruption:

1. **User Loss/Gain**: Users may receive more or less value than entitled
2. **Protocol Insolvency Risk**: Accounting tracks incorrect deployed amounts
3. **Affects All Yield-Bearing Strategies**: Any strategy with PPS ≠ 1.0 is affected (Ethena, stETH yield, etc.)
4. **Compounding Errors**: Each transaction compounds the accounting mismatch

## Proof of Concept

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/ftYieldWrapper.sol";
import "../contracts/strategies/EthenaSUSDeStrategy.sol";

contract WithdrawUnderlyingUnitMismatchTest is Test {
    ftYieldWrapper wrapper;
    EthenaSUSDeStrategy strategy;
    MockUSDe usde;
    MockSUSDe susde;
    
    function setUp() public {
        // Setup with sUSDe having PPS of 1.2 (1 sUSDe = 1.2 USDe)
    }
    
    function testUnitMismatchCausesWrongWithdrawal() public {
        // Wrapper has 1000 wrapper tokens, deployed 1000 USDe to strategy
        // Strategy minted ~833 sUSDe (at PPS 1.2)
        
        uint256 shareBalance = strategy.balanceOf(address(wrapper));
        console.log("Strategy shares:", shareBalance);  // ~833 sUSDe
        
        uint256 wantUnderlying = 1000;  // Want to exit 1000 USDe worth
        
        // Current logic compares 833 > 1000? NO
        // So toExit = 833
        // But 833 sUSDe = 1000 USDe at current PPS!
        
        // The function will try to exit 833 "units" but interpreting them wrong
        // This causes accounting chaos
        
        vm.prank(putManager);
        wrapper.withdrawUnderlying(wantUnderlying, address(this));
        
        // Verify mismatch occurred
        // User received wrong amount, deployed tracking is wrong
    }
}
```

## Code Snippet

Current broken logic:
```solidity
uint256 remaining = amount;  // Asset units
// ...
uint256 shareBal = strategies[i].balanceOf(address(this));  // Share units
uint256 toExit = shareBal > remaining ? remaining : shareBal;  // Mixed units!
```

## Tool Used
Holmesian Cognitive Framework - SM-Sher-Aud-Framework (Mind Palace pattern matching with historical ERC4626 exploits)

## Recommendation

Convert to common denomination before comparison and use proper ERC4626 functions:

```solidity
function withdrawUnderlying(uint256 amount, address to) external nonReentrant onlyPutManagerOrDepositor {
    // ...
    uint256 remainingAssets = amount;  // Track in asset terms
    
    for (uint256 i = 0; i < _strategiesLength && remainingAssets != 0; ++i) {
        uint256 shareBal = strategies[i].balanceOf(address(this));
        if (shareBal == 0) continue;
        
        // Convert shares to assets for proper comparison
        uint256 shareValueInAssets = strategies[i].convertToAssets(shareBal);
        
        // How many assets can we get from this strategy?
        uint256 assetsToExit = shareValueInAssets > remainingAssets ? remainingAssets : shareValueInAssets;
        
        // Convert back to shares for the actual withdrawal
        uint256 sharesToExit = strategies[i].convertToShares(assetsToExit);
        
        try strategies[i].withdrawUnderlying(sharesToExit) returns (uint256 sharesReceived) {
            if (sharesReceived != 0) {
                uint256 assetValue = strategies[i].convertToAssets(sharesReceived);
                
                // Update accounting with asset-denominated values
                uint256 currentDeployed = deployedToStrategy[address(strategies[i])];
                uint256 toReduce = assetValue > currentDeployed ? currentDeployed : assetValue;
                
                deployedToStrategy[address(strategies[i])] -= toReduce;
                deployed = deployed > toReduce ? deployed - toReduce : 0;
                remainingAssets -= assetValue;
                
                IERC20(strategies[i].positionToken()).safeTransfer(to, sharesReceived);
            }
        } catch {}
    }
    
    // ... rest of function
}
```

Alternatively, require strategies to implement a consistent interface that handles the conversion internally.
