import structlog
from pathlib import Path
from typing import List, Dict, Any
import json
from sherlock.core.llm_interface import LLMInterface
from sherlock.core.config_loader import ConfigLoader

logger = structlog.get_logger()

class InspectorAgent:
    """
    The Inspector Agent (Deep Context Builder).
    Enables ultra-granular, line-by-line code analysis to build deep architectural context.
    Follows audit-context-building skill protocols: First Principles, 5 Whys, 5 Hows.
    """

    def __init__(self, db=None, run_id=None):
        self.db = db
        self.run_id = run_id
        try:
            self.llm = LLMInterface(ConfigLoader())
        except Exception as e:
            logger.warning("inspector_llm_init_failed", error=str(e))
            self.llm = None

    def analyze_file(self, file_path: str):
        """
        Performs ultra-granular analysis of a single file.
        """
        logger.info("inspector_analyzing_file", file=file_path)
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # 1. Orientation Scan (Phase 1)
            # 2. Function Decomposition
            blocks = self._decompose_into_blocks(content)
            
            for block in blocks:
                self._micro_analyze_block(file_path, block)
                
        except Exception as e:
            logger.error("inspector_file_analysis_failed", file=file_path, error=str(e))

    def _decompose_into_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Simple logic to split into functions/contracts.
        In a real scenario, this would use a proper parser (e.g. solc or tree-sitter).
        For now, we use regex as a placeholder.
        """
        blocks = []
        # Basic heuristic for block splitting
        lines = content.splitlines()
        current_block = []
        start_line = 1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Solidity & Python support
            if any(stripped.startswith(kw) for kw in ["function", "contract", "def ", "class "]):
                if current_block:
                    blocks.append({
                        "name": "Block_" + str(len(blocks)), 
                        "content": "\n".join(current_block),
                        "lines": f"{start_line}-{i}"
                    })
                current_block = [line]
                start_line = i + 1
            else:
                current_block.append(line)
        
        if current_block:
            blocks.append({
                "name": "Final_Block", 
                "content": "\n".join(current_block),
                "lines": f"{start_line}-{len(lines)}"
            })
            
        return blocks

    def analyze_code_location(self, location: Dict[str, Any]):
        """
        Analyzes a specific code location from the database.
        Used for targeted Deep Context Building on key vulnerabilities.
        """
        file_path = location.get('path', 'unknown')
        block = {
            'name': location.get('function_name', 'snippet'),
            'lines': f"{location.get('start_line')}-{location.get('end_line')}",
            'content': location.get('snippet', '')
        }
        logger.info("inspector_analyzing_location", file=file_path, block=block['name'])
        self._micro_analyze_block(file_path, block, context_type="db_location")

    def _micro_analyze_block(self, file_path: str, block: Dict[str, Any], context_type: str = "raw_file"):
        """
        Implements the Ultra-Granular Function Analysis (Phase 2).
        Uses First Principles, 5 Whys, and 5 Hows.
        """
        if not self.llm:
            return

        prompt = f"""
### Deep Context Builder Protocol (audit-context-building)
Analyze the following code block from {file_path}. 
Perform ultra-granular analysis using:
1. **First Principles**: What are the fundamental truths here?
2. **5 Whys**: Why is this logic structured this way? (Drill down 5 levels)
3. **5 Hows**: How does this impact the state/invariants?

CODE BLOCK (Lines {block.get('lines', 'N/A')}):
```
{block.get('content', '')}
```

OUTPUT FORMAT (JSON):
{{
  "purpose": "2-3 sentences max",
  "invariants": ["list of explicit invariants"],
  "assumptions": ["list of trust assumptions"],
  "risks": ["list of risk considerations"],
  "micro_analysis": "Detailed 5-Whys analysis and architectural implications."
}}
"""
        try:
            response = self.llm.generate(prompt)
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                insight = json.loads(response[start:end])
                insight['file_path'] = file_path
                insight['block_name'] = block.get('name', 'Unknown')
                insight['line_range'] = block.get('lines', '0-0')
                
                if self.db:
                    self.db.log_granular_insight(self.run_id, insight)
                    logger.info("inspector_insight_logged", block=block.get('name'))
                    
        except Exception as e:
            logger.warning("inspector_block_analysis_failed", block=block.get('name'), error=str(e))
