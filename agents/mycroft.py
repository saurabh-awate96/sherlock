"""
Google Antigravity: Mycroft Agent (Enhanced)
=============================================

Mycroft is THE SYNTHESIS ENGINE - 'Omniscience' at Scale.

"All other men are specialists, but his specialism is omniscience."
- Sherlock Holmes, describing Mycroft

Mycroft specializes in the GENERAL and ABSTRACT:
- How a naval treaty in India affects the Canadian currency market
- How a state change in Contract A affects Contract B
- How a governance vote affects TVL across the ecosystem

He is a STRATEGIC genius, a SYSTEMS ANALYST.

Key difference from Sherlock:
- Sherlock: Micro (crimes, individuals, physical evidence)
- Mycroft: Macro (governments, geopolitics, systems)

Trade-off: Superior processing power, but PHYSICAL INERTIA.
Mycroft provides the strategic solution; Sherlock does the legwork.

"I hear of Sherlock everywhere since you became his chronicler. 
By the way, Sherlock, I expected to see you round last week to 
consult me over that Manor House case. I thought you might be 
a little out of your depth."
"""

import argparse
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum


# ==============================================================================
# Strategic Analysis Data Structures
# ==============================================================================

class SystemicRisk(Enum):
    """Levels of systemic risk."""
    CATASTROPHIC = "catastrophic"    # Entire protocol at risk
    SEVERE = "severe"                # Major impact
    SIGNIFICANT = "significant"      # Notable impact
    MODERATE = "moderate"            # Limited impact
    MINIMAL = "minimal"              # Isolated impact


class CascadeType(Enum):
    """Types of cascade effects."""
    LIQUIDITY = "liquidity"          # Liquidity drain
    PRICE = "price"                  # Price collapse
    GOVERNANCE = "governance"        # Governance attack
    CROSS_PROTOCOL = "cross_protocol" # Multi-protocol impact
    CONFIDENCE = "confidence"        # User confidence loss


@dataclass
class CascadeEffect:
    """A second-order effect from a vulnerability."""
    order: int                       # 1st, 2nd, 3rd order effect
    effect_type: CascadeType
    description: str
    probability: float
    impact_estimate: str
    affected_systems: List[str]


@dataclass
class StrategicFinding:
    """A finding with strategic implications."""
    id: str
    title: str
    description: str
    severity: str
    
    # Tactical details (from Sherlock)
    vulnerability_type: str
    location: str
    probability: float
    
    # Strategic analysis (Mycroft's contribution)
    systemic_risk: SystemicRisk
    tvl_at_risk: str
    cascade_effects: List[CascadeEffect]
    ecosystem_impact: str
    
    # Recommendations
    tactical_fix: str
    strategic_recommendation: str
    
    # Triage score
    triage_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "vulnerability_type": self.vulnerability_type,
            "location": self.location,
            "probability": self.probability,
            "systemic_risk": self.systemic_risk.value,
            "tvl_at_risk": self.tvl_at_risk,
            "cascade_effects": [
                {
                    "order": c.order,
                    "type": c.effect_type.value,
                    "description": c.description,
                    "probability": c.probability,
                    "impact": c.impact_estimate,
                    "affected": c.affected_systems
                }
                for c in self.cascade_effects
            ],
            "ecosystem_impact": self.ecosystem_impact,
            "tactical_fix": self.tactical_fix,
            "strategic_recommendation": self.strategic_recommendation,
            "triage_score": self.triage_score
        }


@dataclass
class AuditReport:
    """Complete audit report."""
    protocol_name: str
    audit_date: datetime
    executive_summary: str
    findings: List[StrategicFinding]
    overall_risk: SystemicRisk
    recommendations: List[str]
    
    # Aggregated metrics
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # Strategic assessment
    tvl_risk_summary: str
    ecosystem_risk_summary: str


# ==============================================================================
# Mycroft Agent
# ==============================================================================

