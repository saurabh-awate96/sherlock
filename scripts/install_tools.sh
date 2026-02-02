#!/bin/bash
# Install security audit tools

echo "Installing Foundry..."
curl -L https://foundry.paradigm.xyz | bash
foundryup

echo "Installing Slither..."
pip install slither-analyzer

echo "Installing Aderyn..."
cargo install aderyn

echo "Done!"

