# 🔍 SM-Sher-Aud-Framework: Holmesian Cognitive Architecture

> *"You see, but you do not observe. The distinction is clear."*
> — Sherlock Holmes

An **industrial-grade smart contract security auditing framework** powered by a 4-agent multi-agent system (MAS) implementing Holmesian cognitive principles for deep reasoning, probabilistic analysis, and adversarial verification.

---

## 🧠 The Holmesian Cognitive Core

This framework implements the **Science of Deduction** as described in the canonical Holmes mysteries—but with one critical correction: Holmes's primary methodology is actually **abduction** (inference to the best explanation), not pure deduction.

### Core Cognitive Principles

| Principle | Implementation | Agent |
|-----------|---------------|-------|
| **Observing vs. Seeing** | System 2 attention with anomaly detection | Watson |
| **Abductive Reasoning** | Generating hypotheses that best explain observations | Sherlock |
| **Bayesian Updating** | Real-time probability refinement as evidence accumulates | Sherlock |
| **Strategic Ignorance** | Brain Attic filtering for noise reduction | All |
| **Backward Reasoning** | Tracing effects to causes | Sherlock |
| **Game Theory** | Nash Equilibrium and dominant strategy analysis | Moriarty |
| **Utilitarian Triage** | Prioritizing findings by systemic impact | Mycroft |
| **Cascade Modeling** | 2nd and 3rd order effect prediction | Mycroft |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GOOGLE ANTIGRAVITY                                │
│                 Holmesian Cognitive Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │  MIND PALACE │    │ BRAIN ATTIC  │    │   BAYESIAN   │           │
│  │ (Vector DB)  │    │  (Filtering) │    │   ENGINE     │           │
│  │ Semantic     │    │  Strategic   │    │ Probabilistic│           │
│  │ Memory       │    │  Ignorance   │    │ Reasoning    │           │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘           │
│         │                   │                   │                    │
│         └───────────────────┼───────────────────┘                    │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────┐       │
│  │                   REASONING PROTOCOLS                      │       │
│  │   Deduction │ Induction │ Abduction │ Backward Reasoning  │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
├─────────────────────────────┼────────────────────────────────────────┤
│                             ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║                    4-AGENT COGNITIVE LOOP                      ║  │
│  ║                                                                 ║  │
│  ║  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐ ║  │
│  ║  │ WATSON  │───▶│ SHERLOCK │───▶│ MORIARTY │───▶│  MYCROFT  │ ║  │
│  ║  │Perception│   │ Deduction│    │Adversarial    │ Synthesis │ ║  │
│  ║  │         │    │          │    │          │    │           │ ║  │
│  ║  │"Observe"│    │"Abduce"  │    │"Exploit" │    │"Synthesize"║  │
│  ║  └─────────┘    └──────────┘    └──────────┘    └───────────┘ ║  │
│  ║       │                                              │        ║  │
│  ║       └──────────── FEEDBACK LOOP ◀──────────────────┘        ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 👤 The Four Agents

### 🔬 Watson — The Perception Engine

> *"The world is full of obvious things which nobody by any chance ever observes."*

Watson implements **active observation** rather than passive seeing:

- **System 2 Thinking**: Deliberate, energy-intensive attention to detail
- **Anomaly Detection**: Automatically tags deviations from expected patterns
- **Brain Attic Integration**: Filters irrelevant noise before it enters memory
- **Mind Palace Storage**: Encodes significant observations for retrieval

**Key Capability**: Fights *inattentional blindness* by scanning EVERYTHING and flagging what matters.

```python
# Watson transforms passive seeing into active observation
watson = WatsonAgent(observation_level=ObservationLevel.OBSERVING)
observation = watson.observe(code, location, force_deep=True)
# Returns: signals detected, anomalies found, confidence score
```

---

### 🎯 Sherlock — The Deduction Engine

> *"When you have eliminated the impossible, whatever remains, however improbable, must be the truth."*

Sherlock implements **abductive reasoning** with Bayesian updating:

- **Abduction**: Inference to the Best Explanation (not pure deduction!)
- **Bayesian Engine**: Rapid-fire probability updates as evidence accumulates
- **Mind Palace Consultation**: Retrieves similar patterns from memory
- **Backward Reasoning**: Traces effects to causes

**Key Capability**: Generates hypotheses with probability scores, continuously updating beliefs.

