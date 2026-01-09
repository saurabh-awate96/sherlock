# MEDIUM-02: EthenaSUSDeStrategy Queue Entries Never Cleared Leading to State Bloat and Incorrect Head Tracking

## Summary
The `EthenaSUSDeStrategy` contract's withdrawal queue never deletes completed entries and improperly manages the `head` pointer, leading to unbounded storage growth and potential confusion in queue state management.

## Finding Type  
State Management / Storage Inefficiency

## Relevant GitHub Links
- [EthenaSUSDeStrategy.sol:275-285](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/strategies/EthenaSUSDeStrategy.sol#L275-L285) - claimQueued with improper head management
- [EthenaSUSDeStrategy.sol:244-272](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/strategies/EthenaSUSDeStrategy.sol#L244-L272) - withdrawQueued that creates entries

## Vulnerability Detail

The Ethena strategy implements a queued withdrawal system using escrow contracts:

```solidity
mapping(uint256 id => address escrow) public queue;
uint256 public head;
uint256 public tail;

function withdrawQueued(uint256 amount) external nonReentrant onlyftYieldWrapper returns (uint256 id) {
    // ... validation and escrow creation ...
    id = tail;
    queue[id] = address(esc);
    tail++;
    emit WithdrawQueued(msg.sender, amount, id);
}

function claimQueued(uint256 id) external nonReentrant onlyftYieldWrapper returns (uint256 received) {
    address q = queue[id];
    head = id;  // ⚠️ BUG: Sets head to id, not id+1. Also never validates id >= head
    received = SUSDeCoolingEscrow(q).claimToBeneficiary();
    // ⚠️ BUG: queue[id] is never deleted!
    emit WithdrawClaimed(msg.sender, received, id);
}
```

**Issues Identified:**

1. **Queue Entry Never Deleted**: After claiming, `queue[id]` still points to the old escrow address. While the escrow is drained (so re-claiming reverts), the storage slot is never cleared.

2. **Head Pointer Incorrectly Set**: `head = id` instead of `head = id + 1`. This means:
   - After claiming id=5, head=5 (should be head=6)
   - The head never advances past claimed entries properly

3. **No FIFO Enforcement**: There's no check that `id >= head`, allowing out-of-order claims

4. **No Range Validation**: The code doesn't verify `id < tail`

## Impact

**MEDIUM** - Storage inefficiency and state confusion:

1. **Unbounded Storage Growth**: Every queued withdrawal permanently occupies storage
2. **Gas Costs Over Time**: As the queue grows, any iteration over tracked state becomes more expensive
3. **State Confusion**: External systems reading `head` get incorrect information about queue progress
4. **No Direct Fund Risk**: Escrows prevent double-claiming (second claim reverts), so no direct value extraction

**Likelihood**: Low to Medium (operational issue that accumulates over time)
**Impact**: Medium (storage costs, potential for off-chain system confusion)

## Proof of Concept

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/strategies/EthenaSUSDeStrategy.sol";

contract QueueStorageBloatTest is Test {
    EthenaSUSDeStrategy strategy;
    
    function testQueueNeverCleared() public {
        // Simulate many queue operations
        for (uint i = 0; i < 100; i++) {
            vm.prank(address(wrapper));
            uint256 id = strategy.withdrawQueued(1000e18);
            
            // Wait for cooldown
            vm.warp(block.timestamp + 8 days);
            
            // Claim
            vm.prank(address(wrapper));
            strategy.claimQueued(id);
        }
        
        // After 100 operations:
        assertEq(strategy.tail(), 100);  // Expected
        assertEq(strategy.head(), 99);   // Should be 100, but is 99 due to bug
        
        // All 100 queue entries still exist in storage
        for (uint i = 0; i < 100; i++) {
            assertTrue(strategy.queue(i) != address(0));  // Never cleared!
        }
        
        // This is ~100 storage slots (~3200 bytes) wasted permanently
    }
}
```

## Code Snippet

Current broken implementation:
```solidity
function claimQueued(uint256 id) external returns (uint256 received) {
    address q = queue[id];
    head = id;  // Wrong: should be id + 1
    received = SUSDeCoolingEscrow(q).claimToBeneficiary();
    // Missing: delete queue[id];
}
```

## Tool Used
Holmesian Cognitive Framework - SM-Sher-Aud-Framework (Watson observation of state management patterns)

## Recommendation

```solidity
function claimQueued(uint256 id) external nonReentrant onlyftYieldWrapper returns (uint256 received) {
    // Validate queue bounds
    require(id >= head && id < tail, "Invalid queue id");
    
    address q = queue[id];
    require(q != address(0), "Already claimed");
    
    // Claim from escrow
    received = SUSDeCoolingEscrow(q).claimToBeneficiary();
    
    // Clear storage and advance head if claiming the head entry
    delete queue[id];
    
    // Only advance head if this was the head entry
    // Alternative: Allow out-of-order but just delete entries
    if (id == head) {
        // Advance head past all consecutive claimed (deleted) entries
        while (head < tail && queue[head] == address(0)) {
            head++;
        }
    }
    
    emit WithdrawClaimed(msg.sender, received, id);
}
```

For stricter FIFO enforcement:
```solidity
function claimQueued(uint256 id) external nonReentrant onlyftYieldWrapper returns (uint256 received) {
    require(id == head, "Must claim in order");
    require(id < tail, "Invalid queue id");
    
    address q = queue[id];
    require(q != address(0), "Already claimed");
    
    received = SUSDeCoolingEscrow(q).claimToBeneficiary();
    
    delete queue[id];
    head = id + 1;
    
    emit WithdrawClaimed(msg.sender, received, id);
}
```
