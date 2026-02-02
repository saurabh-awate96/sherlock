import os

import yaml


class ConfigLoader:
    """
    Loads audit_config.yaml and provides access
    No more juggling 3 files
    """

    def __init__(self, config_path='sherlock/audit_config.yaml'):
        # Allow running from root or sherlock dir
        if not os.path.exists(config_path):
            if os.path.exists(f"../{config_path}"):
                config_path = f"../{config_path}"
            elif os.path.exists("audit_config.yaml"):
                config_path = "audit_config.yaml"

        self.config_path = config_path

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_primitive_config(self, primitive_name):
        return self.config['primitives'][primitive_name]

    def get_all_primitives(self):
        return list(self.config['primitives'].keys())

    def get_llm_config(self):
        return self.config['llm_behavior']

    def get_runtime_config(self):
        return self.config['runtime']

    def generate_skill_md(self, output_path='SKILL.md'):
        """
        Generate SKILL.md from config
        This ensures they never get out of sync
        """
        primitives = self.get_all_primitives()

        skill_content = f"""
# Sherlock Skill Configuration

## Supported Primitives

{self._format_primitives(primitives)}

## Capabilities

{self._format_capabilities()}

## Usage

These primitives are automatically detected by the SemanticDetector.
When a primitive is detected, the corresponding handler template and invariants are used to generate tests.
"""

        with open(output_path, 'w') as f:
            f.write(skill_content)

        print(f"Generated {output_path} from {self.config_path}")

    def _format_primitives(self, primitives):
        lines = []
        for p in primitives:
            config = self.get_primitive_config(p)
            lines.append(f"### {p.title()}")
            lines.append(f"{config['description']}")
            lines.append("")
            lines.append("**Invariants:**")
            for inv in config['invariants']:
                lines.append(f"- **{inv['name']}**: {inv['description']}")
                lines.append(f"  - Code: `{inv['code']}`")
            lines.append("")
        return "\n".join(lines)

    def _format_capabilities(self):
        return self.config['llm_behavior']['system_prompt']

if __name__ == "__main__":
    # Test generation
    loader = ConfigLoader()
    loader.generate_skill_md()
