// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {CommonBase, StdCheats, StdUtils} from "forge-std/Base.sol";

/**
 * @title Protocol Handler Template
 * @notice Template for Protocol Wrapping - enables stateful fuzzing
 * @dev Based on Deep Logic Verification research - Handler Pattern
 * 
 * Core Capabilities:
 * 1. INPUT BOUNDING - Constrain fuzz inputs to valid ranges (no revert walls)
 * 2. ACTOR MANAGEMENT - Multi-user simulation with persistent identities
 * 3. GHOST STATE TRACKING - Shadow ledger for drift detection
 */
abstract contract HandlerBase is CommonBase, StdCheats, StdUtils {
    
    // ============================================================
    // ACTOR MANAGEMENT
    // ============================================================
    
    /// @notice Registry of simulated actors
    address[] public actors;
    mapping(address => bool) public isActor;
    
    /// @notice Current actor for pranking
    address public currentActor;
    
    /// @notice Maximum number of actors to simulate
    uint256 public constant MAX_ACTORS = 10;
    
    /// @notice Initial balance to seed each actor
    uint256 public constant ACTOR_INITIAL_BALANCE = 1_000_000 ether;
    
    // ============================================================
    // GHOST STATE (Shadow Ledger)
    // ============================================================
    
    /// @notice Ghost tracking of total assets deposited
    uint256 public ghost_totalDeposited;
    
    /// @notice Ghost tracking of total assets withdrawn
    uint256 public ghost_totalWithdrawn;
    
    /// @notice Ghost tracking of total shares minted
    uint256 public ghost_totalSharesMinted;
    
    /// @notice Ghost tracking of total shares burned
    uint256 public ghost_totalSharesBurned;
    
    /// @notice Per-actor ghost balance tracking
    mapping(address => uint256) public ghost_balances;
    
    /// @notice Per-actor ghost share tracking
    mapping(address => uint256) public ghost_shares;
    
    // ============================================================
    // CALL TRACKING (For Trace Analysis)
    // ============================================================
    
    /// @notice Total number of successful calls
    uint256 public ghost_callCount;
    
    /// @notice Mapping of function selector to call count
    mapping(bytes4 => uint256) public ghost_selectorCalls;
    
    // ============================================================
    // MODIFIERS
    // ============================================================
    
    /**
     * @notice Selects an actor based on fuzzed seed and pranks as them
     * @param actorSeed Random seed from fuzzer to select actor
     */
    modifier useActor(uint256 actorSeed) {
        currentActor = _getOrCreateActor(actorSeed);
        vm.startPrank(currentActor);
        _;
        vm.stopPrank();
    }
    
    /**
     * @notice Tracks function calls for analysis
     */
    modifier countCall(bytes4 selector) {
        ghost_callCount++;
        ghost_selectorCalls[selector]++;
        _;
    }
    
    // ============================================================
    // ACTOR HELPERS
    // ============================================================
    
    /**
     * @notice Gets existing actor or creates new one
     * @param seed Random seed for actor selection/creation
     * @return actor The selected or created actor address
     */
    function _getOrCreateActor(uint256 seed) internal virtual returns (address actor) {
        if (actors.length == 0 || (actors.length < MAX_ACTORS && seed % 3 == 0)) {
            // Create new actor
            actor = address(uint160(uint256(keccak256(abi.encode(seed, block.timestamp)))));
            
            // Ensure unique
            if (!isActor[actor]) {
                actors.push(actor);
                isActor[actor] = true;
                _seedActor(actor);
            }
        } else {
            // Use existing actor
            actor = actors[seed % actors.length];
        }
        
        return actor;
    }
    
    /**
     * @notice Seeds an actor with initial funds
     * @dev Override to customize initial funding (e.g., deal specific tokens)
     */
    function _seedActor(address actor) internal virtual {
        vm.deal(actor, ACTOR_INITIAL_BALANCE);
    }
    
    /**
     * @notice Returns all registered actors
     */
    function getActors() external view returns (address[] memory) {
        return actors;
    }
    
    /**
     * @notice Returns number of registered actors
     */
    function actorCount() external view returns (uint256) {
        return actors.length;
    }
    
    // ============================================================
    // GHOST STATE HELPERS
    // ============================================================
    
    /**
     * @notice Computes the ghost net assets (deposited - withdrawn)
     */
    /// @notice Tolerance for rounding errors (10 wei)
    uint256 public constant TOLERANCE = 10;

    /**
     * @notice Computes the ghost net assets (deposited - withdrawn)
     */
    function ghost_netAssets() external view returns (uint256) {
        if (ghost_totalWithdrawn > ghost_totalDeposited) {
             // If drift is within tolerance, clamp to 0
            if (ghost_totalWithdrawn - ghost_totalDeposited <= TOLERANCE) {
                return 0;
            }
            return 0; // Should trigger invariant failure if > tolerance
        }
        return ghost_totalDeposited - ghost_totalWithdrawn;
    }
    
    /**
     * @notice Computes ghost net shares (minted - burned)
     */
    function ghost_netShares() external view returns (uint256) {
        if (ghost_totalSharesBurned > ghost_totalSharesMinted) {
            return 0;
        }
        return ghost_totalSharesMinted - ghost_totalSharesBurned;
    }
    
    // ============================================================
    // BOUNDING HELPERS
    // ============================================================
    
    /**
     * @notice Bounds amount to user's actual balance (prevents reverts)
     * @param amount Fuzzed amount
     * @param maxAmount Maximum valid amount (e.g., user's balance)
     * @param minAmount Minimum valid amount (e.g., 1 wei to avoid 0)
     */
    function _boundAmount(
        uint256 amount, 
        uint256 minAmount, 
        uint256 maxAmount
    ) internal pure returns (uint256) {
        if (maxAmount < minAmount) {
            return 0; // Invalid range, return 0 to skip action
        }
        return bound(amount, minAmount, maxAmount);
    }
}

