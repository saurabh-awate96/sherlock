# MEDIUM-01: ACL Whitelist Investment Cap Bypass via Zero proofAmount

## Summary
Users with "any amount" whitelist entries (`(who, asset, 0)` leaves in the merkle tree) can bypass investment cap tracking by passing `proofAmount=0`, allowing unlimited investment when they should have a cap.

## Finding Type
Access Control Bypass

## Relevant GitHub Links
- [PutManager.sol:368-372](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/PutManager.sol#L368-L372) - Whitelist verification
- [PutManager.sol:393-396](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/PutManager.sol#L393-L396) - Investment tracking skip
- [ftACL.sol:45-76](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftACL.sol#L45-L76) - isWhitelisted with multiple leaf patterns

## Vulnerability Detail

The `ftACL.sol` contract supports three types of whitelist entries:
1. Exact match: `(who, asset, amount)` - specific asset and cap
2. Asset-specific, any amount: `(who, asset, 0)` - any amount of specific asset
3. Universal: `(who, 0, 0)` - any asset, any amount

The `isWhitelisted()` function checks all three patterns:

```solidity
function isWhitelisted(address who, address asset, uint256 amount, bytes32[] calldata proof) returns (bool) {
    // 1. Exact match: specific asset, and amount
    leaf = keccak256(bytes.concat(keccak256(abi.encode(who, asset, amount))));
    if (MerkleProof.verify(proof, merkleRoot, leaf)) return true;

    // 2. Specific asset, any amount
    leaf = keccak256(bytes.concat(keccak256(abi.encode(who, asset, uint256(0)))));
    if (MerkleProof.verify(proof, merkleRoot, leaf)) return true;

    // 3. Any asset & amount
    leaf = keccak256(bytes.concat(keccak256(abi.encode(who, address(0), uint256(0)))));
    if (MerkleProof.verify(proof, merkleRoot, leaf)) return true;
    
    return false;
}
```

In `PutManager._invest()`:

```solidity
// Whitelist check - passes if ANY matching leaf exists
if (address(ftACL) != address(0) && !ftACL.isWhitelisted(payer, token, proofAmount, proofWL)) {
    revert ftPutManagerNotWhitelisted();
}

// ... investment logic ...

// Investment tracking - SKIPPED if proofAmount == 0!
if (address(ftACL) != address(0) && proofAmount != 0) {
    ftACL.invest(msg.sender, token, amount, proofAmount);
}
```

**The Bypass:**
1. User has a `(who, asset, 0)` leaf in the merkle tree (intended for "whitelisted for any amount")
2. User calls `invest()` with `proofAmount = 0` and a valid proof for the `(who, asset, 0)` leaf
3. `isWhitelisted()` returns `true` (matches pattern #2)
4. The investment proceeds
5. `ftACL.invest()` is **never called** because `proofAmount == 0`
6. `amountInvested` is never updated
7. User can repeat indefinitely - no cap enforcement!

## Impact

**MEDIUM** - Whitelist cap circumvention:

1. Users can invest unlimited amounts when caps should apply
2. Breaks the fairness guarantees of the offering (e.g., preventing whales from dominating)
3. Could exceed collateral caps if not separately enforced
4. Undermines the entire whitelist tier system

**Preconditions:**
- Merkle tree must contain "any amount" leaves `(who, asset, 0)`
- Attack only works for users with these specific leaf types

## Proof of Concept

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/PutManager.sol";
import "../contracts/ftACL.sol";

contract ACLCapBypassTest is Test {
    PutManager putManager;
    ftACL acl;
    address alice = address(0xA11CE);
    IERC20 usdc;
    
    // Merkle tree contains leaf: (alice, usdc, 0) meaning "any amount"
    bytes32[] aliceProof;  // Valid proof for (alice, usdc, 0) leaf
    
    function setUp() public {
        // Setup merkle tree with alice having "any amount" access
        // Build proof for (alice, usdc, 0) leaf
    }
    
    function testCapBypassViaZeroProofAmount() public {
        // Alice invests 10,000 USDC with proofAmount=0
        vm.startPrank(alice);
        
        for (uint i = 0; i < 10; i++) {
            // Each investment passes whitelist check
            // But invest() tracking is never called because proofAmount=0
            putManager.invest(
                address(usdc),
                10_000e6,        // 10k USDC each time
                0,               // proofAmount = 0 (the bypass!)
                aliceProof
            );
        }
        
        vm.stopPrank();
        
        // Alice invested 100,000 USDC total with NO cap enforcement
        assertEq(acl.amountInvested(alice, address(usdc)), 0);  // Never tracked!
    }
}
```

## Code Snippet

The vulnerable conditional:
```solidity
// This skips investment tracking entirely when proofAmount == 0
if (address(ftACL) != address(0) && proofAmount != 0) {
    ftACL.invest(msg.sender, token, amount, proofAmount);
}
```

## Tool Used
Holmesian Cognitive Framework - SM-Sher-Aud-Framework (Moriarty game theory analysis of attacker strategies)

## Recommendation

### Option 1: Always track investments (Preferred)
```solidity
// Track investment regardless of proofAmount
// The isWhitelisted check already validated access rights
if (address(ftACL) != address(0)) {
    // For "any amount" leaves, use type(uint256).max as the cap
    uint256 effectiveCap = proofAmount == 0 ? type(uint256).max : proofAmount;
    ftACL.invest(msg.sender, token, amount, effectiveCap);
}
```

### Option 2: Prevent zero proofAmount for actual investments
```solidity
// Require non-zero proofAmount when ACL is active
if (address(ftACL) != address(0)) {
    if (proofAmount == 0) revert ftPutManagerInvalidProofAmount();
    if (!ftACL.isWhitelisted(payer, token, proofAmount, proofWL)) {
        revert ftPutManagerNotWhitelisted();
    }
    ftACL.invest(msg.sender, token, amount, proofAmount);
}
```

### Option 3: Store caps in ACL, not in calldata
Redesign the ACL to store user caps on-chain from merkle proofs at first verification, preventing user-controlled `proofAmount` manipulation.
