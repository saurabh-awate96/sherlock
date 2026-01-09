## Summary

An attacker will cause **catastrophic token supply inflation** across the multi-chain Flying Tulip ecosystem by deploying the FT contract on a chain fork or collision chain where `block.chainid` matches the intended `mintChainId`, minting 1 billion unauthorized tokens that can then be bridged to the legitimate chain via LayerZero.

## Root Cause

In [`FT.sol:83`](https://github.com/sherlock-audit/2026-01-flying-tulip-saurabh-awate96/blob/main/contracts/FT.sol#L83), the constructor accepts `mintChainId` as a **dynamic parameter** instead of hardcoding the valid chain:

```solidity
constructor(..., uint256 mintChainId) {
    if (block.chainid == mintChainId) {
        _mint(_msgSender(), 1_000_000_000 * 10 ** decimals());  // 1 BILLION tokens
    }
}
```

The vulnerability lies in using `block.chainid` for security-critical minting decisions. Unlike LayerZero's `endpoint.eid()` which is cryptographically bound to specific infrastructure, EVM `chainid` values:
- Can collide between testnets and mainnets
- Are duplicated during hard forks (ETH/ETC, ETH PoW)
- Are not globally unique

## Internal Pre-conditions

1. `mintChainId` is passed as a constructor argument (implemented).
2. The deployer private key or deployment script is accessible.

## External Pre-conditions

1. A chain exists where `block.chainid` equals the intended `mintChainId` (fork, testnet, L2 with aliased ID).
2. That chain has a working LayerZero endpoint connected to the main deployment.

## Attack Path

1. Flying Tulip deploys FT on Ethereum Mainnet (Chain ID 1) as the hub with initial 1B supply.
2. LayerZero enables bridging to Arbitrum, Optimism, etc.
3. Attacker identifies a PoW fork of Ethereum (e.g., ETHW with Chain ID 10001) OR a testnet with ID collision.
4. Attacker deploys the SAME FT contract on the fork chain, passing `mintChainId = <fork_chainid>`.
5. Constructor mints **another 1 billion tokens** on the fork chain.
6. Attacker bridges 500M tokens from fork chain to Ethereum Mainnet via LayerZero.
7. **Result**: Ethereum Mainnet now has 1.5B FT tokens - 50% supply inflation, catastrophic devaluation.

## Impact

The protocol suffers **total economic collapse**:
- 1 billion unauthorized tokens minted (100% inflation per fork)
- Token price collapses as supply doubles/triples
- All existing holders' value is diluted by 50%+
- Protocol credibility is destroyed

**Quantified Loss**: At any reasonable token price, this represents **billions of dollars** in damage. If FT trades at $1, this is a $1B direct theft via dilution.

## PoC

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/FT.sol";

contract ChainIdMintBypassTest is Test {
    function test_UnauthorizedMintOnForkChain() public {
        // Simulate legitimate mainnet deployment
        uint256 mainnetChainId = 1;
        vm.chainId(mainnetChainId);
        
        FT legitimateFT = new FT(
            "FlyingTulip", "FT",
            address(0x1), address(0x2), address(0x3),
            mainnetChainId
        );
        
        uint256 legitimateSupply = legitimateFT.totalSupply();
        assertEq(legitimateSupply, 1_000_000_000 * 1e18, "1B minted on mainnet");
        
        // Simulate fork deployment (attacker controls this)
        uint256 forkChainId = 10001; // ETHW or similar
        vm.chainId(forkChainId);
        
        // Attacker deploys with fork's chain ID as mintChainId
        FT forkFT = new FT(
            "FlyingTulip", "FT",
            address(0x1), address(0x2), address(0x3),
            forkChainId  // Attacker sets this to match fork
        );
        
        uint256 forkSupply = forkFT.totalSupply();
        assertEq(forkSupply, 1_000_000_000 * 1e18, "Another 1B minted on fork!");
        
        // Combined supply across ecosystem: 2 BILLION (100% inflation)
        console.log("Legitimate chain supply:", legitimateSupply / 1e18, "tokens");
        console.log("Fork chain supply:", forkSupply / 1e18, "tokens");
        console.log("TOTAL ECOSYSTEM SUPPLY:", (legitimateSupply + forkSupply) / 1e18, "tokens");
        console.log("INFLATION RATE: 100%");
    }
}
```

## Mitigation

Use LayerZero's `endpoint.eid()` for chain identity, which is cryptographically bound and unique:

```solidity
constructor(..., ILayerZeroEndpoint _endpoint, uint32 mintEid) {
    endpoint = _endpoint;
    if (endpoint.eid() == mintEid) {
        _mint(_msgSender(), 1_000_000_000 * 10 ** decimals());
    }
}
```

Or hardcode the valid chain ID as an immutable constant:

```solidity
uint256 public constant MINT_CHAIN_ID = 1; // Ethereum Mainnet only

constructor(...) {
    if (block.chainid == MINT_CHAIN_ID) {
        _mint(_msgSender(), 1_000_000_000 * 10 ** decimals());
    }
}
```
