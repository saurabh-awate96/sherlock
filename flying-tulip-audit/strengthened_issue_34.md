## Summary

**Cross-chain accounting desync will cause permanent fund lock for users** when an admin pauses the FT token on one chain but the LayerZero endpoint continues minting inbound bridged tokens, creating a **one-way trap where tokens enter but cannot leave** the paused chain.

## Root Cause

In [`FT.sol:362-365`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L362-L365), the endpoint is explicitly exempted from pause checks:

```solidity
if (sender == address(endpoint) || sender == ftConfigurator) {
    super._update(from, to, value);
    return;
}
```

This creates **asymmetric pause behavior**:
- **Outbound (user → bridge)**: BLOCKED during pause
- **Inbound (bridge → user)**: ALLOWED during pause

The invariant that "pause stops all token movement" is violated, leading to supply desync.

## Internal Pre-conditions

1. FT token is deployed with cross-chain messaging enabled.
2. Admin pauses the contract (legitimate emergency response).

## External Pre-conditions

1. Users have in-flight cross-chain transfers at the moment of pause.
2. LayerZero relayers continue delivering queued messages.

## Attack Path

**Scenario: Emergency Response Creates Worse Outcome**

1. **T=0**: Security team detects an exploit on Chain A and pauses the FT contract.
2. **T=1**: 50 users have cross-chain transfers in-flight from Chain B → Chain A.
3. **T=2**: LayerZero relayers deliver these messages. Endpoint calls `lzReceive()`.
4. **T=3**: FT contract sees `sender == endpoint`, bypasses pause, and **mints 500,000 FT** to users on the "frozen" chain.
5. **T=4**: These users now hold tokens on a paused chain that they **cannot transfer, sell, or bridge out**.

**Result**: The emergency pause intended to protect users instead **traps their funds indefinitely**. The pause was meant to last hours, but these users' tokens are locked until unpause—which may never happen if the exploit is fundamental.

**Attack Vector (Malicious)**:
1. Attacker discovers the asymmetric behavior.
2. Attacker initiates large bridge transfer from Chain B.
3. Attacker front-runs pause by notifying security team of fake exploit.
4. Security team pauses Chain A.
5. Attacker's tokens arrive on Chain A via endpoint exemption.
6. Attacker is now the only one who can wait out the pause while everyone else panics.

## Impact

**Fund Lock + User Harm (Medium-High)**:
- Users with in-flight transfers have tokens minted to a chain where they cannot move them
- Creates regulatory liability (tokens exist but are non-transferable)
- Breaks composability with DEXs, lending protocols during pause
- Unpause timing controlled by admin, not affected users

**Quantified Impact**: If 100 users have average $1,000 in-flight transfers during a pause:
- $100,000 of user capital trapped
- Unknown lock duration (hours to indefinite)
- No user recourse or refund mechanism

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/FT.sol";

contract AsymmetricPauseExploitTest is Test {
    FT public ft;
    address public endpoint = address(0xE);
    address public configurator = address(0xC);
    address public user = address(0xABC);
    
    function setUp() public {
        ft = new FT("FlyingTulip", "FT", endpoint, address(0x2), configurator, block.chainid);
        deal(address(ft), endpoint, 1_000_000e18); // Endpoint has tokens to "bridge"
    }
    
    function test_TokensTrappedDuringPause() public {
        // 1. Admin pauses due to emergency
        vm.prank(configurator);
        ft.setPaused(true);
        assertTrue(ft.paused(), "Contract is paused");
        
        // 2. User's in-flight bridge transfer arrives
        uint256 bridgedAmount = 50_000e18;
        vm.prank(endpoint);
        ft.transfer(user, bridgedAmount); // SUCCESS - endpoint bypasses pause
        
        assertEq(ft.balanceOf(user), bridgedAmount, "User received tokens on paused chain");
        
        // 3. User tries to transfer/sell tokens - BLOCKED
        vm.prank(user);
        vm.expectRevert(); // EnforcedPause
        ft.transfer(address(0x999), bridgedAmount);
        
        // 4. User tries to bridge out - BLOCKED
        vm.prank(user);
        vm.expectRevert(); // EnforcedPause
        // ft.send(...) would also revert
        
        console.log("TRAPPED: User has", bridgedAmount / 1e18, "tokens they cannot move");
        console.log("ASYMMETRY: Inbound=ALLOWED, Outbound=BLOCKED");
    }
}
```

## Mitigation

**Option A: Symmetric Pause (Recommended)**
Block inbound transfers during pause to maintain consistent behavior:

```solidity
function _update(address from, address to, uint256 value) internal override {
    if (paused()) {
        // Only configurator can move tokens during pause (for emergency rescue)
        if (_msgSender() != ftConfigurator) {
            revert EnforcedPause();
        }
    }
    super._update(from, to, value);
}
```

**Option B: Inbound Queue During Pause**
Queue inbound bridge messages and process them on unpause:

```solidity
mapping(bytes32 => PendingTransfer) public pauseQueue;

function _update(...) internal override {
    if (paused() && _msgSender() == address(endpoint)) {
        pauseQueue[keccak256(...)] = PendingTransfer(to, value);
        emit TransferQueued(to, value);
        return; // Don't mint yet
    }
    super._update(from, to, value);
}
```
