# 📚 Smart Contract Security Learning Resources

> **Curated Educational Materials, Tutorials, Video Courses, and Research**

---

## Table of Contents

1. [🏆 Essential Libraries & Repositories](#-essential-libraries--repositories)
2. [🎥 Video Courses & Playlists](#-video-courses--playlists)
3. [📖 Documentation & Best Practices](#-documentation--best-practices)
4. [🔬 Research & Articles](#-research--articles)
5. [🏴‍☠️ CTF & Hands-On Practice](#️-ctf--hands-on-practice)
6. [🛠️ Free Security Tools (2025)](#️-free-security-tools-2025)
7. [📊 Bug Bounty Writeups & Case Studies](#-bug-bounty-writeups--case-studies)
8. [🎓 Learning Paths](#-learning-paths)

---

## 🏆 Essential Libraries & Repositories

### Immunefi Web3 Security Library
> **The definitive collection for Web3 security research**

🔗 **[github.com/immunefi-team/Web3-Security-Library](https://github.com/immunefi-team/Web3-Security-Library)**

| Section | Contents |
|---------|----------|
| **Starting Guides** | [Hacking the Blockchain: Ethereum](https://medium.com/immunefi/hacking-the-blockchain-an-ultimate-guide-4f34b33c6e8b), [Your First Day as a Bug Bounty Hunter](https://medium.com/immunefi/your-first-day-as-a-bug-bounty-hunter-on-immunefi-9b101768a40c) |
| **Blockchain Concepts** | Web3, EVM, Non-EVM chains, Consensus types, Wallets |
| **Smart Contracts** | Solidity, Vyper, Huff, EVM internals |
| **Tools** | Foundry, Hardhat, Truffle, Brownie, Analysis tools |
| **Vulnerabilities** | Logic errors, Reentrancy, Access control, Flash loans, Oracle manipulation, MEV |
| **Hack Analyses** | 2022-2023 exploit breakdowns |
| **Bugfix Reviews** | 2021-2023 vulnerability patches |

---

### Immunefi Bug Bounty Writeups
> **Real-world vulnerability reports from top hunters**

🔗 **[github.com/sayan011/Immunefi-bug-bounty-writeups-list](https://github.com/sayan011/Immunefi-bug-bounty-writeups-list)**

Curated collection of:
- Critical vulnerability discoveries
- Step-by-step exploitation techniques
- Bounty reward breakdowns
- Mitigation strategies implemented

---

### Past Audit Competitions
> **Historical audit contest data for study**

🔗 **[github.com/immunefi-team/Past-Audit-Competitions](https://github.com/immunefi-team/Past-Audit-Competitions)**

Study past competitions to:
- Understand judging criteria
- Learn from winning submissions
- Identify common vulnerability patterns
- Benchmark your finding quality

---

## 🎥 Video Courses & Playlists

### Smart Contract Hacking Course (Foundry 2024)
> **Comprehensive Foundry-based security course**

🔗 **[YouTube Playlist](https://www.youtube.com/playlist?list=PLO5VPQH6OWdX-Rh7RonjZhOd9pb9zOnHW)**

**Topics Covered:**
- Foundry setup and testing
- Fuzzing with Echidna
- Invariant testing
- Exploit development
- PoC creation

---

### Smart Contract Security & Auditing
> **In-depth security methodology**

🔗 **[YouTube Playlist](https://www.youtube.com/playlist?list=PLS01nW3RtgopJOtsMVOK3N7n7qyNMPbJ)**

**Topics Covered:**
- Audit workflow
- Common vulnerabilities
- Tool usage
- Report writing
- Client communication

---

### Intro to Web3 Security (Fall 2023)
> **Academic-style foundation course**

🔗 **[solidity-atl.kittlabs.io/intro-to-web3-security-fall-23](https://solidity-atl.kittlabs.io/intro-to-web3-security-fall-23/)**

**Curriculum:**
- Blockchain fundamentals
- Solidity security patterns
- Vulnerability categories
- Hands-on exercises
- Real-world case studies

---

## 📖 Documentation & Best Practices

### Consensys Smart Contract Best Practices
> **Industry-standard security guidelines**

🔗 **[consensysdiligence.github.io/smart-contract-best-practices](https://consensysdiligence.github.io/smart-contract-best-practices/)**

**Key Sections:**
- General philosophy
- Recommendations
- Known attacks
- Software engineering
- Token standards
- Documentation

**Must-Read Topics:**
```
├── Recommendations/
│   ├── External Calls
│   ├── Reentrancy
│   ├── Integer Overflow/Underflow
│   ├── DoS
│   └── Access Control
├── Known Attacks/
│   ├── Race Conditions
│   ├── Front-Running
│   ├── Timestamp Dependence
│   └── Force Feeding
└── Development/
    ├── Security Tools
    ├── Testing
    └── Deployment
```

---

### Mastering Effective Test Writing for Web3 Audits
> **Advanced testing methodology for auditors**

🔗 **[mixbytes.io/blog/mastering-effective-test-writing-for-web3-protocol-audits](https://mixbytes.io/blog/mastering-effective-test-writing-for-web3-protocol-audits)**

**Key Concepts:**
- Property-based testing strategies
- Edge case identification
- Invariant testing patterns
- Coverage optimization
- PoC development workflow

---

## 🔬 Research & Articles

### Immunefi Research Portal
> **Cutting-edge Web3 security research**

🔗 **[immunefi.com/research](https://immunefi.com/research/)**

**Research Areas:**
- Novel attack vectors
- Protocol-specific vulnerabilities
- Cross-chain security
- DeFi economic attacks
- Governance exploits

---

### Hashlock Free Security Tools Guide (2025)
> **Comprehensive tool comparison and usage**

🔗 **[hashlock.com/blog/top-free-smart-contract-security-and-audit-tools-2025](https://hashlock.com/blog/top-free-smart-contract-security-and-audit-tools-2025)**

**Tools Covered:**

| # | Tool | Type | Key Feature |
|---|------|------|-------------|
| 1 | **Hashlock AI Audit** | AI Analysis | Deep protocol-specific vulnerability detection |
| 2 | **Halmos** | Formal Verification | Symbolic testing for deep logic flaws |
| 3 | **Echidna** | Fuzzing | Property-based testing with coverage |
| 4 | **Solodit** | Research | 10,000+ aggregated vulnerabilities |
| 5 | **Slither** | Static Analysis | 90+ detectors, minimal false positives |
| 6 | **Medusa** | Fuzzing | Parallel fuzzing, coverage-guided |
| 7 | **Foundry** | Framework | Forge, Cast, Anvil, Chisel suite |
| 8 | **Aderyn** | Static Analysis | Rust-based, <1 sec per contract |
| 9 | **QuillShield** | AI Analysis | Logical error detection, auto-fixes |
| 10 | **Diligence Fuzzing** | Cloud Fuzzing | Harvey-powered FaaS |

---

## 🏴‍☠️ CTF & Hands-On Practice

### Damn Vulnerable DeFi
> **The gold standard for DeFi security practice**

🔗 **[damnvulnerabledefi.xyz](https://www.damnvulnerabledefi.xyz/)**

```bash
# Get started
git clone https://github.com/tinchoabbate/damn-vulnerable-defi.git
cd damn-vulnerable-defi
forge install
forge test --match-path test/unstoppable/Unstoppable.t.sol -vvvv
```

**Challenges:**
- Unstoppable
- Naive Receiver
- Truster
- Side Entrance
- The Rewarder
- Selfie
- Compromised
- Puppet
- Free Rider
- Backdoor
- Climber
- Safe Miners

---

### Ethernaut
> **Beginner-friendly Solidity security challenges**

🔗 **[ethernaut.openzeppelin.com](https://ethernaut.openzeppelin.com/)**

**Levels:** 29 challenges covering:
- Fallback/Receive
- Fallout
- Coin Flip
- Telephone
- Token
- Delegation
- Force
- Vault
- King
- Re-entrancy
- Elevator
- Privacy
- Gatekeeper (1-3)
- Naught Coin
- Preservation
- Recovery
- And more...

---

### Other CTF Platforms

| Platform | Difficulty | Focus |
|----------|------------|-------|
| **Paradigm CTF** | Advanced | Complex multi-contract |
| **QuillCTF** | All levels | Varied challenges |
| **Secureum A-MAZE-X** | Advanced | Research-oriented |
| **Capture the Ether** | Beginner | Legacy (historical) |

---

## 🛠️ Free Security Tools (2025)

### Static Analysis

```bash
# Slither - 90+ vulnerability detectors
pip3 install slither-analyzer
slither .

# Aderyn - Rust-based, lightning fast
cargo install aderyn
aderyn .
```

### Fuzzing

```bash
# Echidna - Property-based testing
brew install echidna  # Mac
echidna-test . --contract MyTest

# Medusa - Parallel fuzzing
go install github.com/crytic/medusa@latest
medusa fuzz --config medusa.json
```

### Formal Verification

```bash
# Halmos - Symbolic testing
pip3 install halmos
halmos --contract MyContract
```

### AI-Powered

| Tool | URL | Features |
|------|-----|----------|
| **Hashlock AI** | [aiaudit.hashlock.com](https://aiaudit.hashlock.com/) | Deep analysis, severity ratings |
| **QuillShield** | [shield.quillai.network](https://shield.quillai.network/) | Logic errors, auto-fixes |
| **SmartLLMSentry** | Research framework | 91.1% accuracy LLM detection |

### Development Framework

```bash
# Foundry - Complete toolkit
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Components:
# - Forge: Testing & compilation
# - Cast: Contract interaction
# - Anvil: Local node
# - Chisel: Solidity REPL
```

---

## 📊 Bug Bounty Writeups & Case Studies

### Top Resources for Learning from Real Bugs

| Resource | Content |
|----------|---------|
| [Rekt News](https://rekt.news/) | Post-mortem analyses of major hacks |
| [De.Fi REKT Database](https://de.fi/rekt-database) | 3000+ documented incidents |
| [Solodit](https://solodit.cyfrin.io/) | 10,000+ aggregated vulnerabilities |
| [Immunefi Bounty Writeups](https://github.com/sayan011/Immunefi-bug-bounty-writeups-list) | Hunter writeups |
| [Code4rena Reports](https://code4rena.com/reports) | Audit contest findings |
| [Sherlock Reports](https://audits.sherlock.xyz/) | Contest submissions |

### Notable Case Studies to Study

| Exploit | Amount | Vulnerability Type | Year |
|---------|--------|-------------------|------|
| Bybit | $1.5B | Key compromise | 2025 |
| Ronin Bridge | $624M | Multi-sig compromise | 2022 |
| Poly Network | $611M | Cross-chain | 2021 |
| Wormhole | $326M | Signature verification | 2022 |
| DMM Bitcoin | $305M | Key compromise | 2024 |
| Euler Finance | $197M | Donate + liquidation | 2023 |
| Mango Markets | $117M | Oracle manipulation | 2022 |
| Curve/Vyper | $70M | Reentrancy (compiler) | 2023 |
| The DAO | $60M | Reentrancy | 2016 |

---

## 🎓 Learning Paths

### Beginner Path (0-3 months)

```
Week 1-2: Solidity Fundamentals
├── CryptoZombies
├── Solidity by Example
└── Official Solidity Docs

Week 3-4: Security Basics
├── Consensys Best Practices (read all)
├── SWC Registry (study entries)
└── Ethernaut (Levels 1-15)

Week 5-8: Intermediate Practice
├── Damn Vulnerable DeFi (Challenges 1-8)
├── Immunefi Web3 Security Library
└── Real audit reports (5+ reports)

Week 9-12: Tool Proficiency
├── Foundry deep dive
├── Slither mastery
├── Echidna fuzzing
└── First shadow audit
```

### Intermediate Path (3-6 months)

```
Month 4: Advanced Vulnerabilities
├── Complete DVDF
├── Cross-contract reentrancy
├── Flash loan mechanics
└── Oracle manipulation patterns

Month 5: Tooling Mastery
├── Halmos formal verification
├── Medusa parallel fuzzing
├── Custom Slither detectors
└── Invariant testing

Month 6: Competition Ready
├── Shadow 2-3 past contests
├── First real Code4rena/Sherlock
├── Build reputation
└── Specialize in an area
```

### Expert Path (6-12 months)

```
Months 7-9: Deep Specialization
├── Choose focus: DeFi/Cross-chain/Governance
├── Study 50+ real exploits in-depth
├── Develop custom detection tools
└── Contribute to open-source security

Months 10-12: Industry Recognition
├── Consistent contest participation
├── Bug bounty hunting (Immunefi)
├── Publish research/writeups
└── Consider audit firm applications
```

---

## 🔗 Quick Links Summary

### Essential Repositories
- [Immunefi Web3 Security Library](https://github.com/immunefi-team/Web3-Security-Library)
- [Immunefi Bug Bounty Writeups](https://github.com/sayan011/Immunefi-bug-bounty-writeups-list)
- [Past Audit Competitions](https://github.com/immunefi-team/Past-Audit-Competitions)

### Video Learning
- [Smart Contract Hacking (Foundry)](https://www.youtube.com/playlist?list=PLO5VPQH6OWdX-Rh7RonjZhOd9pb9zOnHW)
- [Security & Auditing](https://www.youtube.com/playlist?list=PLS01nW3RtgopJOtsMVOK3N7n7qyNMPbJ)

### Documentation
- [Consensys Best Practices](https://consensysdiligence.github.io/smart-contract-best-practices/)
- [Intro to Web3 Security](https://solidity-atl.kittlabs.io/intro-to-web3-security-fall-23/)
- [MixBytes Testing Guide](https://mixbytes.io/blog/mastering-effective-test-writing-for-web3-protocol-audits)

### Research
- [Immunefi Research](https://immunefi.com/research/)
- [Hashlock Tools 2025](https://hashlock.com/blog/top-free-smart-contract-security-and-audit-tools-2025)

### Practice
- [Damn Vulnerable DeFi](https://www.damnvulnerabledefi.xyz/)
- [Ethernaut](https://ethernaut.openzeppelin.com/)

---

*Keep learning. Keep hunting. Stay sharp.* 🎯
