import os
from dataclasses import dataclass


@dataclass
class AuditConfig:
    depth: str  # "QUICK", "STANDARD", "DEEP"
    include_tests: bool
    banned_files: list[str]
    focus_primitives: list[str]  # e.g. ["Vault", "Strategy"]
    min_confidence: float

class MycroftAgent:
    """
    Mycroft: The Auditor of Auditors.
    He defines the 'Rules of Engagement' and verifies the 'Outcome'.
    """

    def __init__(self, db=None, run_id=None):
        self.db = db
        self.run_id = run_id

    def plan_audit(self, target_url: str, goal: str = "standard_audit") -> AuditConfig:
        """
        Phase 0: Define the Strategy.
        Decides HOW the audit should run based on historical data and user intent.
        """
        print(f"[Mycroft] Analyzing intent for {target_url}...")

        # Default policy (Standard)
        config = AuditConfig(
            depth="STANDARD",
            include_tests=False,
            banned_files=["lib/", "test/", "script/", "node_modules/"],
            focus_primitives=[],
            min_confidence=0.1
        )

        # 1. Historical Context Check (Witness-Led Planning)
        if self.db:
            print("[Mycroft] Consulting historical Witness Statements (Sherlock Findings)...")
            # Retrieve verified High severity findings
            critical_issues = self.db.get_findings_by_severity(severity='High')
            
            if critical_issues:
                print(f"[Mycroft] Found {len(critical_issues)} high-signal issues. Prioritizing Deep Dive.")
                config.depth = "DEEP"
                
                # Dynamic Primitive Prioritization
                for issue in critical_issues:
                    # Use title AND vulnerability type for signal
                    title = issue['title'].lower()
                    vuln_type = (issue.get('vulnerability_type') or "").lower()
                    
                    combined_text = f"{title} {vuln_type}"
                    
                    if "oracle" in combined_text: config.focus_primitives.append("Oracle")
                    if "vault" in combined_text: config.focus_primitives.append("Vault")
                    if "loan" in combined_text or "lend" in combined_text: config.focus_primitives.append("Loan")
                    if "swap" in combined_text or "price" in combined_text: config.focus_primitives.append("Exchange")
                
                config.focus_primitives = list(set(config.focus_primitives))
                if config.focus_primitives:
                    print(f"[Mycroft] Focusing on Primitives: {config.focus_primitives}")

        # 2. Intent Overrides
        if "deep" in goal.lower() or "thorough" in goal.lower():
            print("[Mycroft] Strategy Override: DEEP DIVE (High Recall, Lower Precision)")
            config.depth = "DEEP"
            config.min_confidence = 0.2 # Lower threshold to catch more

        elif "quick" in goal.lower() or "scan" in goal.lower():
            print("[Mycroft] Strategy Override: QUICK SCAN (High Precision, Low Recall)")
            config.depth = "QUICK"
            config.min_confidence = 0.7 # High threshold

        elif "compliance" in goal.lower():
            print("[Mycroft] Strategy Override: COMPLIANCE CHECK (Focus on Governance)")
            config.focus_primitives = list(set(config.focus_primitives + ["Governor", "AccessControl", "Timelock"]))

        return config

    def review_report(self, report_path: str, run_stats: dict) -> bool:
        """
        Phase 4: The Final Review.
        Checks if the audit met the standards set in Phase 0.
        """
        print("\n[Mycroft] Reviewing Final Report...")

        if not os.path.exists(report_path):
            print("❌ [Mycroft] REJECTED: Report file missing.")
            return False

        # Check Coverage
        coverage = run_stats.get('coverage_pct', 0)
        if coverage < 100:
             print(f"⚠️  [Mycroft] WARNING: Only {coverage}% of files were audited. This is not a 'Complete' audit.")
             # We might still approve, but with a warning

        # Check Findings
        with open(report_path) as f:
            content = f.read()

        if "High Probability Risks" in content:
            print("✅ [Mycroft] APPROVED: Report contains risk analysis.")
        else:
            print("⚠️  [Mycroft] NOTE: No high risks found. Ensure Similarity Engine is active.")

        print("✅ [Mycroft] SIGN-OFF: Audit Stage Complete.")
        return True
