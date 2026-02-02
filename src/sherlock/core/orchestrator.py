import os
import sys
import uuid
import structlog
from pathlib import Path
from typing import Optional, List, Any

from sherlock.core.config_loader import ConfigLoader
from sherlock.core.semantic_detector import SemanticDetector
from sherlock.core.handler_generator import HandlerGenerator
from sherlock.core.compiler_loop import CompilationLoop
from sherlock.core.audit_trail import AuditTrail
from sherlock.core.confidence import ConfidenceScorer
from sherlock.core.sequencer import Sequencer, AuditState
from sherlock.core.dependency_mapper import DependencyMapper
from sherlock.agents.mycroft import MycroftAgent
from sherlock.agents.inspector import InspectorAgent
from sherlock.agents.irene import Irene
from sherlock.agents.moriarty import Moriarty
from sherlock.core.report_generator import ReportGenerator

# ... (logging config) ...



# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

class Orchestrator:
    """
    Central brain of Sherlock 2.0.
    Orchestrates the multi-agent audit lifecycle:
    1. Lestrade (Ingestion)
    2. Mycroft (Planning)
    3. Irene (Research)
    4. Hudson/Sherlock (Deep Dive & Logic)
    5. Report Synthesis
    """

    def __init__(self, target: str, output_dir: str = "./test/handlers", min_confidence: float = 0.7, ingest_issues: bool = False):
        self.target = target
        self.output_dir = output_dir
        self.min_confidence = min_confidence
        self.ingest_issues = ingest_issues
        self.run_id = str(uuid.uuid4())
        
        # 0. Lestrade: Secure the Scene
        from sherlock.agents.lestrade import Lestrade
        self.inspector = Lestrade()
        logger.info("orchestrator_deploying_lestrade", target=self.target)
        evidence_path = self.inspector.gather_evidence(self.target)
        self.contract_dir = Path(evidence_path)

        # Initialize Core Components
        self.config = ConfigLoader('sherlock/audit_config.yaml')
        self.trail = AuditTrail("sherlock_output", db_path="sherlock/sherlock_output/sherlock.db")
        self.db = self.trail.db
        
        # Inject DB into Lestrade for issue storage
        self.inspector.db = self.db
        
        self.sequencer = Sequencer(self.db, self.run_id)
        
        # Agents & Engines
        self.mycroft = MycroftAgent(db=self.db, run_id=self.run_id)
        self.inspector_agent = InspectorAgent(db=self.db, run_id=self.run_id)
        self.moriarty = Moriarty(self.contract_dir, db=self.db)
        self.detector = SemanticDetector(self.config)
        self.scorer = ConfidenceScorer(self.config)
        self.generator = HandlerGenerator(self.config)
        self.compiler = CompilationLoop(self.config, db=self.db)
        
        logger.info("orchestrator_initialized", run_id=self.run_id, contract_dir=str(self.contract_dir))

    def run_audit(self) -> None:
        """Execute the full audit lifecycle."""
        try:
            # Phase 0.5: Ingest Issues (if requested)
            if self.ingest_issues:
                logger.info("phase_start", phase="issue_ingestion")
                # Use local Appledore KB for verified/structured findings
                self.inspector.ingest_from_appledore()

            # Phase 0: Planning
            audit_plan = self._phase_planning()
            
            # Phase 0.5: Context Anchoring (Ultra-Granular Analysis)
            self._phase_context_anchoring()

            # Phase 1: Research & Scope
            audit_order = self._phase_research(audit_plan)
            
            # Phase 2: Deep Dive (Logic Shells)
            raw_results = self._phase_deep_dive(audit_order, audit_plan)
            
            # Phase 3: Verification (Proof is God)
            verified_results = self._phase_verification(raw_results)
            
            # Phase 4: Reporting
            report_path = self._phase_reporting()
            
            # Phase 5: Review
            self._phase_review(report_path, audit_order, verified_results)
            
        except Exception as e:
            logger.error("audit_failed", error=str(e), exc_info=True)
            raise

    def _phase_planning(self) -> Any:
        logger.info("phase_start", phase="planning")
        audit_plan = self.mycroft.plan_audit(self.target, goal="Standard Audit")
        logger.info("plan_created", plan=audit_plan)
        return audit_plan

    def _phase_context_anchoring(self):
        """
        Phase 0.5: Deep Context Building.
        Performs ultra-granular line-by-line analysis of key files.
        Prioritizes 'High Signal' code locations from the Knowledge Graph.
        """
        logger.info("phase_start", phase="context_anchoring")
        
        # 1. High Priority: Analyze Known Vulnerability Locations (from DB)
        try:
            conn = self.db._get_conn()
            conn.row_factory = self.db.sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM code_locations")
            locations = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            if locations:
                logger.info("context_anchoring_db", count=len(locations))
                for loc in locations:
                    self.inspector_agent.analyze_code_location(loc)
                return # If we have targeted locations, focus on them!
                
        except Exception as e:
            logger.warning("context_anchoring_db_failed", error=str(e))

        # 2. Fallback: Analyze All Source Files (if no DB context)
        files = list(Path(self.contract_dir).rglob("*.sol"))
        if not files:
            files = list(Path(self.contract_dir).rglob("*.py"))
            
        for f in files:
            if any(part in str(f) for part in ['test', 'node_modules', 'venv', 'lib']):
                continue
            self.inspector_agent.analyze_file(str(f))

    def _phase_research(self, audit_plan: Any) -> List[str]:
        logger.info("phase_start", phase="research")
        
        # Irene Research
        irene = Irene(target_url=self.target, db=self.db, run_id=self.run_id, root_dir=str(self.contract_dir))
        irene.execute(intent="Standard Audit")
        
        # Dependency Mapping
        mapper = DependencyMapper(self.contract_dir)
        raw_order = mapper.build_graph()
        
        # Filter based on Plan
        audit_order = []
        for f in raw_order:
            if any(banned in f for banned in audit_plan.banned_files):
                continue
            audit_order.append(f)
            
        # Queue files
        for f in audit_order:
            self.sequencer.add_to_queue(f)
            
        logger.info("scope_defined", total_files=len(audit_order))
        return audit_order

    def _phase_deep_dive(self, audit_order: List[str], audit_plan: Any) -> List[dict]:
        logger.info("phase_start", phase="deep_dive")
        results = []
        
        mapper = DependencyMapper(self.contract_dir) # Re-instantiate if needed or pass from phase 1
        
        for contract_path_str in audit_order:
            contract_path = Path(contract_path_str)
            
            if self.sequencer.is_complete(contract_path_str):
                logger.info("skipping_completed", file=contract_path.name)
                continue
                
            self.sequencer.update_status(contract_path_str, AuditState.ANALYZING, "Starting Deep Dive")
            
            # Skip test files or handlers
            if "_Handler" in contract_path.name or ".t.sol" in contract_path.name:
                self.sequencer.update_status(contract_path_str, AuditState.COMPLETE, "Skipped Test File")
                continue

            # 1. Detect
            detection = self.detector.detect_primitive(str(contract_path), db=self.db)
            
            # 2. Score
            # 2. Score
            score = self.scorer.score_detection(str(contract_path), detection.primitive, detection.evidence)
            db_id = self.trail.log_detection(str(contract_path), detection)
            
            logger.info("detection_result", file=contract_path.name, primitive=detection.primitive, confidence=score.confidence)
            
            # 3. Check Threshold
            threshold = max(self.min_confidence, audit_plan.min_confidence)
            if score.confidence < threshold:
                logger.info("low_confidence_skip", file=contract_path.name, confidence=score.confidence, threshold=threshold)
                self.sequencer.update_status(contract_path_str, AuditState.COMPLETE, "Low Confidence")
                continue
                
            # 4. Generate
            self.sequencer.update_status(contract_path_str, AuditState.GENERATING, "Templating")
            initial_code = self.generator.generate_handler(str(contract_path), detection.primitive, mapper=mapper)
            
            # 5. Compile & Fix
            self.sequencer.update_status(contract_path_str, AuditState.VERIFYING, "Compiler Loop")
            handler_path = f"{self.output_dir}/{contract_path.stem}_Handler.sol"
            os.makedirs(self.output_dir, exist_ok=True)
            
            final_code, success = self.compiler.generate_with_feedback(str(contract_path), detection.primitive, initial_handler_code=initial_code)
            self.trail.log_generation(detection.primitive, "jinja_template", success)
            
            if success:
                with open(handler_path, 'w') as f:
                    f.write(final_code)
                self.sequencer.update_status(contract_path_str, AuditState.COMPLETE, "Success")
            else:
                self.sequencer.update_status(contract_path_str, AuditState.FAILED, "Compilation Failed")

            results.append({
                'contract': contract_path.name,
                'primitive': detection.primitive,
                'confidence': score.confidence,
                'handler': handler_path if success else None,
                'db_id': db_id
            })
            
        self.trail.save()
        return results

    def _phase_verification(self, results: List[dict]) -> List[dict]:
        logger.info("phase_start", phase="verification")
        
        verified_results = []
        for finding in results:
            if not finding.get('primitive'):
                continue
                
            # Delegate to Moriarty
            verification = self.moriarty.verify_finding({
                "id": finding['contract'],
                "title": f"Invariant Violation in {finding['contract']}",
                "primitive": finding['primitive']
            })
            
            # Update Runtime Dict
            finding['verified'] = verification['verified']
            finding['proof_status'] = verification['status']
            finding['poc_path'] = verification.get('poc_path')
            
            # Persist to DB (Proof is God)
            if finding.get('db_id'):
                self.trail.update_verification(finding['db_id'], {
                    "verified": verification['verified'],
                    "proof_status": verification['status'],
                    "poc_path": verification.get('poc_path')
                })
            
            verified_results.append(finding)
            
        logger.info("verification_complete", verified=len([r for r in verified_results if r['verified']]))
        return verified_results

    def _phase_reporting(self) -> str:
        logger.info("phase_start", phase="reporting")
        reporter = ReportGenerator(self.db, self.run_id)
        report_path = "sherlock/sherlock_output/sherlock_report.md"
        reporter.generate_report(report_path)
        return report_path

    def _phase_review(self, report_path: str, audit_order: List[str], results: List[dict]) -> None:
        logger.info("phase_start", phase="review")
        stats = {
            'coverage_pct': (len(results) / len(audit_order) * 100) if audit_order else 0
        }
        self.mycroft.review_report(report_path, stats)
