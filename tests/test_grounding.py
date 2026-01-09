import sys
import os
from dataclasses import dataclass

# Add parent dir to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.llm_router import LLM, GroundedContext, ContextBlock, LLMResponse, Provider
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

# Mock Response to avoid network calls
@dataclass
class MockResponse:
    content: str
    model: str = "mock"
    provider: Provider = Provider.LOCAL
    usage: dict = None
    raw: dict = None

class MockLLM(LLM):
    def __init__(self):
        super().__init__()
        # Bypass API key check for mock
        self.api_keys = {Provider.OPENROUTER: "mock_key"}

    def _call(self, messages, model, temperature, max_tokens):
        # Return the Full Prompt (System + User) for inspection
        full_text = "\n=== SYSTEM ===\n" + messages[0]['content'] + "\n=== USER ===\n" + messages[1]['content']
        return MockResponse(content=full_text, usage={})

def test_grounding_structure():
    print("initializing MockLLM...")
    llm = MockLLM()
    
    print("Creating Context...")
    ctx = GroundedContext(
        observation=ContextBlock("OBSERVATION", "function transfer() { ... }", "Contract.sol"),
        mind_palace=[ContextBlock("MIND_PALACE", "Transfer functions often have reentrancy", "mem_123")],
        research=[ContextBlock("RESEARCH", "ERC20 standard requires...", "erc20_spec")],
        constraints=["Output JSON only"]
    )
    
    print("Calling ask_grounded...")
    # Using 'sherlock' persona to check if Constitution is injected
    response = llm.ask_grounded("Analyze vulnerabilities", ctx, persona="sherlock")
    prompt = response.content
    
    print("\n--- Verifying Prompt Components ---")
    
    # Check 1: Context Sections
    if "<CURRENT_OBSERVATION>" in prompt and 'id="Contract.sol"' in prompt:
        print("✅ Observation Block Present")
    else:
        print("❌ Observation Block Missing")
        
    if "<MIND_PALACE_ARCHIVE>" in prompt and 'id="mem_123"' in prompt:
        print("✅ Mind Palace Block Present")
    else:
        print("❌ Mind Palace Block Missing")

    if "<RESEARCH_LIBRARY>" in prompt:
        print("✅ Research Block Present")
    else:
        print("❌ Research Block Missing")

    # Check 2: Constitution in System Prompt
    if "CONSTITUTION OF TRUTH" in prompt:
        print("✅ Constitution Present in System Prompt")
    else:
        print("❌ Constitution Missing from System Prompt")
        
    # Check 3: Task formatted correctly
    if "TASK:" in prompt and "Analyze vulnerabilities" in prompt:
        print("✅ Task Prompts Correctly")
    else:
        print("❌ Task Formatting Incorrect")

if __name__ == "__main__":
    test_grounding_structure()
