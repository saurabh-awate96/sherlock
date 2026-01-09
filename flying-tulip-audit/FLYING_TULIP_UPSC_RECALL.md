# Flying Tulip (pFT) Master Study Guide
## UPSC Smart Contract Security Examination - 2026 Preparation

This guide summarizes the cognitive architecture of the Flying Tulip (pFT) system for high-recall preparation.

---

### I. The Core Philosophy
The Flying Tulip protocol is a **Capital-Efficient Cash-Secured Put** engine. Unlike traditional vaults, it isolates **Principal Protection** from **Yield Accumulation**.

*   **Principal**: Stored in `ftYieldWrapper.sol` with 1:1 share mapping.
*   **Yield**: Accrues in strategy position tokens (e.g., aTokens) and is swept to the `Treasury`.

### II. State Machine & Phases
1.  **Offering Phase (`saleEnabled`)**:
    *   Users call `invest()`.
    *   Collateral is deposited into a `vault` (wrapper).
    *   `pFT` NFT is minted with a fixed exercise ratio (`strike` / `ftPerUSD`).
2.  **Post-Offering Phase (`transferable`)**:
    *   Users can `divest()` (Execute Put) or `withdrawFT()` (Invalidate Put).
    *   Transfer of NFTs is enabled.

### III. Mathematical Invariants
- **Exercise Formula**:
  `collateral = ftAmount * (1e16 * 10^d) / (strike * ftPerUSD)`
- **Principal Invariant**:
  `wrapper.totalSupply() == wrapper.totalPrincipalDeposited()`
- **Yield Invariant**:
  `strategy.valueOfCapital() - strategy.totalSupply() == accumulatedYield`

### IV. Security & Defensive Layers
*   **Greedy Withdrawal**: Wrapper drains strategies based on manual order; `try-catch` prevents a single failure from blocking user liquidity.
*   **Circuit Breaker (ERC-7265)**: Dual-buffer rate limiting (Main + Elastic) prevents liquidity drains from flashloan-funded attacks.
*   **Access Control**: 
    *   `msig`: Governance/Configuration changes.
    *   `yieldClaimer`: Operational yield harvesting.
    *   `depositor`: Permissioned entry point for the wrapper.

### V. Critical Recall Points
- **pFT Storage**: Uses `uint96` for accounting variables to optimize gas.
- **Oracle Bounds**: Hardcoded `minPrice` and `maxPrice` in `FlyingTulipOracle.sol`.
- **CB Fail-Open**: Wrap of CB calls ensures user withdrawals are never bricked by a rate-limiter logic bug.

---
*End of Study Guide*
