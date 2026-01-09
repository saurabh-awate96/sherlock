## Summary

The missing decrement logic in `ftACL.sol` will cause a **permanent investment lockout** for Users as their `amountInvested` only increases on invest but is never decremented on divest, causing users to hit their lifetime cap regardless of current holdings.

## Links to affected code

* [ftACL.sol#L84-L100](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftACL.sol#L84-L100)

## Root Cause

In [ftACL.sol:94-99](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/ftACL.sol#L94-L99), the `amountInvested` mapping acts as a monotonic counter with no decrement function:

```solidity
function invest(
    address account,
    address token,
    uint256 amount,
    uint256 proofAmount
) external onlyPutManager {
    uint256 newInvestedAmount = amountInvested[account][token] + amount;
    if (newInvestedAmount > proofAmount) {
        revert ftACLCapReached();
    }
    amountInvested[account][token] = newInvestedAmount;
}
```

The contract has 127 total lines and contains NO `divest()` or `decrementInvested()` function.

## Internal Pre-conditions

1. User has a whitelist proof with a specific cap (e.g., 1000 USDC).
2. User invests and later divests their position.

## External Pre-conditions

None.

## Attack Path

1. **User invests 500 USDC**. `amountInvested` becomes 500.
2. **User divests 500 USDC**. PutManager processes divest but `amountInvested` remains 500 (no ACL call).
3. **User invests another 500 USDC**. `amountInvested` becomes 1000 (at cap).
4. **User divests again**. `amountInvested` remains 1000.
5. **User tries to invest 1 USDC**. Transaction reverts with `ftACLCapReached` because `1000 + 1 > 1000`.
6. User is permanently locked out despite having $0 current investment.

## Impact

The Users suffer a permanent Denial of Service after trading a certain volume. The `Cap` behaves as a "Lifetime Volume Limit" rather than a "Current Exposure Limit", which is unintended for a DeFi protocol.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/ftACL.sol";

contract ACLLockoutTest is Test {
    ftACL public acl;
    address public user = address(0x123);
    address public token = address(0x456);
    address public putManager = address(0x789);
    
    function setUp() public {
        bytes32 root = keccak256(abi.encodePacked("test"));
        acl = new ftACL(root, putManager);
    }
    
    function test_PermanentLockout() public {
        uint256 cap = 1000e18;
        
        // Round 1: Invest 500
        vm.prank(putManager);
        acl.invest(user, token, 500e18, cap);
        assertEq(acl.amountInvested(user, token), 500e18);
        
        // Simulate divest - NO ACL call exists
        // amountInvested stays at 500
        
        // Round 2: Invest another 500
        vm.prank(putManager);
        acl.invest(user, token, 500e18, cap);
        assertEq(acl.amountInvested(user, token), 1000e18);
        
        // Round 3: Try to invest 1 wei - FAILS
        vm.prank(putManager);
        vm.expectRevert(ftACL.ftACLCapReached.selector);
        acl.invest(user, token, 1, cap);
        
        console.log("PERMANENT LOCKOUT: User has $0 invested but cannot invest anymore");
    }
}
```

## Mitigation

Add a `divest` function to `ftACL.sol` and ensure `PutManager` calls it during divest operations:

```solidity
function divest(
    address account,
    address token,
    uint256 amount
) external onlyPutManager {
    uint256 current = amountInvested[account][token];
    if (amount > current) {
        amountInvested[account][token] = 0;
    } else {
        amountInvested[account][token] = current - amount;
    }
}
```
