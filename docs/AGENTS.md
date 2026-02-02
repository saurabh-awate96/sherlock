# Sherlock Agents

## Agent Overview

| Agent | File | Phase | Core Responsibility |
|-------|------|-------|---------------------|
| Mycroft | `mycroft.py` | 0, 5 | Strategy & Review |
| Lestrade | `lestrade.py` | 1 | Code Ingestion |
| Irene | `irene.py` | 2 | Research |
| Watson | `watson.py` | 2 | Primitive Mapping |
| Inspector | `inspector.py` | 3 | Context Building |
| Hudson | `hudson.py` | 3 | Tool Execution |
| Sherlock | `sherlock.py` | 3 | Invariant Verification |
| Magnussen | `magnussen.py` | 4 | Strategy Analysis |
| Moriarty | `moriarty.py` | 4 | PoC Generation |

---

## Detailed Descriptions

### 🎩 Mycroft - The Auditor of Auditors

**File**: `agents/mycroft.py`

Mycroft acts as the meta-auditor who:
- Defines audit strategy based on historical findings
- Sets confidence thresholds and focus primitives
- Reviews final report for completeness
- Signs off on audit quality

### 🔍 Lestrade - The Ingester

**File**: `agents/lestrade.py`

Parses the target repository:
- Clones/downloads source code
- Builds dependency graph
- Populates knowledge graph with entities

### 💃 Irene - The Researcher

**File**: `agents/irene.py`

Researches protocol context:
- Identifies protocol archetype (DEX, Lending, Vault)
- Finds similar historical vulnerabilities
- Maps to known vulnerability patterns

### 🔬 Watson - The Perceiver

**File**: `agents/watson.py`

Maps code to financial primitives:
- Vault: Asset/share accounting
- Loan: Collateral/debt relationships
- Exchange: Swap mechanics
- Governor: Access control

### 🕵️ Inspector - The Context Builder

**File**: `agents/inspector.py`

Performs deep code analysis:
- Line-by-line examination of critical functions
- Identifies high-signal code locations
- Builds execution context

### 🛠️ Hudson - The Tool Runner

**File**: `agents/hudson.py`

Executes security tools:
- Slither for static analysis
- Aderyn for Rust-based checks
- Forge for compilation and testing

### 🎯 Sherlock - The Verifier

**File**: `agents/sherlock.py`

Checks mathematical invariants:
- Solvency conditions
- Conservation of value
- Share accounting integrity

### 📊 Magnussen - The Strategist

**File**: `agents/magnussen.py`

Identifies systemic risks:
- Centralization vectors
- Economic griefing paths
- Incentive misalignments

### 💀 Moriarty - The Exploiter

**File**: `agents/moriarty.py`

Generates proof-of-concept exploits:
- Creates Foundry test files
- Validates exploitability
- Produces reproducible attack paths
