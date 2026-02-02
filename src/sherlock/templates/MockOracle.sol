// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MockOracle
 * @notice Resilience Component: Simulates Chainlink/Pyth price feeds
 * @dev Used to break dependencies on real mainnet state during fuzzing
 */
contract MockOracle {
    int256 private _price;
    uint8 private _decimals;
    uint256 private _updatedAt;

    constructor(int256 initialPrice, uint8 decimals_) {
        _price = initialPrice;
        _decimals = decimals_;
        _updatedAt = block.timestamp;
    }

    /// @notice Updates the mock price (for fuzzing different scenarios)
    function setPrice(int256 newPrice) external {
        _price = newPrice;
        _updatedAt = block.timestamp;
    }

    // Chainlink Interface
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        return (1, _price, _updatedAt, _updatedAt, 1);
    }

    function decimals() external view returns (uint8) {
        return _decimals;
    }
}
