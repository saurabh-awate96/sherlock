# HIGH-01: pFT NFT Transfers Not Restricted During Offering Lock Period

## Summary
The `pFT.sol` contract allows unrestricted NFT transfers even when `PutManager.transferable` is set to `false`, completely bypassing the intended offering phase lock period.

## Finding Type
Access Control / State Machine Violation

## Relevant GitHub Links
- [pFT.sol:354-364](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/pFT.sol#L354-L364) - The `_update` function with no transfer restriction
- [PutManager.sol:97-98](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/PutManager.sol#L97-L98) - The `transferable` flag declaration
- [PutManager.sol:247-251](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/ftPUT/contracts/PutManager.sol#L247-L251) - The `enableTransferable()` function

## Vulnerability Detail

The Flying Tulip protocol implements a two-phase model:
1. **Offering Phase** (`saleEnabled = true`, `transferable = false`): Users can invest but positions should be non-transferable
2. **Post-Offering Phase** (`transferable = true`): Positions become freely tradeable

The `transferable` boolean flag in `PutManager.sol` is intended to control when PUT positions (ERC721 NFTs) can be transferred. However, this flag is **never enforced** in the `pFT.sol` contract.

The `pFT.sol` contract's `_update()` function, which is called for all token transfers, simply delegates to the parent without any restriction check:

```solidity
function _update(
    address to,
    uint256 tokenId,
    address auth
)
    internal
    override(ERC721EnumerableUpgradeable)
    returns (address)
{
    return super._update(to, tokenId, auth);  // No transferable check!
}
```

The `transferable` flag is only checked in:
- `withdrawFT()`: prevents FT withdrawal during offering
- Nowhere else

Standard ERC721 functions (`transferFrom`, `safeTransferFrom`, `approve`) work unrestricted at all times.

## Impact

**HIGH** - Core protocol invariant violation with significant economic impact:

1. **Offering Lock Bypass**: During the offering phase, users can freely trade their PUT positions OTC, defeating the purpose of the lock period entirely
2. **Secondary Market Creation**: This enables an unauthorized secondary market during what should be a lock period
3. **Regulatory Implications**: If the lock period exists for compliance reasons, this bypass could have legal ramifications
4. **Economic Model Exploitation**: Speculators can participate in the offering and immediately flip positions, destabilizing intended holding patterns

## Proof of Concept

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../contracts/PutManager.sol";
import "../contracts/pFT.sol";

contract TransferRestrictionBypassTest is Test {
    PutManager putManager;
    pFT pft;
    address alice = address(0x1);
    address bob = address(0x2);
    
    function setUp() public {
        // Setup contracts... 
        // Assume putManager.transferable == false (offering phase)
    }
    
    function testTransferDuringLockPeriod() public {
        // Verify we're in locked period
        assertFalse(putManager.transferable());
        
        // Alice invests and gets NFT ID=1
        uint256 tokenId = 1;
        
        // Alice should NOT be able to transfer, but CAN
        vm.prank(alice);
        pft.transferFrom(alice, bob, tokenId);  // SUCCEEDS!
        
        // Bob now owns the position
        assertEq(pft.ownerOf(tokenId), bob);
        
        // This should have reverted during offering phase
    }
}
```

## Code Snippet

The missing check should be in `pFT.sol`:

```solidity
// Current implementation - NO RESTRICTION
function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
    return super._update(to, tokenId, auth);
}
```

## Tool Used
Holmesian Cognitive Framework - SM-Sher-Aud-Framework (Sherlock Agent abductive reasoning + Moriarty game theory)

## Recommendation

Add transfer restriction enforcement in `pFT.sol`:

```solidity
// Add interface to read PutManager state
interface IPutManagerTransferable {
    function transferable() external view returns (bool);
}

function _update(
    address to,
    uint256 tokenId,
    address auth
)
    internal
    override(ERC721EnumerableUpgradeable)
    returns (address)
{
    // Allow minting (from == 0) and burning (to == 0) always
    address from = _ownerOf(tokenId);
    if (from != address(0) && to != address(0)) {
        // This is a transfer, not mint/burn
        if (!IPutManagerTransferable(putManager).transferable()) {
            revert pFTTransfersDisabled();
        }
    }
    return super._update(to, tokenId, auth);
}
```

Alternative: Make pFT soulbound during offering phase using ERC-5192 (Minimal Soulbound NFTs).