```python
# Sherlock generates and refines hypotheses
sherlock = SherlockAgent()
finding = sherlock.analyze(observation)
# Returns: hypothesis, probability, evidence chain, reasoning trace
```

---

### 🎭 Moriarty — The Adversarial Engine

> *"Every fairy tale needs a good old-fashioned villain."*

Moriarty implements **Game Theory** for adversarial analysis:

- **Game Modeling**: Models protocol as multi-player game
- **Nash Equilibrium**: Finds optimal attack strategies
- **Dominant Strategies**: Identifies attacks that work regardless of defense
- **"Breaking the Game"**: Finds irrational third-option attacks
- **ReX Protocol**: Generates self-healing exploit PoCs

**Key Capability**: Thinks like an attacker to verify vulnerabilities.

```python
# Moriarty models the game and finds attack vectors
moriarty = MoriartyAgent()
game = moriarty.model_game(protocol, hypothesis)
nash_attack = moriarty.find_nash_equilibrium(game)
result = moriarty.generate_exploit(hypothesis, nash_attack)
```

---

### 🏛️ Mycroft — The Synthesis Engine

> *"All other men are specialists, but his specialism is omniscience."*

Mycroft implements **macro-strategic synthesis**:

- **Correlation Analysis**: Cross-references findings to find systemic patterns
- **Cascade Modeling**: Predicts 2nd and 3rd order effects
- **Utilitarian Triage**: Prioritizes by "greatest good" (TVL × probability)
- **Strategic Recommendations**: Beyond tactical fixes

**Key Capability**: Sees the forest, not just the trees. A Medium finding with cascade potential may outrank an isolated Critical.

```python
# Mycroft synthesizes strategic recommendations
mycroft = MycroftAgent()
strategic_findings = mycroft.correlate_findings(sherlock_findings, moriarty_results)
report = mycroft.generate_report(protocol_name, strategic_findings)
```

---

## 🧩 Cognitive Core Components

### Mind Palace (Method of Loci)

The Mind Palace provides **semantic memory storage** using the ancient memory technique:

```python
from agents.cognitive_core import MindPalace, Room, MemoryType

palace = MindPalace()

# Encode a vulnerability pattern
palace.encode_vulnerability_pattern(
    pattern_code="external_call(); state_change();",
    vuln_type="reentrancy",
    severity="CRITICAL",
    association="🔄 The recursive vampire that drains funds"
)

# Retrieve similar patterns
result = palace.retrieve(
    query="external call before balance update",
    rooms=[Room.REENTRANCY],
    top_k=5
)

# Simulate a scenario
simulation = palace.simulate(
    scenario="withdraw function with external call",
    hypothesis="Reentrancy vulnerability exploitable"
)
```

### Brain Attic (Strategic Ignorance)

> *"A fool takes in all the lumber of every sort... the skillful workman is very careful indeed as to what he takes into his brain-attic."*

The Brain Attic **filters irrelevant information** to optimize retrieval:

```python
from agents.brain_attic import BrainAttic

attic = BrainAttic()

# Filter code chunks
filtered = attic.filter(code_chunk, file_path)
# Returns: relevance category, action (admit/defer/reject), signals

# Curate findings
relevance = attic.curate(finding)
# Returns: relevance score, category, action, explanation
```

### Bayesian Engine

Implements **Bayes' theorem** for hypothesis probability updates:

```python
from agents.bayesian_engine import BayesianReasoner, EvidenceType

reasoner = BayesianReasoner()

# Create hypothesis with prior
hyp = reasoner.create_hypothesis(
    name="Reentrancy in withdraw()",
    vulnerability_type="reentrancy",
    location="Bank.sol:45"
)

# Update with evidence
reasoner.apply_rag_match(hyp.id, match_score=0.85, "The DAO pattern", is_historical_exploit=True)
reasoner.apply_exploit_result(hyp.id, success=True, "Drained 100 ETH in test")

# Get posterior probability
probability = reasoner.get_posterior(hyp.id)  # 0.92
```

### Reasoning Protocols

Implements the full suite of Holmesian reasoning:

```python
from agents.reasoning_protocols import ReasoningEngine, Observation

engine = ReasoningEngine()

# Abductive reasoning (the primary engine)
obs = Observation(
    id="obs_1",
    description="External call before state update",
    context="withdraw function"
)
hypotheses = engine.abduce(obs)
best = engine.select_best_explanation(hypotheses)

# Backward reasoning
chain = engine.reason_backwards("funds drained")
# Returns: potential causes ranked by probability

# Full analysis
result = engine.analyze(code, context, known_facts)
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/SM-Sher-Aud-Framework.git
cd SM-Sher-Aud-Framework

# Install dependencies
pip install -r requirements.txt

# Optional: Set up Qdrant for production Mind Palace
docker run -p 6333:6333 qdrant/qdrant
```

### Run an Audit

```bash
# Full cognitive loop audit
./scripts/audit_workflow.sh <target_directory>

# Individual agent operations
python agents/watson.py --action observe --input contract.sol --output observations.json
python agents/sherlock.py --action detect --input observations.json --output findings.json
python agents/moriarty.py --action exploit --input findings.json --output-dir ./exploits
python agents/mycroft.py --action report --input findings.json --output report.md
```

### Configuration

Edit `config/cognitive_config.yaml` to tune:

- Mind Palace rooms and retrieval priorities
- Brain Attic filtering patterns
- Bayesian priors and evidence weights
- Triage weights and thresholds

---

## 📊 Cognitive Loop Flow

```
1. INGEST    → Watson chunks code, filters via Brain Attic
2. OBSERVE   → Watson performs System 2 observation, detects anomalies
3. RECALL    → Sherlock queries Mind Palace for similar patterns
4. HYPOTHESIZE → Sherlock generates abductive hypotheses
5. UPDATE    → Bayesian Engine updates probabilities with evidence
6. MODEL     → Moriarty models protocol as game
7. ATTACK    → Moriarty finds Nash Equilibrium, generates exploits
8. VERIFY    → Exploits run, results feed back to Bayesian Engine
9. CORRELATE → Mycroft cross-references, models cascades
10. TRIAGE   → Mycroft applies utilitarian prioritization
11. REPORT   → Mycroft generates strategic recommendations

IF significant new evidence → LOOP BACK to Step 3
```

---

## 📖 The Holmesian Philosophy

### Why "Abduction" Not "Deduction"?

The "Science of Deduction" is a misnomer. Holmes's primary methodology is **abduction**:

| Type | Direction | Guarantee |
|------|-----------|-----------|
| Deduction | General → Specific | Certain (if premises true) |
| Induction | Specific → General | Probabilistic |
| **Abduction** | Observation → Best Explanation | Plausible |

Holmes observes mud on boots and scratches on a watch, then *abduces* the best explanation. This is not deductive certainty—it's creative hypothesis generation.

### The Micro-Macro Split

- **Sherlock**: Tactical genius. Focuses on the specific—the mud on the shoe, the ash type, the scratch pattern.
- **Mycroft**: Strategic genius. Focuses on the general—how a naval treaty affects currency markets.

This framework mirrors this split:
- Sherlock: Individual vulnerabilities, code patterns, specific exploits
- Mycroft: Protocol-wide risk, cascade effects, ecosystem impact

---

## 📁 Directory Structure

```
SM-Sher-Aud-Framework/
├── agents/
│   ├── cognitive_core.py     # Mind Palace implementation
│   ├── brain_attic.py        # Strategic ignorance filtering
│   ├── bayesian_engine.py    # Probabilistic reasoning
│   ├── reasoning_protocols.py # Deduction, induction, abduction
│   ├── watson.py             # Perception agent
│   ├── sherlock.py           # Deduction agent
│   ├── moriarty.py           # Adversarial agent
│   └── mycroft.py            # Synthesis agent
├── config/
│   ├── cognitive_config.yaml # Full cognitive architecture config
│   ├── slither.config.json
│   └── echidna.yaml
├── scripts/
│   └── audit_workflow.sh     # Main orchestration script
├── learning/
│   └── LEARNING_RESOURCES.md
└── README.md
```

---

## 🔮 Future Enhancements

- [ ] Production Qdrant integration for Mind Palace
- [ ] Real LLM embeddings (text-embedding-3-large)
- [ ] Formal verification integration (Certora, Halmos)
- [ ] Cross-protocol dependency analysis
- [ ] Historical exploit database import
- [ ] Real-time Bayesian dashboard

---

## 📜 License

MIT License

---

> *"The game is afoot!"*
> — Sherlock Holmes

*Built with 🔍 by the Google Antigravity Team*
# sherlock
