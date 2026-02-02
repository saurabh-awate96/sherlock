import os
import re
import subprocess
import uuid
from dataclasses import dataclass

from .llm_interface import LLMInterface


@dataclass
class CompileResult:
    success: bool
    error: str | None
    output: str | None

class CompilationLoop:
    def __init__(self, config_loader, llm_interface=None, db=None):
        self.config = config_loader.get_runtime_config()
        self.max_retries = self.config.get('max_compilation_retries', 3)
        self.timeout = self.config.get('compilation_timeout_seconds', 30)
        self.foundry_path = self.config.get('foundry_path', 'forge')
        self.db = db

        if llm_interface:
            self.llm = llm_interface
        else:
            self.llm = LLMInterface(config_loader)

    def generate_with_feedback(self, contract_path, primitive_type, initial_handler_code=None):
        """
        Generate handler, try to compile, fix errors, repeat
        If initial_handler_code is provided, starts from Step 2.
        """
        handler_code = initial_handler_code

        # If no initial code, we would generate it here (but HandlerGenerator usually does that)
        # For this loop, we assume we get the drafted code or we generate it if missing
        if not handler_code:
            # TODO: Call HandlerGenerator (circular dependency if not careful)
            # For now, return error or mock
            return None, False

        print(f"[CompilerLoop] Starting feedback loop for {primitive_type} (Max retries: {self.max_retries})")

        for attempt in range(self.max_retries + 1):
            print(f"  -> Attempt {attempt+1}/{self.max_retries+1}...", end=" ", flush=True)

            # Step 2: Try to compile
            result = self.try_compile(handler_code)

            if result.success:
                print("SUCCESS ✓")

                # Learn from success if we had previous errors
                if attempt > 0 and hasattr(self, 'db') and self.db and last_error:
                    print("     [Smart] Learning from this fix...")
                    # Store the fix that solved 'last_error'
                    #Ideally we store the DIFF or the explanation.
                    # For now we store the entire code as the "fix strategy" (naive RAG)
                    self.db.learn_fix(last_error, handler_code)

                return handler_code, True

            print("FAILED ✗")
            last_error = result.error # Capture for learning next turn

            # Step 3: Fix based on error
            if attempt < self.max_retries:
                print(f"     Fixing error: {result.error[:100].replace(chr(10), ' ')}...")
                handler_code = self.fix_compilation_error(handler_code, result.error)
            else:
                 print("     Max retries reached. Giving up.")

        return handler_code, False

    def try_compile(self, handler_code: str) -> CompileResult:
        """
        Actually run forge build and capture the error
        """
        # Write handler to temp file
        # We need to put it in a place where forge can find it and imports work
        # Usually inside `test/handlers` or similar, but for temp check we can use a temp file
        # IF imports are absolute or remapped correctly.

        # Assumption: We are in the workspace root.
        # We'll create a temporary file in `test/temp/` to ensure remappings work if they are standard.
        temp_dir = "test/temp"
        os.makedirs(temp_dir, exist_ok=True)

        filename = f"Handler_{uuid.uuid4().hex[:8]}.sol"
        temp_path = os.path.join(temp_dir, filename)

        with open(temp_path, 'w') as f:
            f.write(handler_code)

        try:
            # Run forge build
            # We target ONLY this file to be fast
            cmd = [self.foundry_path, 'build', '--contracts', temp_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                text=True
            )

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            is_success = (result.returncode == 0)
            return CompileResult(
                success=is_success,
                error=result.stderr if not is_success else None,
                output=result.stdout
            )

        except subprocess.TimeoutExpired:
             if os.path.exists(temp_path):
                os.remove(temp_path)
             return CompileResult(success=False, error="Compilation Timed Out", output="")
        except Exception as e:
             if os.path.exists(temp_path):
                os.remove(temp_path)
             return CompileResult(success=False, error=str(e), output="")

    def fix_compilation_error(self, handler, error):
        """
        Ask LLM to fix the error, OR use Knowledge Base if available.
        """
        # Try Knowledge Base first (RAG)
        if hasattr(self, 'db') and self.db:
            known_fix = self.db.get_known_fix(error)
            if known_fix:
                print("     [Smart] Found known fix in Knowledge Base!")
                # For now, we assume the 'fix' is a generic strategy or replacement pattern
                # But to keep it simple, if we stored the *entire* fixed code, we can't reuse it easily for different contracts.
                # ideally 'known_fix' is a diff or a specific instruction.
                # However, the recipe implies we store "successful error fixes".
                # Let's try to prompt the LLM *with* the known fix strategy if available,
                # OR if the fix is exact code (unlikely unique), we return it.

                # Better approach for RAG: "I saw this error before, the fix was to <Change X to Y>"
                # Since we store the raw LLM output in `learn_fix`, and LLM output is full code...
                # We actually can't reuse full code directly unless it's identical context.
                # So we will store the *Diff* or *Explanation* in a real system.

                # For this prototype: We will just log that we found it, but still ask LLM
                # potentially passing the "known strategy" to guide it.
                pass

        fix_prompt = f"""
The following Solidity handler failed to compile:

```solidity
{handler}
```

Compiler error:
```
{error}
```

Fix the code. Return ONLY the corrected Solidity code, no explanation.
Do not wrap in markdown blocks, just the code.
"""
        response = self.llm.generate(fix_prompt, temperature=0.2)

        # Clean up response if it has markdown blocks
        cleaned = self._clean_llm_response(response)

        # Learn from this (Optimistic learning: we assume it works,
        # but real learning happens if the caller confirms success.
        # The caller (generate_with_feedback) knows if it worked.
        # So we should probably move the learning step to the loop.)
        return cleaned

    def _clean_llm_response(self, text):
        # Remove ```solidity ... ```
        pattern = r"```(?:solidity)?\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
