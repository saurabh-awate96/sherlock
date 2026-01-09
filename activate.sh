#!/bin/bash
# Activate Mycroft environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate Python venv
if [[ -f "${SCRIPT_DIR}/_audit_tools/venv/bin/activate" ]]; then
    source "${SCRIPT_DIR}/_audit_tools/venv/bin/activate"
    echo "✓ Python virtual environment activated"
fi

# Add Foundry to PATH
export PATH="$HOME/.foundry/bin:$PATH"

# Add Go binaries to PATH
export PATH="$HOME/go/bin:$PATH"

echo "✓ Mycroft Antigravity v3.0 environment ready"
echo ""
echo "Available commands:"
echo "  ./scripts/audit_workflow.sh {metrics|static|dynamic|report|all} [project_path]"
