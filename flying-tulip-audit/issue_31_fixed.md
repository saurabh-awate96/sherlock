## Summary

The owner/configurator will cause **mass denial-of-service for all gasless approval integrations** (Permit2, Uniswap, aggregators) by calling `setName()`, which immediately invalidates ALL pending off-chain permit signatures across the entire ecosystem without warning or grace period.

## Root Cause

In [`FT.sol:169-171`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L169-L171), the token name can be changed by the owner at any time:

```solidity
function setName(string memory newName) external onlyOwner {
    _name = newName;
}
```

Combined with the dynamic EIP-712 domain separator in [`FT.sol:209-219`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L209-L219):

```solidity
function _domainSeparatorDynamic() internal view returns (bytes32) {
    return keccak256(
        abi.encode(
            _EIP712_DOMAIN_TYPEHASH,
            keccak256(bytes(name())),  // <-- Uses CURRENT name
            keccak256(bytes("1")),
            block.chainid,
            address(this)
        )
    );
}
```

When `setName()` is called, the domain separator changes immediately, invalidating every pending signature that was created with the old name.

## Internal Pre-conditions

1. Owner has permission to call `setName()` (implemented).
2. Users have valid pending permit signatures.

## External Pre-conditions

1. DeFi integrations (DEXs, aggregators, lending protocols) rely on permit/Permit2 for gasless approvals.

## Attack Path

**Scenario 1: Accidental Mass DoS (Rebrand)**
1. Flying Tulip protocol DAO decides to rebrand from "Flying Tulip" to "FlyTulip".
2. Governance proposal passes, owner calls `setName("FlyTulip")`.
3. **Immediately**, all pending permits across the ecosystem become invalid:
   - User A's pending Uniswap V3 swap (permit-based) fails
   - User B's Permit2 approval for aggregator fails
   - User C's gasless transfer (meta-tx) fails
4. Users experience transaction failures, potential MEV losses on failed attempts.

**Scenario 2: Targeted Griefing Attack**
1. Attacker identifies a large whale's pending permit transaction in the mempool.
2. Attacker front-runs with a governance proposal or compromised owner key to change name.
3. `setName("FlyT")` executes.
4. Whale's permit transaction reverts due to invalid signature.
5. Whale must re-sign, losing time-sensitive trading opportunity.

## Impact

**Quantified Damage**:
- **100% of pending permits** become invalid instantly (could be thousands of users)
- **Every DeFi integration** breaks simultaneously (Uniswap, 1inch, CoW Swap, etc.)
- **MEV losses** for users whose transactions fail mid-execution
- **User trust damage** - unexplained transaction failures

This is a **critical access control issue** because the owner can unilaterally break core protocol functionality for all users without any grace period or warning mechanism.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/FT.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract PermitInvalidationTest is Test {
    FT public ft;
    address public owner;
    uint256 public userPrivateKey = 0x1234;
    address public user;
    
    function setUp() public {
        owner = address(this);
        user = vm.addr(userPrivateKey);
        
        ft = new FT("FlyingTulip", "FT", address(0x1), address(0x2), owner, block.chainid);
        deal(address(ft), user, 1000e18);
    }
    
    function test_SetNameInvalidatesAllPermits() public {
        // 1. Capture domain separator BEFORE name change
        bytes32 domainSepBefore = ft.DOMAIN_SEPARATOR();
        
        // 2. User signs a permit with current name
        bytes32 permitHash = keccak256(abi.encodePacked(
            "\x19\x01",
            domainSepBefore,
            keccak256(abi.encode(
                keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)"),
                user,
                address(0x5),
                100e18,
                0,
                block.timestamp + 1 hours
            ))
        ));
        
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(userPrivateKey, permitHash);
        
        // 3. Owner changes name (rebrand, governance, or attack)
        ft.setName("FlyTulip");
        
        // 4. Domain separator changed immediately
        bytes32 domainSepAfter = ft.DOMAIN_SEPARATOR();
        assertTrue(domainSepBefore != domainSepAfter, "Domain separator changed");
        
        // 5. User's valid signature is now INVALID
        vm.expectRevert(); // Invalid signature
        ft.permit(user, address(0x5), 100e18, block.timestamp + 1 hours, v, r, s);
        
        console.log("RESULT: All pending permits invalidated by name change");
        console.log("Old domain separator:", uint256(domainSepBefore));
        console.log("New domain separator:", uint256(domainSepAfter));
    }
}
```

## Mitigation

**Option A: Timelock on name changes** (Recommended)
```solidity
uint256 public constant NAME_CHANGE_DELAY = 7 days;
uint256 public pendingNameChangeTime;
string public pendingName;

function proposeNameChange(string memory newName) external onlyOwner {
    pendingName = newName;
    pendingNameChangeTime = block.timestamp + NAME_CHANGE_DELAY;
    emit NameChangeProposed(newName, pendingNameChangeTime);
}

function executeNameChange() external {
    require(block.timestamp >= pendingNameChangeTime, "Too early");
    _name = pendingName;
    emit NameChanged(pendingName);
}
```

**Option B: Cache domain separator** (EIP-712 standard)
```solidity
bytes32 private immutable _CACHED_DOMAIN_SEPARATOR;

constructor() {
    _CACHED_DOMAIN_SEPARATOR = _computeDomainSeparator();
}

function DOMAIN_SEPARATOR() public view returns (bytes32) {
    return block.chainid == _CACHED_CHAIN_ID 
        ? _CACHED_DOMAIN_SEPARATOR 
        : _computeDomainSeparator();
}
```

**Option C: Make name immutable**
```solidity
function finalizeName() external onlyOwner {
    _nameFinalized = true;
}

function setName(string memory newName) external onlyOwner {
    require(!_nameFinalized, "Name is finalized");
    _name = newName;
}
```
