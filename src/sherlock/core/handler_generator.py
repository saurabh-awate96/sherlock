import os

from jinja2 import Environment, FileSystemLoader, select_autoescape


class HandlerGenerator:
    """
    Generates initial Solidity handlers using Jinja2 templates.
    """

    def __init__(self, config_loader):
        self.config = config_loader
        # Robust template path resolution
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(base_path, "templates")
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape()
        )

    def generate_handler(self, contract_path: str, primitive_type: str, mapper=None) -> str:
        """
        Generate handler code for a specific contract and primitive.
        Now supports Scoped Context (Dependencies).
        """
        # Get primitive config to find template name
        try:
            prim_config = self.config.get_primitive_config(primitive_type.lower())
            template_path = prim_config.get('handler_template')
            if not template_path:
                print(f"[Generator] No template defined for {primitive_type}")
                return "// No template found"

            # Extract template filename
            template_name = os.path.basename(template_path)

            # Load template
            template = self.env.get_template(template_name)

            # Prepare context
            contract_name = os.path.splitext(os.path.basename(contract_path))[0]

            # SCOPE ENHANCEMENT: Fetch Imports
            imports_content = ""
            if mapper:
                dependencies = mapper.get_direct_dependencies(contract_path)
                if dependencies:
                    imports_content = "\n// --- Dependency Context ---\n"
                    for dep in dependencies:
                        # For now, we simple-read the file.
                        # Ideally, we'd extract just the interface/ABI.
                        # But for "Grounding", reading the file ensures we know what we can call.
                        try:
                            fname = os.path.basename(dep)
                            imports_content += f"// Import: {fname}\n"
                            # We don't inline the full content as it might be too large and `forge` handles imports.
                            # But we might want to expose it to the LLM if we were using `llm.generate`.
                            # Since we are using Jinja2 here, we just pass the names for now.
                        except:
                            pass

            # Render
            return template.render(
                contract={
                    "name": contract_name,
                    "path": contract_path
                },
                contract_name=contract_name, # Legacy support
                contract_path=contract_path, # Legacy support
                primitive=primitive_type,
                dependency_context=imports_content
            )

        except Exception as e:
            print(f"[Generator] Error generating handler: {e}")
            return f"// Error generating handler: {e}"
