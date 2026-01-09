## Summary

A **privilege escalation vulnerability** allows a compromised configurator to **permanently maintain backdoor access** even after the compromise is detected, because the configurator role can transfer itself to a secondary attacker address without owner approval, timelock, or event emission.

## Root Cause

In [`FT.sol:60-63`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L60-L63), the `transferConfigurator` function has no oversight mechanism:

```solidity
function transferConfigurator(address newConfigurator) external {
    require(msg.sender == configurator, "Only configurator");
    configurator = newConfigurator;
    // NO event emission
    // NO owner approval
    // NO timelock
}
```

This violates the **principle of least privilege** and **defense in depth**. A critical privileged role can be rotated instantly and silently.

## Internal Pre-conditions

1. Configurator role is assigned to an address (initial deployment).

## External Pre-conditions

1. Configurator private key or multisig is compromised (phishing, key leak, insider threat).

## Attack Path

**Phase 1: Silent Persistence**
1. Attacker compromises configurator key via phishing email targeting the ops team.
2. Attacker immediately calls `transferConfigurator(attacker_wallet_2)`.
3. No on-chain event is emitted. No alarm is raised.
4. Attacker waits.

**Phase 2: Incident Discovery**
5. Security team discovers unusual pause/unpause activity.
6. Team identifies compromised configurator address.
7. Team rotates the key they think is compromised (the original one).
8. **But the configurator role already belongs to attacker_wallet_2**.

**Phase 3: Exploitation**
9. Team believes they have remediated.
10. Attacker uses `attacker_wallet_2` to:
    - Bypass pause and drain tokens during an exploit
    - Pause the contract to grief users
    - Set malicious parameters
11. Attack succeeds because the "fix" didn't actually revoke attacker access.

## Impact

**Privilege Persistence + Delayed Attack (Medium)**:

| Impact | Severity |
|--------|----------|
| Attacker maintains hidden access after detection | Medium |
| No audit trail (no events) | Increases attack surface |
| Enables multi-stage attacks | Higher damage potential |
| Defense-in-depth completely bypassed | Critical design flaw |

**Real-World Parallel**: This is similar to how advanced persistent threats (APTs) operate—they establish multiple access paths so that patching one doesn't remove their access.

**Sherlock Scope Alignment**: This is an **access control vulnerability** per the audit scope. The configurator has privileged access to the pause mechanism, which is explicitly in-scope security functionality.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/FT.sol";

contract ConfiguratorPersistenceTest is Test {
    FT public ft;
    address public owner = address(0x1);
    address public originalConfigurator = address(0xC);
    address public attackerWallet1 = address(0xBAD1);
    address public attackerWallet2 = address(0xBAD2);
    
    function setUp() public {
        vm.prank(owner);
        ft = new FT("FlyingTulip", "FT", address(0xE), address(0x2), originalConfigurator, block.chainid);
    }
    
    function test_SilentPersistenceAttack() public {
        // Phase 1: Attacker compromises original configurator
        vm.prank(originalConfigurator);
        ft.transferConfigurator(attackerWallet1);
        
        // Attacker creates hidden backup access
        vm.prank(attackerWallet1);
        ft.transferConfigurator(attackerWallet2);
        
        // Phase 2: Team "fixes" by checking current configurator
        address currentConfig = ft.ftConfigurator();
        console.log("Team sees configurator:", currentConfig);
        // Team rotates attackerWallet1's key (futile)
        
        // Phase 3: Attacker still has access via wallet2
        vm.prank(attackerWallet2);
        ft.setPaused(true); // Full control maintained
        
        assertTrue(ft.paused(), "Attacker maintained access after 'remediation'");
        console.log("ATTACK SUCCESS: Configurator persistence achieved");
    }
    
    function test_NoEventEmitted() public {
        // Verify no event is emitted during transfer
        vm.recordLogs();
        
        vm.prank(originalConfigurator);
        ft.transferConfigurator(attackerWallet1);
        
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 0, "No events emitted - silent transfer");
    }
}
```

## Mitigation

**Option A: Two-Step Transfer with Owner Approval (Recommended)**

```solidity
address public pendingConfigurator;
uint256 public configuratorTransferInitiated;

event ConfiguratorTransferProposed(address indexed current, address indexed proposed);
event ConfiguratorTransferCompleted(address indexed oldConfig, address indexed newConfig);

function proposeConfiguratorTransfer(address newConfigurator) external {
    require(msg.sender == ftConfigurator, "Only configurator");
    require(newConfigurator != address(0), "Zero address");
    pendingConfigurator = newConfigurator;
    configuratorTransferInitiated = block.timestamp;
    emit ConfiguratorTransferProposed(ftConfigurator, newConfigurator);
}

function acceptConfiguratorTransfer() external {
    require(msg.sender == owner(), "Only owner can approve");
    require(pendingConfigurator != address(0), "No pending transfer");
    require(block.timestamp >= configuratorTransferInitiated + 2 days, "Timelock not passed");
    
    address oldConfig = ftConfigurator;
    ftConfigurator = pendingConfigurator;
    pendingConfigurator = address(0);
    emit ConfiguratorTransferCompleted(oldConfig, ftConfigurator);
}
```

**Option B: Minimum - Add Event Emission**

```solidity
event ConfiguratorTransferred(address indexed oldConfigurator, address indexed newConfigurator);

function transferConfigurator(address newConfigurator) external {
    require(msg.sender == ftConfigurator, "Only configurator");
    address old = ftConfigurator;
    ftConfigurator = newConfigurator;
    emit ConfiguratorTransferred(old, newConfigurator);  // At minimum, enable monitoring
}
```