class MycroftAgent:
    """
    THE SYNTHESIS ENGINE - Omniscience at Scale
    
    Mycroft's process:
    1. Correlate findings from Sherlock and Moriarty
    2. Analyze systemic risk across the entire system
    3. Model cascade effects (2nd, 3rd order impacts)
    4. Apply utilitarian triage (greatest good)
    5. Generate strategic recommendations
    
    "Mycroft has the tidiest and most orderly brain, with the greatest 
    capacity for storing facts, of any man living."
    """
    
    # Triage weights for utilitarian optimization
    TRIAGE_WEIGHTS = {
        "tvl_at_risk": 0.40,
        "cascade_potential": 0.25,
        "exploitation_likelihood": 0.20,
        "remediation_difficulty": 0.15,
    }
    
    def __init__(self):
        """Initialize Mycroft Agent."""
        self.findings: List[StrategicFinding] = []
        self.cascade_models: Dict[str, List[CascadeEffect]] = {}
        
        print("[Mycroft] Initialized synthesis engine")
        print("[Mycroft] 'All other men are specialists, but his specialism is omniscience.'")
    
    # --------------------------------------------------------------------------
    # Correlation Analysis
    # --------------------------------------------------------------------------
    
    def correlate_findings(
        self,
        sherlock_findings: List[Dict[str, Any]],
        moriarty_results: List[Dict[str, Any]]
    ) -> List[StrategicFinding]:
        """
        Cross-reference findings to identify systemic patterns.
        
        Mycroft sees macro patterns:
        - Finding A: Oracle latency issue
        - Finding B: Liquidation threshold too tight
        - Finding C: Flash loan availability
        
        Mycroft's insight: These combine into a cascade liquidation attack.
        
        Args:
            sherlock_findings: Tactical findings from Sherlock
            moriarty_results: Exploitation results from Moriarty
        
        Returns:
            List of strategic findings with cross-correlations
        """
        print(f"[Mycroft] Correlating {len(sherlock_findings)} findings with {len(moriarty_results)} exploit results...")
        
        strategic_findings = []
        
        # Index Moriarty results by task ID
        exploit_index = {r.get("task_id", ""): r for r in moriarty_results}
        
        for finding in sherlock_findings:
            finding_id = finding.get("id", f"finding_{len(strategic_findings)}")
            
            # Check if Moriarty verified this
            task_id = f"task_{finding_id}"
            exploit_result = exploit_index.get(task_id, {})
            
            # Determine if verified
            is_verified = exploit_result.get("status") == "success"
            
            # Analyze cascade effects
            cascade_effects = self._model_cascade_effects(finding)
            
            # Calculate systemic risk
            systemic_risk = self._assess_systemic_risk(finding, cascade_effects, is_verified)
            
            # Calculate triage score
            triage_score = self._calculate_triage_score(finding, cascade_effects, is_verified)
            
            # Generate recommendations
            tactical_fix = self._generate_tactical_fix(finding)
            strategic_rec = self._generate_strategic_recommendation(finding, cascade_effects)
            
            strategic_finding = StrategicFinding(
                id=finding_id,
                title=finding.get("title", "Unknown Finding"),
                description=finding.get("description", ""),
                severity=self._elevate_severity(finding, is_verified),
                vulnerability_type=finding.get("vulnerability_type", "unknown"),
                location=finding.get("location", "unknown"),
                probability=finding.get("probability", 0.5),
                systemic_risk=systemic_risk,
                tvl_at_risk=self._estimate_tvl_risk(finding, cascade_effects),
                cascade_effects=cascade_effects,
                ecosystem_impact=self._assess_ecosystem_impact(cascade_effects),
                tactical_fix=tactical_fix,
                strategic_recommendation=strategic_rec,
                triage_score=triage_score
            )
            
            strategic_findings.append(strategic_finding)
        
        # Sort by triage score (highest priority first)
        strategic_findings.sort(key=lambda f: f.triage_score, reverse=True)
        
        self.findings = strategic_findings
        
        print(f"[Mycroft] Correlation complete. {len(strategic_findings)} strategic findings.")
        
        return strategic_findings
    
    # --------------------------------------------------------------------------
    # Cascade Modeling
    # --------------------------------------------------------------------------
    
    def _model_cascade_effects(
        self,
        finding: Dict[str, Any]
    ) -> List[CascadeEffect]:
        """
        Model second and third-order cascade effects.
        
        Example cascade:
        1st order: $2M drained from lending pool
        2nd order: Liquidity drops → slippage increases
        3rd order: Arbitrageurs leave → governance token crashes
        
        Args:
            finding: The tactical finding
        
        Returns:
            List of cascade effects
        """
        cascades = []
        vuln_type = finding.get("vulnerability_type", "unknown").lower()
        
        # Model cascades based on vulnerability type
        if "reentrancy" in vuln_type or "drain" in vuln_type:
            cascades.extend([
                CascadeEffect(
                    order=1,
                    effect_type=CascadeType.LIQUIDITY,
                    description="Direct fund drainage from affected contracts",
                    probability=0.9,
                    impact_estimate="Up to 100% of contract TVL",
                    affected_systems=["lending_pool", "treasury"]
                ),
                CascadeEffect(
                    order=2,
                    effect_type=CascadeType.CONFIDENCE,
                    description="User confidence drops → mass withdrawals",
                    probability=0.7,
                    impact_estimate="40-60% TVL exodus within 48 hours",
                    affected_systems=["all_pools", "governance"]
                ),
                CascadeEffect(
                    order=3,
                    effect_type=CascadeType.PRICE,
                    description="Governance token crashes due to confidence loss",
                    probability=0.5,
                    impact_estimate="30-70% token price decline",
                    affected_systems=["token_market", "defi_ecosystem"]
                )
            ])
        
        elif "oracle" in vuln_type:
            cascades.extend([
                CascadeEffect(
                    order=1,
                    effect_type=CascadeType.PRICE,
                    description="Price manipulation enables unfair trades",
                    probability=0.85,
                    impact_estimate="Arbitrage profits at protocol expense",
                    affected_systems=["trading_pairs", "lending_positions"]
                ),
                CascadeEffect(
                    order=2,
                    effect_type=CascadeType.LIQUIDITY,
                    description="Incorrect prices trigger unnecessary liquidations",
                    probability=0.6,
                    impact_estimate="Cascade liquidation of healthy positions",
                    affected_systems=["lending_pool", "collateral_positions"]
                )
            ])
        
        elif "governance" in vuln_type:
            cascades.extend([
                CascadeEffect(
                    order=1,
                    effect_type=CascadeType.GOVERNANCE,
                    description="Malicious proposal passes",
                    probability=0.8,
                    impact_estimate="Protocol parameters compromised",
                    affected_systems=["governance", "treasury"]
                ),
                CascadeEffect(
                    order=2,
                    effect_type=CascadeType.CROSS_PROTOCOL,
                    description="Protocols depending on this governance affected",
                    probability=0.4,
                    impact_estimate="Cross-protocol contamination",
                    affected_systems=["dependent_protocols", "integrations"]
                )
            ])
        
        elif "liquidation" in vuln_type:
            cascades.extend([
                CascadeEffect(
                    order=1,
                    effect_type=CascadeType.LIQUIDITY,
                    description="Unfair liquidations drain user collateral",
                    probability=0.9,
                    impact_estimate="Direct loss of liquidated collateral",
                    affected_systems=["lending_pool"]
                ),
                CascadeEffect(
                    order=2,
                    effect_type=CascadeType.PRICE,
                    description="Liquidation fire sale crashes collateral prices",
                    probability=0.6,
                    impact_estimate="Price death spiral",
                    affected_systems=["token_markets", "other_lending_protocols"]
                ),
                CascadeEffect(
                    order=3,
                    effect_type=CascadeType.CROSS_PROTOCOL,
                    description="Other protocols using same collateral affected",
                    probability=0.4,
                    impact_estimate="DeFi-wide contagion",
                    affected_systems=["defi_ecosystem"]
                )
            ])
        
        else:
            # Generic cascade
            cascades.append(CascadeEffect(
                order=1,
                effect_type=CascadeType.LIQUIDITY,
                description="Direct impact from vulnerability exploitation",
                probability=0.7,
                impact_estimate="Variable based on TVL",
                affected_systems=["target_contract"]
            ))
        
        return cascades
    
    def predict_outcome(
        self,
        action: str,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predictive modeling for system outcomes.
        
        "If this vulnerability is exploited, what are the 
        second-order effects on the ecosystem?"
        
        Args:
            action: The action/exploit being considered
            system_state: Current state of the system
        
        Returns:
            Prediction with probabilities
        """
        print(f"[Mycroft] Running predictive model for: {action}")
        
        # This is a simplified model - in production would use
        # more sophisticated simulation
        
        tvl = system_state.get("tvl", 0)
        integrations = system_state.get("integrations", [])
        
        return {
            "action": action,
            "direct_impact": {
                "tvl_loss": f"${tvl * 0.5:,.0f} - ${tvl:,.0f}",
                "probability": 0.7
            },
            "cascade_impacts": [
                {
                    "order": 2,
                    "description": "Liquidity providers exit",
                    "probability": 0.6,
                    "impact": f"${tvl * 0.3:,.0f} additional TVL loss"
                },
                {
                    "order": 3,
                    "description": "Governance token crashes",
                    "probability": 0.4,
                    "impact": "30-50% token price decline"
                }
            ],
            "affected_integrations": integrations
        }
    
    # --------------------------------------------------------------------------
    # Utilitarian Triage
    # --------------------------------------------------------------------------
    
    def utilitarian_triage(
        self,
        findings: List[StrategicFinding]
    ) -> List[StrategicFinding]:
        """
        Utilitarian triage - sacrifice the few to save the many.
        
        Prioritize findings by:
        1. Systemic risk to entire protocol
        2. TVL at risk
        3. Likelihood of exploitation
        4. Cascading effects
        
        A Medium finding that could cascade > Critical isolated finding.
        
        Args:
            findings: List of strategic findings
        
        Returns:
            Prioritized list
        """
        print("[Mycroft] Applying utilitarian triage...")
        
        # Already sorted by triage_score in correlate_findings
        # But we can do additional analysis here
        
        for finding in findings:
            # Check for cross-protocol impacts
            for cascade in finding.cascade_effects:
                if cascade.effect_type == CascadeType.CROSS_PROTOCOL:
                    # Elevate priority for cross-protocol risks
                    finding.triage_score *= 1.5
                    print(f"  [Elevated] {finding.title} - cross-protocol risk")
                    break
        
        # Re-sort after adjustments
        findings.sort(key=lambda f: f.triage_score, reverse=True)
        
        return findings
    
    def _calculate_triage_score(
        self,
        finding: Dict[str, Any],
        cascades: List[CascadeEffect],
        is_verified: bool
    ) -> float:
        """Calculate utilitarian triage score."""
        score = 0.0
        
        # TVL at risk (weight: 0.40)
        severity = finding.get("severity", "MEDIUM").upper()
        severity_tvl = {"CRITICAL": 1.0, "HIGH": 0.7, "MEDIUM": 0.4, "LOW": 0.2}
        score += severity_tvl.get(severity, 0.3) * self.TRIAGE_WEIGHTS["tvl_at_risk"]
        
        # Cascade potential (weight: 0.25)
        cascade_score = sum(c.probability for c in cascades) / max(1, len(cascades))
        score += cascade_score * self.TRIAGE_WEIGHTS["cascade_potential"]
        
        # Exploitation likelihood (weight: 0.20)
        probability = finding.get("probability", 0.5)
        if is_verified:
            probability = 0.95
        score += probability * self.TRIAGE_WEIGHTS["exploitation_likelihood"]
        
        # Remediation difficulty (inverse - easy fixes get priority for quick wins)
        # This is simplified - would need actual analysis
        score += 0.5 * self.TRIAGE_WEIGHTS["remediation_difficulty"]
        
        return score
    
    # --------------------------------------------------------------------------
    # Strategic Recommendations
    # --------------------------------------------------------------------------
    
    def _generate_tactical_fix(self, finding: Dict[str, Any]) -> str:
        """Generate tactical fix recommendation."""
        vuln_type = finding.get("vulnerability_type", "unknown").lower()
        
        fixes = {
            "reentrancy": "Add ReentrancyGuard modifier and follow Checks-Effects-Interactions pattern",
            "oracle_manipulation": "Use TWAP oracle with minimum period and price deviation bounds",
            "access_control": "Implement role-based access control with multi-sig for critical functions",
            "flash_loan": "Add same-block detection and minimum holding period",
            "liquidation": "Add liquidation threshold buffer and gradual liquidation mechanism",
            "governance": "Add time-lock and voting escrow to prevent flash loan governance attacks",
            "timestamp": "Use block.number instead or implement randomness from external source",
        }
        
        for key, fix in fixes.items():
            if key in vuln_type:
                return fix
        
        return "Review and fix the identified vulnerability following security best practices"
    
    def _generate_strategic_recommendation(
        self,
        finding: Dict[str, Any],
        cascades: List[CascadeEffect]
    ) -> str:
        """Generate strategic recommendation beyond tactical fix."""
        recommendations = []
        
        # Check for cross-protocol risks
        has_cross_protocol = any(
            c.effect_type == CascadeType.CROSS_PROTOCOL for c in cascades
        )
        if has_cross_protocol:
            recommendations.append(
                "Coordinate disclosure with dependent protocols before public disclosure"
            )
        
        # Check for governance risks
        has_governance = any(
            c.effect_type == CascadeType.GOVERNANCE for c in cascades
        )
        if has_governance:
            recommendations.append(
                "Consider emergency governance proposal to pause affected functionality"
            )
        
        # Check for liquidity risks
        has_liquidity = any(
            c.effect_type == CascadeType.LIQUIDITY and c.order <= 2 for c in cascades
        )
        if has_liquidity:
            recommendations.append(
                "Prepare emergency pause mechanism and communication plan for users"
            )
        
        if not recommendations:
            recommendations.append(
                "Implement fix and conduct follow-up audit of related functionality"
            )
        
        return "; ".join(recommendations)
    
    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------
    
    def _assess_systemic_risk(
        self,
        finding: Dict[str, Any],
        cascades: List[CascadeEffect],
        is_verified: bool
    ) -> SystemicRisk:
        """Assess systemic risk level."""
        severity = finding.get("severity", "MEDIUM").upper()
        cascade_count = len([c for c in cascades if c.probability > 0.5])
        
        if is_verified and severity == "CRITICAL":
            return SystemicRisk.CATASTROPHIC
        elif severity == "CRITICAL" or cascade_count >= 3:
            return SystemicRisk.SEVERE
        elif severity == "HIGH" or cascade_count >= 2:
            return SystemicRisk.SIGNIFICANT
        elif severity == "MEDIUM":
            return SystemicRisk.MODERATE
        else:
            return SystemicRisk.MINIMAL
    
    def _elevate_severity(
        self,
        finding: Dict[str, Any],
        is_verified: bool
    ) -> str:
        """Elevate severity if exploit was verified."""
        severity = finding.get("severity", "MEDIUM").upper()
        
        if is_verified:
            # Verified exploits are at least HIGH
            if severity in ["LOW", "MEDIUM", "INFORMATIONAL"]:
                return "HIGH"
            elif severity == "HIGH":
                return "CRITICAL"
        
        return severity
    
    def _estimate_tvl_risk(
        self,
        finding: Dict[str, Any],
        cascades: List[CascadeEffect]
    ) -> str:
        """Estimate TVL at risk."""
        severity = finding.get("severity", "MEDIUM").upper()
        
        severity_risk = {
            "CRITICAL": "100% of affected contract TVL",
            "HIGH": "50-100% of affected contract TVL",
            "MEDIUM": "10-50% of affected contract TVL",
            "LOW": "< 10% of affected contract TVL",
        }
        
        base_risk = severity_risk.get(severity, "Variable")
        
        # Check for cascade amplification
        if any(c.order >= 2 and c.probability > 0.5 for c in cascades):
            base_risk += " + cascade effects may amplify impact"
        
        return base_risk
    
    def _assess_ecosystem_impact(self, cascades: List[CascadeEffect]) -> str:
        """Assess broader ecosystem impact."""
        if any(c.effect_type == CascadeType.CROSS_PROTOCOL for c in cascades):
            return "HIGH - Cross-protocol contamination possible"
        elif any(c.effect_type == CascadeType.CONFIDENCE for c in cascades):
            return "MEDIUM - User confidence and TVL at risk"
        elif len([c for c in cascades if c.order >= 2]) >= 2:
            return "MEDIUM - Multiple cascade effects identified"
        else:
            return "LOW - Isolated impact expected"
    
    # --------------------------------------------------------------------------
    # Report Generation
    # --------------------------------------------------------------------------
    
    def generate_report(
        self,
        protocol_name: str,
        findings: List[StrategicFinding]
    ) -> AuditReport:
        """
        Generate comprehensive audit report.
        
        Not just findings, but STRATEGIC RECOMMENDATIONS:
        - Protocol-level architectural changes
        - Ecosystem-level risk mitigation
        - Governance proposals for systemic fixes
        
        Args:
            protocol_name: Name of the audited protocol
            findings: Strategic findings
        
        Returns:
            Complete AuditReport
        """
        print(f"[Mycroft] Generating strategic audit report for {protocol_name}...")
        
        # Aggregate counts
        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity == "HIGH")
        medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in findings if "LOW" in f.severity.upper())
        
        # Determine overall risk
        if critical_count > 0:
            overall_risk = SystemicRisk.CATASTROPHIC
        elif high_count > 2:
            overall_risk = SystemicRisk.SEVERE
        elif high_count > 0:
            overall_risk = SystemicRisk.SIGNIFICANT
        elif medium_count > 0:
            overall_risk = SystemicRisk.MODERATE
        else:
            overall_risk = SystemicRisk.MINIMAL
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            protocol_name, findings, overall_risk,
            critical_count, high_count, medium_count, low_count
        )
        
        # Generate recommendations
        recommendations = self._generate_overall_recommendations(findings)
        
        # Risk summaries
        tvl_risk = self._generate_tvl_risk_summary(findings)
        ecosystem_risk = self._generate_ecosystem_risk_summary(findings)
        
        report = AuditReport(
            protocol_name=protocol_name,
            audit_date=datetime.now(),
            executive_summary=exec_summary,
            findings=findings,
            overall_risk=overall_risk,
            recommendations=recommendations,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            tvl_risk_summary=tvl_risk,
            ecosystem_risk_summary=ecosystem_risk
        )
        
        return report
    
    def export_report_markdown(self, report: AuditReport) -> str:
        """Export report as Markdown."""
        md = f"""# Security Audit Report: {report.protocol_name}

**Date:** {report.audit_date.strftime("%Y-%m-%d")}
**Auditor:** Google Antigravity (Mycroft Synthesis Engine)

---

## Executive Summary

{report.executive_summary}

### Finding Summary

| Severity | Count |
|----------|-------|
| Critical | {report.critical_count} |
| High | {report.high_count} |
| Medium | {report.medium_count} |
| Low | {report.low_count} |

**Overall Risk Assessment:** {report.overall_risk.value.upper()}

---

## Strategic Risk Assessment

### TVL Risk
{report.tvl_risk_summary}

### Ecosystem Impact
{report.ecosystem_risk_summary}

---

## Findings

"""
        for i, finding in enumerate(report.findings, 1):
            md += f"""
### [{finding.severity}] {finding.title}

**Location:** `{finding.location}`
**Vulnerability Type:** {finding.vulnerability_type}
**Probability:** {finding.probability:.0%}
**Systemic Risk:** {finding.systemic_risk.value}
**TVL at Risk:** {finding.tvl_at_risk}

#### Description
{finding.description}

#### Cascade Effects
"""
            for cascade in finding.cascade_effects:
                md += f"- **Order {cascade.order}** ({cascade.effect_type.value}): {cascade.description}\n"
            
            md += f"""
#### Recommendations
- **Tactical Fix:** {finding.tactical_fix}
- **Strategic:** {finding.strategic_recommendation}

---
"""
        
        md += """
## Overall Recommendations

"""
        for i, rec in enumerate(report.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        md += """
---

*Generated by Google Antigravity - Mycroft Synthesis Engine*
*"All other men are specialists, but his specialism is omniscience."*
"""
        
        return md
    
    def _generate_executive_summary(
        self,
        protocol_name: str,
        findings: List[StrategicFinding],
        overall_risk: SystemicRisk,
        critical: int, high: int, medium: int, low: int
    ) -> str:
        """Generate executive summary."""
        total = critical + high + medium + low
        
        summary = f"""This security audit of **{protocol_name}** identified **{total} findings** across critical, high, medium, and low severity levels.

The overall systemic risk assessment is **{overall_risk.value.upper()}**. """
        
        if critical > 0:
            summary += f"\n\n⚠️ **{critical} CRITICAL vulnerabilities** require immediate attention. These pose immediate risk to protocol TVL and user funds."
        
        if high > 0:
            summary += f"\n\n**{high} HIGH severity issues** could lead to significant loss of funds or protocol functionality under specific conditions."
        
        # Check for cascade risks
        cascade_findings = [f for f in findings if len(f.cascade_effects) >= 2]
        if cascade_findings:
            summary += f"\n\n**Cascade Risk:** {len(cascade_findings)} findings have identified second-order effects that could amplify impact beyond the immediate vulnerability."
        
        return summary
    
    def _generate_overall_recommendations(
        self,
        findings: List[StrategicFinding]
    ) -> List[str]:
        """Generate overall strategic recommendations."""
        recommendations = []
        
        # Check for critical findings
        critical_findings = [f for f in findings if f.severity == "CRITICAL"]
        if critical_findings:
            recommendations.append(
                "IMMEDIATE: Implement emergency pause on critical functionality until fixes are deployed"
            )
        
        # Check for systemic issues
        severe_findings = [f for f in findings if f.systemic_risk in [SystemicRisk.CATASTROPHIC, SystemicRisk.SEVERE]]
        if severe_findings:
            recommendations.append(
                "URGENT: Conduct comprehensive review of protocol architecture - multiple systemic risks identified"
            )
        
        # Cross-protocol risks
        cross_protocol = [
            f for f in findings 
            if any(c.effect_type == CascadeType.CROSS_PROTOCOL for c in f.cascade_effects)
        ]
        if cross_protocol:
            recommendations.append(
                "COORDINATION: Notify integrated protocols of potential cross-protocol risks before public disclosure"
            )
        
        # General recommendations
        recommendations.extend([
            "Implement tiered monitoring and alerting for all critical state changes",
            "Establish bug bounty program on Immunefi with appropriate rewards",
            "Create incident response runbook with pre-authorized emergency actions",
            "Schedule follow-up audit after implementing recommended fixes"
        ])
        
        return recommendations
    
    def _generate_tvl_risk_summary(self, findings: List[StrategicFinding]) -> str:
        """Generate TVL risk summary."""
        critical = [f for f in findings if f.severity == "CRITICAL"]
        high = [f for f in findings if f.severity == "HIGH"]
        
        if critical:
            return f"**EXTREME**: {len(critical)} critical vulnerabilities could result in complete loss of affected contract TVL. Immediate action required."
        elif high:
            return f"**HIGH**: {len(high)} high-severity vulnerabilities could result in significant TVL loss under exploitation."
        else:
            return "**MODERATE**: No immediate critical risk to TVL, but recommended fixes should be prioritized."
    
    def _generate_ecosystem_risk_summary(self, findings: List[StrategicFinding]) -> str:
        """Generate ecosystem risk summary."""
        cross_protocol = [
            f for f in findings
            if any(c.effect_type == CascadeType.CROSS_PROTOCOL for c in f.cascade_effects)
        ]
        
        if cross_protocol:
            return f"**HIGH**: {len(cross_protocol)} findings have potential for cross-protocol contamination. Coordinated response recommended."
        else:
            return "**CONTAINED**: Impact expected to be contained within protocol boundaries."
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Mycroft's statistics."""
        severity_counts = {}
        risk_counts = {}
        
        for finding in self.findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            risk_counts[finding.systemic_risk.value] = risk_counts.get(finding.systemic_risk.value, 0) + 1
        
        return {
            "total_findings": len(self.findings),
            "by_severity": severity_counts,
            "by_systemic_risk": risk_counts,
            "cascade_models": len(self.cascade_models)
        }


# ==============================================================================
# CLI Interface (Backward Compatible)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Mycroft Synthesis Agent (Enhanced)")
    parser.add_argument("--action", required=True, choices=["triage", "report", "stats"])
    parser.add_argument("--hypotheses")
    parser.add_argument("--exploits")
    parser.add_argument("--output", required=True)
    parser.add_argument("--input")
    parser.add_argument("--template")
    parser.add_argument("--protocol-name", default="Target Protocol")
    args = parser.parse_args()

    mycroft = MycroftAgent()
    
    print(f"[Mycroft] Executing action: {args.action}")
    print(f"[Mycroft] 'Omniscience is my specialty.'")

    if args.action == "triage":
        # Load findings and exploits
        try:
            with open(args.hypotheses, 'r') as f:
                findings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            findings = []
        
        try:
            with open(args.exploits, 'r') as f:
                exploits = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            exploits = []
        
        # Correlate and triage
        strategic_findings = mycroft.correlate_findings(findings, exploits)
        strategic_findings = mycroft.utilitarian_triage(strategic_findings)
        
        # Export
        output = {
            "timestamp": datetime.now().isoformat(),
            "findings": [f.to_dict() for f in strategic_findings],
            "score": "F" if any(f.severity == "CRITICAL" for f in strategic_findings) else "C"
        }
        
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"[Mycroft] Triage complete. Results saved to {args.output}")

    elif args.action == "report":
        # Load triaged findings
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        # Reconstruct findings
        strategic_findings = []
        for f_data in data.get("findings", []):
            cascades = [
                CascadeEffect(
                    order=c["order"],
                    effect_type=CascadeType(c["type"]),
                    description=c["description"],
                    probability=c["probability"],
                    impact_estimate=c["impact"],
                    affected_systems=c["affected"]
                )
                for c in f_data.get("cascade_effects", [])
            ]
            
            finding = StrategicFinding(
                id=f_data.get("id", "unknown"),
                title=f_data.get("title", "Unknown"),
                description=f_data.get("description", ""),
                severity=f_data.get("severity", "MEDIUM"),
                vulnerability_type=f_data.get("vulnerability_type", "unknown"),
                location=f_data.get("location", "unknown"),
                probability=f_data.get("probability", 0.5),
                systemic_risk=SystemicRisk(f_data.get("systemic_risk", "moderate")),
                tvl_at_risk=f_data.get("tvl_at_risk", "Variable"),
                cascade_effects=cascades,
                ecosystem_impact=f_data.get("ecosystem_impact", "Unknown"),
                tactical_fix=f_data.get("tactical_fix", ""),
                strategic_recommendation=f_data.get("strategic_recommendation", ""),
                triage_score=f_data.get("triage_score", 0.5)
            )
            strategic_findings.append(finding)
        
        # Generate report
        report = mycroft.generate_report(args.protocol_name, strategic_findings)
        markdown = mycroft.export_report_markdown(report)
        
        with open(args.output, "w") as f:
            f.write(markdown)
        
        print(f"[Mycroft] Report generated at {args.output}")

    elif args.action == "stats":
        stats = mycroft.get_statistics()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
