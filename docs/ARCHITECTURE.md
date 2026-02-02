# Sherlock Architecture

## Overview

Sherlock 2.0 is a multi-agent security auditing framework that orchestrates specialized AI agents through a structured audit lifecycle.

## Components

### Orchestrator (`core/orchestrator.py`)

The central brain that manages the audit lifecycle:

1. **Phase 0: Planning** - Mycroft defines strategy
2. **Phase 1: Ingestion** - Lestrade parses code
3. **Phase 2: Research** - Irene + Watson analyze
4. **Phase 3: Analysis** - Inspector + Hudson + Sherlock deep dive
5. **Phase 4: Exploitation** - Magnussen + Moriarty generate PoCs
6. **Phase 5: Review** - Mycroft validates output

### Knowledge Graph (`core/db.py`)

SQLite-based graph storing:
- Parsed code entities
- Detected vulnerabilities
- Historical audit patterns
- Semantic relationships

### Invariant Engine (`logic/invariant_engine.py`)

Checks fundamental DeFi laws:
- Solvency: Assets >= Liabilities
- Conservation: ΔWealth == ΔExternalFlows
- Incentive Compatibility: Reward > Cost

### Semantic Detector (`core/semantic_detector.py`)

Classifies code into financial primitives:
- **Vault**: Asset holding logic
- **Loan**: Debt/collateral mapping
- **Exchange**: Swap logic
- **Governor**: Admin powers

## Data Flow

```
Target Repo → Lestrade → Knowledge Graph → Irene/Watson
    ↓                                           ↓
Sherlock ← Hudson ← Inspector ← Primitive Map
    ↓
Magnussen → Moriarty → PoC Templates → Report
```

## Configuration

See `audit_config.yaml` for tunable parameters:
- Confidence thresholds
- Primitive priorities
- Tool configurations
