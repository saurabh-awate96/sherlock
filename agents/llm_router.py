#!/usr/bin/env python3
"""
LLM Router: Universal AI Interface for the Holmesian Framework
===============================================================

A lightweight, zero-dependency LLM router that provides:
- OpenRouter integration (100+ models with one key)
- Fallback chain support
- Streaming and sync modes  
- CLI and Python API
- Agent-specific personas

Usage:
    # CLI
    python llm_router.py "Analyze this code for vulnerabilities"
    python llm_router.py --model claude-3-opus --persona sherlock "Find bugs"
    
    # Python
    from llm_router import LLM
    llm = LLM()
    response = llm.ask("What vulnerabilities exist here?", persona="sherlock")
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List, Generator
from typing import Optional, Dict, Any, List, Generator,  Union
from dataclasses import dataclass, field
from enum import Enum

# Use urllib to avoid external dependencies
import urllib.request
import urllib.error


# ==============================================================================
# Configuration
# ==============================================================================

# Default model preferences (best for security auditing)
DEFAULT_MODELS = [
    "xiaomi/mimo-v2-flash:free",          # Free, excellent quality
    "anthropic/claude-3-haiku",           # Fast fallback
    "openai/gpt-4o",                      # Alternative
    "google/gemini-pro",                  # Backup
]

# The Constitution of Truth - Enforced on all Personas and Grounded calls
CONSTITUTION = """
## CONSTITUTION OF TRUTH ##
1. You are a GROUNDED engine. You cannot invent facts.
2. ABSOLUTE PROVENANCE: Every claim must cite its source.
3. DISTINGUISH SOURCES: 
   - [OBSERVATION] is the absolute truth (the code/data in front of you).
   - [MIND_PALACE] is historical context (what happened before/patterns).
   - [RESEARCH] is general knowledge (patterns, docs).
4. Do not hallucinate code that is not in [OBSERVATION].
5. If information is missing, explicitly state "MISSING_INFO".
"""

# Agent personas - how each agent should "think"
PERSONAS = {
    "watson": f"""You are Watson, the Perception Engine.
{CONSTITUTION}
Your role is to OBSERVE code with System 2 attention - deliberate, thorough, missing nothing.
Focus on: signals, patterns, anomalies, what's present and what's suspiciously absent.
Be precise and structured. Tag everything you notice.""",

    "sherlock": f"""You are Sherlock, the Deduction Engine.
{CONSTITUTION}
Your role is to apply ABDUCTIVE REASONING - inference to the best explanation.
Given observations, generate hypotheses about what vulnerability could explain them.
Think probabilistically. Consider multiple hypotheses. Rank by likelihood.
"When you have eliminated the impossible, whatever remains must be the truth." """,

    "moriarty": f"""You are Moriarty, the Adversarial Engine.
{CONSTITUTION}
Your role is to THINK LIKE AN ATTACKER. Find the exploit. Break the system.
Apply game theory: What is the dominant strategy? What's the Nash equilibrium?
Generate concrete attack vectors and proof-of-concept exploits.
Be ruthless. Find the weakness.""",

    "mycroft": f"""You are Mycroft, the Synthesis Engine.
{CONSTITUTION}
Your role is STRATEGIC ANALYSIS - see the forest, not just trees.
Correlate findings. Model cascades. Predict 2nd and 3rd order effects.
Apply utilitarian triage: prioritize by (Probability × Impact × Systemic Risk).
Provide strategic recommendations, not just tactical fixes.""",

    "auditor": f"""You are an expert smart contract security auditor.
{CONSTITUTION}
Analyze code for vulnerabilities including but not limited to:
- Reentrancy, flash loan attacks, oracle manipulation
- Access control issues, privilege escalation
- Arithmetic issues, precision loss
- Logic errors, race conditions
- Economic exploits, MEV attacks
Be thorough. Provide severity ratings. Suggest mitigations.""",

    "default": f"""You are a helpful AI assistant specialized in smart contract security.
{CONSTITUTION}
Provide clear, accurate, and actionable responses."""
}


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ContextBlock:
    """A distinct block of context with strict provenance."""
    source_type: str  # OBSERVATION, MIND_PALACE, RESEARCH, RULES
    content: str
    provenance: str   # File path, memory ID, URL, etc.
    can_cite: bool = True

    def to_xml(self) -> str:
        return f"""
