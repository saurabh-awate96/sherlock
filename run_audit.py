
import sys
import os
import json
from agents.universal_orchestrator import UniversalOrchestrator

def main():
    # Set paths
    base_dir = os.getcwd()
    target_dir = os.path.join(base_dir, "framework Test/repo")
    output_dir = os.path.join(base_dir, "framework Test")
    
    if not os.path.exists(target_dir):
        print(f"Error: Target directory {target_dir} does not exist")
        sys.exit(1)

    print(f"Initializing Orchestrator for target: {target_dir}")
    
    try:
        orchestrator = UniversalOrchestrator()
        
        print("Starting Deep Audit...")
        # Deep mode settings: risk=high for moriarty usage, higher timeout
        result = orchestrator.execute(
            intent="Analyze the security of the Flying Tulip protocol code to find critical vulnerabilities",
            scope=target_dir,
            risk_tolerance="high",
            timeout=7200
        )
        
        # Save output
        output_file = os.path.join(output_dir, "findings.json")
        full_report_file = os.path.join(output_dir, "full_report.json")
        
        print(f"Audit Complete. Status: {result.status}")
        print(f"Cycles: {result.cycles_completed}")
        print(f"Findings: {len(result.findings)}")
        
        # Save simple findings
        with open(output_file, "w") as f:
            json.dump(result.findings, f, indent=2, default=str)
            
        # Save full result
        with open(full_report_file, "w") as f:
            # result is a dataclass, convert to dict
            result_dict = {
                "session_id": result.session_id,
                "intent": result.intent,
                "status": result.status,
                "cycles_completed": result.cycles_completed,
                "findings": result.findings,
                "observations": result.observations,
                "actions_taken": result.actions_taken,
                "execution_time_ms": result.execution_time_ms,
                "final_report": result.final_report
            }
            json.dump(result_dict, f, indent=2, default=str)
            
        print(f"Findings saved to {output_file}")
        print(f"Full report saved to {full_report_file}")
        
    except Exception as e:
        print(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
