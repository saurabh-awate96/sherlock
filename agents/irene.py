#!/usr/bin/env python3
"""
Irene Adler Agent: The Research Engine
=====================================================

"To Sherlock Holmes she is always THE woman."
- A Scandal in Bohemia

This agent implements a "Deep Research" loop:
1.  **Formulate**: Generates specific, targeted questions about the target.
2.  **Investigate**: Uses external tools (Web Search, Doc Retrieval) or LLM internal knowledge.
3.  **Synthesize**: Aggregates findings into the ResearchContext.
4.  **Refine**: Iterates deeper based on missing information.

It goes beyond passive "Context Loading" to active "Knowledge Hunting".
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import simplified framework components
try:
    from llm_router import LLM, GroundedContext, ContextBlock
    from leann_palace import LEANNMindPalace, Room, MemoryType
except ImportError:
    # Standalone support
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.llm_router import LLM, GroundedContext, ContextBlock
    from agents.leann_palace import LEANNMindPalace, Room, MemoryType

# ==============================================================================
# Tools & Capabilities
# ==============================================================================

class SearchProvider(Enum):
    SERPER = "serper"
    TAVILY = "tavily"
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo" # simulated/html
    LLM_KNOWLEDGE = "llm_knowledge"

class SearchTool:
    """
    Abstraction for Web Search. 
    Tries to use real APIs if keys verify, otherwise falls back to LLM Knowledge.
    """
    
    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.provider = self._detect_provider()
        print(f"[Irene] Search Provider: {self.provider.value}")

    def _detect_provider(self) -> SearchProvider:
        if os.getenv("SERPER_API_KEY"):
            return SearchProvider.SERPER
        if os.getenv("TAVILY_API_KEY"):
            return SearchProvider.TAVILY
        return SearchProvider.LLM_KNOWLEDGE

    def search(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Perform a search."""
        print(f"[Irene] Searching: '{query}' via {self.provider.value}...")
        
        try:
            if self.provider == SearchProvider.SERPER:
                return self._search_serper(query, n_results)
            elif self.provider == SearchProvider.TAVILY:
                return self._search_tavily(query, n_results)
            else:
                return self._search_llm(query, n_results)
        except Exception as e:
            print(f"[Irene] Search failed ({e}), falling back to LLM.")
            return self._search_llm(query, n_results)

    def _search_serper(self, query: str, n: int) -> List[Dict[str, str]]:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": n})
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY", ""),
            'Content-Type': 'application/json'
        }
        
        req = urllib.request.Request(url, data=payload.encode(), headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "serper"
            })
        return results

    def _search_tavily(self, query: str, n: int) -> List[Dict[str, str]]:
        # Simplified Tavily implementation
        url = "https://api.tavily.com/search"
        payload = json.dumps({"query": query, "max_results": n})
        headers = {
            'Authorization': f"Bearer {os.getenv('TAVILY_API_KEY', '')}",
            'Content-Type': 'application/json'
        }
        req = urllib.request.Request(url, data=payload.encode(), headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            
        return [{
            "title": r.get("title", ""),
            "link": r.get("url", ""),
            "snippet": r.get("content", ""),
            "source": "tavily"
        } for r in data.get("results", [])]

    def _search_llm(self, query: str, n: int = 3) -> List[Dict[str, str]]:
        """Simulate search using LLM's internal knowledge base."""
        if not self.llm:
            return [{"title": "No Search Capability", "snippet": "Search unavailable.", "link": "#"}]
            
        prompt = f"""
        You are acting as a Search Engine.
        Query: "{query}"
        
        Provide {n} search results based on your training data.
        Format as JSON list of objects with 'title', 'link' (can be dummy), and 'snippet'.
        Real facts only. If unknown, return empty list.
        """
        
        response = self.llm.ask(prompt, persona="default", temperature=0.1, model="google/gemini-2.0-flash-exp:free") # Use a smart model
        
        try:
            # Clean for JSON parsing
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    item["source"] = "llm_knowledge"
                return data
        except:
            pass
            
        return [{"title": "LLM Knowledge", "snippet": response.content[:200], "link": "#", "source": "llm"}]

# ==============================================================================
# Irene Adler Agent
# ==============================================================================

@dataclass
class Finding:
    topic: str
    content: str
    source: str
    confidence: float

class Irene:
    """
    Irene Adler: The Research Engine.
    "To Sherlock Holmes she is always THE woman."

    Attributes:
        Formulate -> Investigate -> Synthesize -> Refine
    """
    
    def __init__(self):
        self.llm = LLM()
        self.search_tool = SearchTool(self.llm)
        try:
            self.palace = LEANNMindPalace()
        except:
            self.palace = None
            
        print("[Irene] 'I have known him for some years. I can tell you all about him.'")

    def research(self, intent: str, scope: str, depth: int = 2) -> Dict[str, Any]:
        """
        Execute the Deep Research Loop.
        
        Args:
            intent: What we want to know
            scope: The target codebase/project
            depth: How many recursive iterations
            
        Returns:
            Structured Research Context
        """
        print(f"\n[Irene] Beginning research on: {intent}")
        print(f"[Irene] Scope: {scope}")
        
        # 1. Initial Plan
        plan = self._formulate_plan(intent, scope)
        print(f"[Irene] Plan: {len(plan)} questions to investigate.")
        
        gathered_findings: List[Finding] = []
        
        # 2. Execution Loop
        for i, question in enumerate(plan):
            print(f"[Irene] Investigating Q{i+1}: {question}")
            findings = self._investigate(question, scope)
            gathered_findings.extend(findings)
            
            # Refine plan if needed (simple depth control)
            if depth > 1 and i == len(plan) - 1:
                pass 
                
        # 3. Synthesis
        synthesized = self._synthesize(intent, gathered_findings)
        
        # 4. Storage
        if self.palace:
            self._store_findings(synthesized)
            
        return synthesized

    def _formulate_plan(self, intent: str, scope: str) -> List[str]:
        """Ask LLM to break down the research intent into specific search questions."""
        prompt = f"""
        Research Intent: {intent}
        target Scope: {scope}
        
        Break this down into 3-5 specific, search-engine-friendly questions or investigation steps.
        Focus on:
        1. Official documentation/specs.
        2. Known vulnerabilities for this pattern/protocol type.
        3. Historical hacks of similar systems.
        
        Return ONLY a JSON list of strings.
        """
        response = self.llm.ask(prompt, persona="sherlock")
        try:
            return json.loads(response.content.replace("```json", "").replace("```", "").strip())
        except:
            return [intent] # Fallback

    def _investigate(self, question: str, scope: str) -> List[Finding]:
        """Execute investigation for a single question."""
        findings = []
        
        # A. Web Search / Knowledge Retrieval
        search_results = self.search_tool.search(f"{question} {scope}")
        
        # Contextualize results
        context_str = "\n".join([f"- [{r['title']}]({r['link']}): {r['snippet']}" for r in search_results])
        
        # B. Analyze results with LLM to extract facts
        analysis_prompt = f"""
        Question: {question}
        Search Results:
        {context_str}
        
        Extract the key facts relevant to smart contract security.
        Ignore marketing fluff.
        If the results are irrelevant, state "NO_INFO".
        """
        analysis = self.llm.ask(analysis_prompt, persona="watson")
        
        if "NO_INFO" not in analysis.content:
            findings.append(Finding(
                topic=question,
                content=analysis.content,
                source="search_synthesis",
                confidence=0.8
            ))
            
        return findings

    def _synthesize(self, intent: str, findings: List[Finding]) -> Dict[str, Any]:
        """Synthesize all findings into a structured context."""
        findings_text = "\n\n".join([f"### {f.topic}\n{f.content}" for f in findings])
        
        prompt = f"""
        Synthesize the detailed research findings into a structured context for an auditor.
        
        Intent: {intent}
        
        Findings:
        {findings_text}
        
        Format as JSON with keys:
        - protocol_summary
        - critical_mechanisms
        - potential_attack_vectors (list)
        - known_exploits (list)
        - audit_focus_areas (list)
        """
        
        try:
            response = self.llm.ask(prompt, persona="mycroft", model="google/gemini-2.0-flash-exp:free")
        except Exception as e:
            print(f"[Irene] LLM synthesis failed: {e}")
            return {
                "protocol_summary": "Research synthesis incomplete (LLM unavailable)",
                "critical_mechanisms": [],
                "potential_attack_vectors": [f.topic for f in findings],
                "known_exploits": [],
                "audit_focus_areas": [f.content[:100] for f in findings[:5]] if findings else [],
                "raw_findings": findings_text,
                "error": str(e)
            }
        
        try:
            clean_json = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except:
            return {
                "protocol_summary": "Research synthesis incomplete (LLM unavailable)",
                "critical_mechanisms": [],
                "potential_attack_vectors": [f.topic for f in findings],
                "known_exploits": [],
                "audit_focus_areas": [f.content[:100] for f in findings[:5]],
                "raw_findings": findings_text
            }

    def _store_findings(self, data: Dict[str, Any]):
        """Store in Mind Palace."""
        try:
            summary = data.get("protocol_summary", "")
            vectors = data.get("potential_attack_vectors", [])
            
            self.palace.encode_research(
                content=f"Research Summary: {summary}",
                source="IreneAdler",
                topic=summary[:50]
            )
            
            for vector in vectors:
                self.palace.encode(
                    content=str(vector),
                    memory_type=MemoryType.VULNERABILITY_PATTERN,
                    room=Room.RESEARCH,
                    association=f"Research: {str(vector)[:30]}"
                )
        except Exception as e:
            print(f"[Irene] Storage error: {e}")

    def manifest(self) -> Dict[str, Any]:
        """Capability manifest for the Module Registry."""
        return {
            "module_id": "irene",
            "module_type": "reconnaissance",
            "version": "1.0.0", 
            "intent_tags": ["research", "investigate", "context", "learn", "study"],
            "tools": [
                {
                    "name": "deep_research",
                    "description": "Perform deep, iterative research on a target using search and LLM synthesis.",
                    "intent_tags": ["research", "deep_dive"],
                    "input_schema": {
                        "intent": "string",
                        "scope": "string"
                    }
                }
            ],
            "cost_profile": {
                "latency": "high", 
                "compute": "high",
                "risk": "low"
            }
        }

# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Irene Adler: The Research Agent")
    parser.add_argument("--action", default="research", choices=["research", "manifest"])
    parser.add_argument("--input", help="Input file or string (Intent)")
    parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    agent = Irene()
    
    if args.action == "manifest":
        print(json.dumps(agent.manifest(), indent=2))
        return

    # For 'research' action
    intent = args.input or "General Security Assessment"
    # We might get 'scope' from a file if input is a file path, or just use it as string
    scope = "Current Project"
    
    # Check if input is a file path (from orchestrator often)
    if args.input and os.path.exists(args.input):
        try:
            with open(args.input, 'r') as f:
                # Orchestrator might pass a JSON with 'intent' and 'scope'
                data = json.load(f)
                intent = data.get("intent", intent)
                scope = data.get("scope", scope)
        except:
            scope = args.input # Treat path as scope
    
    result = agent.research(intent, scope)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
