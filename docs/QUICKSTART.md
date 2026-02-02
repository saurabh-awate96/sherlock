# Quick Start Guide

## Prerequisites

- Python 3.11+
- [Foundry](https://getfoundry.sh/) (forge, cast, anvil)
- [Slither](https://github.com/crytic/slither)

## Installation

```bash
# Clone repository
git clone https://github.com/saurabh-awate96/sherlock.git
cd sherlock
git checkout sherlock-mycroft

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install package
pip install -e .

# Install security tools
./scripts/install_tools.sh
```

## Basic Usage

### Run an Audit

```python
from sherlock.core.orchestrator import Orchestrator

# Initialize with target
orchestrator = Orchestrator(
    target="https://github.com/protocol/contracts",
    output_dir="./audit_output",
    min_confidence=0.7
)

# Execute full audit lifecycle
orchestrator.run_audit()
```

### Configure Audit Strategy

Edit `src/sherlock/audit_config.yaml`:

```yaml
depth: STANDARD  # QUICK, STANDARD, or DEEP
min_confidence: 0.5
focus_primitives:
  - Vault
  - Oracle
banned_files:
  - lib/
  - test/
  - node_modules/
```

## Output

After running, find results in:

- `audit_output/AUDIT_REPORT.md` - Main findings
- `audit_output/findings.json` - Machine-readable
- `audit_output/pocs/` - Foundry exploit tests

## Next Steps

- Read [Architecture](ARCHITECTURE.md) for system design
- See [Agents](AGENTS.md) for agent responsibilities
- Check `examples/` for sample audits