<{self.source_type} id="{self.provenance}">
{self.content}
</{self.source_type}>"""


@dataclass
class GroundedContext:
    """Immutable context wrapper for LLM calls."""
    observation: ContextBlock                # The undeniable truth (code, logs)
    mind_palace: List[ContextBlock] = field(default_factory=list) # Relevant memories
    research: List[ContextBlock] = field(default_factory=list)    # External knowledge
    constraints: List[str] = field(default_factory=list)          # specific constraints

    def to_prompt_section(self) -> str:
        sections = []
        
        # 1. Mind Palace (Historical)
        if self.mind_palace:
            sections.append("<MIND_PALACE_ARCHIVE>")
            for b in self.mind_palace:
                sections.append(b.to_xml())
            sections.append("</MIND_PALACE_ARCHIVE>\n")

        # 2. Research (External)
        if self.research:
            sections.append("<RESEARCH_LIBRARY>")
            for b in self.research:
                sections.append(b.to_xml())
            sections.append("</RESEARCH_LIBRARY>\n")

        # 3. Observation (Immediate Truth)
        sections.append("<CURRENT_OBSERVATION>")
        sections.append(self.observation.to_xml())
        sections.append("</CURRENT_OBSERVATION>\n")

        # 4. Constraints
        if self.constraints:
            sections.append("<CONSTRAINTS>")
            for c in self.constraints:
                sections.append(f"- {c}")
            sections.append("</CONSTRAINTS>\n")
            
        return "\n".join(sections)

class Provider(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    provider: Provider
    usage: Dict[str, int]
    raw: Dict[str, Any]
    
    def __str__(self) -> str:
        return self.content


@dataclass  
class LLMConfig:
    """Configuration for LLM calls."""
    model: str = "xiaomi/mimo-v2-flash:free"
    temperature: float = 0.3
    max_tokens: int = 1000
    provider: Provider = Provider.OPENROUTER
    api_key: Optional[str] = None
    timeout: int = 120


# ==============================================================================
# LLM Router Core
# ==============================================================================

class LLM:
    """
    Universal LLM Router.
    
    Provides a simple interface to multiple LLM providers with:
    - Automatic API key detection from environment
    - Fallback chains
    - Agent personas
    - Both sync and streaming modes
    """
    
    ENDPOINTS = {
        Provider.OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
        Provider.OPENAI: "https://api.openai.com/v1/chat/completions",
        Provider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
    }
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM router."""
        self.config = config or LLMConfig()
        self._load_api_keys()
        
    def _load_api_keys(self):
        """Load API keys from environment."""
        self.api_keys = {
            Provider.OPENROUTER: os.getenv("OPENROUTER_API_KEY"),
            Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
            Provider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
        }
        
        # Use config key if provided
        if self.config.api_key:
            self.api_keys[self.config.provider] = self.config.api_key
    
    def ask(
        self,
        prompt: str,
        persona: str = "default",
        model: Optional[str] = None,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Ask the LLM a question.
        
        Args:
            prompt: The user's question/request
            persona: Agent persona to use (watson, sherlock, moriarty, mycroft, auditor)
            model: Override default model
            context: Additional context to prepend
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLMResponse with the AI's response
        """
        # Build system message from persona
        system_msg = PERSONAS.get(persona, PERSONAS["default"])
        
        # Add context if provided
        if context:
            system_msg += f"\n\nContext:\n{context}"
        
        # Build messages
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        
        # Make the call
        return self._call(
            messages=messages,
            model=model or self.config.model,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens
        )

    def ask_grounded(
        self,
        question: str,
        context: GroundedContext,
        persona: str = "default",
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Ask the LLM a question with strict grounding enforcement.
        
        Args:
            question: The specific query
            context: The GroundedContext object containing provenanced data
            persona: Agent persona
            
        Returns:
            LLMResponse
        """
        # Construct the grounded prompt
        prompt = f"""
{context.to_prompt_section()}

TASK:
{question}

REMINDER:
- You must cite your sources.
- Do not invent code/facts not present in <CURRENT_OBSERVATION>.
- Use the provided Mind Palace memories as context, but prioritize Observation if they conflict.
"""
        return self.ask(prompt, persona=persona, model=model)

    def _verify_citations(self, response: str, context: GroundedContext) -> bool:
        """
        Stub for citation verification.
        In future: check if cited line numbers/definitions actually exist in context.observation.
        """
        # TODO: Implement strict regex checks here
        return True
    
    def analyze_code(
        self,
        code: str,
        focus: Optional[str] = None,
        persona: str = "auditor"
    ) -> LLMResponse:
        """
        Analyze code for security issues.
        
        Args:
            code: The code to analyze
            focus: Specific vulnerability type to focus on
            persona: Which persona to use
            
        Returns:
            Analysis response
        """
        if focus:
            prompt_q = f"Analyze for security vulnerabilities. Focus specifically on: {focus}"
        else:
            prompt_q = "Analyze this code for security vulnerabilities."

        ctx = GroundedContext(
            observation=ContextBlock("OBSERVATION", code, "target_code"),
            constraints=["Cite line numbers for every finding", "Rate severity (High/Medium/Low)"]
        )
        
        return self.ask_grounded(prompt_q, ctx, persona=persona)
    
    def generate_exploit(
        self,
        vulnerability: str,
        context: str,
        target: str
    ) -> LLMResponse:
        """
        Generate a proof-of-concept exploit.
        
        Args:
            vulnerability: Description of the vulnerability
            context: Code context
            target: Target function/contract
            
        Returns:
            Exploit PoC
        """
        prompt = f"""Generate a Foundry proof-of-concept exploit for this vulnerability:

Vulnerability: {vulnerability}
Target: {target}

Context:
```solidity
{context}
```

Provide:
1. Complete Foundry test file
2. Attack contract if needed
3. Step-by-step explanation
4. Expected outcome"""
        
        
        # Create grounded context
        ctx = GroundedContext(
            observation=ContextBlock(
                source_type="OBSERVATION", 
                content=context, 
                provenance="local_file"
            ),
            constraints=["Output must be a self-contained Foundry test"]
        )
        
        # Use grounded ask logic
        return self.ask_grounded(
             question=f"Generate a Foundry proof-of-concept exploit for: {vulnerability}\nTarget: {target}",
             context=ctx,
             persona="moriarty"
        )
    
    def classify_project(self, file_list: List[str], readme: Optional[str] = None) -> LLMResponse:
        """
        Classify a project type and determine audit scope.
        
        Args:
            file_list: List of files in the project
            readme: README content if available
            
        Returns:
            Project classification
        """
        prompt = f"""Analyze this project structure and determine:
1. Project type (Foundry, Hardhat, Brownie, raw Solidity)
2. Main contracts to audit
3. Test coverage presence
4. Recommended audit focus areas

Files:
{chr(10).join(file_list[:50])}

{"README:" + chr(10) + readme[:2000] if readme else ""}

Respond in JSON format:
{{
    "project_type": "foundry|hardhat|brownie|raw",
    "build_command": "forge build|npx hardhat compile|...",
    "main_contracts": ["Contract1.sol", ...],
    "scope_pattern": "src/*.sol|contracts/*.sol|...",
    "focus_areas": ["reentrancy", "access control", ...],
    "complexity": "low|medium|high"
}}"""
        
        return self.ask(prompt, persona="mycroft")
    
    def _call(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Make the actual API call."""
        provider = self.config.provider
        api_key = self.api_keys.get(provider)
        
        if not api_key:
            raise ValueError(f"No API key found for {provider.value}. Set OPENROUTER_API_KEY environment variable.")
        
        endpoint = self.ENDPOINTS[provider]
        
        # Build request body
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add provider-specific headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        if provider == Provider.OPENROUTER:
            headers["HTTP-Referer"] = "https://github.com/sherlock-audit"
            headers["X-Title"] = "Holmesian Audit Framework"
        
        # Make request
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"LLM API error ({e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")
        
        # Parse response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = result.get("usage", {})
        
        return LLMResponse(
            content=content,
            model=result.get("model", model),
            provider=provider,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            raw=result
        )
    
    def with_fallback(self, models: Optional[List[str]] = None) -> "LLMWithFallback":
        """Create an LLM instance with fallback chain."""
        return LLMWithFallback(self, models or DEFAULT_MODELS)


class LLMWithFallback:
    """LLM wrapper with automatic fallback on failures."""
    
    def __init__(self, llm: LLM, models: List[str]):
        self.llm = llm
        self.models = models
    
    def ask(self, prompt: str, **kwargs) -> LLMResponse:
        """Try each model in the fallback chain until one succeeds."""
        last_error = None
        
        for model in self.models:
            try:
                return self.llm.ask(prompt, model=model, **kwargs)
            except Exception as e:
                last_error = e
                print(f"[LLM] Model {model} failed: {e}, trying next...")
                continue
        
        raise RuntimeError(f"All models failed. Last error: {last_error}")


# ==============================================================================
# CLI Interface
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LLM Router - Universal AI interface for Holmesian Framework"
    )
    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--model", "-m", default="xiaomi/mimo-v2-flash:free",
                       help="Model to use (default: xiaomi/mimo-v2-flash:free)")
    parser.add_argument("--persona", "-p", default="default",
                       choices=["watson", "sherlock", "moriarty", "mycroft", "auditor", "default"],
                       help="Agent persona to use")
    parser.add_argument("--temperature", "-t", type=float, default=0.3,
                       help="Temperature (0-1)")
    parser.add_argument("--max-tokens", type=int, default=1000,
                       help="Maximum tokens in response")
    parser.add_argument("--file", "-f", help="Read prompt from file")
    parser.add_argument("--code", "-c", help="Analyze code file for vulnerabilities")
    parser.add_argument("--json", "-j", action="store_true",
                       help="Output raw JSON response")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Only output the response content")
    
    args = parser.parse_args()
    
    # Determine prompt source
    if args.code:
        with open(args.code, 'r') as f:
            code = f.read()
        prompt = f"Analyze this code for vulnerabilities:\n\n```\n{code}\n```"
    elif args.file:
        with open(args.file, 'r') as f:
            prompt = f.read()
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    # Initialize LLM
    config = LLMConfig(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    llm = LLM(config)
    
    try:
        if not args.quiet:
            print(f"[LLM] Model: {args.model} | Persona: {args.persona}", file=sys.stderr)
        
        response = llm.ask(prompt, persona=args.persona)
        
        if args.json:
            print(json.dumps({
                "content": response.content,
                "model": response.model,
                "usage": response.usage
            }, indent=2))
        else:
            print(response.content)
            
        if not args.quiet:
            print(f"\n[LLM] Tokens: {response.usage.get('total_tokens', 'N/A')}", file=sys.stderr)
            
    except Exception as e:
        print(f"[LLM] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
