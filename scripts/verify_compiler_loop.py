import os
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sherlock.core.compiler_loop import CompilationLoop
from sherlock.core.config_loader import ConfigLoader


def main():
    print("--- Verifying Compiler Loop ---")

    loader = ConfigLoader('sherlock/audit_config.yaml')
    loop = CompilationLoop(loader)

    # Broken contract
    broken_code = """
    pragma solidity ^0.8.0;
    contract Broken {
        unit256 public x; // Typo: unit256 instead of uint256
    }
    """

    print("Input: Broken Code (unit256 typo)")

    # We expect this to fail compilation, then the mock LLM will 'fix' it
    # (The mock LLM returns a generic FixedHandler, but that's enough to prove the loop works)

    final_code, success = loop.generate_with_feedback("dummy_path", "Vault", initial_handler_code=broken_code)

    if success:
        print("\n[PASS] Loop successfully 'fixed' the code.")
        print("Final Code Snippet:")
        print(final_code[:100] + "..." if len(final_code) > 100 else final_code)
    else:
        print("\n[FAIL] Loop failed to produce compiling code.")
        sys.exit(1)

if __name__ == "__main__":
    main()
