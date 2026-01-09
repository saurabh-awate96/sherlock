## Summary

The LayerZero endpoint whitelist in `FT.sol` creates a **critical pause bypass** that allows attackers to **continue minting tokens via inbound bridge transfers** even when the contract is paused during an active exploit, effectively rendering the emergency pause mechanism useless for cross-chain attack containment.

## Links to affected code

* [FT.sol#L362-L365](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L362-L365)

## Root Cause

In [FT.sol:362-365](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L362-L365), the endpoint is unconditionally whitelisted:

```solidity
if (sender == address(endpoint) || sender == ftConfigurator) {
    super._update(from, to, value);
    return;  // Bypass ALL pause checks
}
```

During a security incident, pausing is the first line of defense. But if an attacker can continue minting tokens via cross-chain messages, the pause provides zero protection against supply inflation attacks.

## Internal Pre-conditions

1. FT token deployed with cross-chain bridging enabled.
2. Pause mechanism active (emergency detected).

## External Pre-conditions

1. LayerZero messaging remains operational (decentralized, not controlled by FT team).
2. Attacker has access to FT on source chain.

## Attack Path

1. **T=0**: Attacker discovers an infinite mint vulnerability in FT on Chain A.
2. **T=1**: Attacker begins minting unbounded FT tokens on Chain A.
3. **T=5**: Security team detects the attack and pauses FT on Chain A.
4. **T=6**: Team believes attack is contained. Local minting is blocked.
5. **T=7**: Attacker mints on unpaused Chain B and bridges TO Chain A.
6. **T=8**: On Chain A (still paused): `endpoint.lzReceive()` → `ft._update()` → `sender == endpoint` ✓ → bypass pause → MINT SUCCESSFUL.
7. **T=10**: Attacker has minted 500M tokens on Chain A despite the pause.

## Impact

**Complete Failure of Emergency Response (High)**. The pause mechanism is rendered useless for cross-chain attack containment. If exploit on chain B can mint and bridge, chain A pause is bypassed. This undermines the entire security model of having a pause function.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/FT.sol";

contract PauseBypassExploitTest is Test {
    FT public ft;
    address public endpoint = address(0xE);
    address public configurator = address(0xC);
    address public attacker = address(0xBAD);
    uint256 public constant EXPLOITED_AMOUNT = 500_000_000e18;
    
    function setUp() public {
        ft = new FT("FlyingTulip", "FT", endpoint, address(0x2), configurator, block.chainid);
    }
    
    function test_InboundMintDuringPause() public {
        // Admin pauses the contract
        vm.prank(configurator);
        ft.setPaused(true);
        assertTrue(ft.paused(), "Contract is paused");
        
        // Verify normal transfers are blocked
        deal(address(ft), address(this), 1000e18);
        vm.expectRevert();
        ft.transfer(attacker, 1000e18);
        
        // Attacker's inbound bridge message arrives via endpoint
        deal(address(ft), endpoint, EXPLOITED_AMOUNT);
        vm.prank(endpoint);
        ft.transfer(attacker, EXPLOITED_AMOUNT); // SUCCESS - bypasses pause!
        
        assertEq(ft.balanceOf(attacker), EXPLOITED_AMOUNT);
        console.log("Attacker received tokens DURING PAUSE via endpoint bypass");
    }
}
```

## Mitigation

Remove endpoint from pause bypass to ensure full isolation:

```solidity
function _update(address from, address to, uint256 value) internal override {
    if (paused()) {
        // ONLY configurator can move tokens during pause
        require(_msgSender() == ftConfigurator, "EnforcedPause");
    }
    super._update(from, to, value);
}
```
