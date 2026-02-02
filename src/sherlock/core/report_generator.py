from datetime import datetime

from .db import Database


class ReportGenerator:
    """
    Stage 3: The Synthesizer.
    Generates a human-readable audit report from the Database state.
    """

    def __init__(self, db: Database, run_id: str):
        self.db = db
        self.run_id = run_id

    def generate_report(self, output_path: str):
        """
        Synthesize findings into a Markdown report.
        """
        conn = self.db._get_conn()
        cur = conn.cursor()

        # 1. Fetch Run Stats
        cur.execute("SELECT COUNT(*) FROM audit_lifecycle WHERE run_id = ?", (self.run_id,))
        total_files = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM audit_lifecycle WHERE run_id = ? AND status = 'COMPLETE'", (self.run_id,))
        completed_files = cur.fetchone()[0]

        # 2. Fetch Detections
        cur.execute("""
            SELECT file_path, primitive, evidence 
            FROM detections 
            WHERE run_id = ? 
            ORDER BY file_path
        """, (self.run_id,))
        detections = cur.fetchall()

        # 3. Fetch Fingerprints (Similiarity)
        # We need to join with protocol_fingerprints if we linked them in detections
        # For now, we'll parse evidence JSON if we stored 'similar_issues' there.

        report = []
        report.append("# Sherlock Audit Report")
        report.append(f"**Run ID**: `{self.run_id}`")
        report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Coverage**: {completed_files}/{total_files} files analyzed.")
        report.append("\n---")

        report.append("## 🔍 Executive Summary")
        report.append("| File | Primitive | Risks Found |")
        report.append("|---|---|---|")

        import json

        high_risk_issues = []

        for file_path, primitive, evidence_json in detections:
            fname = file_path.split("/")[-1]
            try:
                evidence = json.loads(evidence_json)
            except:
                evidence = {}

            # Check for Similarity Issues
            similar_issues = evidence.get('similar_issues', [])
            risk_count = len(similar_issues)
            
            # Proof is God Status
            proof_status = evidence.get('proof_status', 'Pending')
            status_icon = "✅" if proof_status == "Verified" else "⚠️" if proof_status == "Quarantined" else "❓"

            report.append(f"| `{fname}` | {primitive} | {risk_count} | {status_icon} {proof_status} |")

            if similar_issues:
                for issue in similar_issues:
                    high_risk_issues.append({
                        "file": fname,
                        "type": issue.get('type'),
                        "desc": issue.get('description'),
                        "fix": issue.get('fix'),
                        "verified": evidence.get('verified', False)
                    })

        report.append("\n## 🚨 High Probability Risks")
        if high_risk_issues:
            for issue in high_risk_issues:
                report.append(f"### {issue['type']} in `{issue['file']}`")
                report.append(f"- **Description**: {issue['desc']}")
                report.append(f"- **Recommendation**: {issue['fix']}")
                report.append("")
        else:
            report.append("No known vulnerability patterns matched via Similarity Engine.")

        report.append("\n## 📋 Detailed Findings")
        for file_path, primitive, evidence_json in detections:
            fname = file_path.split("/")[-1]
            report.append(f"### {fname}")
            report.append(f"- **Type**: {primitive}")
            # Could add more detail here from evidence

        # Write to file
        with open(output_path, 'w') as f:
            f.write("\n".join(report))

        print(f"[Report] Generated: {output_path}")
        conn.close()