/**
 * @title Example: ERC4626 Vault Handler
 * @notice Demonstrates Handler Pattern for a Yield Vault
 */
// contract VaultHandler is HandlerBase {
//     IVault public vault;
//     IERC20 public asset;
//     
//     constructor(IVault _vault, IERC20 _asset) {
//         vault = _vault;
//         asset = _asset;
//     }
//     
//     /// @notice Seeds actor with asset tokens
//     function _seedActor(address actor) internal override {
//         super._seedActor(actor);
//         deal(address(asset), actor, ACTOR_INITIAL_BALANCE);
//     }
//     
//     /// @notice Wrapped deposit action with bounded inputs
//     function deposit(uint256 assets, uint256 actorSeed) 
//         public 
//         useActor(actorSeed) 
//         countCall(this.deposit.selector) 
//     {
//         // BOUND: Constrain to actor's actual balance
//         uint256 balance = asset.balanceOf(currentActor);
//         assets = _boundAmount(assets, 1, balance);
//         
//         if (assets == 0) return; // Skip if no valid amount
//         
//         // PRE: Ensure approval
//         asset.approve(address(vault), assets);
//         
//         // EXECUTE
//         uint256 shares = vault.deposit(assets, currentActor);
//         
//         // GHOST UPDATE
//         ghost_totalDeposited += assets;
//         ghost_totalSharesMinted += shares;
//         ghost_balances[currentActor] += assets;
//         ghost_shares[currentActor] += shares;
//     }
//     
//     /// @notice Wrapped withdraw action
//     function withdraw(uint256 assets, uint256 actorSeed) 
//         public 
//         useActor(actorSeed) 
//         countCall(this.withdraw.selector) 
//     {
//         // BOUND: Constrain to what actor can actually withdraw
//         uint256 maxAssets = vault.maxWithdraw(currentActor);
//         assets = _boundAmount(assets, 0, maxAssets);
//         
//         if (assets == 0) return;
//         
//         // EXECUTE
//         uint256 sharesBurned = vault.withdraw(assets, currentActor, currentActor);
//         
//         // GHOST UPDATE
//         ghost_totalWithdrawn += assets;
//         ghost_totalSharesBurned += sharesBurned;
//         ghost_balances[currentActor] -= assets;
//         ghost_shares[currentActor] -= sharesBurned;
//     }
// }
