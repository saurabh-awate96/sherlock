import os

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

class LLMInterface:
    def __init__(self, config):
        self.config = config.get_llm_config()
        self.model = self.config.get('model', 'claude-3-sonnet-20240229')
        self.system_prompt = self.config.get('system_prompt', '')

        self.client = None
        self.provider = None

        if "claude" in self.model and anthropic:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.provider = "anthropic"
        elif "gpt" in self.model and openai:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                self.provider = "openai"

    def generate(self, prompt, temperature=None):
        if not temperature:
            temperature = self.config.get('temperature', 0.1)

        full_system_prompt = self.system_prompt

        if self.provider == "anthropic":
            return self._call_anthropic(prompt, temperature, full_system_prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt, temperature, full_system_prompt)
        else:
            return self._mock_call(prompt)

    def _call_anthropic(self, prompt, temperature, system_prompt):
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"[LLM Error] Anthropic call failed: {e}")
            return self._mock_call(prompt)

    def _call_openai(self, prompt, temperature, system_prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
             print(f"[LLM Error] OpenAI call failed: {e}")
             return self._mock_call(prompt)

    def _mock_call(self, prompt):
        print(f"[[MOCK LLM CALL]] Prompt length: {len(prompt)}")
        print(">> No API Key or Client available. Returning dummy response.")

        # Determine strictness of return based on prompt content
        if "Return ONLY the corrected Solidity code" in prompt:
            return "// Fixed Solidity Code based on mock logic\ncontract FixedHandler {}"
        return "I am a mock LLM. Please set ANTHROPIC_API_KEY or install the library."
