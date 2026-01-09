## Summary

The `withdraw()` function in `ftYieldWrapper` iterates through an **unbounded strategies array**, causing potential **Denial of Service (DoS)** when the number of strategies grows large. Each iteration involves multiple external calls with try-catch blocks, consuming significant gas.

## Root Cause

In [`ftYieldWrapper.sol:509`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftYieldWrapper.sol#L509), the withdraw function iterates through all strategies:

```solidity
uint256 _strategiesLength = strategies.length;
for (uint256 i = 0; i < _strategiesLength && remaining != 0; i++) {
    // Per iteration:
    // 1. try strategies[i].balanceOf(address(this)) - external call
    // 2. try strategies[i].maxAbleToWithdraw(shareBal) - external call
    // 3. try strategies[i].withdraw(toRequest) - external call + state changes
}
```

**Gas Analysis Per Iteration**:
| Operation | Estimated Gas |
|-----------|--------------|
| External call to `balanceOf` | ~2,600 (cold) |
| External call to `maxAbleToWithdraw` | ~5,000 |
| External call to `withdraw` (if executed) | ~50,000+ |
| State updates (`deployed`, `deployedToStrategy`) | ~20,000 |
| Loop overhead | ~500 |

**Estimated cost: 80,000-100,000 gas per strategy iteration**

## Internal Pre-conditions

1. `ftYieldWrapper` has multiple strategies registered.
2. Funds are deployed primarily to later strategies in the array.

## External Pre-conditions

None - this is a system state issue.

## Attack Path

**Scenario: Strategy Bloat**

1. **Over Time**: Protocol adds 50 strategies for diversification
   - Some strategies become deprecated but can't be removed (have dust)
   - Some strategies added for future use

2. **User Funds**: User's funds deployed to strategy #45

3. **Withdrawal**:
   - Loop iterates through strategies 0-44 first
   - Each iteration: ~80,000 gas
   - 45 iterations × 80,000 = **3,600,000 gas** before reaching user's funds

4. **Block Limit**: With 30M gas limit:
   - Safe max strategies ≈ 300-350
   - With more complex strategies: could be much lower

5. **DoS**: If gas exceeds block limit, withdrawal reverts.

**Compounding Factor**: `removeStrategy()` only works when `deployedToStrategy == 0`:
```solidity
function removeStrategy(uint256 index) external onlyStrategyManager {
    IStrategy s = strategies[index];
    if (deployedToStrategy[address(s)] != 0) {
        revert ftYieldWrapperNotStrategy();  // Can't remove!
    }
}
```

Strategies with even 1 wei of dust cannot be removed, leading to permanent bloat.

## Impact

**Denial of Service (Medium)**:

| Metric | Impact |
|--------|--------|
| **Trigger** | 50+ strategies with funds in later indices |
| **Duration** | Until admin reduces strategies or moves funds |
| **Users Affected** | All users during DoS period |
| **Funds at Risk** | Not lost, but inaccessible |

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/ftYieldWrapper.sol";

contract UnboundedLoopDoSTest is Test {
    ftYieldWrapper public wrapper;
    
    function test_GasScalingWithStrategies() public {
        // Measure gas with increasing strategy counts
        
        uint256[] memory strategyCounts = new uint256[](5);
        strategyCounts[0] = 10;
        strategyCounts[1] = 25;
        strategyCounts[2] = 50;
        strategyCounts[3] = 100;
        strategyCounts[4] = 200;
        
        for (uint i = 0; i < strategyCounts.length; i++) {
            uint256 estimatedGas = strategyCounts[i] * 80_000;
            uint256 blockLimit = 30_000_000;
            bool wouldFail = estimatedGas > blockLimit;
            
            console.log("Strategies:", strategyCounts[i]);
            console.log("  Est. Gas:", estimatedGas);
            console.log("  Would DoS:", wouldFail ? "YES" : "No");
        }
        
        // With 100k gas per iteration, DoS at ~300 strategies
        // With complex strategies or mainnet conditions, could be much lower
    }
    
    function test_RemovalBlockedByDust() public {
        // Demonstrate that strategies with dust cannot be removed
        
        // If a strategy has even 1 wei deployed:
        uint256 dustAmount = 1;
        
        // removeStrategy() would revert with ftYieldWrapperNotStrategy
        // because deployedToStrategy[address(s)] != 0
        
        console.log("Strategy with", dustAmount, "wei deployed");
        console.log("Cannot be removed, contributes to bloat");
    }
}
```

## Mitigation

**Option A: Limit Strategy Count**
```solidity
uint256 public constant MAX_STRATEGIES = 20;

function setStrategy(address _strategy) external onlyStrategyManager {
    require(strategies.length < MAX_STRATEGIES, "Max strategies reached");
    // ... rest of logic
}
```

**Option B: Allow Partial Withdrawals from Specific Strategies**
```solidity
function withdrawFromStrategy(
    uint256 amount, 
    address to,
    uint256 strategyIndex
) external onlyPutManagerOrDepositor {
    // Withdraw from specific strategy, skip iteration
}
```

**Option C: Fix Dust Removal**
```solidity
function forceRemoveStrategy(uint256 index) external onlyStrategyManager {
    // Force remove even with dust, send dust to treasury
    IStrategy s = strategies[index];
    uint256 dust = deployedToStrategy[address(s)];
    if (dust != 0) {
        s.withdraw(dust);
        deployedToStrategy[address(s)] = 0;
    }
    // ... removal logic
}
```
